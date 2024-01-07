import pytest
from check_tex_url import check_tex_url

def test_bib_file():
    check_tex_url.check_tex_url("cv.bib")

def test_cv_tex():
    check_tex_url.check_tex_url("cv.tex")

def test_phd_students_tex():
    check_tex_url.check_tex_url("generated/phd_students.tex")

def test_ms_students_tex():
    check_tex_url.check_tex_url("generated/ms_students.tex")

def test_pdfs_tex():
    check_tex_url.check_tex_url("generated/pdfs.tex")
    
def test_pdfs_tex():
    check_tex_url.check_tex_url("generated/TPCs.tex")

def test_cv10page_tex():
    check_tex_url.check_tex_url("cv-10page.tex")

