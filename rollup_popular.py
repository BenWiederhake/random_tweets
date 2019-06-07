#!/usr/bin/env python3

from collections import defaultdict, Counter
import popular_categories
import sys


def is_informational(l):
    return any(l.startswith(x) for x in
               ['Most popular ', 'Waiting to resolve', '\tResolved ', 'Reading '])


def run_file(filename):
    with open(filename, 'r') as fp:
        lines = fp.readlines()
    parts = [[part.strip("',") for part in l.strip().split()]
             for l in lines if not is_informational(l)]
    host_lists = defaultdict(list)
    for fingerprint, _, b64, host, count, _, tweet in parts:
        if fingerprint in popular_categories.HOST_KNOWN:
            continue
        host_lists[(fingerprint,b64,host)].append((count,tweet))
    host_counts = Counter({host: (sum(int(x) for x, _ in l), l[0][1])
                           for host, l in host_lists.items()})
    for (fingerprint, b64, host), (count, tweet) in host_counts.most_common(50):
        print("    '{f}',  # {b}, {h}, {c}, e.g. {t}".format(f=fingerprint, b=b64, h=host, c=count, t=tweet))


def run(args):
    if len(args) != 2:
        print('USAGE: {} <PATH/TO/LOG>'.format(args[0]), file=sys.stderr)
        exit(1)
    run_file(args[1])


if __name__ == '__main__':
    run(sys.argv)
