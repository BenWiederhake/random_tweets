#!/usr/bin/env python3

import account_secrets
import datetime
import json
import secrets
import store
import time  # sleep
import twython


#KEYWORDS = ['uutiset', 'ニュース', 'hírek', 'Νέα', 'невс', 'חדשות', 'খবর', 'أخبار', 'ข่าว', 'समाचार', 'мэдээ', 'خبریں', 'naidheachdan']
KEYWORDS = ['uutiset', 'ニュース', 'חדשות', 'খবর', 'أخبار']
RETWEET_PERIOD = datetime.timedelta(minutes=5)


class StreamerIn(twython.TwythonStreamer):
    def __init__(self, pk, ps, ct, cts):
        super().__init__(pk, ps, ct, cts)
        self.twitter = twython.Twython(pk, access_token=ct)
        self.store = store.Store()
        self.last_retweet = datetime.datetime.now()

    def do_retweet(self):
        tweet = self.store.pop_random()
        print('Retweeting #{}'.format(tweet['id']))
        self.twitter.retweet(id=tweet['id'])

    def on_success(self, tweet_data):
        if 'text' not in tweet_data:
            return
        if 'scopes' in tweet_data and 'followers' in tweet_data['scopes'] and not tweet_data['scopes']['followers']:
            # Ad
            return
        with open('tweets/{}_{}.json'.format(secrets.token_hex(8), tweet_data.get('id')), 'w') as fp:
            json.dump(tweet_data, fp, sort_keys=True, indent=1)
        retained = dict()
        for key in ['id', 'lang', 'text']:
            if key in tweet_data:
                retained[key] = tweet_data[key]
        self.store.append(retained)
        now = datetime.datetime.now()
        if now - self.last_retweet >= RETWEET_PERIOD:
            self.last_retweet = now
            self.do_retweet()

    def on_error(self, status_code, data):
        print(status_code, data)


def run_firehose():
    print('Waiting ...')
    time.sleep(2)
    print('Starting up')
    stream = StreamerIn(account_secrets.API_KEY, account_secrets.API_SECRET, account_secrets.ACCESS_TOKEN,
                        account_secrets.ACCESS_TOKEN_SECRET)
    print('Begin filtering ...')
    stream.statuses.filter(track=KEYWORDS)
    print('Done filtering ...')


if __name__ == '__main__':
    run_firehose()
