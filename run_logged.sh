#!/bin/sh

unbuffer ./random_tweets.py | tee -a bot.log
