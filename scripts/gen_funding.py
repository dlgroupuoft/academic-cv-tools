#!/usr/bin/env python3

import argparse
from functools import cmp_to_key
from pylatexenc.latexencode  import unicode_to_latex
import logging
import os
import csv
import re
import uuid
from cv_utils import ordinal, latex_format, format_xml, field_present

YEAR_STR = 'year'
STATUS_STR = 'status'
TITLE_STR = 'title'
SPONSOR_STR = 'sponsor'
TOTAL_AMOUNT_STR = 'total_amount'
CURRENCY_STR = 'currency'
CO_PIS_STR = 'co_pis'
SHARE_STR = 'share'
TYPE_STR = 'type'
START_DATE_STR = 'start_date'
END_DATE_STR = 'end_date'
ORG_STR = 'organization'
PROGRAM_STR = 'program'
REF_NUMBER_STR = 'ref_number'
PI_STR = 'pi'
COMPETITIVE_STR = 'competitive'

def gen_latex_xml(funding_file, logger, debug, tex_out, total_tex_out, funding_xml):
    if os.name == 'nt':
        logger.info("Opening csv files in Windows mode")
        funding_f = open(funding_file,'r', newline='', )
    else:
        logger.info(f"Opening csv files in {os.name} mode")
        funding_f = open(funding_file,'r',encoding='utf-8-sig')
        
    funds = csv.DictReader(funding_f)
    
    tex_f = open(tex_out, 'w')
    total_tex_f = open(total_tex_out, 'w')
    total_funds = 0
    number_of_funds = 0
    
    xml_f = open(funding_xml, 'w')
    gen_xml_header(xml_f)
    for fund in funds:
        logger.debug(f"Processing {fund}")
        fund_str =  "\\begin{minipage}{\\linewidth}\n"
        fund_str = fund_str + f"\\textbf{{{latex_format(fund[STATUS_STR])}}}, \\textit{{{latex_format(fund[TITLE_STR])}}}, {latex_format(fund[SPONSOR_STR])}, \\textit{{\\${latex_format(fund[TOTAL_AMOUNT_STR])}}}" 
        if fund[CURRENCY_STR] != '':
            fund_str = fund_str + f" \\textit{{({latex_format(fund[CURRENCY_STR])})}}"
        #if fund[SHARE_STR] != '':
        #    fund_str = fund_str + f" (U of T's share: \\${latex_format(fund[SHARE_STR])})"
        year_str = latex_format(fund[YEAR_STR])
        # regex to replace - with --
        year_str = re.sub(r'(\d+)-(\d+)', r'\1--\2', year_str)
        fund_str = fund_str + f", {year_str}"        
        if fund[CO_PIS_STR] != '':
            fund_str = fund_str + f". Collaborators: {latex_format(fund[CO_PIS_STR])}"  
        fund_str = fund_str + ".\n\\vspace{6pt}\n\\end{minipage}\n"
        tex_f.write(fund_str)
        number_of_funds = number_of_funds + 1
        total_funds = total_funds + int(re.sub(",","",fund[TOTAL_AMOUNT_STR]))
        
        gen_xml_funding(xml_f, fund)
    tex_f.close()
    total_tex_f.write(f"\\newcommand{{\\numoffunds}}{{{number_of_funds}}}\n")
    total_tex_f.write(f"\\newcommand{{\\totalfunds}}{{\${'{:,}'.format(total_funds)}}}\n")
    total_tex_f.close()
    
    gen_xml_footer(xml_f)
    xml_f.close()
    
    funding_f.close()
    
def gen_xml_header(xml_f):
    xml_f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    xml_f.write('<generic-cv:generic-cv dateTimeGenerated="2016-03-26 09:43:18" lang="en" xmlns:generic-cv="http://www.cihr-irsc.gc.ca/generic-cv/1.0.0">\n')
    
