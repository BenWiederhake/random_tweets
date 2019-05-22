# random_tweets

> A tiny but random slice of world news tweets.

There's local news, regional news, country news, global news, …
and they're all still kind of biased by whatever country you live in.

So I made a [thing that retweets all kinds of News tweets from all over the place, and called it Random News Tweets](https://twitter.com/RngNewsTweets).

For me it was important that the randomness is meaningful.  Too many people just use uniform or normal distribution, say "Random!", and stop caring.
This bot tries to go cleverly about it, and I feel as if this represents a "natural-random" slice of the world news I'd miss otherwise.

## Table of Contents

- [Background](#background)
- [Install](#install)
- [Usage](#usage)
- [TODOs](#todos)
- [Contribute](#contribute)

## Background

I translated "News" into several language, with strong preference for languages that use entirely different scripts,
and that's what the bot is searching for.  Obviously, different countries tweet different amounts,
and I don't want that kind of bias in my bot.

The bot listens in for a period of time, records the most recent tweets,
and when it decides it can retweet something (not overwhelming Twitter is also important!),
it randomly selects a language, and retweets the most recent tweet from that language.
Thankfully, Twitter tags everything with a language code, but I think I [would have managed even without.](https://github.com/BenWiederhake/ear)

How exactly does it choose the next language?  Uniform distribution has the disadvantage of not feeling natural.
The frequency of immediate repetition just feels too high.
Thus the `feel_random` module is responsible for keeping memory about which options were picked recently,
and avoiding repetitions.  However, always staying in the same permutation and *never* repeating *anything* will also feel too un-random eventually,
so I tried to find a better distribution.  Implementation details are in `feel_random.py`.

## Install

### Packages

This bot uses Twython.  You can install it with `pip3 --user install twython`
or `pip -r requirements.txt`, or something in between.

### Twitter account

You will need an account on which the bot runs.
Make one, ideally also make a nice profile foto and backdrop,
so that it looks nice.

### Twitter app

You will need to register as a developer on `https://developer.twitter.com/en/apps/`
where they want a creepy amount of personal information and a buttload of justification
about your app.  I don't have the impression anyone actually looks at it,
but I felt like stripping in front of a camera anyway.  What a Brave New World.

Anyway, create the account, register your app, and you should see it pop up under ["Settings & privacy > Apps and devices"](https://twitter.com/settings/sessions).

Back on developer.twitter.com, copy your tokens and keys into `account_secrets.py`.  Note the template file `account_secrets_TEMPLATE.py`.

At that point, it's basically ready to be used, but please read the Usage section first:

## Usage

If you cloned it, you're probably unhappy with some config options, and want to run your own bot after changing
these options.

- `KEYWORDS` controls the set of keywords that the bot looks for.  "Hashtags" may have been more fitting, but whatever.
  I strongly recommend that you don't choose too many.  The keyword set of @RngWorldTweets is already pretty large.
- `RETWEET_PERIOD` controls the time between retweets.  Please leave enough time between retweets.  2 minutes is already very short.
- To run it unattended, you may want to use `screen` or `tmux` or something, and invoke it like `unbuffer ./random_tweets.py | tee bot.log` to have a permanent log of it.

The bot should be fairly stable and robost against many corner cases.  For example, if there are too few
tweets to choose from, it waits until it gathered an acceptable sample.  If the randomly selected tweet cannot be retweeted,
it discards it until an appropriate tweet is found.  On the other hand, I ignored corner cases that
would never happen to my use case, for example running out of tweets while discarding un-retweetables.

## TODOs

- Let it run and enjoy it.

## Contribute

Feel free to dive in! [Open an issue](https://github.com/BenWiederhake/random_tweets/issues/new) or submit PRs.
