from flask import Flask, render_template, request, jsonify, session, send_file, url_for

import requests
from flask_session import Session
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io, os, datetime
import ollama # Import the new ollama library
import json   # Import the json library for data extraction

app = Flask(__name__)
app.secret_key = "replace_with_a_random_secret"
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Document fields remain the same
DOC_FIELDS = {
    "WILL": [
        ("testator_name", "Testator's full name"),
        ("testator_address", "Testator's residential address"),
        ("date_place", "Date and place of making the Will"),
        ("executor_name", "Full name and address of the Executor"),
        ("beneficiaries", "List of beneficiaries with their relation and share percentage"),
        ("assets", "List of assets/properties"),
        ("special_clauses", "Any special instructions (or 'N/A')"),
        ("guardian", "Guardian name for minors (or 'N/A')"),
        ("witness1", "Witness 1 - Name & Address"),
        ("witness2", "Witness 2 - Name & Address")
    ],
    # ... (other document fields are unchanged, so they are omitted here for brevity)
    # The full DOC_FIELDS dictionary from your original file should be here.
    "FIR": [("complainant_name", "Complainant full name"), ("complainant_address", "Complainant address & contact"), ("date_time_of_incident", "Date & time of incident"), ("incident_location", "Location of incident"), ("incident_details", "Describe incident in chronological order"), ("accused", "Name(s) of accused (if known) or 'Unknown'"), ("witnesses", "Witness details (if any)"), ("loss_details", "Loss/damage (if any)"), ("sections", "Suspected sections of law (optional)"), ("signature_date", "Signature date")],
    "RTI": [("applicant_name", "Applicant full name"), ("applicant_address", "Applicant address & contact"), ("public_authority", "Name & address of Public Authority / PIO"), ("subject_info", "Subject of information requested (short line)"), ("detailed_questions", "Numbered questions / details of information required"), ("period", "Period for which information is sought (from - to)"), ("preferred_format", "Preferred format (Paper / Digital / Inspection)"), ("fee_details", "RTI fee details (if paid) or 'N/A'"), ("declaration", "Declaration (if any)"), ("application_date", "Application date")],
    "AFFIDAVIT": [("deponent_name", "Deponent full name"), ("father_or_husband", "Father's / Husband's name"), ("deponent_address", "Deponent residential address"), ("age_dob", "Age / Date of birth"), ("occupation", "Occupation"), ("purpose", "Purpose of affidavit (short)"), ("statements", "Statement paragraphs (numbered facts)"), ("place_date", "Place & Date of oath"), ("notary_details", "Notary / Oath officer details (Name, reg no.)"), ("signature", "Signature of Deponent")],
    "LEGAL_NOTICE": [("sender_name", "Sender full name / Firm name"), ("sender_address", "Sender address & contact"), ("recipient_name", "Recipient full name"), ("recipient_address", "Recipient address & contact"), ("notice_date", "Date of issuing notice"), ("subject_nature", "Subject / nature of dispute"), ("facts_chronology", "Chronology of facts with dates"), ("legal_basis", "Legal basis / contract clause (brief)"), ("demand_relief", "Specific relief / remedy demanded"), ("deadline_days", "Deadline to comply (in days)")],
    "GRIEVANCE_LETTER": [("complainant_name", "Your full name"), ("complainant_address", "Your address & contact"), ("designation", "Your designation / relation to organization (if any)"), ("recipient_org", "Recipient organization / authority"), ("recipient_designation", "Recipient designation (if known)"), ("incident_date_place", "Date & place of incident"), ("incident_details", "Describe grievance / incident"), ("previous_steps", "Previous complaints / steps taken (if any)"), ("desired_resolution", "Desired resolution or remedy"), ("signature_date", "Signature & Date")],
    "BUSINESS_LICENSE": [("applicant_name", "Applicant / Owner full name"), ("business_name", "Registered business / trade name"), ("business_address", "Business address"), ("nature_business", "Nature / type of business activities"), ("license_type", "Type of license required (Trade / Food / GST / Other)"), ("duration_period", "License period requested (e.g., 1 year)"), ("documents_attached", "List of documents attached (ID, proof, plan)"), ("compliance_declaration", "Declaration of compliance with local regulations"), ("contact_info", "Contact number & email"), ("application_date", "Application date")],
    "LEGAL_LETTER": [("sender", "Sender full name / Firm"), ("recipient", "Recipient full name / Firm"), ("letter_date", "Date of the letter"), ("subject", "Subject / short purpose of letter"), ("background_facts", "Brief factual background (dates and events)"), ("legal_position", "Legal position / rights asserted"), ("request_action", "Specific action or remedy requested"), ("response_deadline", "Deadline for response/compliance (in days)"), ("further_action", "Consequences / further legal action if ignored"), ("signature_info", "Sender signature & contact details")]
}


