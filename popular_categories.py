#!/usr/bin/env python3

from collections import Counter, defaultdict
import json
import make_fingerprint
import os
import requests
import random_tweets
import sys
from time import sleep
from tarchives import tar2json


LOOKUP_FORMAT = 'https://fortiguard.com/webfilter?q={}&version=8'
LOOKUP_REALLY = False

RESOLVE_SHORTENERS = True
SHORTENER_DB = 'shortener_cache.json'

HOST_KNOWN = [
    '0a137b375cc3881a70e186ce2172c8d1',  # d3d3Lmdvb2dsZS5jb20
    '12bd7404d35af44f7ca87f73f7b9020c',  # d3d3Lm9raW5hd2F0aW1lcy5jby5qcA
    '1583bf6990be11ccac318beb9d9e67a6',  # d3d3Lm1va2VkbmV3cy5jby5pbA
    '1722c2193b8f46c7d720620a9e839a6f',  # ZGF5cGx1cy5pbmZv
    '18c4a11304c9e6807f76632aa9531706',  # eWxlLmZp
    '21d0ab52d7dc898bda18646e9136f825',  # YWx3YXRhbm5ld3MubmV0
    '24e93f851545d2995ad1b426cfceff6a',  # dy5yYXNoLmpw
    '447becabaf8b220e5ebd8dbe8853da1d',  # ZmVlZHMuZmVlZGJ1cm5lci5jb20
    '4d05ee95a9892d5eb504dcaa1584cbe9',  # bmV3czM2NS5saW5r
    '6bc805a12f9c985a0290a576fe2cf736',  # aXR1bmVzLmFwcGxlLmNvbQ
    '7905d1c4e12c54933a44d19fcd5f9356',  # dHdpdHRlci5jb20
    'ab3201c6103205c14f6e56b11b2fcd46',  # d3d3LnlvdXR1YmUuY29t
    'ae149eeb662da67b732c712075edcfb2',  # YW5pbWVuZXdzLWhhc3V0ZXJzLmJsb2cuanA
    'b8d631dd6a1ffd871cf9cd7a25f88cac',  # eW91dHUuYmU
    'c23f02e238724486dfb613e4535a4ec1',  # YWZmeS5qcA  # Who or what are you?
    'd88e23b2b9dd6eddd5fd9230eb4da404',  # bmV3cy5nb28ubmUuanA
    'db2d498a19b456cdccdbed290c6ec5cf',  # d3d3LjQ3bmV3cy5qcA
    'f0bf3d4fb79fa4c17578fba3a01516e4',  # YW16bi50bw
    'f76120cf5ce766a2017c92496482a7c5',  # dGhpcy5raWppLmlz
    'f8c798e436e1d1f71c21538aa4477412',  # ZG93bmxvYWQuY28uanA
]


KNOWN_SHORTENERS = [
    '604d5c5ec67df1a11cfaacc25418d7d8',  # Yml0Lmx5
    '8e3e2fed309a0b47bd276bf93f378e67',  # dGlueXVybC5jb20
    '95093b1e69e4eb7ba6d15ee439dbb9cb',  # Z29vLmds
    'a466d94da0e2455c6ffdbb0f9443ea88',  # dXJ4Lm51
    'aa5d4d50224090abe7a1eacc6212a8f9',  # ZGx2ci5pdA
    'b848f29bc505368fb62e6065fe5345b6',  # enByLmlv
]

_SHORTENER_CACHE = None


def get_host(url):
    host, fingerprint, _ = make_fingerprint.make_fingerprint(url)
    if not RESOLVE_SHORTENERS or fingerprint not in KNOWN_SHORTENERS:
        return host, fingerprint

    # Have to load it.
    # Or do we?  Try the local cache first:
    global _SHORTENER_CACHE
    if _SHORTENER_CACHE is not None:
        shortener_cache = _SHORTENER_CACHE
    elif os.path.exists(SHORTENER_DB):
        with open(SHORTENER_DB, 'r') as fp:
            shortener_cache = json.load(fp)
        _SHORTENER_CACHE = shortener_cache
    else:
        shortener_cache = dict()
        _SHORTENER_CACHE = shortener_cache

    if url in shortener_cache:
        # Hooray!
        next_url = shortener_cache[url]
    else:
        # We have to ask that host to resolve it.
        # Make absolutely sure we don't accidentally overload the server:
        print('Waiting to resolve {} ...'.format(url))
        sleep(10)
        response = requests.get(url, allow_redirects=False)
        if not response.ok or response.next is None:
            print('\tGiving up - not cached!')
            # Give up
            return host, fingerprint
        next_url = response.next.url
        print('\tResolved as {}'.format(next_url))
        shortener_cache[url] = next_url
        with open(SHORTENER_DB, 'w') as fp:
            json.dump(shortener_cache, fp, sort_keys=True, separators=(',', ':'))

    real_host, real_fingerprint, _ = make_fingerprint.make_fingerprint(next_url)

    return real_host, real_fingerprint


def read_interesting_tweets(filenames):
    assert type(filenames) is not str
    tweets = []
    for filename in filenames:
        for tweet in tar2json.import_json(filename):
            if random_tweets.tweet_is_interesting(tweet):
                tweets.append(tweet)
    return tweets


def analyze_hosts(tweets, use_knownlist=True):
    host_ctr = Counter()
    host_tweets = defaultdict(list)
    for tweet in tweets:
        for ue in tweet['entities']['urls']:
            host, fingerprint = get_host(ue['expanded_url'])
            if use_knownlist and fingerprint in HOST_KNOWN:
                continue
            host_ctr[host] += 1
            host_tweets[host].append(tweet)
    return host_ctr, dict(host_tweets)


def run(filenames):
    tweets = read_interesting_tweets(filenames)
    host_ctr, host_tweets = analyze_hosts(tweets, use_knownlist=True)
    print('Most popular link-hosts:')
    for host, count in host_ctr.most_common(50):
        _, fingerprint, comment = make_fingerprint.make_fingerprint(host)
        print("    '{f}',  # {c}, {h}, {n}, e.g. {tid}".format(
            f=fingerprint, c=comment, h=host, n=count, tid=host_tweets[host][0]['id']))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('USAGE: {} <ARCHIVE.json.xz...>'.format(sys.argv[0]))
        exit(1)
    run(sys.argv[1:])
