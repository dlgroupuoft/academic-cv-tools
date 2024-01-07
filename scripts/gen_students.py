#!/usr/bin/env python3

import argparse
from datetime import datetime
from functools import cmp_to_key
from pylatexenc.latexencode import unicode_to_latex
from dateutil.relativedelta import relativedelta
from cv_utils import extract_year, extract_month, format_xml, field_present
import logging
import os
import csv
import uuid
import dateutil.parser as dparser

LAST_KNOWN_STR = "Last known position"
PDF_TYPE = "PDF"
PHD_TYPE = "PhD"
MS_TYPE = "MS"
MENG_TYPE = "MEng"
UG_TYPE = "UG"

def student_type(student):
    if field_present('PDF Start Date', student):
        return PDF_TYPE
    elif field_present('PhD Start Date', student):
        return PHD_TYPE
    elif field_present('MS Start Date', student):   
        return MS_TYPE
    elif field_present('MEng Start Date', student):
        return MENG_TYPE
    elif field_present('UG Start Date', student):
        return UG_TYPE
    else:
        raise ValueError("Unknown Student type")

def sort_by_completed(i, j, type):
    start_date = type + " Start Date"
    end_date = type + " End Date"

    i_end = i[end_date] if field_present(end_date,i) else ''    
    j_end = j[end_date] if field_present(end_date,j) else ''

    # Put incomplete students first
    if not i_end and j_end:       
        return -1
    elif not j_end and i_end:        
        return 1
    else:
        return 0

def sort_by_end_date(i, j, type):    
    end_date = type + " End Date"

    if field_present(end_date,i) and field_present(end_date,j):
        i_end = i[end_date]
        j_end = j[end_date]
        
        i_end_date = dparser.parse(i_end, fuzzy=False)
        j_end_date = dparser.parse(j_end, fuzzy=False)
        if i_end_date < j_end_date:
            return 1
        elif j_end_date < i_end_date:
            return -1
        else:            
            return 0
    else:
        return 0

def sort_by_start_date(i, j, type):
    start_date = type + " Start Date"
    assert field_present(start_date, i) and field_present(start_date, j)
    i_start = i[start_date]
    j_start = j[start_date]
    
    i_start_date = dparser.parse(i_start, fuzzy=False)
    j_start_date = dparser.parse(j_start, fuzzy=False)
    
    if i_start_date < j_start_date:
        return 1
    elif j_start_date < i_start_date:
        return -1
    else:            
        return 0

def sort_by_last_name(i,j):
    # break tie by last name        
    assert field_present('Last Name', i) and field_present('Last Name', j)
    return -1 if i['Last Name'] < j['Last Name'] else 1    

def prefix_new(file):
    return os.path.dirname(file) + "/new_" + os.path.basename(file)

def student_sort_fn(i, j, type):
    start_date = type + " Start Date"
    end_date = type + " End Date"

    assert field_present(start_date, i) and field_present(start_date, j)
    i_start = i[start_date]
    i_end = i[end_date] if field_present(end_date,i) else ''
    j_start = j[start_date]
    j_end = j[end_date] if field_present(end_date,j) else ''

    # Put incomplete students first
    if not i_end and j_end:       
        return -1
    elif not j_end and i_end:        
        return 1
    # if both incomplete sort by start date            
    elif not i_end and not j_end:
        i_start_date = dparser.parse(i_start, fuzzy=False)
        j_start_date = dparser.parse(j_start, fuzzy=False)
        
        if i_start_date < j_start_date:
            return 1
        elif j_start_date < i_start_date:
            return -1
        else:            
            # break tie by last name        
            return -1 if i['Last Name'] < j['Last Name'] else 1
    # else if both complete sort by end_date
    else:
        i_end_date = dparser.parse(i_end, fuzzy=False)
        j_end_date = dparser.parse(j_end, fuzzy=False)
        
        if i_end_date < j_end_date:
            return 1
        elif j_end_date < i_end_date:
            return -1
        else:            
            # break tie by last name        
            return -1 if i['Last Name'] < j['Last Name'] else 1

def gen_key_names (student_type):
    start_date_key = student_type + ' Start Date'
    end_date_key = student_type + ' End Date'
    thesis_key = student_type + ' Thesis'
    thesis_url_key = student_type + ' Thesis URL'
    cosup_key = student_type + ' Co-Supervisor'
    last_pos_key = student_type + ' Last Position'
    program_key = student_type + ' Program'
    external_key = 'PhD External Examiner'

    return start_date_key, end_date_key, thesis_key, thesis_url_key, cosup_key, last_pos_key, program_key, external_key 