def gen_xml_organization(xml_f, fund): 
            
    if field_present(ORG_STR, fund):
        other_org_str = ''
        if fund[ORG_STR] == 'NSERC':
            org_str = '<lov id="00000000000000000000000014012321">Natural Sciences and Engineering Research Council of Canada (NSERC)</lov>'
        elif fund[ORG_STR] == 'ONR':
            org_str = '<lov id="00000000000000000000000014012937">Office of Naval Research</lov>'
        elif fund[ORG_STR] == 'Connaught':
            org_str = '<lov id="00000000000000000000000014005013">Connaught Foundation (Ontario)</lov>'
        elif fund[ORG_STR] == 'Google':
            org_str = '<lov id="00000000000000000000000014008089">Google</lov>'
        elif fund[ORG_STR] == 'Telus':
            org_str = '<lov id="00000000000000000000000014016502">TELUS Mobility</lov>'
        elif fund[ORG_STR] == 'OPC':
            org_str = '<lov id="00000000000000000000000014012941">Office of the Privacy Commissioner of Canada</lov>'
        elif fund[ORG_STR] == 'OCE':
            org_str = '<lov id="00000000000000000000000014013024">Ontario Center of Excellence (OCE)</lov>'
        elif fund[ORG_STR] == 'MRI':
            org_str = '<lov id="00000000000000000000000014011635">Ministry of Research and Innovation (MRI) (Ontario)</lov>'
        elif fund[ORG_STR] == 'CSE':
            org_str = '<lov id="00000000000000000000000014004901">Communications Security Establishment (Canada)</lov>'
        elif fund[ORG_STR] == 'DND':
            org_str = '<lov id="00000000000000000000000014012125">National Defence (Canada)</lov>'
        else:
            org_str = ''        
            other_org_str = format_xml(fund[ORG_STR])
    else:
        org_str = ''
        other_org_str = format_xml(fund[SPONSOR_STR]) if field_present(SPONSOR_STR, fund) else ''
    
    if org_str:
        xml_f.write('\t\t\t<field id="67e083b070954e91bcbb1cc70131145a" label="Funding Organization">\n'                  
                f'\t\t\t\t{org_str}\n'
                '\t\t\t</field>\n'
                '\t\t\t<field id="1bdead14642545f3971a59997d82da67" label="Other Funding Organization">\n'
                '\t\t\t\t<value type="String"></value>\n'
                '\t\t\t</field>\n'
                )
    else:
        xml_f.write('\t\t\t<field id="67e083b070954e91bcbb1cc70131145a" label="Funding Organization"/>\n'
                    '\t\t\t<field id="1bdead14642545f3971a59997d82da67" label="Other Funding Organization">\n'
                    f'\t\t\t\t<value type="String">{other_org_str}</value>\n'
                    '\t\t\t</field>\n')
        
def xml_parse_copis(fund):
    if field_present(CO_PIS_STR,fund):
        # remove everything after semicolon
        names = fund[CO_PIS_STR].split(';')[0]
        # remove everything between brackets
        names = re.sub("[\(\[].*?[\)\]]", "", names)
        return names.split(',')
    else:
        return []

