# -*- coding: utf-8 -*-
"""生成机器学习实验课程报告 v2 — 含代码和图片占位"""
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
import os

BASE = r"D:\Xx\大二下\机器学习\大作业"

def read_code(filename):
    path = os.path.join(BASE, filename)
    with open(path, 'r', encoding='utf-8-sig' if 'app.py' in filename else 'utf-8') as f:
        return f.read()

# Read all source code
CODE_PHASE1 = read_code('phase1_clustering.py')
CODE_PHASE2 = read_code('phase2_mbti_classifier.py')
CODE_APP = read_code('app.py')
print("All code files loaded")