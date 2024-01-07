# Academic CV Tools
Scripts to manage academic CVs

## Benefits

This package generates academic style CVs based on boilerplate latex files, CSV files for students, awards, etc... and bibtex files for publications. It will automatically generate a PDF of your CV, html files for inclusion into a web page and XML files for upload to the Canadian CCV website. 

## Usage

You will need python and latex to compile and generate the files. To setup your python environment, you can either use [Poetry](https://python-poetry.org/) or the [requirements.txt](https://pip.pypa.io/en/stable/reference/requirements-file-format/) file. To populate your CV you need to:
1. Fill in the latex files in the sections/ directory
1. Populate the various csv files in the root directory
1. Populate the cv.bib file in the root directory

Running "make" with the appropriate python environment setup will then generate all the appropriate files in the generated/ directory

## Overview of files

scripts/ - All the scripts to generate files
sections/ - Various latex sections
generated/\*.tex - generated latex files
generated/\*.html - generated html files
generated/\*.xml - generated xml files for upload to CCV website
generated/\conflicts.txt - set of conflicts in the last 2 years (configurable), useful for listing conflicts on review sites like hotcrp
people.csv - generated database file of collaborators extracted from grants and publications
conference_keys.csv - list of conference venues for TPCs