def gen_tex_table(tex_file, csv, student_type, cosup_list):

    start_date_key, end_date_key, thesis_key, thesis_url_key, cosup_key, last_pos_key, program_key, external_key = gen_key_names(student_type)
    
    stats_current = 0
    stats_completed = 0

    tex_f = open(tex_file, 'w')
    new_tex_f = open(prefix_new(tex_file), 'w')
    if student_type == PDF_TYPE:                      
        tex_f.write(r"""\begin{longtable}[h]{|p{\namelength}|p{\datelength}|p{\textwidth-\datelength-\datelength-30pt}|} \hline
                    \multicolumn{1}{|c|}{\bf Name} &
                    \multicolumn{1}{|c|}{\bf Dates} &  
                    \multicolumn{1}{|c|}{\bf Current Position} \\ 
                    \hline""")
    else:
        tex_f.write(r"""\begin{longtable}[h]{|p{\namelength}|p{\textwidth-\namelength-\datelength-30pt}|p{\datelength}|}
                        \hline
                        \multicolumn{1}{|c|}{\bf Name} &
                        \multicolumn{1}{|c|}{\bf Thesis Title} &
                        \multicolumn{1}{|c|}{\bf Dates \& } \\ 
                        \multicolumn{1}{|c|}{\bf } &
                        \multicolumn{1}{|c|}{\bf } & 
                        \multicolumn{1}{|c|}{\bf Last Pos.} \\ \hline \hline """)
    new_tex_f.write(r"""\vspace{2pt}""")
    for student in csv:        
        if (start_date_key in student.keys() and student[start_date_key]):          
            # updated stats
            if end_date_key in student.keys() and student[end_date_key]:
                stats_completed = stats_completed + 1
            else:
                stats_current = stats_current + 1
            # extract information
            if ('Home Page' in student.keys() and student['Home Page']):
                name_str = f"\href{{{student['Home Page']}}}{{{unicode_to_latex(student['First Name'].strip())} {unicode_to_latex(student['Last Name'].strip())}}}"
            else:
                name_str = f"{unicode_to_latex(student['First Name'].strip())} {unicode_to_latex(student['Last Name'].strip())}"
            if (program_key in student.keys() and student[program_key]):
                program_str = f"{unicode_to_latex(student[program_key].strip())}"
            else:
                program_str = ''
            if (thesis_key in student.keys() and student[thesis_key]):
                if (thesis_url_key in student.keys() and student[thesis_url_key]):
                    title_str = f"\href{{{student[thesis_url_key].strip()}}}{{{unicode_to_latex(student[thesis_key].strip())}}}"
                else:
                    title_str = f"{unicode_to_latex(student[thesis_key].strip())}"
            else:
                title_str = ''  
            start_date_str = dparser.parse(student[start_date_key], fuzzy=False).strftime('%m/%Y')
            end_date_str = dparser.parse(student[end_date_key], fuzzy=False).strftime('%m/%Y') \
                if end_date_key in student.keys() and student[end_date_key] else ''             
            date_str = f"{start_date_str}--{end_date_str}"
            if (cosup_key in student.keys() and student[cosup_key]):
                try:    
                    i = cosup_list.index(student[cosup_key]) + 1 
                except ValueError: 
                    cosup_list.append(student[cosup_key])
                    i = len(cosup_list)
                except:
                    # we shouldn't get here
                    exit()
                cosup_str = f"\\footnotemark[{i}]"
            else:
                cosup_str = ''
            new_student_str = "\\begin{minipage}{\\linewidth}\n"
            
            if student_type == PDF_TYPE:                      
                if (last_pos_key in student.keys()  and student[last_pos_key]):
                    student_str = f"{name_str}{cosup_str} & {date_str} & {unicode_to_latex(student[last_pos_key].strip())}\\\\ \hline\n"
                    new_student_str = new_student_str + ( 
                                        f"{{\\bfseries{{{name_str}{cosup_str} \\hfill {date_str}}}}}\\\\\n" 
                                        f"Current Position: {unicode_to_latex(student[last_pos_key].strip())}\n")
                else:
                    student_str = f"{name_str}{cosup_str} & {date_str} & \\\\ \hline\n"            
                    new_student_str = new_student_str + f"\\bfseries{{{name_str}{cosup_str} \\hfill {date_str}}}\n"
            elif student_type == UG_TYPE or student_type == MENG_TYPE:
                student_str = f"{name_str}{cosup_str} & {title_str} & {date_str} \\\\ \hline\n"                          
                # MENG students don't have an explicit program, so they default to ECE        
                new_student_str = new_student_str + f"{{\\bfseries{{{name_str}{cosup_str}{', ' + program_str if program_str else ', ECE'} \\hfill {date_str}}}}}"
                if (title_str):
                    new_student_str = new_student_str + f"\\\\\n{{Project: {title_str}}}\n"
                else:                                         
                    new_student_str = new_student_str + "\n"
            else:
                if (last_pos_key in student.keys()  and student[last_pos_key]):
                    student_str = f"{name_str}{cosup_str} & {title_str} & \makecell[l]{{{date_str} \\\\ {unicode_to_latex(student[last_pos_key].strip())}}}\\\\ \hline\n"                                      
                else:
                    student_str = f"{name_str}{cosup_str} & {title_str} & {date_str} \\\\ \hline\n"                                  
                new_student_str = new_student_str + f"{{\\bfseries{{{name_str}{cosup_str}{', ' + program_str if program_str else ''} \\hfill {date_str}}}}}" 
                if (title_str):
                    new_student_str = new_student_str + f"\\\\\n{{Thesis: {title_str}}}\n"                                         
                    if (student_type == PHD_TYPE):
                        if external_key in student.keys() and student[external_key]:
                            new_student_str = new_student_str + f"\\\\\nExternal Examiner: {unicode_to_latex(student[external_key].strip())}"
                            if (last_pos_key in student.keys()  and student[last_pos_key]):
                                new_student_str = new_student_str + ", "
                            else:
                                new_student_str = new_student_str + "\n"
                        if (last_pos_key in student.keys()  and student[last_pos_key]):
                            new_student_str = new_student_str +  f"Current Position: {unicode_to_latex(student[last_pos_key].strip())}\n"                                    
                    else:
                        if ('PhD Last Position' in student.keys() and student['PhD Last Position'] != ""):
                            new_student_str = new_student_str +  f"\\\\\nCurrent Position: {unicode_to_latex(student['PhD Last Position'].strip())}\n"                                                                
                        elif (last_pos_key in student.keys() and student[last_pos_key]):
                            new_student_str = new_student_str +  f"\\\\\nCurrent Position: {unicode_to_latex(student[last_pos_key].strip())}\n"                                    
                else:                                         
                    new_student_str = new_student_str + "\n"
            if title_str or (last_pos_key in student.keys()  and student[last_pos_key]):
                new_student_str = new_student_str +  "\\vspace{6pt}\n\\end{minipage}\n"
            else:
                new_student_str = new_student_str +  "\\vspace{4pt}\n\\end{minipage}\n"
            tex_f.write(student_str)
            new_tex_f.write(new_student_str)
    tex_f.write(r"\end{longtable}")
    tex_f.close()
    new_tex_f.close()
    return (stats_completed, stats_current)
    