# The draft formatting function remains the same
def format_draft(doc_type, answers):
    # ... (The format_draft function is unchanged)
    # The full format_draft function from your original file should be here.
    header = f"{doc_type} - Draft\nGenerated on {datetime.datetime.now().strftime('%d %b %Y %H:%M')}\n\n"; body = "";
    if doc_type == "WILL": body += "LAST WILL AND TESTAMENT\n\n"; body += f"I, {answers.get('testator_name','')} of {answers.get('testator_address','')}, being of sound mind, declare this to be my last will made on {answers.get('date_place','')}.\n\n"; body += "APPOINTMENT OF EXECUTOR:\n"; body += f"{answers.get('executor_name','')}\n\n"; body += "BEQUESTS / BENEFICIARIES:\n"; body += f"{answers.get('beneficiaries','')}\n\n"; body += "ASSETS:\n"; body += f"{answers.get('assets','')}\n\n"; sc = answers.get('special_clauses','');
    elif doc_type == "FIR": body += "FIRST INFORMATION REPORT (Draft)\n\n"; body += f"Complainant: {answers.get('complainant_name','')}\nAddress: {answers.get('complainant_address','')}\n\n"; body += f"Date & Time of Incident: {answers.get('date_time_of_incident','')}\nLocation: {answers.get('incident_location','')}\n\n"; body += "DETAILS OF INCIDENT (Chronological):\n" + answers.get('incident_details','') + "\n\n"; body += f"Accused (if known): {answers.get('accused','')}\nWitnesses: {answers.get('witnesses','')}\nLoss/Damage: {answers.get('loss_details','')}\n\n";
    elif doc_type == "RTI": body += "APPLICATION UNDER THE RIGHT TO INFORMATION ACT, 2005\n\n"; body += f"To,\nPublic Information Officer,\n{answers.get('public_authority','')}\n\n"; body += f"Subject: {answers.get('subject_info','')}\n\n"; body += "Details of Applicant:\n"; body += f"Name: {answers.get('applicant_name','')}\nAddress: {answers.get('applicant_address','')}\n\n"; body += "Information required (numbered):\n" + answers.get('detailed_questions','') + "\n\n"; body += f"Period: {answers.get('period','')}\nPreferred Format: {answers.get('preferred_format','')}\nFee Details: {answers.get('fee_details','')}\n\n";
    elif doc_type == "AFFIDAVIT": body += "AFFIDAVIT\n\n"; body += f"I, {answers.get('deponent_name','')}, S/O or D/O {answers.get('father_or_husband','')}, aged {answers.get('age_dob','')}, residing at {answers.get('deponent_address','')}, do hereby solemnly affirm and state as follows:\n\n"; body += answers.get('statements','') + "\n\n"; body += f"This affidavit is made for the purpose of {answers.get('purpose','')}.\n\n";
    elif doc_type == "LEGAL_NOTICE": body += "LEGAL NOTICE\n\n"; body += f"From: {answers.get('sender_name','')}\nAddress: {answers.get('sender_address','')}\n\nTo: {answers.get('recipient_name','')}\nAddress: {answers.get('recipient_address','')}\n\n"; body += f"Date: {answers.get('notice_date','')}\nSubject: {answers.get('subject_nature','')}\n\n"; body += "Facts:\n" + answers.get('facts_chronology','') + "\n\n"; body += "Legal Basis:\n" + answers.get('legal_basis','') + "\n\n"; body += "Demand / Relief Sought:\n" + answers.get('demand_relief','') + "\n\n"; body += f"You are requested to comply within {answers.get('deadline_days','')} days, failing which legal action will be initiated without further notice.\n\n";
    elif doc_type == "GRIEVANCE_LETTER": body += f"Grievance Letter to {answers.get('recipient_org','')}\n\n"; body += f"Complainant: {answers.get('complainant_name','')}\nContact: {answers.get('complainant_address','')}\nDesignation: {answers.get('designation','')}\n\n"; body += "Details of Grievance:\n" + answers.get('incident_details','') + "\n\n"; body += "Previous Steps Taken:\n" + answers.get('previous_steps','') + "\n\n"; body += "Desired Resolution:\n" + answers.get('desired_resolution','') + "\n\n";
    elif doc_type == "BUSINESS_LICENSE": body += "APPLICATION FOR BUSINESS / TRADE LICENSE\n\n"; body += f"Applicant: {answers.get('applicant_name','')}\nBusiness: {answers.get('business_name','')}\nAddress: {answers.get('business_address','')}\n\n"; body += f"Nature of Business: {answers.get('nature_business','')}\nLicense Type: {answers.get('license_type','')}\nDuration: {answers.get('duration_period','')}\n\n"; body += "Documents Attached:\n" + answers.get('documents_attached','') + "\n\n";
    else: body += f"Date: {answers.get('letter_date',answers.get('letter_date',''))}\n\n"; body += f"From: {answers.get('sender','')}\nTo: {answers.get('recipient','')}\n\n"; body += f"Subject: {answers.get('subject','')}\n\n"; body += "Background:\n" + answers.get('background_facts',answers.get('background_facts','')) + "\n\n"; body += "Legal Position:\n" + answers.get('legal_position',answers.get('legal_position','')) + "\n\n"; body += "Request / Relief:\n" + answers.get('request_action',answers.get('request_action','')) + "\n\n";
    draft = header + body + "\nDisclaimer: This draft is auto-generated and should be reviewed by a qualified legal professional before official use."; return draft

