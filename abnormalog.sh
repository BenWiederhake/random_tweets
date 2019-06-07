#!/bin/sh

set -e

if [ ! "$#" -ge 1 ]
then
	echo "Must provide at least one logfile."
	exit 1
fi

grep -Pv ': Retweet!  Saw |^\t(Selected language |Retweeting #|Whoops, )|: Too few tweets' "$@"
