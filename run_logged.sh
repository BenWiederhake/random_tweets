#!/bin/sh

unbuffer ./random_tweets.py | tee bot.log
