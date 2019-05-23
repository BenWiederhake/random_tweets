#!/usr/bin/env python3

from collections import defaultdict
import feel_random
import twython


class OverflowingQueue:
    def __init__(self):
        self.backing = []

    def append(self, x):
        self.backing.append(x)
        if len(self.backing) > 20:
            self.backing = self.backing[-10:]

    def pop(self):
        if self.backing:
            return self.backing.pop()

    def __bool__(self):
        return bool(self.backing)


class Store:
    def __init__(self):
        self.per_lang = defaultdict(OverflowingQueue)
        self.random = feel_random.ChoiceMemory()

    def append(self, tweet):
        if 'quoted_status' in tweet or 'retweeted_status' in tweet:
            # Skip
            return
        for key in ['id', 'lang', 'text']:
            if key not in tweet:
                # Weird incomplete tweet
                return
        self.per_lang[tweet['lang']].append(tweet)

    def pop_random(self, auto_update=True):
        random_lang = self.random.choose(list(self.per_lang.keys()), auto_update=auto_update)
        print('\tSelected language {}'.format(random_lang))
        random_queue = self.per_lang[random_lang]
        x = random_queue.pop()
        if not random_queue:
            del self.per_lang[random_lang]
        return x

    def update(self, lang):
        # Note: If that was the last known tweet of that language,
        # it could be that self.per_lan[lang] no longer exists.
        self.random.update(lang)


def run_test():
    import glob
    import json

    f = glob.glob('tweets/*.json')
    print('Found {} files.'.format(len(f)))
    store = Store()
    for (i, name) in enumerate(f):
        if i % 50 == 30:
            tweet = store.pop_random()
            print(tweet['id'], tweet['lang'], tweet['text'])
        with open(name, 'r') as fp:
            store.append(json.load(fp))
    print('Done.')


if __name__ == '__main__':
    run_test()
