#!/bin/bash

python -c $'import sys\nif sys.version_info[0:2] < (3,7):\n    sys.exit(1)\n' || {
	echo "You need at least Python 3.7 to run this."
	echo "Please install it from https://www.python.org/downloads/"
	echo "or use pyenv: https://github.com/pyenv/pyenv#installation"
	exit 1
}

type pipenv >& /dev/null || {
	echo "Please install pipenv: https://pipenv.pypa.io/en/latest/"
	exit 2
}

pipenv install || exit 1

export PYTHONPATH="$PWD"
python tests/prepare.py || exit 1

echo "Ready to run the tests."
exit 0