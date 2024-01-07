SHELL = /bin/bash

ISWSL = $(shell uname -r)
ifneq ($(filter %Microsoft, $(shell uname -r)),)
	LATEXMK = latexmk.exe
else
	LATEXMK = latexmk
endif

SECTION_DIR = sections/
GENERATED_DIR = generated/

PYTHON = python3

SECTIONS = academic_appointments.tex awards.tex education.tex other.tex pubs.tex research_support.tex
# add a prefix
SECTION_FILES = $(addprefix ${SECTION_DIR}, ${SECTIONS})
PDFS = cv-new.pdf cv-expert-witness.pdf
BIB_TEX = $(addprefix ${GENERATED_DIR}, bib_summary.tex publications.xml)
STUDENT_TEX = $(addprefix ${GENERATED_DIR}, phd_students.tex ms_students.tex ug_students.tex phd_footnotes.tex ms_footnotes.tex pdfs.tex meng_students.tex students.html students.xml)
NEW_STUDENT_TEX = $(addprefix ${GENERATED_DIR}, new_ug_students.tex new_ms_students.tex new_phd_students.tex new_pdfs.tex new_meng_students.tex)
TEACHING_TEX = $(addprefix ${GENERATED_DIR}, grad_teaching.tex ug_teaching.tex)
TALKS_TEX = $(addprefix ${GENERATED_DIR}, invited_talks.tex conference_talks.tex talks.xml)
TPCS_TEX = $(addprefix ${GENERATED_DIR}, TPCs.tex tpcs.xml)
FUNDING_TEX = $(addprefix ${GENERATED_DIR}, funding.tex funding.xml)
CASES_TEX = $(addprefix ${GENERATED_DIR}, cases.tex)
COLLABORATORS_TEX = $(addprefix ${GENERATED_DIR}, collabs.tex conflicts.txt)
TEX_FILES = ${STUDENT_TEX} ${NEW_STUDENT_TEX} ${TEACHING_TEX} ${TALKS_TEX} ${TPCS_TEX} ${BIB_TEX} ${FUNDING_TEX} ${CASES_TEX} ${COLLABORATORS_TEX}
XML_FILES = $(addprefix ${GENERATED_DIR}, funding.xml publications.xml students.xml talks.xml tpcs.xml)

all: $(PDFS)

tex-files: ${TEX_FILES}

bib: ${BIB_TEX}

students: $(STUDENT_TEX)	

teaching: $(TEACHING_TEX)

talks: $(TALKS_TEX)

tpcs: ${TPCS_TEX}

funding: ${FUNDING_TEX}

collabs: ${COLLABORATORS_TEX}

xml: ${XML_FILES}

fix-urls:
	${PYTHON} scripts/gen_tpcs.py TPCs.csv conference_keys.csv --fix_urls -d info

cv-new.pdf: cv-new.tex cv.bib ${TEX_FILES} ${SECTION_FILES}
	$(LATEXMK) -pdf cv-new

cv-expert-witness.pdf: cv-expert-witness.tex cv.bib ${TEX_FILES} ${SECTION_FILES}
	$(LATEXMK) -pdf cv-expert-witness

cv-cites.pdf: cv-cites.tex cv-cites.bib ${TEX_FILES} ${SECTION_FILES}
	$(LATEXMK) -pdf cv-cites

${BIB_TEX}: cv.bib scripts/gen_bibtex.py
	${PYTHON} scripts/gen_bibtex.py cv.bib --out_dir ${GENERATED_DIR}

${STUDENT_TEX}: students.csv scripts/gen_students.py
	${PYTHON} scripts/gen_students.py students.csv --out_dir ${GENERATED_DIR}

${NEW_STUDENT_TEX}: students.csv scripts/gen_students.py
	${PYTHON} scripts/gen_students.py students.csv --out_dir ${GENERATED_DIR}

${TEACHING_TEX}: classes.csv scripts/gen_teaching.py
	${PYTHON} scripts/gen_teaching.py classes.csv --out_dir ${GENERATED_DIR}

${TALKS_TEX}: talks.csv scripts/gen_talks.py
	${PYTHON} scripts/gen_talks.py talks.csv --out_dir ${GENERATED_DIR}

${TPCS_TEX}: conference_keys.csv TPCs.csv scripts/gen_tpcs.py
	${PYTHON} scripts/gen_tpcs.py TPCs.csv conference_keys.csv --out_dir ${GENERATED_DIR}

${FUNDING_TEX}: funding.csv scripts/gen_funding.py
	${PYTHON} scripts/gen_funding.py funding.csv --out_dir ${GENERATED_DIR}

${CASES_TEX}: cases.csv scripts/gen_cases.py
	${PYTHON} scripts/gen_cases.py cases.csv --out_dir ${GENERATED_DIR}

${COLLABORATORS_TEX}: cv.bib students.csv funding.csv people.csv scripts/gen_collaborators.py 
	${PYTHON} scripts/gen_collaborators.py cv.bib students.csv funding.csv people.csv --out_dir ${GENERATED_DIR}

test: ${PDFS}
	pytest --junitxml=report.xml

clean:
	rm ${PDFS} ${STUDENT_TEX} ${NEW_STUDENT_TEX} ${TEACHING_TEX} ${TALKS_TEX} ${BIB_TEX} ${TPCS_TEX} ${FUNDING_TEX} *.dvi *.fls *.fdb_latexmk *.aux *.log *.out *.bbl *.blg *.synctex.gz *.bcf *.run.xml