def gen_latex(csvfile, logger, phd_tex, phd_foot, ms_tex, ms_foot, pdf_tex, ug_tex, meng_tex, stats_tex):
    if os.name == 'nt':
        logger.info("Opening " + csvfile + " in Windows mode")
        csv_in_f = open(csvfile,'r', newline='')
    else:
        csv_in_f = open(csvfile,'r')

    stats_current_phd = 0
    stats_completed_phd = 0
    stats_current_ms = 0
    stats_completed_ms = 0
    stats_current_meng = 0
    stats_completed_meng = 0
    stats_current_pdf = 0
    stats_completed_pdf = 0
    stats_current_ug = 0
    stats_past_ug = 0

    csv_in = csv.DictReader(csv_in_f)
    phd_sorted = sorted(
        filter(lambda student: field_present('PhD Start Date',student), csv_in), 
        key=cmp_to_key(lambda i, j:(student_sort_fn(i=i, j=j, type=PHD_TYPE))))

    cosups = []

    stats_completed_phd, stats_current_phd = gen_tex_table(tex_file=phd_tex, csv=phd_sorted, student_type=PHD_TYPE, cosup_list=cosups)
    num_phd_cosups = len(cosups)

    with open(phd_foot, 'w') as tex_foot:        
        for cosup in cosups:                            
            tex_foot.write(f"\\footnotetext{{Co-supervised with {unicode_to_latex(cosup)}.}}\n")            
            tex_foot.write("\stepcounter{footnote}\n")            
        tex_foot.close()

    # reset csv file
    csv_in_f.seek(0)
    csv_in.__next__()
        
    ms_sorted = sorted(filter(lambda student: field_present('MS Start Date', student), csv_in), 
        key=cmp_to_key(lambda i, j: student_sort_fn(i=i, j=j, type=MS_TYPE)))

    stats_completed_ms, stats_current_ms = gen_tex_table(tex_file=ms_tex, csv=ms_sorted, student_type=MS_TYPE, cosup_list=cosups)

    with open(ms_foot, 'w') as tex_foot:
        cosups_printed=False
        for cosup in cosups:
            if (cosups.index(cosup) >= num_phd_cosups):
                if cosups_printed:
                    tex_foot.write("\stepcounter\{footnote\}\n")             
                tex_foot.write(f"\\footnotetext{{Co-supervised with {unicode_to_latex(cosup)}.}}\n")            
                cosups_printed=True                
        tex_foot.close() 

    csv_in_f.seek(0)
    csv_in.__next__() 

    pdf_sorted = sorted(filter(lambda student: field_present('PDF Start Date',student), csv_in), 
        key=cmp_to_key(lambda i, j: student_sort_fn(i=i, j=j, type=PDF_TYPE)))
    stats_completed_pdf, stats_current_pdf = gen_tex_table(tex_file=pdf_tex, csv=pdf_sorted, student_type=PDF_TYPE, cosup_list=cosups)

    csv_in_f.seek(0)
    csv_in.__next__() 

    meng_sorted = sorted(filter(lambda student: field_present('MEng Start Date',student), csv_in), 
        key=cmp_to_key(lambda i, j: student_sort_fn(i=i, j=j, type=MENG_TYPE)))
    stats_completed_meng, stats_current_meng = gen_tex_table(tex_file=meng_tex, csv=meng_sorted, student_type=MENG_TYPE, cosup_list=cosups)

    csv_in_f.seek(0)
    csv_in.__next__() 

    ug_sorted = sorted(filter(lambda student: field_present('UG Start Date',student), csv_in), 
        key=cmp_to_key(lambda i, j: student_sort_fn(i=i, j=j, type=UG_TYPE)))
    stats_past_ug, stats_current_ug = gen_tex_table(tex_file=ug_tex, csv=ug_sorted, student_type=UG_TYPE, cosup_list=cosups)

    stats_f = open(stats_tex, 'w')
    stats_f.write(f"\\newcommand{{\\numcompletedphd}}{{{stats_completed_phd}}}\n")
    stats_f.write(f"\\newcommand{{\\numcurrentphd}}{{{stats_current_phd}}}\n")
    stats_f.write(f"\\newcommand{{\\numcompletedms}}{{{stats_completed_ms}}}\n")
    stats_f.write(f"\\newcommand{{\\numcurrentms}}{{{stats_current_ms}}}\n")
    stats_f.write(f"\\newcommand{{\\numcompletedpdf}}{{{stats_completed_pdf}}}\n")
    stats_f.write(f"\\newcommand{{\\numcurrentpdf}}{{{stats_current_pdf}}}\n")    
    stats_f.write(f"\\newcommand{{\\numcompletedmeng}}{{{stats_completed_meng}}}\n")
    stats_f.write(f"\\newcommand{{\\numcurrentmeng}}{{{stats_current_meng}}}\n")    
    stats_f.write(f"\\newcommand{{\\numpastug}}{{{stats_past_ug}}}\n")
    stats_f.write(f"\\newcommand{{\\numcurrentug}}{{{stats_current_ug}}}\n")    
    stats_f.close()


