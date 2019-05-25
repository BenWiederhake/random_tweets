#!/bin/sh

unbuffer python3 random_tweets.py | tee -a bot.log