# --- NEW: System prompt for the Ollama model ---
SYSTEM_PROMPT = """
You are 'LegalGen', a friendly and professional AI assistant. Your goal is to help a user draft a legal document.

Your process is as follows:
1.  **Greet the user** and briefly introduce yourself. Ask which document they would like to create. The available options are: Will, FIR, RTI, Affidavit, Legal Notice, Grievance Letter, Business License, Legal Letter.
2.  **Once the user chooses a document, CONFIRM their selection.**
3.  **Ask for the necessary information ONE question at a time.** Be conversational. Do not list all the questions at once.
4.  **Wait for the user's answer** before asking the next question.
5.  **After you have asked for and received answers for ALL the required fields** for the selected document, you MUST end your final message with the exact token: `###ALL_FIELDS_COLLECTED###`. This is a critical signal for the system to proceed. Do not say this token for any other reason.
"""

@app.route('/')
def index():
    session.clear()
    # Initialize the conversation history in the session
    session['messages'] = [{'role': 'system', 'content': SYSTEM_PROMPT}]
    session['stage'] = 'CONVERSATION'
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_msg = (request.json.get('message') or '').strip()
    stage = session.get('stage', 'CONVERSATION')

    if stage == 'CONVERSATION':
        # Append user message to history
        if user_msg:
             session['messages'].append({'role': 'user', 'content': user_msg})

        # Call Ollama to get the next response
        response = ollama.chat(
            model='llama3:8b', # Or another model you have pulled
            messages=session['messages']
        )
        bot_response = response['message']['content']

        # Append bot response to history
        session['messages'].append({'role': 'assistant', 'content': bot_response})
        session.modified = True

        # Check if the collection is finished
        if '###ALL_FIELDS_COLLECTED###' in bot_response:
            session['stage'] = 'EXTRACT_DATA'
            # Clean the token from the response before sending to user
            clean_response = bot_response.replace('###ALL_FIELDS_COLLECTED###', '').strip()
            return jsonify({'type':'text','response': f'{clean_response}\n\nAll information received. Generating your draft...'})
        else:
            return jsonify({'type':'text','response': bot_response})

    elif stage == 'EXTRACT_DATA':
        # --- Data Extraction Step ---
        doc_type_prompt = "Based on the conversation history, which of the following document types was selected? Answer with the single, most likely key. Options: " + ", ".join(DOC_FIELDS.keys())
        doc_type_response = ollama.chat(model='llama3', messages=session['messages'] + [{'role': 'user', 'content': doc_type_prompt}])
        doc_type = doc_type_response['message']['content'].strip().upper()

        if doc_type not in DOC_FIELDS:
            # Fallback if the model returns an invalid doc type
            return jsonify({'type':'text', 'response': 'Sorry, I couldn\'t determine the document type from our conversation. Please refresh to start over.'})

        session['doc_type'] = doc_type
        fields = DOC_FIELDS[doc_type]
        field_keys = {key: desc for key, desc in fields}

        extraction_prompt = f"""
        Analyze the following conversation and extract the information for the fields required for a '{doc_type}' document.
        The required fields are: {json.dumps(field_keys)}

        Return ONLY a valid JSON object where the keys are the field names and the values are the extracted user answers.

        CONVERSATION:
        {json.dumps(session['messages'])}
        """
        
        extracted_data_response = ollama.chat(
            model='llama3',
            messages=[{'role': 'user', 'content': extraction_prompt}],
            options={'temperature': 0.0},
            format='json' # Ollama's JSON mode is perfect for this
        )

        try:
            answers = json.loads(extracted_data_response['message']['content'])
            session['answers'] = answers
            draft = format_draft(doc_type, answers)
            session['last_draft'] = draft
            session['stage'] = 'COMPLETED'
            preview = draft.replace('\n','<br>')
            return jsonify({'type':'preview','response': preview, 'pdf_url': url_for('download_pdf')})
        except (json.JSONDecodeError, KeyError) as e:
            return jsonify({'type':'text', 'response': f'Sorry, I had trouble structuring the data. Error: {e}. Please refresh to try again.'})


    # Completed or fallback
    return jsonify({'type':'text','response':'Session ended. Refresh page to start a new draft.'})