def output_html_name(student):
    if field_present('Home Page', student):
        return f"<a href=\"{student['Home Page']}\">{student['First Name'].strip()} {student['Last Name'].strip()}</a>"
    else:
        return f"{student['First Name'].strip()} {student['Last Name'].strip()}"

def output_html_thesis(type, student):
    thesis_field = type + ' Thesis'
    thesis_url_field = type + ' Thesis URL'

    if field_present(thesis_field, student):        
        if field_present(thesis_url_field, student):
            return f"<a href=\"{student[thesis_url_field].strip()}\">{student[thesis_field].strip()}</a>"
        else:
            return f"{student[thesis_field].strip()}"
    else:
        return ""

def output_html_cosup(type, student):
    cosup_field = type + ' Co-Supervisor'
    if field_present(cosup_field, student):
        return f"Co-supervised with {student[cosup_field].strip()}"
    else:
        return ""

def output_html_position(type, student):
    pos_field = type + ' Last Position'
    if field_present(pos_field, student):
        return f"{LAST_KNOWN_STR}: {student[pos_field].strip()}"
    else:
        return ""

def output_html_end_year(type, student):
    end_date_field = type + " End Date"
    assert(field_present(end_date_field,student))
    retval = dparser.parse(student[end_date_field], fuzzy=False).strftime('%Y')
    return retval

def output_html_program(type, student):
    program_field = type + " Program"
    assert(field_present(program_field,student))
    return student[program_field].strip()


def sort_students(csvfile, logger):
    # sort students
    current_phd = []
    current_ms = []
    current_meng = []
    current_pdf = []
    current_ug = []
    past_phd = []
    past_ms = []
    past_meng = []
    past_pdf = []
    past_ug = []

    if os.name == 'nt':
        logger.info("Opening " + csvfile + " in Windows mode")
        csv_in_f = open(csvfile,'r', newline='')
    else:
        csv_in_f = open(csvfile,'r')
    csv_in = csv.DictReader(csv_in_f)
    for student in csv_in:
        # current PDF
        if (field_present('PDF Start Date',student) and not field_present('PDF End Date',student)):
            current_pdf.append(student)
        # current PhD student
        elif (field_present('PhD Start Date',student) and not field_present('PhD End Date',student)):
            current_phd.append(student)
        # current MS student
        elif (field_present('MS Start Date',student) and not field_present('MS End Date',student)):
            current_ms.append(student)
        # current MEng student
        elif (field_present('MEng Start Date',student) and not field_present('MEng End Date',student)):
            current_meng.append(student)
        # current UG student
        elif (field_present('UG Start Date',student) and not field_present('UG End Date',student)):
            current_ug.append(student)
        # past students        
        if (field_present('PDF End Date',student)):
            past_pdf.append(student)
        if (field_present('PhD End Date',student)):
            past_phd.append(student)
        if (field_present('MS End Date',student)):
            past_ms.append(student)
        if (field_present('MEng End Date',student)):
            past_meng.append(student)
        if (field_present('UG End Date',student)):
            past_ug.append(student)
    csv_in_f.close()

    return current_phd, current_ms, current_meng, current_pdf, current_ug, past_phd, past_ms, past_meng, past_pdf, past_ug

