from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

doc = Document('BaoCaoDeployment.docx')

# Tim vi tri "1. Tong quan kien truc he thong" de chen so do truoc do
target_para = None
for i, para in enumerate(doc.paragraphs):
    if para.text.strip() == '1. Tổng quan kiến trúc hệ thống':
        target_para = para
        break

if target_para:
    # Chen so do he thong (Nginx & Docker)
    new_para = doc.add_paragraph()
    new_para._element.addprevious(target_para._element)
    new_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = new_para.add_run()
    img_path = os.path.join(os.path.dirname(os.path.abspath('BaoCaoDeployment.docx')), 'SoDoNginx_Docker.png')
    run.add_picture(img_path, width=Inches(6.2))
    
    # Chu thich
    caption = doc.add_paragraph()
    caption._element.addprevious(target_para._element)
    caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = caption.add_run('Hinh 1: So do he thong - Cau truc Nginx & Docker (Host vs Container)')
    run.italic = True
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(100, 100, 100)
    
    print('Da chen so do he thong vao bao cao!')
else:
    print('Khong tim thay vi tri de chen!')

doc.save('BaoCaoDeployment.docx')
