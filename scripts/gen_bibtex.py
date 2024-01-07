#!/usr/bin/env python3
# Development Notes
# Currently I don't support patent generation in XML

import argparse
from pybtex.database import parse_file
from pylatexenc.latex2text import LatexNodes2Text
from difflib import SequenceMatcher
from datetime import date
import sys
import logging
import csv
import os
import re
import uuid
from cv_utils import latex2xml, field_present
     
def parse_bib(logger, bib_in_file, debug=False):
    bib = parse_file(bib_in_file)
    
    num_conf_pubs = 0
    num_journal_pubs = 0
    num_patent_pubs = 0
    num_other_pubs = 0
    
    for item in bib.entries:        
        # mark all citation spots
        entry = bib.entries[item]        
        # update stats
        if (entry.type == 'inproceedings'):
            logger.debug("Found conference paper: " + entry.fields['title'])
            num_conf_pubs = num_conf_pubs + 1
        elif (entry.type == 'article'):
            logger.debug("Found journal paper: " + entry.fields['title'])
            num_journal_pubs = num_journal_pubs + 1
        elif (entry.type == 'misc'):

                num_other_pubs = num_other_pubs + 1
        elif (entry.type == 'patent'):
            logger.debug("Found patent: " + entry.fields['title'])
            num_patent_pubs = num_patent_pubs + 1
        else:
            num_other_pubs = num_other_pubs + 1
    
    return bib, num_conf_pubs, num_journal_pubs, num_patent_pubs, num_other_pubs

def output_summary(logger, summary_tex='',  
                   num_conf_pubs=0, num_journal_pubs=0, num_patent_pubs=0, num_other_pubs=0,
                   debug=False):
     if summary_tex:        
        summary_out = open(summary_tex, 'w')
        summary_str = (f"\\newcommand{{\\numconfpubs}}{{{num_conf_pubs}}}\n"
                        f"\\newcommand{{\\numjournalpubs}}{{{num_journal_pubs}}}\n"
                        f"\\newcommand{{\\numpatentpubs}}{{{num_patent_pubs}}}\n"
                        f"\\newcommand{{\\numotherpubs}}{{{num_other_pubs}}}\n")
        summary_out.write(summary_str)
        summary_out.close()

month_to_ordinal = { 'January':1, 'February':2, 'March':3, 'April':4, 'May':5, 'June':6,
                     'July':7, 'August':8, 'September':9, 'October':10, 'November':11, 'December':12}

