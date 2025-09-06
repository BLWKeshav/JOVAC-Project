from flask import Flask, request, send_file, render_template, redirect, url_for
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT, TA_RIGHT
import io
from datetime import date

app = Flask(__name__)

from utils import generate_letter_content, create_pdf_stream

@app.route("/", methods=["GET"])
def home():
    return render_template("form.html")

@app.route("/preview", methods=["POST"])
def preview_letter():
    try:
        name = request.form['name']
        address = request.form['address']
        subject = request.form['subject']
        recipient_name = request.form['recipient_name']
        recipient_address = request.form['recipient_address']
        letter_type = request.form['letter_type']
        body = request.form['body']

        letter_content = generate_letter_content(name, address, subject, letter_type, body, recipient_name, recipient_address)
        current_date = date.today().strftime("%d/%m/%Y")
        
        return render_template("preview.html", 
                                    name=name,
                                    address=address,
                                    sender_address=address,
                                    subject=subject,
                                    recipient_name=recipient_name,
                                    recipient_address=recipient_address,
                                    letter_type=letter_type,
                                    body=body,
                                    letter_content=letter_content,
                                    current_date=current_date)
    
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@app.route("/download", methods=["POST"])
def download_letter():
    try:
        name = request.form['name']
        address = request.form['address']
        subject = request.form['subject']
        recipient_name = request.form['recipient_name']
        recipient_address = request.form['recipient_address']
        letter_type = request.form['letter_type']
        body = request.form['body']

        pdf_buffer = create_pdf_stream(name, address, subject, letter_type, body, recipient_name, recipient_address)

        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f"{letter_type.replace(' ', '_')}_letter.pdf",
            mimetype="application/pdf"
        )
    
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True)
