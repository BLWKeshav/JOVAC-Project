from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import json

def create_pdf_from_data(data: dict, out_path: str):
    c = canvas.Canvas(out_path, pagesize=A4)
    width, height = A4
    title = data.get('document_type', 'Legal Document')
    c.setFont('Helvetica-Bold', 16)
    c.drawString(48, height - 72, title)
    c.setFont('Helvetica', 11)
    y = height - 110
    for key, val in data.items():
        if key == 'document_type':
            continue
        # handle lists/dicts
        if isinstance(val, (list, dict)):
            text = json.dumps(val, ensure_ascii=False)
        else:
            text = str(val)
        # simple wrapping
        while text:
            if y < 80:
                c.showPage()
                y = height - 72
            line = text[:100]
            c.drawString(48, y, f"{key}: {line}")
            text = text[100:]
            y -= 18
    c.showPage()
    c.save()
