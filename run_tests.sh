#!/bin/bash

type pipenv >& /dev/null || {
	echo "Please install pipenv: https://pipenv.pypa.io/en/latest/"
	exit 2
}

pipenv run pytest "$@" tests/
