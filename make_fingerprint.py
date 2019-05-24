#!/usr/bin/env python3

import codecs
import hashlib
import random_tweets
import requests
import sys

if len(sys.argv) == 1:
    print('Usage: {} <HOSTNAMES...>'.format(sys.argv[0]), file=sys.stderr)
    exit(1)

for url in sys.argv[1:]:
    # FIXME: WET: url→host
    host = requests.urllib3.util.url.parse_url(url).host
    if host is None:
        host = '-INVALID-'
    # FIXME: WET: host→fingerprint
    fingerprint = hashlib.md5(host.encode('utf-8')).hexdigest()
    comment = codecs.getencoder('base64')(host.encode('utf-8'))[0].decode('ascii').rstrip('\n=')
    # print("URL: {u}\nHost: {h}\nFingerprint: {f}\nComment: {c}\nCopyable-line:\n---->8----\n    '{f}'  # {c}\n----8<----"
    #     .format(u=url, h=host, f=fingerprint, c=comment))
    #print("    '{f}',  # {c}, {h}"
    print("    '{f}',  # {c}"
        .format(u=url, h=host, f=fingerprint, c=comment))
