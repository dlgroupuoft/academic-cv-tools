#!/usr/bin/env python3

from pylatexenc.latexencode  import unicode_to_latex
from pylatexenc.latex2text import LatexNodes2Text
import urllib.request
import ssl
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
from xml.sax.saxutils import escape
import sys
import dateutil.parser as dparser


def ordinal(n: int):
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    return str(n) + suffix

def latex_format(str):
    return unicode_to_latex(str.strip())

def check_url(url):
    if url.startswith("mailto") or url.startswith('https://www.linkedin.com'):
        return 'skipped'
    try:
        req = urllib.request.Request(
            url, 
            data=None, 
            headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
            }
        )
    except Exception as e:
        return "check_url creation exception: " + str(e) + " on  " + url
    try:
        return urllib.request.urlopen(req, context=ssl._create_unverified_context()).getcode()
    except Exception as e:
        return "check_url urlopen exception: " + str(e) + " on  " + url
    
def extract_year(date_str,increment=0):
    if date_str:
        date = dparser.parse(date_str,fuzzy=False)
        return (date + relativedelta(years=increment)).strftime('%Y')
    else:
        return ''

def extract_month(date_str,increment=0):
    if date_str:
        date = dparser.parse(date_str,fuzzy=False)
        return (date + relativedelta(months=increment)).strftime('%m')
    else:
        return ''
    
def format_xml(str):
    # remove commas from numbers
    if re.match('^[0-9,]*$',str):
        str = str.replace(',','')
    return escape(str.strip()) if str else ''

def field_present(field_name, row):
    return (field_name in row.keys() and row[field_name])

def latex2xml(str):
    return escape(LatexNodes2Text().latex_to_text(str.strip())) if str else ''


