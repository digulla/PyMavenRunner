#!python3
# -*- coding: utf-8 -*-

import pytest
from pmr.tools import WEB_URL_PATTERN

@pytest.mark.parametrize(
	'input,expected',
	[
		#('a domain.com b', 'domain.com'),
        ('a http://domain.com b', 'http://domain.com'),
        ('a http://domain.com/ b', 'http://domain.com/'),
        ('a http://domain.com/index.html b', 'http://domain.com/index.html'),
        ('a http://domain.com/index.html?p=v b', 'http://domain.com/index.html?p=v'),
        ('a http://domain.com/index.html#foo b', 'http://domain.com/index.html#foo'),
        ('a http://domain.com/index.html#foo?p=v b', 'http://domain.com/index.html#foo?p=v'),
        ('a mailto:someone@domain.com b', 'mailto:someone@domain.com'),
	]
)
def test_web_urls(input, expected):
	match = WEB_URL_PATTERN.search(input)
	assert match is not None, f'No match in {input}'

	actual = match.group(0).strip()
	assert actual == expected