def gen_html(current_phd, current_ms, current_pdf, current_ug, past_phd, past_ms, past_pdf, logger, students_html):
    html = open(students_html, 'w')
  
    html.write('<div class="elementor-element elementor-element-7cc73994 elementor-drop-cap-yes student elementor-drop-cap-view-default elementor-widget elementor-widget-text-editor" data-id="7cc73994" data-element_type="widget" data-settings="{&quot;drop_cap&quot;:&quot;yes&quot;}" data-widget_type="text-editor.default">')
    html.write('<div class="elementor-text-editor elementor-clearfix">')
    
    # current PDFs
    if len(current_pdf):
        html.write('<h3>Post-Doctoral Fellows</h3>\n<ul>\n')
        for student in sorted(current_pdf,key=cmp_to_key(    
            lambda i, j: (-sort_by_start_date(i=i , j=j, type=PDF_TYPE) if 
                sort_by_start_date(i=i , j=j, type=PDF_TYPE) else sort_by_last_name(i=i, j=j)))):
            html.write("<li>" + output_html_name(student) + output_html_cosup(PDF_TYPE, student)+"</li>\n")        
        html.write('</ul>\n')

    # current PhD students
    if len(current_phd):
        html.write('<h3>PhD Students</h3>\n<ul>\n')
        for student in sorted(current_phd,key=cmp_to_key(
            lambda i, j: (-sort_by_start_date(i=i , j=j, type=PHD_TYPE) if 
                sort_by_start_date(i=i , j=j, type=PHD_TYPE) else sort_by_last_name(i=i, j=j)))):
            if field_present('PhD Co-Supervisor', student):
                html.write(f"<li>{output_html_name(student)} ({output_html_program(PHD_TYPE,student)}, {output_html_cosup(PHD_TYPE, student)})</li>\n")
            else:
                html.write(f"<li>{output_html_name(student)} ({output_html_program(PHD_TYPE, student)})</li>\n")        
        html.write('</ul>\n')

    # current MS students
    if len(current_ms):
        html.write('<h3>Master\'s Students</h3>\n<ul>\n')
        for student in sorted(current_ms,key=cmp_to_key(    
            lambda i, j: (-sort_by_start_date(i=i , j=j, type=MS_TYPE) if 
                sort_by_start_date(i=i , j=j, type=MS_TYPE) else sort_by_last_name(i=i, j=j)))):
            if field_present('MS Co-Supervisor', student):
                html.write(f"<li>{output_html_name(student)} ({output_html_program(MS_TYPE, student)}, {output_html_cosup(MS_TYPE, student)})</li>\n")
            else:
                html.write(f"<li>{output_html_name(student)} ({output_html_program(MS_TYPE, student)})</li>\n")        
        html.write('</ul>\n')  
        
     # current UG
    if len(current_ug):
        html.write('<h3>Undergraduate Students and Research Interns</h3>\n<ul>\n')
        for student in sorted(current_ug,key=cmp_to_key(    
            lambda i, j: (-sort_by_start_date(i=i , j=j, type=UG_TYPE) if 
                sort_by_start_date(i=i , j=j, type=UG_TYPE) else sort_by_last_name(i=i, j=j)))):
            html.write(f"<li>{output_html_name(student)} ({output_html_program(UG_TYPE, student)})</li>\n")                    
        html.write('</ul>\n')

    html.write('<h3>Alumni</h3>\n')
    # past PDFs
    if len(past_pdf):
        html.write('<h4>Post-Doctoral Fellows</h4>\n<ul>\n')
        for student in sorted(past_pdf,key=cmp_to_key(    
            lambda i, j: (-sort_by_end_date(i=i , j=j, type=PDF_TYPE) if 
                sort_by_end_date(i=i , j=j, type=PDF_TYPE) else sort_by_last_name(i=i, j=j)))):
            if (field_present('PDF Last Position', student)):
                html.write(f"<li>{output_html_name(student)}, {output_html_end_year(PDF_TYPE, student)}. {output_html_position(PDF_TYPE,student)}.</li>\n")        
            else:
                html.write(f"<li>{output_html_name(student)}, {output_html_end_year(PDF_TYPE, student)}.</li>\n")        
        html.write('</ul>\n')

    # past PhD
    if len(past_phd):
        html.write('<h4>PhD Students</h4>\n<ul>\n')
        for student in sorted(past_phd,key=cmp_to_key(    
            lambda i, j: (-sort_by_end_date(i=i , j=j, type=PHD_TYPE) if 
                sort_by_end_date(i=i , j=j, type=PHD_TYPE) else sort_by_last_name(i=i, j=j)))):
            if (field_present('PhD Last Position', student)):
                html.write(f"<li>{output_html_name(student)} ({output_html_program(PHD_TYPE, student)}): {output_html_thesis(PHD_TYPE, student)}, {output_html_end_year(PHD_TYPE, student)}. {output_html_position(PHD_TYPE,student)}.</li>\n")        
            else:
                html.write(f"<li>{output_html_name(student)} ({output_html_program(PHD_TYPE, student)}): {output_html_thesis(PHD_TYPE, student)}, {output_html_end_year(PHD_TYPE, student)}.</li>\n")        
        html.write('</ul>\n')

    # past MS
    if len(past_phd):
        html.write('<h4>Master\'s Students</h4>\n<ul>\n')
        for student in sorted(past_ms,key=cmp_to_key(    
            lambda i, j: (-sort_by_end_date(i=i , j=j, type=MS_TYPE) if 
                sort_by_end_date(i=i , j=j, type=MS_TYPE) else sort_by_last_name(i=i, j=j)))):
            # Current PhD students don't have a post-master's position
            if (not field_present('MS Last Position',student)):
                html.write(f"<li>{output_html_name(student)} ({output_html_program(MS_TYPE, student)}): {output_html_thesis(MS_TYPE, student)}, {output_html_end_year(MS_TYPE, student)}.</li>\n")        
            else:
                html.write(f"<li>{output_html_name(student)} ({output_html_program(MS_TYPE, student)}): {output_html_thesis(MS_TYPE, student)}, {output_html_end_year(MS_TYPE, student)}. {output_html_position(MS_TYPE,student)}.</li>\n")        
        html.write('</ul>\n')

    html.write('</div></div>')
    html.close()

