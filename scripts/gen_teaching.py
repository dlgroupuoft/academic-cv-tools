#!/usr/bin/env python3

import argparse
from datetime import datetime
from functools import cmp_to_key
from pylatexenc.latexencode  import unicode_to_latex
import logging
import os
import csv

def field_present(field_name, dict):
    return (field_name in dict.keys() and dict[field_name])

def class_sort_fn(i, j):    
    if (i['Year'] > j['Year']):
        return -1
    else:
        return 1


def gen_course_latex(tex_f, courses):    
    for course in courses:
        course_str = f"{course['Year']} & {course['Code']} & {course['Title']} & {course['Enrollment']} \\\\ \n"        
        tex_f.write(course_str)


def gen_latex(csvfile, logger, grad_tex, ug_tex):
    if os.name == 'nt':
        logger.info("Opening " + csvfile + " in Windows mode")
        csv_in_f = open(csvfile,'r', newline='', fileEncoding="UTF-8-BOM")
    else:
        csv_in_f = open(csvfile,'r')

    csv_in = csv.DictReader(csv_in_f)
    grad_sorted = sorted(
        filter(lambda course: course['Type'].strip() == 'Grad', csv_in), 
        key=cmp_to_key(lambda i, j:(class_sort_fn(i=i, j=j))))
    tex_f = open(grad_tex, 'w')
    tex_f.write(r"""\begin{classtab}""" +"\n")
    gen_course_latex(tex_f, grad_sorted)
    tex_f.write(r"""\end{classtab}"""+ "\n")
    tex_f.close()

    # reset csv file
    csv_in_f.seek(0)
    csv_in.__next__()    

    ug_sorted = sorted(
        filter(lambda course: course['Type'].strip() == 'UG', csv_in), 
        key=cmp_to_key(lambda i, j:(class_sort_fn(i=i, j=j))))
    tex_f = open(ug_tex, 'w')
    tex_f.write(r"""\begin{classtab}""" +"\n")
    gen_course_latex(tex_f, ug_sorted)
    tex_f.write(r"""\end{classtab}"""+ "\n")
    tex_f.close()

def main():
    parser = argparse.ArgumentParser(description='Generate Teaching tex file for CV')
    parser.add_argument('file', type=str, help='Input csv file')
    parser.add_argument('-d', dest='debug', type=str, default='critical', choices = ['debug', 'info', 'error', 'critical'], help='Produce debug output')
    parser.add_argument('--grad_tex', dest='grad_tex', type=str, default='grad_teaching.tex', help='Grad Teaching Tex output file')
    parser.add_argument('--ug_tex', dest='ug_tex', type=str, default='ug_teaching.tex', help='UG Teaching Tex output file')
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
        grad_tex = os.path.join(args.out_dir, os.path.basename(args.grad_tex))
        ug_tex = os.path.join(args.out_dir, os.path.basename(args.ug_tex))
    else:
        grad_tex = args.grad_tex
        ug_tex = args.ug_tex

    gen_latex(csvfile=args.file, logger=logger, grad_tex=grad_tex, ug_tex=ug_tex)

    

# Start program
if __name__ == "__main__":
    main()