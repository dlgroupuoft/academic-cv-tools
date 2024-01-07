#!/usr/bin/env python3

import argparse
from  pybtex.database import parse_file

from pylatexenc.latex2text import LatexNodes2Text
from datetime import datetime
from nameparser import HumanName
import sys
import logging
import csv
import os
import re
from tempfile import NamedTemporaryFile
import shutil
from cv_utils import check_url, latex_format, ordinal

FIRST_NAME = 'First Name'
LAST_NAME = 'Last Name'
MS_START = 'MS Start Date'
PHD_START = 'PhD Start Date'
PDF_START = 'PDF Start Date'
PDF_LAST_POSITION = 'PDF Last Position'
PDF_START = 'PDF Start Date'
PHD_LAST_POSITION = 'PhD Last Position'
PHD_START = 'PhD Start Date'
MS_LAST_POSITION = 'MS Last Position'

CO_PIS = 'co_pis'
YEAR = 'year'

NAME = 'name'
MIDDLE_NAME = 'Middle Name'
NICK_NAME = 'Nick Name'
AFFILIATION = 'Affiliation'

class Person:
    first_name = ""
    middle_name = ""
    last_name = ""
    affiliation = ""
    
    def __init__(self, last_name, nick_name='', first_name='', middle_name='', affiliation=''):
        self.first_name = first_name
        self.nick_name = nick_name
        self.middle_name = middle_name
        self.nick_name = nick_name
        self.last_name = last_name
        self.affiliation = affiliation
        
    def __str__(self) -> str:
        return self.first_name + ' ' + self.middle_name + (' (' + self.nick_name + ')' if self.nick_name else '') + ' ' + self.last_name + ' (' + self.affiliation + ')'
    
    def __eq__(self, o: object) -> bool:
        return self.first_name == o.first_name and self.middle_name == o.middle_name and self.nick_name == o.nick_name and  self.last_name == o.last_name and self.affiliation == o.affiliation

