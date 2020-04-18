#!/bin/bash

type pyenv >& /dev/null || {
	echo "Please install pyenv: https://github.com/pyenv/pyenv#installation"
	exit 2
}
type pipenv >& /dev/null || {
	echo "Please install pipenv: https://pipenv.pypa.io/en/latest/"
	exit 2
}

pipenv run pytest tests/
