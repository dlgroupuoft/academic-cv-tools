#!/usr/bin/env python3

import argparse
from datetime import datetime
from dateutil.relativedelta import relativedelta
from functools import cmp_to_key
import logging
import os
import csv
from tempfile import NamedTemporaryFile
import shutil
import uuid
from cv_utils import ordinal, latex_format, check_url, field_present

CONF_SHORT_STR = 'conf_short'
CONF_FULL_STR = 'conf_full'
CONF_STR = 'conf'
URL_STR = 'URL'
YEAR_STR = 'year'
MONTH_STR = 'month'
START_YEAR_STR = 'start_year'
START_NUM_STR = 'start_num'
ROLE_STR = 'role'
NOTES_STR = 'notes'

def lookup_conf(conferences, conf_short):    
    for conference in conferences:
        if conference[CONF_SHORT_STR] == conf_short:
            return conference

def format_conf(tpc, conferences, conf_short, url=''):
    conference = lookup_conf(conferences, conf_short)
    
    if conference:
        conf_number = int(tpc[YEAR_STR]) - int(conference[START_YEAR_STR]) + 1
        conf_ordinal = ordinal(conf_number)
        if (url == ''):        
            if conference[URL_STR] == '':
                return (f"The {conf_ordinal} {conference[CONF_FULL_STR].strip()}","")
            else:
                # compute year
                url_formatted = conference[URL_STR].replace("<year>",tpc[YEAR_STR])
                url_formatted = url_formatted.replace("<year-short>",tpc[YEAR_STR][-2:])
                return (f"The {conf_ordinal} {conference[CONF_FULL_STR].strip()}",url_formatted)
        else:
            return (f"The {conf_ordinal} {conference[CONF_FULL_STR].strip()}",url)        
    else:
        return (f"The {latex_format(conf_short)}",url)

def gen_latex(tpcs_file, conferences_file, logger, debug, tex_out):
    if os.name == 'nt':
        logger.info("Opening csv files in Windows mode")
        tpcs_f = open(tpcs_file,'r', newline='', )
        conferences_f = open(conferences_file,'r', newline='')
    else:
        logger.info(f"Opening csv files in {os.name} mode")
        tpcs_f = open(tpcs_file,'r',encoding='utf-8-sig')
        conferences_f = open(conferences_file,'r',encoding='utf-8-sig')
        
    tpcs = csv.DictReader(tpcs_f)
    conferences = csv.DictReader(conferences_f)
    
    tex_f = open(tex_out, 'w')
    
    tex_f.write(r"\begin{innerenum}" + "\n")
    for tpc in tpcs:
        logger.debug(f"Processing {tpc}")
        # reset csv file
        conferences_f.seek(0)
        conf_name, url_str = format_conf(tpc, conferences, tpc[CONF_STR], tpc[URL_STR])
        if url_str and url_str != 'none':
            tpc_row = f"\\item \\textit{{\\href{{{url_str}}}{{{latex_format(conf_name)}}}}}, {tpc[YEAR_STR].strip()}{' (' + latex_format(tpc[NOTES_STR]) + ')' if tpc[NOTES_STR] else ''}.\n"
        else:            
            tpc_row = f"\\item \\textit{{{latex_format(conf_name)}}}, {tpc[YEAR_STR].strip()}{' (' + latex_format(tpc[NOTES_STR]) + ')' if tpc[NOTES_STR] else ''}.\n"
        tex_f.write(tpc_row)        
    tex_f.write(r"\end{innerenum}")
    
    tex_f.close()
    tpcs_f.close()
    conferences_f.close()
    
