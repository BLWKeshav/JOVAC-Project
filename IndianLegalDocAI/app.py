import os
from flask import Flask, render_template, request, send_file

from flask_cors import CORS
import base64
import time
from generator import create_pdf_from_data
from utils.pdf_generator import generate_pdf

app = Flask(__name__)

DOCUMENT_TEMPLATES = {
    'FIR': 'documents/FIR_template.txt',
    'RTI': 'documents/RTI_template.txt',
    'Will': 'documents/Will_template.txt',
    'Legal Notice': 'documents/LegalNotice_template.txt',
    'Business License': 'documents/BusinessLicense_template.txt',
    'Affidavit': 'documents/Affidavit_template.txt'
}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        doc_type = request.form.get('doc_type')
        inputs = {key: request.form[key] for key in request.form if key != 'doc_type'}
        template_path = DOCUMENT_TEMPLATES.get(doc_type)
        if template_path:
            filled_text = ''
            with open(template_path, 'r', encoding='utf-8') as f:
                filled_text = f.read()
            for placeholder, value in inputs.items():
                filled_text = filled_text.replace(f'[{placeholder}]', value)
            pdf_path = os.path.join('documents', f'{doc_type}_Generated.pdf')
            generate_pdf(filled_text, pdf_path)
            return render_template('preview.html', content=filled_text, pdf_file=pdf_path)
    return render_template('form.html', doc_types=DOCUMENT_TEMPLATES.keys())

@app.route('/download')
def download():
    pdf_file = request.args.get('file')
    return send_file(pdf_file, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)



# --- Integration endpoints added by integrator ---
# Ensure CORS is enabled for local integration
try:
    CORS(app)
except Exception:
    pass

GENERATED_DIR = os.path.join(app.static_folder or 'static', 'generated')
os.makedirs(GENERATED_DIR, exist_ok=True)

@app.route('/api/generate_pdf', methods=['POST'])
def generate_pdf_api():
    try:
        data = request.get_json(force=True)
    except Exception as e:
        return jsonify({'error': 'Invalid JSON', 'details': str(e)}), 400

    timestamp = int(time.time())
    docname = data.get('document_type', 'document')
    safe_name = ''.join(c for c in docname if c.isalnum() or c in (' ', '-', '_')).rstrip().replace(' ', '_')
    filename = f"{timestamp}_{safe_name}.pdf"
    out_path = os.path.join(GENERATED_DIR, filename)

    try:
        create_pdf_from_data(data, out_path)
    except Exception as e:
        return jsonify({'error': 'PDF generation failed', 'details': str(e)}), 500

    preview_url = f"/preview/{filename}"
    # also return base64
    with open(out_path, 'rb') as f:
        pdf_b64 = base64.b64encode(f.read()).decode('ascii')

    return jsonify({'preview_url': preview_url, 'filename': filename, 'pdf_b64': pdf_b64})

@app.route('/preview/<path:filename>')
def preview(filename):
    file_path = os.path.join(GENERATED_DIR, filename)
    if not os.path.exists(file_path):
        abort(404)
    return render_template('preview.html', filename=filename)

@app.route('/generated/<path:filename>')
def serve_generated(filename):
    return send_from_directory(GENERATED_DIR, filename, as_attachment=False)

# --- End integration block ---