student_type2ccv_type = { PDF_TYPE: PDF_TYPE, PHD_TYPE: PHD_TYPE, MS_TYPE: 'Master', UG_TYPE: 'Undergraduate'}

def anticipated_completion_date(student):
    # the later of 1 year from now or 4 years from start of PhD, 2 years from start of Masters
    start_date_str = student_type(student) + ' Start Date'
       
    if student_type(student) == PHD_TYPE:
        degree_length = 4
    elif student_type(student) == MS_TYPE or student_type(student) == MENG_TYPE or student_type(student) == PDF_TYPE:
        degree_length = 2
    elif student_type(student) == UG_TYPE:
        degree_length = 1
    else:
        raise Exception('Unknown student type: ' + student_type(student))
    start_date = dparser.parse(student[start_date_str], fuzzy=False)
    expected_completion_date = start_date + relativedelta(years=degree_length)
    
    if expected_completion_date > datetime.now():
        return expected_completion_date
    else:
        return datetime.now() + relativedelta(years=1)
    
def students2ccv(fid,students,type,status,ccv_years):
 
    start_date_key, end_date_key, thesis_key, thesis_url_key, cosup_key, last_pos_key, program_key, external_key = gen_key_names(type)    
    
    count = 0
    
    # Output record for each student
    for student in students:
        today = datetime.today()
        if extract_year(student[end_date_key]) and (today.year - int(extract_year(student[end_date_key])) > ccv_years) and ccv_years > 0:
            continue   		
        count += 1
        
        # generates a random uuid
        fid.write('			<section id="4b36fa1eef2549f6ab3a3df7c1c81e0b" label="Student/Postdoctoral Supervision" recordId="{}">\n'.format(
            uuid.uuid4().hex))
        fid.write('				<field id="78a3e68f1ab74f31b9284c2acdb70739" label="Supervision Role">\n')
        # COsupervision or not
        if field_present(cosup_key,student):
            fid.write('					<lov id="00000000000000000000000100002901">Co-Supervisor</lov>\n')
        else:
            fid.write('					<lov id="00000000000000000000000100002900">Principal Supervisor</lov>\n')
        fid.write('				</field>\n')
        fid.write('				<field id="19964df0a8524f2bb44d5eb53729f9cc" label="Supervision Start Date">\n')
        fid.write('					<value format="yyyy/MM" type="YearMonth">{}/{}</value>\n'.format(extract_year(student[start_date_key]),extract_month(student[start_date_key])))
        fid.write('				</field>\n')
        fid.write('				<field id="bd3619f7970441dc83ada1d2fdbf0780" label="Supervision End Date">\n')
        if field_present(end_date_key,student):
            fid.write('					<value format="yyyy/MM" type="YearMonth">{}/{}</value>\n'.format(extract_year(student[end_date_key]),extract_month(student[end_date_key])))
        else:
            fid.write('					<value format="yyyy/MM" type="YearMonth">{}</value>\n'.format(anticipated_completion_date(student).strftime('%Y/%m')))
        fid.write('				</field>\n')
        fid.write('				<field id="3c504aafda28418ea439d8f92c28aef0" label="Student Name">\n')
        fid.write('					<value type="String">{} {}</value>\n'.format(format_xml(student["First Name"]), format_xml(student["Last Name"])))
        fid.write('				</field>\n')
        fid.write('				<field id="e36ccf9a00a241dc942e608df32c8c84" label="Student Institution">\n')
        if field_present('Institution',student):
            fid.write('					<value type="String">{}</value>\n'.format(format_xml(student["Institution"])))
        else:
            fid.write('					<value type="String">University of Toronto</value>\n')
        fid.write('				</field>\n')
        fid.write('				<field id="bb322e0195b540779bf4bdb4f1a04210" label="Student Canadian Residency Status"/>\n')
        fid.write('				<field id="5b8638e8646448dcb8edef2c21e01c87" label="Degree Type or Postdoctoral Status">\n')

        # Degree type
        if type == UG_TYPE:
            fid.write('					<lov id="523470197e8942d89d951d922f4abb0d">Bachelor\'s</lov>\n')
        elif type == MS_TYPE:
            fid.write('					<lov id="6bb179b92d1d46059bae10f6d21ea096">Master’s Thesis</lov>\n')
        elif type == PHD_TYPE:
            fid.write('					<lov id="971953ad86ca49f3b32ac5c7c2758a1b">Doctorate</lov>\n')
        elif type == PDF_TYPE:
            fid.write('					<lov id="e0b26301c88d4be5a6f7143981c9b3bb">Post-doctorate</lov>\n')	
        elif type == MENG_TYPE:
            fid.write('\t\t\t\t\t<lov id="4f0939ef786e4c23b441f8fbbcaf4ac4">Master’s non-Thesis</lov>\n')
        elif type == 'RA':
            fid.write('					<lov id="f572c198c89f43ca815aca9731fbcafe">Research Associate</lov>\n')	
        else:
            raise Exception('Wrong student type')					
        fid.write('				</field>\n')
        fid.write('				<field id="e5d331dca0fc4000992e43b695b2db21" label="Student Degree Status">\n')
        
        if status == 'completed':
            fid.write('					<lov id="00000000000000000000000000000068">Completed</lov>\n')
        elif status == 'current':
            fid.write('					<lov id="00000000000000000000000000000070">In Progress</lov>\n')
        else:
            raise Exception('Wrong degree status')
        
        fid.write('				</field>\n')
        fid.write('				<field id="3cf3d0de12f44222b941fdbf57ad51a6" label="Student Degree Start Date">\n')
        fid.write('					<value format="yyyy/MM" type="YearMonth"></value>\n')
        fid.write('				</field>\n')
        fid.write('				<field id="8284dbdd03aa4277b7fca7662bd1758c" label="Student Degree Received Date">\n')
        fid.write('					<value format="yyyy/MM" type="YearMonth"></value>\n')
        fid.write('				</field>\n')
        fid.write('				<field id="ab1293e2fee8472481457d4f8493c7f1" label="Student Degree Expected Date">\n')
        fid.write('					<value format="yyyy/MM" type="YearMonth"></value>\n')
        fid.write('				</field>\n')
        fid.write('				<field id="420e5bbd57104c3c9823b5e6850ee6f8" label="Thesis/Project Title">\n')
        # Thesis title...
        if field_present(thesis_key,student):
            fid.write('					<value type="String">{}</value>\n'.format(format_xml(student[thesis_key])))
        # elif "Topic" in fields:
        # 	fid.write('					<value type="String">{}</value>\n'.format(gf(row,fields,"Topic")))
        elif type == PDF_TYPE:
            fid.write('					<value type="String">None</value>\n')
        else:
            fid.write('					<value type="String">TBD</value>\n')
        fid.write('				</field>\n')
        fid.write('				<field id="804797ed2fe54da88f326743e38e270e" label="Project Description">\n')
        fid.write('					<value type="Bilingual"></value>\n')
        fid.write('					<bilingual>\n')
        fid.write('						<french></french>\n')
        fid.write('						<english></english>\n')
        fid.write('					</bilingual>\n')
        fid.write('				</field>\n')				
        fid.write('				<field id="0f2f1601c24144308e0966d75b781db9" label="Present Position">\n')
        
        if field_present(last_pos_key,student):
            fid.write('					<value type="String">{}</value>\n'.format(format_xml(student[last_pos_key])))
        else:
            if type == PHD_TYPE:
                fid.write('					<value type="String">Doctoral candidate in my group</value>\n')
            elif type == MS_TYPE:
                fid.write('					<value type="String">Masters candidate in my group</value>\n')
            else:
                if status == 'current':
                    fid.write('					<value type="String">Student in my group</value>\n')
                else:
                    fid.write('					<value type="String">Unknown</value>\n')
        fid.write('				</field>\n')
        fid.write('				<field id="8789e49ef39b4249aa53d414045ebfd2" label="Degree Name">\n')
        fid.write('					<value type="Bilingual"/>\n')
        fid.write('					<bilingual/>\n')
        fid.write('				</field>\n')
        fid.write('				<field id="17957ada91964db18a3b0526f5b4e341" label="Specialization">\n')
        fid.write('					<value type="Bilingual"/>\n')
        fid.write('					<bilingual/>\n')
        fid.write('				</field>\n')
        fid.write('				<field id="c20e3ae276a2429d888ae8e16216182f" label="Present Organization">\n')
        fid.write('					<value type="String"></value>\n')
        fid.write('				</field>\n')
        fid.write('			</section>\n')

    return (count)