def gen_html(tpcs_file, conferences_file, logger, debug, html_out):
    if os.name == 'nt':
        logger.info("Opening csv files in Windows mode")
        tpcs_f = open(tpcs_file,'r', newline='', )
        conferences_f = open(conferences_file,'r', newline='')
    else:
        logger.info(f"Opening csv files in {os.name} mode")
        tpcs_f = open(tpcs_file,'r',encoding='utf-8-sig')
        conferences_f = open(conferences_file,'r',encoding='utf-8-sig')
        
    tpcs = csv.DictReader(tpcs_f)
    conferences = csv.DictReader(conferences_f)
    
    html_f = open(html_out, 'w')
    
    # html_f.write(r'<div class="accordion"><input type="radio" name="select" class="accordion-select" checked /><div class="accordion-title"><span><b>Current Program Committees</b></span></div><div class="accordion-content"><ul>'+ "\n")
    
    html_f.write(r'''
                 <div class="tabs">
    <div class="tab">
      <input class="accordian" type="radio" id="rd1" name="rd" checked>
      <label class="tab-label" for="rd1">Current Program Committees</label>
      <div class="tab-content">
        <ul>''' + "\n")
    current_tpcs = True
    for tpc in tpcs:
        logger.debug(f"Processing {tpc}")
        # reset csv file
        conferences_f.seek(0)
        conf_name, url_str = format_conf(tpc, conferences, tpc[CONF_STR], tpc[URL_STR])
        if current_tpcs and int(tpc[YEAR_STR]) < int(datetime.now().year):
            # html_f.write(r'</ul></div><input type="radio" name="select" class="accordion-select" /><div class="accordion-title"><span><b>Past Program Committees</span></b></span></div><div class="accordion-content"><ul>'+ "\n")
            html_f.write(r'''</ul>
      </div>
    </div>
    <div class="tab">
      <input class="accordian" type="radio" id="rd2" name="rd">
      <label class="tab-label" for="rd2">Past Program Committees</label>
      <div class="tab-content">
        <ul>''' + "\n")
            current_tpcs = False
        if url_str and url_str != 'none':
            tpc_row = f'<li><a href="{url_str}">{conf_name}</a>, {tpc[YEAR_STR].strip()}{" (" + tpc[NOTES_STR].strip() + ")" if tpc[NOTES_STR] else ""}.</li>\n'
        else:            
            tpc_row = f'<li>{conf_name}, {tpc[YEAR_STR].strip()}{" (" + tpc[NOTES_STR].strip() + ")" if tpc[NOTES_STR] else ""}</li>\n'
        html_f.write(tpc_row)        
        
    html_f.write(r'</ul></div></div></div>')
    
    html_f.close()
    tpcs_f.close()
    conferences_f.close()
    
