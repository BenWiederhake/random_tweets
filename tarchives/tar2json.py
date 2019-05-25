#!/usr/bin/env python3

import tarfile
import json
import lzma
import os
import sys

ARG_SUFFIX = '.tar.gz'


def convert(srcfile):
    assert srcfile.endswith(ARG_SUFFIX)
    basename = srcfile[:-len(ARG_SUFFIX)]
    tweets = []
    with tarfile.open(srcfile) as thetar:
        for member in thetar:
            tweets.append(json.load(thetar.extractfile(member)))

    kilotweets = (len(tweets) + 500) // 1000
    dstfile = '{}_{}KT.json.xz'.format(basename, kilotweets)
    print('Converting {} to {} ...'.format(srcfile, dstfile))
    tweets.sort(key=lambda x: x['id'])

    with lzma.open(dstfile, 'wt') as fp:
        json.dump(tweets, fp, check_circular=False, separators=(',', ':'), sort_keys=True)
    print('Success.')


def run(args):
    if len(args) < 1:
        print('Usage: {} <FOO.tar.gz...>'.format(sys.argv[0]), file=sys.stderr)
        print('Converts FOO.tar.gz into FOO_XKT.json.xz, for each FOO.', file=sys.stderr)
        print('("XKT" is the number of tweets, e.g. "26KT".)', file=sys.stderr)
        print('Note that this is highly CPU- and memory-intensive.', file=sys.stderr)
        exit(1)

    if args[0].startswith('-'):
        print('Usage: {} <FOO.tar.gz...>'.format(sys.argv[0]), file=sys.stderr)
        print('Cowardly refusing to access files starting with "-".', file=sys.stderr)
        exit(1)

    if any(not arg.endswith(ARG_SUFFIX) for arg in args):
        print('Usage: {} <FOO.tar.gz...>'.format(sys.argv[0]), file=sys.stderr)
        print('Suffix must be ".tar.gz".', file=sys.stderr)
        exit(1)

    for srcfile in args:
        convert(srcfile)


def import_json(filename):
    with lzma.open(filename, 'rt') as fp:
        return json.load(fp)


if __name__ == '__main__':
    run(sys.argv[1:])