def gen_xml_funding(xml_f, fund):
    if not field_present(START_DATE_STR, fund) or not field_present(END_DATE_STR, fund) or not field_present(TITLE_STR, fund):
        return
    
    if fund[TYPE_STR] == 'Grant':      
        fund_type = '<lov id="00000000000000000000000100000900">Grant</lov>'        
    elif fund[TYPE_STR] == 'Contract':      
        fund_type = '<lov id="00000000000000000000000100000904">Contract</lov>'        
    elif fund[TYPE_STR] == 'Research Chair':
        fund_type = '<lov id="00000000000000000000000100000901">Research Chair</lov>'        
    else:
        raise Exception(f'Unknown funding type: {fund[TYPE_STR]}')    
    
    start_date = format_xml(fund[START_DATE_STR]) if field_present(START_DATE_STR, fund) else ''
    end_date = format_xml(fund[END_DATE_STR]) if field_present(END_DATE_STR, fund) else ''
    fund_title = format_xml(fund[TITLE_STR]) if field_present(TITLE_STR, fund) else ''
    program_name = format_xml(fund[PROGRAM_STR]) if field_present(PROGRAM_STR, fund) else ''    
    ref_number = format_xml(fund[REF_NUMBER_STR]) if field_present(REF_NUMBER_STR, fund) else ''
    currency = format_xml(fund[CURRENCY_STR]) if field_present(CURRENCY_STR, fund) else ''
    total_amount = format_xml(fund[TOTAL_AMOUNT_STR]) if field_present(TOTAL_AMOUNT_STR, fund) else ''
    share = format_xml(fund[SHARE_STR]) if field_present(SHARE_STR, fund) else total_amount        
    pi = format_xml(fund[PI_STR]) if field_present(PI_STR, fund) else ''
    if field_present(COMPETITIVE_STR, fund) and fund[COMPETITIVE_STR] == 'No':
        competitive = '<lov id="00000000000000000000000000000401">No</lov>'
    else:
        competitive = '<lov id="00000000000000000000000000000400">Yes</lov>'
    
    if (fund[STATUS_STR][:2] == 'PI'):
        role = '<lov id="00000000000000000000000100002800">Principal Investigator</lov>'
    elif (fund[STATUS_STR][:5] == 'Co-PI'):
        role = '<lov id="00000000000000000000000100002801">Co-investigator</lov>'
    else:
         raise Exception(f'Unknown funding role: {fund[STATUS_STR]}')    
    
    xml_f.write(f'\t<section id="aaedc5454412483d9131f7619d10279e" label="Research Funding History" recordId="{uuid.uuid4().hex}">\n'
            '\t\t<field id="931b92a5ffed4e5aa9c7b3a0afd5f8ba" label="Funding Type">\n'
            f'\t\t\t{fund_type}\n'
            '\t\t</field>\n'
            '\t\t<field id="9c1db4674334436ca891b7b8a9e114bd" label="Funding Start Date">\n'
            f'\t\t\t<value format="yyyy/MM" type="YearMonth">{start_date}</value>\n'
            '\t\t</field>\n'
            '\t\t<field id="b63179ab0f0e4c9eaa7e9a8130d60ee3" label="Funding End Date">\n'
            f'\t\t\t<value format="yyyy/MM" type="YearMonth">{end_date}</value>\n'
            '\t\t</field>\n'
            '\t\t<field id="735545eb499e4cc6a949b4b375a804e8" label="Funding Title">\n'
            f'\t\t\t<value type="String">{fund_title}</value>\n'
            '\t\t</field>\n'
            '\t\t<field id="c8e3451d1e3a405bb1e8aa0ebeb66c8d" label="Grant Type"/>\n'
            '\t\t<field id="0674312de78f4647aba3bf202a41d58e" label="Project Description">\n'
            '\t\t\t<value type="Bilingual"></value>\n'
            '\t\t\t<bilingual>\n'
            '\t\t\t\t<french></french>\n'
            '\t\t\t\t<english></english>\n'
            '\t\t\t</bilingual>\n'
            '\t\t</field>\n'
            '\t\t<field id="f7bfa6e647fd48cf8d404263df5843b1" label="Clinical Research Project?"/>\n'
            '\t\t<field id="0991ead151e3445ca7537aa15acbec57" label="Funding Status">\n'
            '\t\t\t<lov id="00000000000000000000000100000800">Awarded</lov>\n'
            '\t\t</field>\n'
            '\t\t<field id="7496de092dc84038a1881e8f9d77e713" label="Funding Role">\n'
            f'\t\t\t{role}\n'
            '\t\t</field>\n'
            '\t\t<field id="32ce1c0c194447c19c6847b1915d35f1" label="Research Uptake">\n'
            '\t\t\t<value type="Bilingual"></value>\n'
            '\t\t\t<bilingual>\n'
            '\t\t\t\t<french></french>\n'
            '\t\t\t\t<english></english>\n'
            '\t\t\t</bilingual>\n'
            '\t\t</field>\n'
            
            f'\t\t<section id="376b8991609f46059a3d66028f005360" label="Funding Sources" recordId="{uuid.uuid4().hex}">\n');
    gen_xml_organization(xml_f, fund)
    xml_f.write('\t\t\t<field id="97231512141a452a82151cc162e9a59c" label="Program Name">\n'
            f'\t\t\t\t<value type="String">{program_name}</value>\n'
            '\t\t\t</field>\n'
            '\t\t\t<field id="3fb9015d879f435d937ae9aa7ccd2973" label="Funding Reference Number">\n'
            f'\t\t\t\t<value type="String">{ref_number}</value>\n'
            '\t\t\t</field>\n'
            '\t\t\t<field id="dfe6a0b34347486aaa677f07306a141e" label="Total Funding">\n'
            f'\t\t\t\t<value type="Number">{total_amount}</value>\n'
            '\t\t\t</field>\n'
            '\t\t\t<field id="4775aa8f2a3f4f5083dd1c816462f260" label="Currency of Total Funding"/>\n'
            '\t\t\t<field id="882a94c7548744ca992e2647346d2e14" label="Portion of Funding Received">\n'
            f'\t\t\t\t<value type="Number">{share}</value>\n'
            '\t\t\t</field>\n'
            '\t\t\t<field id="a445f692a0d54760bcf2ed9c8a829eff" label="Funding Renewable?"/>\n'
            '\t\t\t<field id="00efdc7e790a48ac8675696c66afc3ad" label="Funding Competitive?">\n'
            f'\t\t\t\t{competitive}\n'
            '\t\t\t</field>\n'
            '\t\t\t<field id="d62313c1cdb9419caf79014f07e1cfe0" label="Funding Start Date">\n'
            f'\t\t\t\t<value format="yyyy/MM" type="YearMonth">{start_date}</value>\n'
            '\t\t\t</field>\n'
            '\t\t\t<field id="efc68e7d74f849eebb59f9a3bb85e5db" label="Funding End Date">\n'
            f'\t\t\t\t<value format="yyyy/MM" type="YearMonth">{end_date}</value>\n'
            '\t\t\t</field>\n'
            '\t\t</section>\n')
    for co_pi in xml_parse_copis(fund):
        xml_f.write(f'\t\t<section id="c7c473d1237b432fb7f2abd831130fb7" label="Other Investigators" recordId="{uuid.uuid4().hex}">\n'
            '\t\t\t<field id="ddd551dfb26344fbb17f07afcffc94ed" label="Investigator Name">\n'
            f'\t\t\t\t<value type="String">{format_xml(co_pi)}</value>\n'
            '\t\t\t</field>\n'
            '\t\t\t<field id="13806a6772d248158619261afaab2fe0" label="Role">\n')
        if format_xml(co_pi) == pi:
            xml_f.write('\t\t\t\t<lov id="00000000000000000000000100002800">Principal Investigator</lov>\n')
        else:
            xml_f.write('\t\t\t\t<lov id="00000000000000000000000100002801">Co-investigator</lov>\n')
        xml_f.write('\t\t\t</field>\n'
            '\t\t</section>\n')

    xml_f.write(f'\t</section>\n')
 
    
    return