def gen_xml(tpcs_file, conferences_file, logger, debug, xml_out):   
    if os.name == 'nt':
        logger.info("Opening csv files in Windows mode")
        tpcs_f = open(tpcs_file,'r', newline='', )
        conferences_f = open(conferences_file,'r', newline='')
    else:
        logger.info(f"Opening csv files in {os.name} mode")
        tpcs_f = open(tpcs_file,'r',encoding='utf-8-sig')
        conferences_f = open(conferences_file,'r',encoding='utf-8-sig')
        
    tpcs = csv.DictReader(tpcs_f)
    conferences = csv.DictReader(conferences_f)
    
    xml_f = open(xml_out, 'w')
    
    gen_xml_header(xml_f)
    
    for tpc in tpcs:
        logger.debug(f"Processing {tpc} for CCV")
        xml_f.write(f'\t\t\t<section id="7564fc922478441c97c9857809028895" label="Event Administration" recordId="{uuid.uuid4().hex}">\n')
        
        if field_present(ROLE_STR, tpc):
            if tpc[ROLE_STR] == 'TPC Chair':
                role = 'Technical Program Committee Chair'
            elif tpc[ROLE_STR] == 'General Chair':
                role = 'General Chair'
            else:
                raise Exception(f"Unknown role {tpc[ROLE_STR]}")
        else:
            role = 'Technical Program Committee Member'
            
         # reset csv file
        conferences_f.seek(0)
        conf_name, url_str = format_conf(tpc, conferences, tpc[CONF_STR], tpc[URL_STR])
        
        conf_date = datetime(int(tpc[YEAR_STR]),int(tpc[MONTH_STR]) if field_present(MONTH_STR,tpc) else 1,1)
        tpc_start_date = conf_date - relativedelta(years=1)
                       
        xml_f.write('\t\t\t\t<field id="31cdeb30328e410cb6b78fa48435be08" label="Role">\n'
                    f'\t\t\t\t\t<value type="String">{role}</value>\n'
                    '\t\t\t</field>\n'
                    '\t\t\t<field id="7878a016f370434a8364beca1a47ea20" label="Event Type">\n'
                    '\t\t\t\t<lov id="00000000000000000000000100000700">Conference</lov>\n'
                    '\t\t\t</field>\n'
                    '\t\t\t<field id="f5389531adca4f54a4e9bee39532323c" label="Event Name">\n'
                    f'\t\t\t\t<value type="String">{conf_name}</value>\n'
                    '\t\t\t</field>\n'
                    '\t\t\t<field id="9def30776da74a1597de4fd0d9a0e74b" label="Activity Start Date">\n'
                    f'\t\t\t\t<value format="yyyy/MM" type="YearMonth">{tpc_start_date.strftime("%Y/%m")}</value>\n'
                    '\t\t\t</field>\n'
                    '\t\t\t<field id="0dc7af4aa5ff4bb880bb6a5db48a9b55" label="Activity End Date">\n'
                    f'\t\t\t\t<value format="yyyy/MM" type="YearMonth">{conf_date.strftime("%Y/%m")}</value>\n'
                    '\t\t\t</field>\n'
                    '\t\t\t<field id="7cf2f82472bd4d7086f58b43c488b39e" label="Primary Event Organizer">\n'
                    '\t\t\t\t<value type="String"></value>\n'
                    '\t\t\t</field>\n'
                    '\t\t\t<field id="cf11be8d0fa94624b80a11ad83a911e8" label="Event Start Date">\n'
                    f'\t\t\t\t<value format="yyyy/MM" type="YearMonth">{conf_date.strftime("%Y/%m")}</value>\n'
                    '\t\t\t</field>\n'
                    '\t\t\t<field id="aabcc98da2b348ea9502c35177096674" label="Event End Date">\n'
                    f'\t\t\t\t<value format="yyyy/MM" type="YearMonth">{conf_date.strftime("%Y/%m")}</value>\n'
                    '\t\t\t</field>\n'
                    '\t\t\t<field id="32a0b4e43c8147cdae1ad306b4cb3353" label="Activity Description">\n'
                    '\t\t\t\t<value type="Bilingual"></value>\n'
                    '\t\t\t\t<bilingual>\n'
                    '\t\t\t\t\t<french></french>\n'
                    '\t\t\t\t\t<english></english>\n'
                    '\t\t\t\t</bilingual>\n'
                    '\t\t\t</field>\n')
        xml_f.write('\t\t\t</section>\n')                 
        
    gen_xml_footer(xml_f)
    return
    
def gen_xml_header(xml_f):
    xml_f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    xml_f.write('<generic-cv:generic-cv dateTimeGenerated="2016-03-26 09:43:18" lang="en" xmlns:generic-cv="http://www.cihr-irsc.gc.ca/generic-cv/1.0.0">\n')
    xml_f.write('\t<section id="95c29504d0aa4b51b84659cafaf2b38d" label="Activities">\n')
    xml_f.write('\t\t<section id="9fa2e1cd0274429f9fde16616bf3939f" label="Administrative Activities">\n')

def gen_xml_footer(xml_f):
    xml_f.write('\t\t</section>\n')
    xml_f.write('\t</section>\n')
    xml_f.write('</generic-cv:generic-cv>\n')  
    
