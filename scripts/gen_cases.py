#!/usr/bin/env python3

import argparse
from datetime import datetime
from functools import cmp_to_key
import logging
import os
import csv
from cv_utils import latex_format

TITLE = 'title'
PLAINTIFF = 'plaintiff'
DEFENDANT = 'defendant'
ROLE = 'role'
JURISDICTION = 'jurisdiction'
CASE = 'case'
YEAR = 'year'

def gen_latex(csvfile, logger, tex_out):
    if os.name == 'nt':
        logger.info("Opening csv files in Windows mode")
        cases_f = open(csvfile,'r', newline='', )
    else:
        logger.info(f"Opening csv files in {os.name} mode")
        cases_f = open(csvfile,'r',encoding='utf-8-sig')
        
    cases = csv.DictReader(cases_f)
    tex_f = open(tex_out, 'w')
    
    for case in cases:
        logger.debug(f"Processing {case}")
        case_str =  "\\begin{minipage}{\\linewidth}\n"
        case_str = case_str + f"\\textit{{{latex_format(case[TITLE]) if case[TITLE] else ''}{latex_format(case[PLAINTIFF]) + ' v. ' + latex_format(case[DEFENDANT]) if (case[PLAINTIFF] and case[DEFENDANT]) else ''}}}, Expert {case[ROLE]}{', ' + latex_format(case[JURISDICTION]) if case[JURISDICTION] != ''else ''}{', Case no. ' + latex_format(case[CASE]) if case[CASE] else ''}{', ' + case[YEAR] if case[YEAR] else ''}"
        case_str = case_str + ".\n\\vspace{6pt}\n\\end{minipage}\n"
        tex_f.write(case_str)
    tex_f.close()
    cases_f.close()
    

def main():
    parser = argparse.ArgumentParser(description='Generate Cases tex file for CV')
    parser.add_argument('file', type=str, help='Input csv file')
    parser.add_argument('-d', dest='debug', type=str, default='critical', choices = ['debug', 'info', 'error', 'critical'], help='Produce debug output')
    parser.add_argument('--tex_out', dest='cases_tex', type=str, default='cases.tex', help='Case Tex output file')
    parser.add_argument('--out_dir', dest='out_dir', type=str, default='', help='Output directory')
    args = parser.parse_args()   

    if (args.debug == 'debug'):
        logging.basicConfig(level=logging.DEBUG)
    elif (args.debug == 'info'):
        logging.basicConfig(level=logging.INFO)
    elif (args.debug == 'error'):
        logging.basicConfig(level=logging.ERROR)

    logger = logging.getLogger("gen_cases")
    
    if args.out_dir:
        cases_tex = os.path.join(args.out_dir, os.path.basename(args.cases_tex))        
    else:
        cases_tex = args.cases_tex
        
    gen_latex(csvfile=args.file, logger=logger, tex_out=cases_tex)

# Start program
if __name__ == "__main__":
    main()