def gen_xml_footer(xml_f):
    xml_f.write('</generic-cv:generic-cv>\n')    
    
def main():
    parser = argparse.ArgumentParser(description='Generate Student tex/html file for grants')
    parser.add_argument('file', type=str, help='Input funding csv file')
    parser.add_argument('-d', dest='debug', type=str, default='critical', choices = ['debug', 'info', 'error', 'critical'], help='Produce debug output')
    parser.add_argument('--tex_out', dest='tex_out', type=str, default='funding.tex', help='Funding tex output file')
    parser.add_argument('--total_tex_out', dest='total_tex_out', type=str, default='funding_total.tex', help='Funding Total tex output file')
    parser.add_argument('--xml', dest='funding_xml', type=str, default='funding.xml', help='CCV XML output file')    
    parser.add_argument('--out_dir', dest='out_dir', type=str, default='', help='Output directory')
    args = parser.parse_args()   

    if (args.debug == 'debug'):
        logging.basicConfig(level=logging.DEBUG)
    elif (args.debug == 'info'):
        logging.basicConfig(level=logging.INFO)
    elif (args.debug == 'error'):
        logging.basicConfig(level=logging.ERROR)

    logger = logging.getLogger("gen_funding")
    
    
    if args.out_dir:
        tex_out = os.path.join(args.out_dir, os.path.basename(args.tex_out))
        total_tex_out = os.path.join(args.out_dir, os.path.basename(args.total_tex_out))
        funding_xml = os.path.join(args.out_dir, os.path.basename(args.funding_xml))
    else:
        tex_out = args.tex_out
        total_tex_out = args.total_tex_out
        funding_xml = args.funding_xml
    gen_latex_xml(funding_file=args.file, logger=logger, debug=args.debug, tex_out=tex_out, total_tex_out=total_tex_out, funding_xml=funding_xml)    

# Start program
if __name__ == "__main__":
    main()  