def fix_urls(tpcs_file, conferences_file, logger, debug):
    if os.name == 'nt':
        logger.info("Opening csv files in Windows mode")
        tpcs_f = open(tpcs_file,'r', newline='', )
        conferences_f = open(conferences_file,'r', newline='')
    else:
        logger.info(f"Opening csv files in {os.name} mode")
        tpcs_f = open(tpcs_file,'r',encoding='utf-8-sig')
        conferences_f = open(conferences_file,'r',encoding='utf-8-sig')
    tempfile = NamedTemporaryFile('w+t', newline='', delete=False)
    logger.info(f"Using temporary file {tempfile.name}")
    
    tpcs = csv.DictReader(tpcs_f)
    conferences = csv.DictReader(conferences_f)
    tempwriter = csv.DictWriter(tempfile, tpcs.fieldnames)
    tempwriter.writeheader()
    updated = False

    for tpc in tpcs:
        logger.debug(f"Processing {tpc}")
        # reset csv file
        conferences_f.seek(0)
        conf_name, url_str = format_conf(tpc, conferences, tpc[CONF_STR], tpc[URL_STR])
        logger.debug(f"Got URL {url_str}")
        if url_str and url_str != 'none':
            logger.debug(f"Checking URL {url_str}")
            status = check_url(url_str)
            if (status != 200 and status != 'skipped'):
                logger.info(f"Removing {url_str} for {tpc}.")                
                tpc[URL_STR] = 'none'
                updated = True
        tempwriter.writerow(tpc)                  
           
    tpcs_f.close()
    conferences_f.close()
    tempfile.close()
    
    if updated:
        shutil.move(tpcs_file, os.path.splitext(tpcs_file)[0]+'-bak'+ os.path.splitext(tpcs_file)[1])
        shutil.move(tempfile.name, tpcs_file)
            
def main():
    parser = argparse.ArgumentParser(description='Generate Student tex/html file for TPCs')
    parser.add_argument('file', type=str, help='Input TPCs csv file')
    parser.add_argument('conferences', type=str, help='Conference names csv file')    
    parser.add_argument('-d', dest='debug', type=str, default='critical', choices = ['debug', 'info', 'error', 'critical'], help='Produce debug output')
    parser.add_argument('--tex_out', dest='tex_out', type=str, default='TPCs.tex', help='TPCs tex output file')
    parser.add_argument('--html_out', dest='html_out', type=str, default='tpcs.html', help='TPCs html output file')
    parser.add_argument('--fix_urls', dest='fix_urls', default=False, action='store_true', help='Fix URLs in csv file')
    parser.add_argument('--xml', dest='tpcs_xml', type=str, default='tpcs.xml', help='CCV XML output file')    
    parser.add_argument('--out_dir', dest='out_dir', type=str, default='', help='Output directory')
    args = parser.parse_args()   

    if (args.debug == 'debug'):
        logging.basicConfig(level=logging.DEBUG)
    elif (args.debug == 'info'):
        logging.basicConfig(level=logging.INFO)
    elif (args.debug == 'error'):
        logging.basicConfig(level=logging.ERROR)

    logger = logging.getLogger("gen_tpcs")
    
    if args.out_dir:
        tex_out = os.path.join(args.out_dir, os.path.basename(args.tex_out))
        xml_out = os.path.join(args.out_dir, os.path.basename(args.tpcs_xml))
        html_out = os.path.join(args.out_dir, os.path.basename(args.html_out))
    else:
        tex_out = args.tex_out
        html_out = args.html_out
        xml_out = args.tpcs_xml

    if args.fix_urls:
        fix_urls(args.file, args.conferences, logger, args.debug)
    else:
        gen_latex(tpcs_file=args.file, conferences_file=args.conferences, logger=logger, debug=args.debug, tex_out=tex_out)
        gen_html(tpcs_file=args.file, conferences_file=args.conferences, logger=logger, debug=args.debug, html_out=html_out)
        gen_xml(tpcs_file=args.file, conferences_file=args.conferences, logger=logger, debug=args.debug, xml_out=xml_out)

# Start program
if __name__ == "__main__":
    main()  