#!/bin/bash

type pipenv >& /dev/null || {
	echo "Please install pipenv: https://pipenv.pypa.io/en/latest/"
	exit 2
}

if [[ "$*" != "" ]]; then
	pipenv run pytest "$@"
else
	pipenv run pytest --cov=pmr --cov-report=html:coverage_reports --cov-report=term-missing tests/
fi