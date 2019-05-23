#!/bin/sh

set -e

# Ideally, want to do the following:
# tar cf - tweets | lz4 - tarchive/archive_today.tar.lz4 && rm -rf tweets/*
# However, there's some problems with that:
# - Don't touch tweets/.gitignore
# - File that appear after tar could get them and before rm runs would get lost
# - tar doesn't like files whose content changes
# So I had to write this abomination.

DIRNAME="tweets/"
TARBASENAME="tarchives/archive_$(date "+%Y%m%d_%H%M%S")"
FILE_TAR="${TARBASENAME}.tar"
FILE_TARLZ4="${TARBASENAME}.tar.lz4"
FILELIST="$(mktemp)"

# This cements the file selection:
find "${DIRNAME}" -name '*.json' -print0 > "${FILELIST}"

# The following `xargs` invocation may cause `tar` to be run multiple times,
# so be compatible with that.
if tar cf "${FILE_TAR}" -T /dev/null
then
    true # pass
else
    EXITCODE=$?
    echo "Creation failed, cleaning up tar file and filelist." >&2
    rm -f "${FILE_TAR}" "${FILELIST}"
    exit "$EXITCODE"
fi

sleep 1 # Hopefully(!) finish writing files.

if xargs -0 -a "${FILELIST}" -r tar rf "${FILE_TAR}"
then
    true # pass
else
    EXITCODE=$?
    echo "Adding failed, cleaning up tar file and filelist." >&2
    rm -f "${FILE_TAR}" "${FILELIST}"
    exit "$EXITCODE"
fi

if tar tf "${FILE_TAR}" | xargs -r rm
then
    true # pass
else
    EXITCODE=$?
    echo "Removal failed, *NOT* cleaning up anything.  Filelist at ${FILELIST}." >&2
    exit "$EXITCODE"
fi

if lz4 -q "${FILE_TAR}" "${FILE_TARLZ4}"
then
    true # pass
else
    EXITCODE=$?
    echo "Recompression failed, *NOT* cleaning up anything.  Filelist at ${FILELIST}." >&2
    exit "$EXITCODE"
fi

rm -f "${FILE_TAR}"