@app.route('/download_pdf', methods=['GET'])
def download_pdf():
    # This function remains unchanged
    draft = session.get('last_draft','')
    if not draft: return "No draft available.", 400
    buffer = io.BytesIO(); c = canvas.Canvas(buffer, pagesize=A4); width, height = A4;
    left_margin = 40; top = height - 50; lines = draft.split('\n'); text_obj = c.beginText(left_margin, top);
    text_obj.setFont('Times-Roman', 11); max_width = width - 2*left_margin;
    for line in lines:
        while len(line) > 0:
            max_chars = int(max_width / 6); chunk = line[:max_chars];
            if len(line) > max_chars:
                last_space = chunk.rfind(' ');
                if last_space > 10: chunk = line[:last_space]
            text_obj.textLine(chunk); line = line[len(chunk):].lstrip();
    c.drawText(text_obj); c.showPage(); c.save(); buffer.seek(0);
    out_path = os.path.join('/mnt/data','generated_document.pdf');
    with open(out_path,'wb') as f: f.write(buffer.read());
    return send_file(out_path, as_attachment=True, download_name='generated_document.pdf')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)




# --- Integration endpoint added by integrator ---
PDF_GENERATOR_URL = 'http://localhost:5001/api/generate_pdf'

@app.route('/finalize_document', methods=['POST'])
def finalize_document():
    data = request.get_json(force=True)
    try:
        resp = requests.post(PDF_GENERATOR_URL, json=data, timeout=30)
    except Exception as e:
        return jsonify({'error': 'Failed to reach PDF generator', 'details': str(e)}), 500

    if resp.status_code != 200:
        return jsonify({'error': 'PDF generator error', 'details': resp.text}), 500

    result = resp.json()
    preview_url = result.get('preview_url')
    if preview_url:
        return jsonify({'preview_full_url': f"http://localhost:5001{preview_url}", 'filename': result.get('filename'), 'pdf_b64': result.get('pdf_b64')})
    return jsonify({'status': 'ok', 'details': result})
# --- End integration block ---
