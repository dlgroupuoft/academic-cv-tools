#!/usr/bin/env python3

import argparse
import re
import urllib.request
import ssl
import sys

def find_urls(filename):
    f = open(filename, 'r')
    f_text = f.read()
    bib_urls = re.findall("url\s*=\s*\{(.*?)\}", f_text)            
    href_urls = re.findall("href\{(.*?)\}", f_text)            
    html_urls = re.findall("a href=[\"\'](.*?)[\"\']", f_text)        
    return bib_urls + href_urls + html_urls

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


def check_tex_url(filename, debug=False, quiet=False):
    retval = 0
    urls = find_urls(filename)     
    for url in urls:
        status = check_url(url)                        
        if (status != 200 and status != 'skipped'):
            print ("Failed: " + url + ": " + str(status))
            retval = -1                
        elif (debug):
            print ("Passed: " + url + ": " + str(status)) 
    if (not quiet):
        print("Checked", len(url), "urls.")
        if (retval != 0):
            print("Failures were detected.")
            
    return retval

def main():
    parser = argparse.ArgumentParser(description='Check URLs in latex file')
    parser.add_argument('file', type=str, help='File to process')
    parser.add_argument('-d', dest='debug', action='store_true', default=False, help='Produce debug output')
    parser.add_argument('-q', dest='quiet', action='store_true', default=False, help='Produce summary output')
    args = parser.parse_args()    
    retval = check_tex_url(args.file, args.debug, args.quiet)     
    
    sys.exit(retval)


# Start program
if __name__ == "__main__":
    main()