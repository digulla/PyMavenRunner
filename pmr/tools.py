#!python3
# -*- coding: utf-8 -*-

import sys
import os
import re

# Based on https://gist.github.com/dperini/729294
def build_url_pattern1():
    # protocol identifier (optional)
    # short syntax // still required
    protocol_identifier = "(?:(?:(?:https?|ftp):)?\\/\\/)"
    # user:pass BasicAuth (optional)
    basic_auth = "(?:\\S+(?::\\S*)?@)?"

    # IP address exclusion
    # private & local networks
    ip_addresses = "(?!(?:10|127)(?:\\.\\d{1,3}){3})" + \
        "(?!(?:169\\.254|192\\.168)(?:\\.\\d{1,3}){2})" + \
        "(?!172\\.(?:1[6-9]|2\\d|3[0-1])(?:\\.\\d{1,3}){2})"
    # IP address dotted notation octets
    # excludes loopback network 0.0.0.0
    # excludes reserved space >= 224.0.0.0
    # excludes network & broadcast addresses
    # (first & last IP address of each class)
    ip_addresses2 = "(?:[1-9]\\d?|1\\d\\d|2[01]\\d|22[0-3])" + \
        "(?:\\.(?:1?\\d{1,2}|2[0-4]\\d|25[0-5])){2}" + \
        "(?:\\.(?:[1-9]\\d?|1\\d\\d|2[0-4]\\d|25[0-4]))"

    # host & domain names, may end with dot
    # can be replaced by a shortest alternative
    # (?![-_])(?:[-\\w\\u00a1-\\uffff]{0,63}[^-_]\\.)+
    host_domain = "(?:" + \
      "(?:" + \
        "[a-z0-9\\u00a1-\\uffff]" + \
        "[a-z0-9\\u00a1-\\uffff_-]{0,62}" + \
      ")?" + \
      "[a-z0-9\\u00a1-\\uffff]\\." + \
    ")+"

    # TLD identifier name, may end with dot
    tld = "(?:[a-z\\u00a1-\\uffff]{2,}\\.?)"
    # port number (optional)
    port = "(?::\\d{2,5})?"

    # resource path (optional)
    path = "(?:[/?#]\\S*)?"

    return re.compile(
        protocol_identifier + 
        basic_auth +
        "(?:" +
            ip_addresses + ip_addresses2 +
        "|" +
            host_domain +
            tld +
        ")" +
        port +
        path
        , re.IGNORECASE)
    

def build_url_pattern2():
    '''Doesn't match anything for some reason'''
    return re.compile(r'''\
\b
(                           # Capture 1: entire matched URL
  (?:
    [a-z][\w-]+:                # URL protocol and colon
    (?:
      /{1,3}                        # 1-3 slashes
      |                             #   or
      [a-z0-9%]                     # Single letter or digit or '%'
                                    # (Trying not to match e.g. "URI::Escape")
    )
    |                           #   or
    www\d{0,3}[.]               # "www.", "www1.", "www2." … "www999."
    |                           #   or
    [a-z0-9.\-]+[.][a-z]{2,4}/  # looks like domain name followed by a slash
  )
  (?:                           # One or more:
    [^\s()<>]                       # Run of non-space, non-()<>
    |                               #   or
    \(([^\s()<>]+|(\([^\s()<>]+\)))*\)  # balanced parens, up to 2 levels
  )+
  (?:                           # End with:
    \(([^\s()<>]+|(\([^\s()<>]+\)))*\)  # balanced parens, up to 2 levels
    |                                   #   or
    [^\s`!()\[\]{};:'".,<>?«»“”‘’]      # not a space or one of these punct char
  )
)''', re.IGNORECASE + re.VERBOSE)

def build_url_pattern3():
    '''Based on https://gist.github.com/gruber/8891611#gistcomment-1310352'''
    return re.compile(r'''(([a-z]{3,6}://)|(^|\s))([a-zA-Z0-9\-]+\.)+[a-z]{2,13}[\.\?\=\&\%\/\w\-]*\b([^@]|$)''', re.IGNORECASE)

def build_url_pattern4():
    '''Based on https://gist.github.com/gruber/249502'''
    return re.compile(r'''(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’]))''')

WEB_URL_PATTERN = build_url_pattern4()
#print(WEB_URL_PATTERN)

class OsSpecificInfo:
    def __init__(self):
        self.commandSearchPathSep = ':'
        self.mavenCommand = 'mvn'

        if sys.platform == 'win32':
            self.initWin32()

    def initWin32(self):
        self.commandSearchPathSep = ';'
        self.mavenCommand = 'mvn.cmd'

    def commandSearchPath(self):
        raw = os.environ['PATH']
        return raw.split(self.commandSearchPathSep)

