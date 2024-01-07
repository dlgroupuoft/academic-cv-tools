#!/usr/bin/env python3

import argparse
from datetime import datetime
from functools import cmp_to_key
from pylatexenc.latexencode  import unicode_to_latex
import logging
import os
import csv
import uuid
from cv_utils import *

TITLE = 'Title'
VENUE = 'Venue'
YEAR = 'Year'
HEADER = 'Header'
URL = 'URL'
COUNTRY = 'Country'
CITY = 'City'
AUDIENCE = 'Audience'
TYPE = 'Type'
CONFERENCE = 'Conference'
INVITED = 'Invited'
KEYNOTE = 'Keynote'

def format(plain_str):
    return unicode_to_latex(plain_str.strip())

def field_present(field_name, dict):
    return (field_name in dict.keys() and dict[field_name])

def talk_sort_fn(i, j):    
    if (i[YEAR] > j[YEAR]):
        return -1
    else:
        return 1

def gen_talks_latex(tex_f, talks):    
    tex_f.write(r"\begin{innerenum}" + "\n")
    first = True
    for talk in talks:
        if first:
            first = False  
        if field_present(URL,talk):
            talk_row = f"\\textit{{\\href{{{talk[URL].strip()}}}{{{format(talk[TITLE])}}}}}, {format(talk[VENUE])}, {talk[YEAR].strip()}\n"      
        else:
            talk_row = f"\\textit{{{format(talk[TITLE])}}}, {format(talk[VENUE])}, {talk[YEAR].strip()}\n"
        if field_present(HEADER,talk):
            talk_row = f"\\item \\textbf{{{format(talk[HEADER])}}}: {talk_row}"            
        else:
            talk_row = f"\\item {talk_row}"
        tex_f.write(talk_row)        
    tex_f.write(r"\end{innerenum}")

def gen_latex(csvfile, logger, conference_tex, invited_tex):
    #if os.name == 'nt':
    logger.info("Opening " + csvfile + " in Windows mode")
    csv_in_f = open(csvfile,'r', newline='', encoding="UTF-8-sig")
    #else:
    #    csv_in_f = open(csvfile,'r')

    csv_in = csv.DictReader(csv_in_f)
    conference_sorted = sorted(
        filter(lambda course: course[TYPE].strip() == CONFERENCE, csv_in), 
        key=cmp_to_key(lambda i, j:(talk_sort_fn(i=i, j=j))))
    tex_f = open(conference_tex, 'w')    
    gen_talks_latex(tex_f, conference_sorted)    
    tex_f.close()

    # reset csv file
    csv_in_f.seek(0)
    csv_in.__next__()    

    invited_sorted = sorted(
        filter(lambda course: course[TYPE].strip() == INVITED, csv_in), 
        key=cmp_to_key(lambda i, j:(talk_sort_fn(i=i, j=j))))
    tex_f = open(invited_tex, 'w')    
    gen_talks_latex(tex_f, invited_sorted)    
    tex_f.close()
    csv_in_f.close()
    
def gen_xml_header(xml_f):
    xml_f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
    '<generic-cv:generic-cv dateTimeGenerated="2016-03-26 09:43:18" lang="en" xmlns:generic-cv="http://www.cihr-irsc.gc.ca/generic-cv/1.0.0">\n'
    '\t<section id="047ec63e32fe450e943cb678339e8102" label="Contributions">\n')    

def gen_xml_footer(xml_f):
    xml_f.write('\t</section>\n'
                '</generic-cv:generic-cv>\n')   
    
ccv_format_country = {
    'Canada': '<lov id="00000000000000000000000000002124">Canada</lov>',
    'USA' : '<lov id="00000000000000000000000000002840">United States of America</lov>',
    'China' : '<lov id="00000000000000000000000000002156">China</lov>',
    'Singapore' : '<lov id="00000000000000000000000000002702">Singapore</lov>',
    'Korea' : '<lov id="00000000000000000000000000002410">Korea, South</lov>',
    'UK' : '<lov id="00000000000000000000000000002826">United Kingdom</lov>',
}

ccv_format_audience = {
    'Researcher' : '<lov id="00000000000000000000000100005000">Researcher</lov>',
    'Knowledge User' : '<lov id="00000000000000000000000100005001">Knowledge User</lov>',
    'Decision Maker' : '<lov id="00000000000000000000000100005002">Decision Maker</lov>',
    'General Public' : '<lov id="00000000000000000000000100005003">General Public</lov>'
}
    