def gen_ccv(current_phd, current_ms, current_meng, current_pdf, current_ug, past_phd, past_ms, past_meng, past_pdf, past_ug, logger, students_xml,ccv_years):
    xml_f = open(students_xml, 'w')
    xml_f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    xml_f.write('<generic-cv:generic-cv dateTimeGenerated="2016-03-26 09:43:18" lang="en" xmlns:generic-cv="http://www.cihr-irsc.gc.ca/generic-cv/1.0.0">\n')
    xml_f.write('	<section id="95c29504d0aa4b51b84659cafaf2b38d" label="Activities">\n')
    xml_f.write('		<section id="90cc172e54904b45948d17cba24d3f25" label="Supervisory Activities">\n')

    students2ccv(fid=xml_f,students=current_pdf,type=PDF_TYPE,status='current',ccv_years=ccv_years)
    students2ccv(fid=xml_f,students=current_phd,type=PHD_TYPE,status='current',ccv_years=ccv_years)
    students2ccv(fid=xml_f,students=current_ms,type=MS_TYPE,status='current',ccv_years=ccv_years)
    students2ccv(fid=xml_f,students=current_meng,type=MENG_TYPE,status='current',ccv_years=ccv_years)
    students2ccv(fid=xml_f,students=current_ug,type=UG_TYPE,status='current',ccv_years=ccv_years)

    students2ccv(fid=xml_f,students=past_pdf,type=PDF_TYPE,status='completed',ccv_years=ccv_years)
    students2ccv(fid=xml_f,students=past_phd,type=PHD_TYPE,status='completed',ccv_years=ccv_years)
    students2ccv(fid=xml_f,students=past_ms,type=MS_TYPE,status='completed',ccv_years=ccv_years)
    students2ccv(fid=xml_f,students=past_meng,type=MENG_TYPE,status='completed',ccv_years=ccv_years)
    students2ccv(fid=xml_f,students=past_ug,type=UG_TYPE,status='completed',ccv_years=ccv_years)

    xml_f.write('		</section>\n')
    xml_f.write('	</section>\n')
    xml_f.write('</generic-cv:generic-cv>\n')    

    return

