#!/bin/bash

TMPOUT=/dev/shm/stdout.txt
TMPERR=/dev/shm/sterrr.txt
OUTDIR=test_output

N_OK=0
N_FAIL=0

ok() {
	((N_OK++))

	if [ -t 1 ]; then
		printf '\e[32mOK\e[0m ' >&2
	else
		printf 'OK ' >&2
	fi
}

fail() {
	((N_FAIL++))

	if [ -t 1 ]; then
		printf '\e[1;31mFAIL\e[0m ' >&2
	else
		printf 'FAIL ' >&2
	fi

	RESULT=1
	mv "$TMPOUT" "$OUTDIR/fail_${NOW}_stdout.txt"
	mv "$TMPERR" "$OUTDIR/fail_${NOW}_stderr.txt"
}


mkdir -p "$OUTDIR"

while :; do
	((N_TOTAL++))

	NOW=$(date --iso-8601=seconds)
	echo -n "$NOW... " >&2

	./test_checker.sh >"$TMPOUT" 2>"$TMPERR"

	if [ $? -eq 0 ]; then
		ok
	else
		fail
	fi

	echo "($N_OK OKs, $N_FAIL FAILs)" >&2
done
