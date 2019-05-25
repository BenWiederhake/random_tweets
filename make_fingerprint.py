#!/usr/bin/env python3

import codecs
import hashlib
import random_tweets
import requests
import sys


def make_fingerprint(url):
    host = requests.urllib3.util.url.parse_url(url).host
    if host is None:
        host = '-INVALID-'
    fingerprint = hashlib.md5(host.encode('utf-8')).hexdigest()
    comment = codecs.getencoder('base64')(host.encode('utf-8'))[0].decode('ascii').rstrip('\n=')
    return host, fingerprint, comment


def run(args):
    if len(args) == 0:
        print('Usage: {} <HOSTNAMES...>'.format(sys.argv[0]), file=sys.stderr)
        return 1

    for url in args:
        host, fingerprint, comment = make_fingerprint(url)
        #print("    '{f}',  # {c}, {h}"
        print("    '{f}',  # {c}"
            .format(u=url, h=host, f=fingerprint, c=comment))
    return 0


if __name__ == '__main__':
    exit(run(sys.argv[1:]))