def main():
    parser = argparse.ArgumentParser(description='Generate Student tex/html file for CV')
    parser.add_argument('file', type=str, help='Input csv file')
    parser.add_argument('-d', dest='debug', type=str, default='critical', choices = ['debug', 'info', 'error', 'critical'], help='Produce debug output')
    parser.add_argument('--phd_tex', dest='phd_tex', type=str, default='phd_students.tex', help='PhD Tex output file')
    parser.add_argument('--phd_footnote_tex', dest='phd_footnote_tex', type=str, default='phd_footnotes.tex', help='PhD Tex output file')
    parser.add_argument('--ms_tex', dest='ms_tex', type=str, default='ms_students.tex', help='MS Tex output file')
    parser.add_argument('--ms_footnote_tex', dest='ms_footnote_tex', type=str, default='ms_footnotes.tex', help='MS Tex output file')
    parser.add_argument('--pdf_tex', dest='pdf_tex', type=str, default='pdfs.tex', help='PDF Tex output file')
    parser.add_argument('--ug_tex', dest='ug_tex', type=str, default='ug_students.tex', help='UG Tex output file')
    parser.add_argument('--meng_tex', dest='meng_tex', type=str, default='meng_students.tex', help='MENG Tex output file')
    parser.add_argument('--stats_tex', dest='stats_tex', type=str, default='student_stats.tex', help='Students Tex output file')
    parser.add_argument('--html', dest='students_html', type=str, default='students.html', help='HTML output file')    
    parser.add_argument('--xml', dest='students_xml', type=str, default='students.xml', help='CCV XML output file')    
    parser.add_argument('--out_dir', dest='out_dir', type=str, default='', help='Output directory')
    parser.add_argument('--ccv_years', dest='ccv_years', type=int, default=6, help='How many years back to include in ccv output.')
    args = parser.parse_args()   

    if (args.debug == 'debug'):
        logging.basicConfig(level=logging.DEBUG)
    elif (args.debug == 'info'):
        logging.basicConfig(level=logging.INFO)
    elif (args.debug == 'error'):
        logging.basicConfig(level=logging.ERROR)

    logger = logging.getLogger("gen_students")
    
    if args.out_dir:
        phd_tex = os.path.join(args.out_dir, os.path.basename(args.phd_tex))
        phd_footnote_tex = os.path.join(args.out_dir, os.path.basename(args.phd_footnote_tex))
        ms_tex = os.path.join(args.out_dir, os.path.basename(args.ms_tex))
        ms_footnote_tex = os.path.join(args.out_dir, os.path.basename(args.ms_footnote_tex))
        pdf_tex = os.path.join(args.out_dir, os.path.basename(args.pdf_tex))
        ug_tex = os.path.join(args.out_dir, os.path.basename(args.ug_tex))
        meng_tex = os.path.join(args.out_dir, os.path.basename(args.meng_tex))
        stats_tex = os.path.join(args.out_dir, os.path.basename(args.stats_tex))
        students_html = os.path.join(args.out_dir, os.path.basename(args.students_html))
        students_xml = os.path.join(args.out_dir, os.path.basename(args.students_xml))
    else:
        phd_tex = args.phd_tex
        phd_footnote_tex = args.phd_footnote_tex
        ms_tex = args.ms_tex
        ms_footnote_tex = args.ms_footnote_tex
        pdf_tex = args.pdf_tex
        ug_tex = args.ug_tex
        meng_tex = args.meng_tex
        stats_tex = args.stats_tex
        students_html = args.students_html
        students_xml = args.students_xml

    gen_latex(csvfile=args.file, logger=logger, phd_tex=phd_tex, phd_foot=phd_footnote_tex, 
        ms_tex=ms_tex, ms_foot=ms_footnote_tex, pdf_tex=pdf_tex, 
        meng_tex=meng_tex, ug_tex=ug_tex, stats_tex=stats_tex)

    current_phd, current_ms, current_meng, current_pdf, current_ug, past_phd, past_ms, past_meng, past_pdf, past_ug = sort_students(csvfile=args.file, logger=logger)

    gen_html(current_phd=current_phd, current_ms=current_ms, current_pdf=current_pdf, current_ug=current_ug, past_phd=past_phd, past_ms=past_ms, past_pdf=past_pdf, logger=logger, students_html=students_html)

    gen_ccv(current_phd=current_phd, current_ms=current_ms, current_meng=current_meng, current_pdf=current_pdf, current_ug=current_ug, past_phd=past_phd, past_ms=past_ms, past_meng=past_meng, past_pdf=past_pdf, past_ug=past_ug, logger=logger, students_xml=students_xml, ccv_years=args.ccv_years)

# Start program
if __name__ == "__main__":
    main()