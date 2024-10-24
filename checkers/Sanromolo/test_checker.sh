#!/bin/bash

export DEV=1
export FLAG='AAAAAAAAAABBBBBBBBBBCCCCCCCCCCD='

RESULT=0

ok() {
	if [ -t 1 ]; then
		printf '\e[32mOK\e[0m\n' >&2
	else
		printf 'OK\n' >&2
	fi
}

fail() {
	if [ -t 1 ]; then
		printf '\e[1;31mFAIL\e[0m\n' >&2
	else
		printf 'FAIL\n' >&2
	fi

	RESULT=1
}

check() {
	if [ $? -eq 101 ]; then
		ok
	else
		fail
	fi
}

echo '--- CHECK_SLA ----------------------------------------' >&2
ACTION=CHECK_SLA python3 -m checker "$@"
check $?

echo '--- PUT_FLAG -----------------------------------------' >&2
ACTION=PUT_FLAG python3 -m checker "$@"
check $?

echo '--- GET_FLAG -----------------------------------------' >&2
ACTION=GET_FLAG python3 -m checker "$@"
check $?

exit $RESULT
