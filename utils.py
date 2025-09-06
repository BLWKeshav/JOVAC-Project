from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
import io
from datetime import date

def generate_letter_content(name, address, subject, letter_type, body, recipient_name, recipient_address):
    if letter_type == "RTI":
        return f"""
<p>Sir/Madam,</p>

<p>I, <b>{name}</b>, resident of <b>{address}</b>, hereby request the following information under the Right to Information Act, 2005:</p>

<p>{body}</p>

<p>The information may please be provided to me within 30 days as mandated by the RTI Act.</p>

<p>If the information is not provided within the stipulated time, I would be constrained to approach the Appellate Authority.</p>
"""
    elif letter_type == "Police Complaint":
        return f"""
<p>Sir/Madam,</p>

<p>I, <b>{name}</b>, resident of <b>{address}</b>, would like to bring the following matter to your kind notice:</p>

<p>{body}</p>

<p>I request you to register an FIR and take appropriate legal action in this matter. I am available to provide any additional information or evidence required.</p>
"""
    elif letter_type == "Leave Application":
        return f"""
<p>Sir/Madam,</p>

<p>I, <b>{name}</b>, would like to apply for leave for the following reason:</p>

<p>{body}</p>

<p>I request you to kindly grant me leave for the mentioned period. I will be available on my phone for any urgent matters.</p>
"""
    elif letter_type == "Official Complaint":
        return f"""
<p>Sir/Madam,</p>

<p>I, <b>{name}</b>, resident of <b>{address}</b>, would like to bring the following issue to your attention:</p>

<p>{body}</p>

<p>I request you to look into this matter and take appropriate action at the earliest.</p>
"""
    else:
        return f"""
<p>Sir/Madam,</p>

<p>I, <b>{name}</b>, resident of <b>{address}</b>, would like to submit the following application:</p>

<p>{body}</p>

<p>I request you to kindly consider my application and take appropriate action.</p>
"""

def create_pdf_stream(name, address, subject, letter_type, body, recipient_name, recipient_address):
    from reportlab.platypus import SimpleDocTemplate
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)
    
    styles = getSampleStyleSheet()
    normal_style = ParagraphStyle(name='NormalStyle', parent=styles['Normal'], fontSize=12, leading=16, alignment=TA_JUSTIFY)

    story = []
    story.append(Paragraph("<b>OFFICIAL LETTER</b>", styles['Heading1']))
    story.append(Spacer(1, 0.2*inch))

    sender_address_text = f"<b>{name}</b><br/>{address.replace(chr(10), '<br/>')}"
    date_text = f"Date: {date.today().strftime('%d/%m/%Y')}"

    sender_data = [[Paragraph(sender_address_text, normal_style), Paragraph(date_text, normal_style)]]
    sender_table = Table(sender_data, colWidths=[4*inch, 2*inch])
    sender_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))

    story.append(sender_table)
    story.append(Spacer(1, 0.3*inch))

    recipient_addr = "To,<br/>" + recipient_name + "<br/>" + recipient_address.replace(chr(10), '<br/>')
    story.append(Paragraph(recipient_addr, normal_style))
    story.append(Spacer(1, 0.3*inch))

    subject_text = f"<b>Subject: {subject}</b>"
    story.append(Paragraph(subject_text, normal_style))
    story.append(Spacer(1, 0.2*inch))

    letter_content = generate_letter_content(name, address, subject, letter_type, body, recipient_name, recipient_address)
    story.append(Paragraph(letter_content, normal_style))

    story.append(Paragraph("Thanking you,", normal_style))
    story.append(Paragraph(f"Yours faithfully,<br/><br/><b>{name}</b>", normal_style))

    doc.build(story)
    buffer.seek(0)
    return buffer
