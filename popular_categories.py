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

HOST_KNOWN = {
    '0a137b375cc3881a70e186ce2172c8d1',  # d3d3Lmdvb2dsZS5jb20
    '12bd7404d35af44f7ca87f73f7b9020c',  # d3d3Lm9raW5hd2F0aW1lcy5jby5qcA
    '1583bf6990be11ccac318beb9d9e67a6',  # d3d3Lm1va2VkbmV3cy5jby5pbA
    '1722c2193b8f46c7d720620a9e839a6f',  # ZGF5cGx1cy5pbmZv
    '18c4a11304c9e6807f76632aa9531706',  # eWxlLmZp
    '21d0ab52d7dc898bda18646e9136f825',  # YWx3YXRhbm5ld3MubmV0
    '24e93f851545d2995ad1b426cfceff6a',  # dy5yYXNoLmpw
    '290ccda0deea6083ee613d358446103e',  # d3d3LmJiYy5jb20
    '36ea9eca4ab266f308634297eca700c3',  # dG9rb3Rva28uMmNoYmxvZy5qcA
    '3bb0fc09c286dcfb95a7fbc80e0029d4',  # cm9vZnRvcC5jYw
    '447becabaf8b220e5ebd8dbe8853da1d',  # ZmVlZHMuZmVlZGJ1cm5lci5jb20
    '44e07809ecec80ee8b8c63fb040c4dac',  # d3d3LnRvcGljemEuY29t
    '4d05ee95a9892d5eb504dcaa1584cbe9',  # bmV3czM2NS5saW5r
    '5f879ce72fc5b82f40b12c6dd73cde22',  # d3d3Lmhva2thaWRvLW5wLmNvLmpw
    '6532d80155c172d91b6274f1ef09a0a6',  # Zmx5dGVhbS5qcA
    '683bb915fe898ed1f24f28df4d2e4e00',  # dmlwdmlwLm1hdG9tZXRhLWFudGVubmEuY29t
    '6bc805a12f9c985a0290a576fe2cf736',  # aXR1bmVzLmFwcGxlLmNvbQ
    '6f77783855a33c3897d3d479a6e7f316',  # anlhbmktanlhbmkuYmxvZy5qcA
    '72d0277103817c1ba7242e2b7a95698a',  # bmV3cy5pbmZvc2Vlay5jby5qcA
    '7905d1c4e12c54933a44d19fcd5f9356',  # dHdpdHRlci5jb20
    '818e946c37f5cb5932133a38c3480955',  # YmxvZy5saXZlZG9vci5qcA
    'ab3201c6103205c14f6e56b11b2fcd46',  # d3d3LnlvdXR1YmUuY29t
    'ae149eeb662da67b732c712075edcfb2',  # YW5pbWVuZXdzLWhhc3V0ZXJzLmJsb2cuanA
    'b8d631dd6a1ffd871cf9cd7a25f88cac',  # eW91dHUuYmU
    'bbd43773b56c998e428db4fd972b1218',  # bWF0b21lLm5hdmVyLmpw
    'c23f02e238724486dfb613e4535a4ec1',  # YWZmeS5qcA  # Who or what are you?
    'c54de091a2ce6cc93229bc9e949620dd',  # bm9ub2tvdG8uaXRpZ28uanA
    'ccb987a8d526a7e7521120259bebe64a',  # d3d3Lm9rYXouY29tLnNh
    'd3445220bb2794d477330dff364c460d',  # d3d3LmthdXBwYWxlaHRpLmZp
    'd88e23b2b9dd6eddd5fd9230eb4da404',  # bmV3cy5nb28ubmUuanA
    'db2d498a19b456cdccdbed290c6ec5cf',  # d3d3LjQ3bmV3cy5qcA
    'eac0e94892c704b88cb18d90e23dd4b5',  # a2FnZWtpLmhhbmt5dS5jby5qcA
    'ed563545c39568abd23e4dad8646ab3e',  # d3d3Lm5pa2thbi5jby5qcA
    'f0bf3d4fb79fa4c17578fba3a01516e4',  # YW16bi50bw
    'f6089a9c155ddd3c2f612d6a0d0efd87',  # d3d3Lm5hc3Nlci15YW1hbmkuY29t
    'f76120cf5ce766a2017c92496482a7c5',  # dGhpcy5raWppLmlz
    'f8c798e436e1d1f71c21538aa4477412',  # ZG93bmxvYWQuY28uanA
}


KNOWN_SHORTENERS = {
    '604d5c5ec67df1a11cfaacc25418d7d8',  # Yml0Lmx5
    '8e3e2fed309a0b47bd276bf93f378e67',  # dGlueXVybC5jb20
    '95093b1e69e4eb7ba6d15ee439dbb9cb',  # Z29vLmds
    'a466d94da0e2455c6ffdbb0f9443ea88',  # dXJ4Lm51
    'aa5d4d50224090abe7a1eacc6212a8f9',  # ZGx2ci5pdA
    'b848f29bc505368fb62e6065fe5345b6',  # enByLmlv
}

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
        print('Reading {} ...'.format(filename))
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