month_dict = {'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
              'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12}

def month_difference(year, month, now):
    return (int(now.year)-int(year))*12 + int(now.month) - month_dict[month]+1
        
def parse_bib(logger, bib_file, years, collaborators):
    bib = parse_file(bib_file)
           
    for item in bib.entries:
        entry = bib.entries[item]
        # check if within the year threshold
        month = entry.fields['month'] if 'month' in entry.fields.keys() else 'December'
        if month_difference(entry.fields['year'], month, datetime.now()) <= years*12:
            for author in entry.persons['author']:
                # check if author is already in the list
                first_name = LatexNodes2Text().latex_to_text(' '.join(author.first_names).strip()) if author.first_names else ''
                last_name = LatexNodes2Text().latex_to_text(' '.join(author.last_names).strip()) if author.last_names else ''
                middle_name = LatexNodes2Text().latex_to_text(' '.join(author.middle_names).strip()) if author.middle_names else ''                
                author_name = first_name + ' ' + last_name                
                if author_name not in collaborators.keys() and author_name != 'David Lie':
                    collaborators[author_name] = Person(last_name=last_name, first_name=first_name, middle_name=middle_name, affiliation='')
    return collaborators

def remove_initials(name):
    return re.sub(r'\s\w\.', '', name)

def process_student_name(first_name):
    # remove any initials
    short_first_name = remove_initials(first_name.strip())
    # check for nicknames
    match = re.search(r' \((\w+)\)', short_first_name)
    if match:
        nick_name = match.group(1).strip()
    else:
        nick_name = ''
    # remove any nicknames
    formal_name = re.sub(r' \(\w+\)', '', short_first_name).strip()   
    return formal_name, nick_name 

def simplify_position(str):
    retval = re.sub(r'Adjunct|Assist\.|Assoc\.|Prof\.|Professor|Instructor|Lecturer|Researcher|Research|Associate|Assistant|Postdoctoral|Postdoctoral|,', '',str)
    return (' '.join(retval.split())).strip()

def student_last_position(student):
    if student[PDF_LAST_POSITION]:
        return simplify_position(student[PDF_LAST_POSITION])
    elif student[PHD_LAST_POSITION] and not student[PDF_START]:
        return simplify_position(student[PHD_LAST_POSITION])
    elif student[MS_LAST_POSITION] and not student[PHD_START] and not student[PDF_START]:
        return student[MS_LAST_POSITION]
    else:
        return 'Toronto'

def parse_students(logger, student_csv, conflicts):
    with open(student_csv, 'r', newline='') if os.name == 'nt' else open(student_csv, 'r', encoding='utf-8-sig') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            # skip UG and MENG students
            if not row[MS_START] and not row[PHD_START] and not row[PDF_START]:
                continue
            formal_name, nick_name = process_student_name(row[FIRST_NAME])
            full_formal_name = formal_name.strip() + ' ' + row[LAST_NAME].strip()
            full_nick_name = nick_name.strip() + ' ' + row[LAST_NAME].strip() if nick_name else ''                
            logger.debug('formal_name: ' + full_formal_name + ', nick_name: ' + full_nick_name)
            if full_formal_name not in conflicts.keys() and full_nick_name not in conflicts.keys():
                conflicts[full_formal_name] = Person(last_name=row[LAST_NAME].strip(), first_name=formal_name, nick_name=nick_name, affiliation=student_last_position(row).strip())
    return conflicts

# return dict of people
def parse_copis(str):
    people = {}
    # remove anything after semicolon
    co_pis = str.split(';')[0]
    # split into people
    people_list = co_pis.split(',')
    # parse each person
    for person in people_list:
        short_person = remove_initials(person.strip())        
        match = re.search(r'(.*) \((.+)\)', short_person)
        if match:
            full_name = match.group(1)            
            affiliation = match.group(2)
            name_parts = HumanName(full_name)
            first_name = name_parts.first
            middle_name = name_parts.middle
            last_name = name_parts.last
            name = first_name + ' ' + last_name            
            people[name] = Person(last_name=last_name, first_name=first_name, middle_name=middle_name, affiliation=affiliation)            
    return people

def parse_funding(logger, funding_csv, years, collaborators):
    with open(funding_csv, 'r', newline='') if os.name == 'nt' else open(funding_csv, 'r', encoding='utf-8-sig') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            grant_year = row[YEAR][-4:]
            if int(datetime.now().year) - int(grant_year) <= years:                
                co_pis = parse_copis(row[CO_PIS])
                for full_name, co_pi in co_pis.items():
                    if full_name not in collaborators.keys():
                        collaborators[full_name] = co_pi                
    return collaborators
    
def update_people(logger, people_csv, conflicts, collaborators):
    with open(people_csv, 'r', newline='') if os.name == 'nt' else open(people_csv, 'r', encoding='utf-8-sig') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        updated = False
        db = {}
        for row in csv_reader:
            db[row[NAME]] = Person(last_name=row[LAST_NAME], first_name=row[FIRST_NAME], nick_name=row[NICK_NAME], middle_name=row[MIDDLE_NAME], affiliation=row[AFFILIATION])        
        # merge in collaborators
        keys_to_remove = []
        keys_to_add = []        
        for name, person in collaborators.items():            
            if name not in db.keys():             
                with_middle_name = person.first_name + ' ' + person.middle_name + ' ' + person.last_name                     
                # see if we got middle name wrong
                if with_middle_name in db.keys():
                    logger.debug('Collaborators: Replacing: ' + name + ' with ' + with_middle_name)
                    keys_to_remove.append(name)
                    keys_to_add.append(with_middle_name)
                else:
                    logger.info('Adding DB: ' + name + ' as ' + str(person))
                    updated = True
                    db[name] = person             
        for key in keys_to_remove:
            collaborators.pop(key)
        for key in keys_to_add:
            collaborators[key] = db[key]
        # merge in conflicts
        keys_to_remove = []
        keys_to_add = []        
        for name, person in conflicts.items():
            altname = person.nick_name + ' ' + person.last_name            
            if name in db.keys():
                if person != db[name]:
                    logger.info('Updating DB: ' + name + ' from ' + str(db[name]) + ' to ' + str(person))
                    updated = True
                    db[name] = person
            # person perfers to use nick name
            elif altname in db.keys():                
                if person != db[altname]:                    
                    logger.info('Updating DB: ' + altname + ' from ' + str(db[altname]) + ' to ' + str(person))                    
                    updated = True
                    db[altname] = person                                        
                # rename in conflicts 
                logger.debug('Conflicts replacing: ' + name + ' with ' + altname)
                keys_to_remove.append(name)
                keys_to_add.append(altname) 
                if name in db.keys():  
                    logger.debug('Removing duplicate DB: ' + name)              
                    updated = True     
                    db.pop(name)                                
            else:
                logger.info('Adding DB: ' + name + ' as ' + str(person))
                updated = True
                db[name] = person        
            # incorrect first name parsing (likely due to middle name)
            err_name = person.first_name.split(' ')[0] + ' ' + person.last_name 
            if len(person.first_name.split(' ')) > 1 and err_name in db.keys():                
                logger.info('Replacing DB: ' + err_name + ' with ' + name)
                db.pop(err_name)
                updated = True
                db[name] = person
        # fix conflicts where a student prefers to use a nickname
        for key in keys_to_remove:
            conflicts.pop(key)
        for key in keys_to_add:
            conflicts[key] = db[key]
        csv_file.close()
        if updated:
            tempfile = NamedTemporaryFile('w+t', newline='', delete=False)
            logger.debug('Writing to: ' + tempfile.name)
            tempwriter = csv.DictWriter(tempfile, csv_reader.fieldnames)
            tempwriter.writeheader()
            for name in sorted(db.keys()):
                tempwriter.writerow({NAME: name, LAST_NAME: db[name].last_name, FIRST_NAME: db[name].first_name, NICK_NAME: db[name].nick_name, MIDDLE_NAME: db[name].middle_name, AFFILIATION: db[name].affiliation})
            tempfile.close()
            shutil.move(people_csv, os.path.splitext(people_csv)[0]+'-bak'+ os.path.splitext(people_csv)[1])
            shutil.move(tempfile.name, people_csv)
    return db
 
def gen_collaborators(logger, collaborators, tex_out, db ):
    with open(tex_out, 'w') as tex_file:
        first = True
        for name in sorted(collaborators.keys()):
            person = db[name]
            if first:
                first = False
            else:
                tex_file.write(", ")                
            tex_file.write(latex_format(f"{name} {'(' + person.affiliation + ')' if person.affiliation else ''}"))
        tex_file.close()
        
def gen_conflicts(logger, conflicts, collaborators, txt_out, db ):
    # merge collaborators and conflicts
    conflicts.update(collaborators)
    with open(txt_out, 'w') as txt_file:    
        for name in sorted(conflicts.keys()):
            person = db[name]            
            txt_file.write(f"{name} {'(' + person.affiliation + ')' if person.affiliation else ''}\n")            
        txt_file.close()

def main():
    parser = argparse.ArgumentParser(description='Generate bibtex/CSV file for CV')
    parser.add_argument('bib_file', type=str, help='Input bibtex file')
    parser.add_argument('student_csv', type=str, help='Input student csv file')
    parser.add_argument('funding_csv', type=str, help='Input funding csv file')
    parser.add_argument('people_csv', type=str, help='People csv file')
    parser.add_argument('--years', dest='years', type=int, default='2', help='Number of years to include')
    parser.add_argument('--txt_out', dest='txt_out', type=str, default='conflicts.txt', help='Output Conflicts txt file')
    parser.add_argument('--tex_out', dest='tex_out', type=str, default='collabs.tex', help='Output collaborators tex file')
    parser.add_argument('--out_dir', dest='out_dir', type=str, default='', help='Output directory')
    parser.add_argument('-d', dest='debug', type=str, default='critical', choices = ['debug', 'info', 'error', 'critical'], help='Produce debug output')
    args = parser.parse_args()   
       
    if (args.debug == 'debug'):
        logging.basicConfig(level=logging.DEBUG)
    elif (args.debug == 'info'):
        logging.basicConfig(level=logging.INFO)
    elif (args.debug == 'error'):
        logging.basicConfig(level=logging.ERROR)
    
    logger = logging.getLogger(__name__)    
       
    if args.out_dir:
        txt_out = os.path.join(args.out_dir, os.path.basename(args.txt_out))
        tex_out = os.path.join(args.out_dir, os.path.basename(args.tex_out))
    else:
        txt_out = args.txt_out
        tex_out = args.tex_out
    
    collaborators = {}
    conflicts = {}
        
    parse_bib(logger, bib_file = args.bib_file, years = args.years, collaborators=collaborators)           
    parse_students(logger, student_csv = args.student_csv, conflicts=conflicts)    
    parse_funding(logger, funding_csv = args.funding_csv, years=args.years, collaborators=collaborators)    
    db = update_people(logger, people_csv = args.people_csv, conflicts=conflicts, collaborators=collaborators)
    gen_collaborators(logger, collaborators=collaborators, tex_out=tex_out, db=db)
    gen_conflicts(logger, conflicts=conflicts, collaborators=collaborators,txt_out=txt_out, db=db)
    
# Start program
if __name__ == "__main__":
    main()