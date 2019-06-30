#!/usr/bin/env python3

import account_secrets
import datetime
import hashlib
import json
import make_fingerprint
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
    '3bb0fc09c286dcfb95a7fbc80e0029d4',  # cm9vZnRvcC5jYw
    '44e07809ecec80ee8b8c63fb040c4dac',  # d3d3LnRvcGljemEuY29t
    '4d05ee95a9892d5eb504dcaa1584cbe9',  # bmV3czM2NS5saW5r
    '683bb915fe898ed1f24f28df4d2e4e00',  # dmlwdmlwLm1hdG9tZXRhLWFudGVubmEuY29t
    '6f77783855a33c3897d3d479a6e7f316',  # anlhbmktanlhbmkuYmxvZy5qcA, soft ban
    '818e946c37f5cb5932133a38c3480955',  # YmxvZy5saXZlZG9vci5qcA
    '920913c7f0a7a02b1dcd29b6f18a497c',  # d3d3MTAubWFrZWJvdC5zaA
    '944c0a950264718ab454db3fcd6af35c',  # d3d3LnNvY2lhbGhvdDI0LmNvbQ
    '94e0416adc87ead296c90428f86828e6',  # cHNheHRpcmkuZXU
    'ae149eeb662da67b732c712075edcfb2',  # YW5pbWVuZXdzLWhhc3V0ZXJzLmJsb2cuanA
    'bbd43773b56c998e428db4fd972b1218',  # bWF0b21lLm5hdmVyLmpw
    'bcecfec2bc758f2cd7c2ae64832427d3',  # d3d3MTcucGxhbGEub3IuanA
    'c23f02e238724486dfb613e4535a4ec1',  # YWZmeS5qcA  # Who or what are you?
    'd36f9ec98c1e51a254c8a81a919bc727',  # c3Rhcm5ld3MyZGF5LmNvbQ
    'eac0e94892c704b88cb18d90e23dd4b5',  # a2FnZWtpLmhhbmt5dS5jby5qcA
    'f0bf3d4fb79fa4c17578fba3a01516e4',  # YW16bi50bw, because it's usually ads
    'f6089a9c155ddd3c2f612d6a0d0efd87',  # d3d3Lm5hc3Nlci15YW1hbmkuY29t
    'f76120cf5ce766a2017c92496482a7c5',  # dGhpcy5raWppLmlz, soft ban
}


def urlent_looks_like_ad(urlent):
    tweet_url = urlent.get('expanded_url')
    if tweet_url is None:
        return True  # Only accept malformed data to a certain point.
    _, fingerprint, _ = make_fingerprint.make_fingerprint(tweet_url)
    if fingerprint in BANNED_HOST_FINGERPRINTS:
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


def tweet_is_interesting(tweet):
    return tweet.get('retweeted_status') is None \
        and not tweet_looks_like_ad(tweet) \
        and 'text' in tweet


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
            except (twython.exceptions.TwythonError, twython.exceptions.TwythonAuthError) as e:
                if 'You have already retweeted this Tweet' in e.msg:
                    # Eh, whatever
                    print('\tWhoops, already retweeted.')
                    pass
                elif 'No status found with that ID.' in e.msg:
                    print('\tWhoops, user deleted it.')
                    pass
                elif "You have been blocked from retweeting this user's tweets at their request." in e.msg:
                    print('\tWhoops, user {} blocked us.'.format(tweet['user_id']))
                    pass
                elif 'Retweet is not permissible for this status.' in e.msg:
                    print('\tWhoops, tweet {} is blocked.'.format(tweet['id']))
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
        if not tweet_is_interesting(tweet_data):
            return
        retained = dict()
        for key in ['id', 'lang', 'text']:
            if key in tweet_data:
                retained[key] = tweet_data[key]
        retained['user_id'] = tweet_data['user']['id']
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
        except (requests.exceptions.ConnectionError, twython.exceptions.TwythonError) as e:
            print(e)
            if ': Read timed out.' in e.msg or ': Twitter API returned a 500 (Internal Server Error)' in e.msg:
                print('{}: Sleeping for a while.'.format(datetime.datetime.now()))
                time.sleep(600)
                print('{}: Restart!'.format(datetime.datetime.now()))
                run = True
            else:
                raise e
        except requests.exceptions.ChunkedEncodingError as e:
            print(e)
            time.sleep(30)
            run = True
            print('{}: Restart!'.format(datetime.datetime.now()))
    print('Good bye.')


if __name__ == '__main__':
    run_firehose()
