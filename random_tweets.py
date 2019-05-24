#!/usr/bin/env python3

import account_secrets
import datetime
import hashlib
import json
import random
import requests
import store
import time  # sleep
import twython


KEYWORDS = ['uutiset', 'ニュース', 'hírek', 'Νέα', 'невс', 'חדשות', 'খবর',
            'أخبار', 'ข่าว', 'समाचार', 'мэдээ','naidheachdan', 'ዜና', 
            'Tin tức', 'novaĵoj', 'સમાચાર', 'Habari']
#KEYWORDS = ['uutiset', 'ニュース', 'חדשות', 'খবর', 'أخبار']
RETWEET_PERIOD = datetime.timedelta(minutes=2)

BANNED_HOST_FINGERPRINTS = {
    # Want to ban certain hosts without writing their hostname too clearly.
    '-INVALID-',
    '944c0a950264718ab454db3fcd6af35c',  # d3d3LnNvY2lhbGhvdDI0LmNvbQ
}


def host_fingerprint(url):
    host = requests.urllib3.util.url.parse_url(url).host
    if host is None:
        return '-INVALID-'
    return hashlib.md5(host.encode('utf-8')).hexdigest()


def urlent_looks_like_ad(urlent):
    tweet_url = urlent.get('expanded_url')
    if tweet_url is None:
        return True  # Only accept malformed data to a certain point.
    if host_fingerprint(tweet_url) in BANNED_HOST_FINGERPRINTS:
        return True
    # Other checks here
    return False


def tweet_looks_like_ad(tweet):
    if 'scopes' in tweet and 'followers' in tweet['scopes'] and not tweet['scopes']['followers']:
        # Inserted by Twitter
        return True
    if 'entities' in tweet and 'urls' in tweet['entities'] \
            and any(urlent_looks_like_ad(urlent) for urlent in tweet['entities']['urls']):
        # Spammy-looking stuff
        return True
    # Other checks here
    return False


class StreamerIn(twython.TwythonStreamer):
    def __init__(self, pk, ps, ct, cts):
        super().__init__(pk, ps, ct, cts)
        self.twitter = twython.Twython(pk, ps, ct, cts)
        self.twitter.verify_credentials()  # Fail early
        self.written = 0
        self.counter = 0
        self.store = store.Store()
        self.last_retweet = datetime.datetime.now()

    def do_retweet(self):
        success = False
        while not success:
            tweet = self.store.pop_random(auto_update=False)
            print('\tRetweeting #{}: {}'.format(tweet['id'], tweet['lang']))
            try:
                self.twitter.retweet(id=tweet['id'])
                success = True
            except twython.exceptions.TwythonError as e:
                if 'You have already retweeted this Tweet' in e.msg:
                    # Eh, whatever
                    print('\tWhoops, already retweeted.')
                    pass
                elif 'No status found with that ID.' in e.msg:
                    print('\tWhoops, user deleted it.')
                    pass
                else:
                    raise e
            self.store.update(tweet['lang'])

    def on_success(self, tweet_data):
        self.written += 1
        if 'text' not in tweet_data:
            return
        random_token = '{:016x}'.format(random.getrandbits(64))
        with open('tweets/{}_{}.json'.format(random_token, tweet_data.get('id')), 'w') as fp:
            json.dump(tweet_data, fp, sort_keys=True, indent=1)
        if tweet_data.get('retweeted_status') is not None:
            # Retweet or reply
            return
        if tweet_looks_like_ad(tweet_data):
            # Ad
            return
        retained = dict()
        for key in ['id', 'lang', 'text']:
            if key in tweet_data:
                retained[key] = tweet_data[key]
        self.counter += 1
        self.store.append(retained)
        now = datetime.datetime.now()
        if now - self.last_retweet < RETWEET_PERIOD:
            #print('{}: Too early for retweet.'.format(now))
            pass
        elif self.counter < 10:
            print('{}: Too few tweets for retweet.'.format(now))
        else:
            print('{}: Retweet!  Saw {} tweets in the meantime; {} usable ones.'.format(now, self.written, self.counter))
            self.counter = 0
            self.written = 0
            self.last_retweet = now
            self.do_retweet()

    def on_error(self, status_code, data):
        print(status_code, data)


def run_firehose():
    run = True
    while run:
        run = False
        print('Waiting ...')
        time.sleep(2)
        print('Starting up')
        stream = StreamerIn(account_secrets.API_KEY, account_secrets.API_SECRET, account_secrets.ACCESS_TOKEN,
                            account_secrets.ACCESS_TOKEN_SECRET)
        print('Begin filtering ...')
        try:
            stream.statuses.filter(track=KEYWORDS)
        except KeyboardInterrupt:
            print('KeyboardInterrupt, exiting ...')
            pass
        except requests.exceptions.ChunkedEncodingError as e:
            print(e)
            time.sleep(30)
            run = True
            print('{}: Restart!'.format(datetime.datetime.now()))
    print('Good bye.')


if __name__ == '__main__':
    run_firehose()
