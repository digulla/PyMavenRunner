#!/bin/bash

type pyenv >& /dev/null || {
	echo "Please install pyenv: https://github.com/pyenv/pyenv#installation"
	exit 2
}
type pipenv >& /dev/null || {
	echo "Please install pipenv: https://pipenv.pypa.io/en/latest/"
	exit 2
}

pyenv install --skip-existing 3.7.7 || exit 1
pyenv rehash
eval "$(pyenv init -)"
pyenv shell 3.7.7

#pyenv version
#python --version

pipenv install || exit 1

export PYTHONPATH="$PWD"
python tests/prepare.py || exit 1

echo "Ready to run the tests."
exit 0