#!/bin/bash

type pyenv >& /dev/null || {
	echo "Please install pyenv: https://github.com/pyenv/pyenv#installation"
	exit 2
}
type pipenv >& /dev/null || {
	echo "Please install pipenv: https://pipenv.pypa.io/en/latest/"
	exit 2
}

pyenv install --skip-existing 3.7.4 || exit 1

pipenv install || exit 1

export PYTHONPATH="$PWD"
pipenv run python tests/prepare.py || exit 1

echo "Ready to run the tests."
exit 0