def gen_xml(logger, bib, xml_file, ccv_years: int, debug=False):    
    
    xml_f = open(xml_file, 'w')
    
    gen_xml_header(xml_f)
    
    for item in bib.entries:                
        entry = bib.entries[item]              
        #Output for each type
        title = latex2xml(entry.fields['title'])
        booktitle = latex2xml(entry.fields['booktitle']) if field_present('booktitle',entry.fields) else ''
        if field_present('year', entry.fields):
            today = date.today()
            if (today.year - int(latex2xml(entry.fields['year']))) > ccv_years and ccv_years > 0:
                continue          
            conference_date = latex2xml(entry.fields['year']) + '/' + str(month_to_ordinal[entry.fields['month'].strip()]) if field_present('month', entry.fields) else '1'
        else:
            conference_date = ''
        pages = latex2xml(entry.fields['pages']) if field_present('pages', entry.fields) else ''
        
        if field_present('comment', entry.fields) and 'To appear' in entry.fields['comment']:
            pub_status = '<lov id="00000000000000000000000100001702">Accepted</lov>'
        else:
            pub_status = '<lov id="00000000000000000000000100001704">Published</lov>'  
            
        pub_year = latex2xml(entry.fields['year']) if field_present('year', entry.fields) else ''
        publisher = latex2xml(entry.fields['publisher']) if field_present('publisher', entry.fields) else ''
        url = latex2xml(entry.fields['url']) if field_present('url', entry.fields) else ''
        
        first_author = entry.persons['author'][0]
        
        if first_author.last_names[0] == 'Lie' and first_author.first_names[0] == 'David':
            role = '<lov id="00000000000000000000000100002100">First Listed Author</lov>'
        else:
            role = '<lov id="00000000000000000000000100002102">Co-Author</lov>'
            
        num_authors = str(len(entry.persons['author']))
        
        authors = ''        
        for author in entry.persons['author']:
            authors = authors + latex2xml(' '.join(author.bibtex_first_names)) + ' ' + latex2xml(author.last_names[0]) + ', '
        # trim last comma and space
        authors = authors[:-2]
        # replace 2nd last comma with and
        if len(entry.persons['author']) > 1:
            authors = authors.rsplit(',',1)[0] + ' and' + authors.rsplit(',',1)[1]
            
        institution = latex2xml(entry.fields['institution']) if field_present('institution', entry.fields) else ''
        
        doi = latex2xml(entry.fields['doi']) if field_present('doi', entry.fields) else ''\
        
        journal = latex2xml(entry.fields['journal']) if field_present('journal', entry.fields) else ''
        volume = latex2xml(entry.fields['volume']) if field_present('volume', entry.fields) else ''
        number = latex2xml(entry.fields['number']) if field_present('number', entry.fields) else ''
        
        if (entry.type == 'inproceedings'):
            logger.debug("XML output conference paper: " + entry.fields['title'])
            xml_f.write(f'\t\t\t<section id="4b9f909503cd4c8aa8d826c87d6d874d" label="Conference Publications" recordId="{uuid.uuid4().hex}">\n'
                        '\t\t\t\t<field id="81ef87c09ded47ae8880b8d79e83406f" label="Conference Publication Type">\n'
                        '\t\t\t\t\t<lov id="00000000000000000000000100007000">Paper</lov>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="8e6ee535c95e42ec866b777c7472bafb" label="Publication Title">\n'
                        f'\t\t\t\t\t<value type="String">{title}</value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="b3c8a60c053a405597b92899d95765a3" label="Conference Name">\n'
                        f'\t\t\t\t\t<value type="String">{booktitle}</value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="5813833859a64bb58ee55e4f55aff29b" label="Conference Location"/>\n'
                        '\t\t\t\t<field id="c2efd9725588489b8df73467c5597c32" label="City">\n'
                        '\t\t\t\t\t<value type="String"></value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="99b57db653a841ccbd5f8e52079745c0" label="Conference Date">\n'
                        f'\t\t\t\t\t<value format="yyyy/MM" type="YearMonth">{conference_date}</value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="1a1b39e861054ee59d270e66271a4ead" label="Published In">\n'
                        '\t\t\t\t\t<value type="String"></value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="684ccb1fcdd7421f89b304ff5c40579d" label="Page Range">\n'
                        f'\t\t\t\t<value type="String">{pages}</value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="080301b1f1c0464bba7fcfa1fa8fe182" label="Publishing Status">\n'
                        f'\t\t\t\t\t{pub_status}\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="0318d139f3e0479083188ff8319a97b2" label="Year">\n'
                        f'\t\t\t\t\t<value format="yyyy" type="Year">{pub_year}</value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="0c357193a93f4137a87394401ac81958" label="Publisher">\n'
                        f'\t\t\t\t\t<value type="String">{publisher}</value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="2fc69f4076f149bda1f0bb3e0ef9d79f" label="Publication Location"/>\n'
                        '\t\t\t\t<field id="a6e901e5f0cf48a3a7d674bf1e6fcd7f" label="Description / Contribution Value">\n'
                        '\t\t\t\t\t<value type="Bilingual"></value>\n'
                        '\t\t\t\t\t<bilingual>\n'
                        '\t\t\t\t\t\t<french></french>\n'
                        '\t\t\t\t\t\t<english></english>\n'
                        '\t\t\t\t\t</bilingual>\n'
                        '\t\t\t\t</field>\n'    
                        '\t\t\t\t<field id="61690b466fb748d99ed29b340c0ee60b" label="URL">\n'
                        f'\t\t\t\t\t<value type="String">{url}</value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="560a2ce08e14497ba575af760eb12ba9" label="Refereed?">\n'
                        '\t\t\t\t\t<lov id="00000000000000000000000000000400">Yes</lov>\n'
                        '\t\t\t\t</field>\n'    
                        '\t\t\t\t<field id="06295e65f66b4c6aa286d08bd9fac59b" label="Invited?">\n'
                        '\t\t\t\t\t<lov id="00000000000000000000000000000401">No</lov>\n'
                        '\t\t\t\t</field>\n'    
                        '\t\t\t\t<field id="b101f8f057db434ba4fdee3a86c387cc" label="Contribution Role">\n'
                        f'\t\t\t\t\t{role}\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="1a66ad40654a45c9a0119b19d7cf20a6" label="Number of Contributors">\n'
                        f'\t\t\t\t\t<value type="Number">{num_authors}</value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="3cc54d9bb92d421da46548979048396f" label="Authors">\n'
                        f'\t\t\t\t\t<value type="String">{authors}</value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="018e656a0f824b1f91a6a2cb33ac61dd" label="Editors">\n'
                        '\t\t\t\t\t<value type="String"></value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="49e5507889954743b104959e62d9e496" label="DOI">\n'
                        f'\t\t\t\t\t<value type="String">{doi}</value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="575eaa1383ac49ed9d78b5a970a76eb8" label="Contribution Percentage"/>\n'
                        '\t\t\t\t<field id="890336779db441d8a38e7709f6866d15" label="Description of Contribution Role">\n'
                        '\t\t\t\t\t<value type="Bilingual"></value>\n'
                        '\t\t\t\t\t<bilingual>\n'
                        '\t\t\t\t\t\t<french></french>\n'
                        '\t\t\t\t\t\t<english></english>\n'
                        '\t\t\t\t\t</bilingual>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t</section>\n')
        elif (entry.type == 'article'):
            logger.debug("Found journal paper: " + entry.fields['title'])
            xml_f.write(f'\t\t\t<section id="9a34d6b273914f18b2273e8de7c48fd6" label="Journal Articles" recordId="{uuid.uuid4().hex}">\n'
                        '\t\t\t\t<field id="f3fd4878d47c4e83aef6959620ba4870" label="Article Title">\n'
                        f'\t\t\t\t\t<value type="String">{title}</value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="5c04ea4dae464499807d0b40b4cad049" label="Journal">\n'
                        f'\t\t\t\t\t<value type="String">{journal}</value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="0a826c656ff34e579dfcbfb373771260" label="Volume">\n'
                        f'\t\t\t\t\t<value type="String">{volume}</value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="cc1d9e14945b4e8496641dbe22b3448a" label="Issue">\n'
                        f'\t\t\t\t\t<value type="String">{number}</value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="00ba1799ece344dc8d0779a3f05a4df8" label="Page Range">\n'
                        f'\t\t\t\t\t<value type="String">{pages}</value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="3b56e4362d6a495aa5d22a1de5914741" label="Publishing Status">\n'
                        f'\t\t\t\t\t{pub_status}\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="6fafe258e19e49a7884428cb49d75424" label="Year">\n'
                        f'\t\t\t\t\t<value format="yyyy" type="Year">{pub_year}</value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="4ad593960aba4a21bf154fa8daf37f9f" label="Publisher">\n'
                        f'\t\t\t\t\t<value type="String">{publisher}</value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="4c3bc805ceaa42259f014514fc4905f8" label="Publication Location"/>\n'
                        '\t\t\t\t<field id="1167905d079c4400ae7a4a76a203a445" label="Description / Contribution Value">\n'
                        '\t\t\t\t\t<value type="Bilingual"></value>\n'
                        '\t\t\t\t\t<bilingual>\n'
                        '\t\t\t\t\t\t<french></french>\n'
                        '\t\t\t\t\t\t<english></english>\n'
                        '\t\t\t\t\t</bilingual>\n'
                        '\t\t\t\t</field>\n'    
                        '\t\t\t\t<field id="478545acac5340c0a73b7e0d2a4bee06" label="URL">\n'
                        f'\t\t\t\t\t<value type="String">{url}</value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="2089ff1a86844b6c9a10fc63469f9a9d" label="Refereed?">\n'
                        '\t\t\t\t\t<lov id="00000000000000000000000000000400">Yes</lov>\n'
                        '\t\t\t\t</field>\n'    
                        '\t\t\t\t<field id="51b7eaff05444990af823b9d80924f5b" label="Open Access?"/>\n'
                        '\t\t\t\t<field id="b779cc6478bd4b09b516c6d55e938583" label="Synthesis?"/>\n'
                        '\t\t\t\t<field id="289c8814fff141d89b12569d49aa2cb3" label="Contribution Role">\n'
                        f'\t\t\t\t\t{role}\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="dc7922dfa04348a3a83c9afb5bbaa24a" label="Number of Contributors">\n'
                        f'\t\t\t\t<value type="Number">{num_authors}</value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="bc3b428d99384b04bb749311bb804e1d" label="Authors">\n'
                        f'\t\t\t\t\t<value type="String">{authors}</value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="707a6e0ca58341a5a82fb923b2842530" label="Editors">\n'
                        '\t\t\t\t\t<value type="String"></value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="375a0e2ea0914291b05b0529c4755aa7" label="DOI">\n'
                        f'\t\t\t\t\t<value type="String">{doi}</value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="9afd9e28df47464faf3f9ee2c4809e25" label="Contribution Percentage"/>\n'
                        '\t\t\t\t<field id="9f2e163dfcbf4abdb73e9d5c4daf03c4" label="Description of Contribution Role">\n'
                        '\t\t\t\t\t<value type="Bilingual"></value>\n'
                        '\t\t\t\t\t<bilingual>\n'
                        '\t\t\t\t\t\t<french></french>\n'
                        '\t\t\t\t\t\t<english></english>\n'
                        '\t\t\t\t\t</bilingual>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t</section>\n')            
        elif (entry.type == 'techreport'):
            xml_f.write(f'\t\t\t<section id="7e57525337d5498a9506fdadee098b10" label="Reports" recordId="{uuid.uuid4().hex}">\n'
                        '\t\t\t\t<field id="dd692787647b495fbadb038b6937950d" label="Report Title">\n'
                        f'\t\t\t\t\t<value type="String">{title}</value>\n'
                        '\t\t\t\t</field>\n'                        
                        '\t\t\t\t<field id="916975e25205410a81832725aef52824" label="Organization"/>\n'
                        '\t\t\t\t<field id="e36ad9761bc94ec48350d86b87489dc2" label="Other Organization Type">\n'
                        '\t\t\t\t\t<lov id="00000000000000000000000000000406">Academic</lov>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="212fa7b750264e6496a9e4a4c4968810" label="Other Organization">\n'
                        f'\t\t\t\t\t<value type="String">{institution}</value>\n'
                        '\t\t\t\t</field>\n'                        
                        '\t\t\t\t<field id="c90158ebf7f648b1b2e4945fef6948c4" label="Number of Pages">\n'
                        f'\t\t\t\t\t<value type="Number">{pages}</value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="a1f619a230b5452b9f0c8337b23f43af" label="Year Submitted">\n'
                        f'\t\t\t\t\t<value format="yyyy" type="Year">{pub_year}</value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="2c74544e67264402825fa6e52154b8c0" label="Synthesis?"/>\n'
                        '\t\t\t\t<field id="694c4c7bf6ad47309ab6f77f4fee1869" label="Description / Contribution Value">\n'
                        '\t\t\t\t\t<value type="Bilingual"></value>\n'
                        '\t\t\t\t\t<bilingual>\n'
                        '\t\t\t\t\t\t<french></french>\n'
                        '\t\t\t\t\t\t<english></english>\n'
                        '\t\t\t\t\t</bilingual>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="d570e2086e0e4e7d911cbb631a631af5" label="URL">\n'
                        f'\t\t\t\t\t<value type="String">{url}</value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="3117e1b94d5b405d818abecf74dce59e" label="Contribution Role">\n'
                        f'\t\t\t\t\t{role}\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="67a5ad87e91e4f92bca8d1a988d8cbe2" label="Number of Contributors">\n'
                        f'\t\t\t\t<value type="Number">{num_authors}</value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="0cf4ffe90f0b496483a8937b96a0224c" label="Authors">\n'
                        f'\t\t\t\t\t<value type="String">{authors}</value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="e3264fc9e17442e492bc8d5dca60e165" label="Editors">\n'
                        '\t\t\t\t\t<value type="String"></value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="5ec4fa552175415a9b45c4e20504007f" label="DOI">\n'
                        f'\t\t\t\t\t<value type="String">{doi}</value>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t\t<field id="0c53b4b8715d4ab9bdd595b6e539936e" label="Contribution Percentage"/>\n'
                        '\t\t\t\t<field id="939eaf56249248d896d3a27abc6338f0" label="Description of Contribution Role">\n'
                        '\t\t\t\t\t<value type="Bilingual"></value>\n'
                        '\t\t\t\t\t<bilingual>\n'
                        '\t\t\t\t\t\t<french></french>\n'
                        '\t\t\t\t\t\t<english></english>\n'
                        '\t\t\t\t\t</bilingual>\n'
                        '\t\t\t\t</field>\n'
                        '\t\t\t</section>\n')
            
    gen_xml_footer(xml_f)
    xml_f.close()
    
    return

