#!/usr/bin/env python3

import tarfile
import json
import lzma
import os
import sys

if len(sys.argv) != 3:
    print('Usage: {} FROMFILE.tar.gz TOFILE.json.xz'.format(sys.argv[0]), file=sys.stderr)
    exit(1)

tweets = []
with tarfile.open(sys.argv[1]) as thetar:
    for member in thetar:
        tweets.append(json.load(thetar.extractfile(member)))

print('Found {} tweets.'.format(len(tweets)))
tweets.sort(key=lambda x: x['id'])

with lzma.open(sys.argv[2], 'wt') as fp:
    json.dump(tweets, fp, check_circular=False, separators=(',', ':'), sort_keys=True)