def gen_xml(csvfile, logger, talks_xml):
    #if os.name == 'nt':
    logger.info("Opening " + csvfile + " in Windows mode")
    csv_in_f = open(csvfile,'r', newline='', encoding="UTF-8-sig")
    #else:
    #    csv_in_f = open(csvfile,'r')

    xml_f = open(talks_xml, 'w')
    gen_xml_header(xml_f)
    csv_in = csv.DictReader(csv_in_f)
    
    for talk in csv_in:
        if not field_present(COUNTRY,talk) or not field_present(AUDIENCE,talk) or not field_present(TITLE,talk) or not field_present(VENUE,talk) or not field_present(YEAR,talk) or not field_present(TYPE,talk):
            continue
        
        title = format_xml(talk[TITLE])
        venue = format_xml(talk[VENUE])
        year = format_xml(talk[YEAR])
        if talk[TYPE] == INVITED:
            invited = '<lov id="00000000000000000000000000000400">Yes</lov>'
        else:
            invited = '<lov id="00000000000000000000000000000401">No</lov>'
            
        if talk[KEYNOTE] == 'Yes':
            keynote = '<lov id="00000000000000000000000000000400">Yes</lov>'
        else:
            keynote = '<lov id="00000000000000000000000000000401">No</lov>'
                        
        if not talk[COUNTRY] in ccv_format_country:
            logger.error("Country " + talk[COUNTRY] + " not found in ccv_format_country")
            country = ''
        else:
            country = ccv_format_country[talk[COUNTRY]]
            
        city = format_xml(talk[CITY]) if field_present(CITY,talk) else ''
        
        if not talk[AUDIENCE] in ccv_format_audience:
            logger.error("Audience " + talk[AUDIENCE] + " not found in ccv_format_audience")
            audience = ''
        else:
            audience = ccv_format_audience[talk[AUDIENCE]] 
            
        url = format_xml(talk[URL]) if field_present(URL,talk) else ''
        copresenters = format_xml(talk['Co-Presenters']) if field_present('Co-Presenters',talk) else ''      
        
        xml_f.write(f'\t\t<section id="c7ce6f054e0941ea8b27127dbd4a26d0" label="Presentations" recordId="{uuid.uuid4().hex}">\n'
                    '\t\t\t<field id="3f6a7ac56ee64b7dbd84dba9d6e3302d" label="Presentation Title">\n'
                    f'\t\t\t\t<value type="String">{title}</value>\n'
                    '\t\t\t</field>\n'
                    '\t\t\t<field id="8d882e55b0a54d0b8eec347f5502a19b" label="Conference / Event Name">\n'
                    f'\t\t\t\t<value type="String">{venue}</value>\n'
                    '\t\t\t</field>\n'
                    '\t\t\t<field id="f4b5f1a1d181404ca9c0fea81f9a7e79" label="Location">\n'
                    f'\t\t\t\t{country}\n'
                    '\t\t\t</field>\n'
                    '\t\t\t<field id="de6f8e0d7a714b07a4671af86405c6c9" label="City">\n'
                    f'\t\t\t\t<value type="String">{city}</value>\n'
                    '\t\t\t</field>\n'
                    '\t\t\t<field id="5f01d3af96d54a7ca3926b467dc946b7" label="Main Audience">\n'
                    f'\t\t\t\t{audience}\n'
                    '\t\t\t</field>\n'
                    '\t\t\t<field id="720d2f02feaf4aacb06ce60be0c6f603" label="Invited?">\n'
                    f'\t\t\t\t{invited}\n'
                    '\t\t\t</field>\n'
                    '\t\t\t\t<field id="9b6d317fd53e4b6a9e2e1d9e2001f3f5" label="Keynote?">\n'
                    f'\t\t\t\t{keynote}\n'
                    '\t\t\t</field>\n'
                    '\t\t\t<field id="9caf21634d984fc597f069f6e4a0a351" label="Competitive?"/>\n'
                    '\t\t\t<field id="725e4c54320b474680feaf530567fdd3" label="Presentation Year">\n'
                    f'\t\t\t\t<value format="yyyy" type="Year">{year}</value>\n'
                    '\t\t\t</field>\n'
                    '\t\t\t<field id="cc257bd89e6341a6bd53cc1cf05935c9" label="Description / Contribution Value">'
                    '\t\t\t\t<value type="Bilingual"></value>\n'
                    '\t\t\t\t<bilingual>\n'
                    '\t\t\t\t\t<french></french>\n'
                    '\t\t\t\t\t<english></english>\n'
                    '\t\t\t\t</bilingual>\n'
                    '\t\t\t</field>\n'
                    '\t\t\t<field id="8f612e2d2b23458fa114d8a790c38e13" label="URL">\n'
                    f'\t\t\t<value type="String">{url}</value>\n'
                    '\t\t\t</field>\n'
                    '\t\t\t<field id="d1dde22650bf4c508cf997beee12ef50" label="Co-Presenters">\n'
                    f'\t\t\t\t<value type="String">{copresenters}</value>\n'
                    '\t\t\t</field>\n'
                    '\t\t</section>\n')
                    
    gen_xml_footer(xml_f)
    csv_in_f.close()
    xml_f.close()

def main():
    parser = argparse.ArgumentParser(description='Generate Talks tex file for CV')
    parser.add_argument('file', type=str, help='Input csv file')
    parser.add_argument('-d', dest='debug', type=str, default='critical', choices = ['debug', 'info', 'error', 'critical'], help='Produce debug output')
    parser.add_argument('--conference_tex', dest='conference_tex', type=str, default='conference_talks.tex', help='Conference Talks Tex output file')
    parser.add_argument('--invited_tex', dest='invited_tex', type=str, default='invited_talks.tex', help='Invited Talks Tex output file')
    parser.add_argument('--xml', dest='talks_xml', type=str, default='talks.xml', help='CCV XML output file')    
    parser.add_argument('--out_dir', dest='out_dir', type=str, default='', help='Output directory')
    args = parser.parse_args()   

    if (args.debug == 'debug'):
        logging.basicConfig(level=logging.DEBUG)
    elif (args.debug == 'info'):
        logging.basicConfig(level=logging.INFO)
    elif (args.debug == 'error'):
        logging.basicConfig(level=logging.ERROR)

    logger = logging.getLogger("gen_students")
    
    if args.out_dir:
        conference_tex = os.path.join(args.out_dir, os.path.basename(args.conference_tex))
        invited_tex = os.path.join(args.out_dir, os.path.basename(args.invited_tex))
        talks_xml = os.path.join(args.out_dir, os.path.basename(args.talks_xml))
    else:
        conference_tex = args.conference_tex
        invited_tex = args.invited_tex
        talks_xml = args.talks_xml

    gen_latex(csvfile=args.file, logger=logger, conference_tex=conference_tex, invited_tex=invited_tex)
    gen_xml(csvfile=args.file, logger=logger, talks_xml=talks_xml)

# Start program
if __name__ == "__main__":
    main()