def gen_xml_header(xml_f):
    xml_f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<generic-cv:generic-cv dateTimeGenerated="2016-03-26 09:43:18" lang="en" xmlns:generic-cv="http://www.cihr-irsc.gc.ca/generic-cv/1.0.0">\n'
                '\t<section id="047ec63e32fe450e943cb678339e8102" label="Contributions">\n'
                '\t\t<section id="46e8f57e67db48b29d84dda77cf0ef51" label="Publications">\n')

def gen_xml_footer(xml_f):
    xml_f.write('\t\t</section>\n'
                '\t</section>\n'
                '</generic-cv:generic-cv>\n')    


def main():
    parser = argparse.ArgumentParser(description='Generate bibtex/CSV file for CV')
    parser.add_argument('file', type=str, help='Input bibtex file')
    parser.add_argument('-d', dest='debug', action='store_true', default=False, help='Produce debug output')
    parser.add_argument('--summary_out', dest='summary_tex', type=str, default='bib_summary.tex', help='Publication numbers files')
    parser.add_argument('--xml', dest='pubs_xml', type=str, default='publications.xml', help='CCV XML output file')    
    parser.add_argument('--out_dir', dest='out_dir', type=str, default='', help='Output directory')
    parser.add_argument('--ccv_years', dest='ccv_years', type=int, default=6, help='How many years back to include in ccv output.')
    args = parser.parse_args()   

    num_conf_pubs = 0
    num_journal_pubs = 0
    num_patent_pubs = 0
    num_other_pubs = 0
    num_citations = 0

    logger = logging.getLogger("gen_bibtex")
    
    if args.debug: 
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    logger.info("Parsing bibfile")    
    
    if args.out_dir:
        summary_tex = os.path.join(args.out_dir, os.path.basename(args.summary_tex))
        xml_file = os.path.join(args.out_dir, os.path.basename(args.pubs_xml))
    else:
        summary_tex = args.summary_tex
        xml_file = args.pubs_xml
    
    bib, num_conf_pubs, num_journal_pubs, num_patent_pubs, num_other_pubs = parse_bib(logger, 
                    bib_in_file=args.file,                    
                    debug=args.debug)
    
    logger.info("Generating summary file")
    
    gen_xml(logger=logger, bib=bib, xml_file=xml_file, ccv_years=args.ccv_years, debug=args.debug)
    
    retval = output_summary(logger, summary_tex=summary_tex, 
                            num_conf_pubs=num_conf_pubs, num_journal_pubs=num_journal_pubs,
                            num_other_pubs=num_other_pubs, num_patent_pubs=num_patent_pubs,
                            debug=args.debug)   

# Start program
if __name__ == "__main__":
    main()