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
    "FIR": [("police_station", "Police station name where FIR is to be filed"), ("complainant_name", "Complainant full name"), ("complainant_address", "Complainant address & contact"), ("date_time_of_incident", "Date & time of incident"), ("incident_location", "Location of incident"), ("incident_details", "Describe incident in chronological order (formal description)"), ("accused", "Name(s) of accused (if known) or 'Unknown'"), ("witnesses", "Witness details (if any)"), ("loss_details", "Loss/damage (if any)"), ("sections", "Suspected sections of law (optional)"), ("signature_date", "Signature date")],
    "RTI": [("applicant_name", "Applicant full name"), ("applicant_address", "Applicant address & contact"), ("public_authority", "Name & address of Public Authority / PIO"), ("subject_info", "Subject of information requested (short line)"), ("detailed_questions", "Numbered questions / details of information required"), ("period", "Period for which information is sought (from - to)"), ("preferred_format", "Preferred format (Paper / Digital / Inspection)"), ("fee_details", "RTI fee details (if paid) or 'N/A'"), ("declaration", "Declaration (if any)"), ("application_date", "Application date")],
    "AFFIDAVIT": [("deponent_name", "Deponent full name"), ("father_or_husband", "Father's / Husband's name"), ("deponent_address", "Deponent residential address"), ("age_dob", "Age / Date of birth"), ("occupation", "Occupation"), ("purpose", "Purpose of affidavit (short)"), ("statements", "Statement paragraphs (numbered facts)"), ("place_date", "Place & Date of oath"), ("notary_details", "Notary / Oath officer details (Name, reg no.)"), ("signature", "Signature of Deponent")],
    "LEGAL_NOTICE": [("sender_name", "Sender full name / Firm name"), ("sender_address", "Sender address & contact"), ("recipient_name", "Recipient full name"), ("recipient_address", "Recipient address & contact"), ("notice_date", "Date of issuing notice"), ("subject_nature", "Subject / nature of dispute"), ("facts_chronology", "Chronology of facts with dates"), ("legal_basis", "Legal basis / contract clause (brief)"), ("demand_relief", "Specific relief / remedy demanded"), ("deadline_days", "Deadline to comply (in days)")],
    "GRIEVANCE_LETTER": [("complainant_name", "Your full name"), ("complainant_address", "Your address & contact"), ("designation", "Your designation / relation to organization (if any)"), ("recipient_org", "Recipient organization / authority"), ("recipient_designation", "Recipient designation (if known)"), ("incident_date_place", "Date & place of incident"), ("incident_details", "Describe grievance / incident"), ("previous_steps", "Previous complaints / steps taken (if any)"), ("desired_resolution", "Desired resolution or remedy"), ("signature_date", "Signature & Date")],
    "BUSINESS_LICENSE": [("applicant_name", "Applicant / Owner full name"), ("business_name", "Registered business / trade name"), ("business_address", "Business address"), ("nature_business", "Nature / type of business activities"), ("license_type", "Type of license required (Trade / Food / GST / Other)"), ("duration_period", "License period requested (e.g., 1 year)"), ("documents_attached", "List of documents attached (ID, proof, plan)"), ("compliance_declaration", "Declaration of compliance with local regulations"), ("contact_info", "Contact number & email"), ("application_date", "Application date")],
    "LEGAL_LETTER": [("sender", "Sender full name / Firm"), ("recipient", "Recipient full name / Firm"), ("letter_date", "Date of the letter"), ("subject", "Subject / short purpose of letter"), ("background_facts", "Brief factual background (dates and events)"), ("legal_position", "Legal position / rights asserted"), ("request_action", "Specific action or remedy requested"), ("response_deadline", "Deadline for response/compliance (in days)"), ("further_action", "Consequences / further legal action if ignored"), ("signature_info", "Sender signature & contact details")]
}


# The draft formatting function with Government of India approved formats
def format_draft(doc_type, answers):
    # No header for official government documents - they start directly with the document title
    body = ""
    # WILL
    if doc_type == "WILL":
        clauses = [
            "LAST WILL AND TESTAMENT\n\n",
            f"I, {answers.get('testator_name','')}, residing at {answers.get('testator_address','')}, "
            f"being of sound mind and disposing memory, do hereby make and publish this Will at "
            f"{answers.get('date_place','')}.\n\n",
            "1. Appointment of Executor:\n",
            f"   I appoint {answers.get('executor_name','')} as the sole Executor of this Will.\n\n",
            "2. Bequests and Beneficiaries:\n",
            f"   {answers.get('beneficiaries','')}\n\n",
            "3. Assets:\n",
            f"   {answers.get('assets','')}\n\n",
        ]
        if answers.get('special_clauses'):
            clauses.extend([
                "4. Special Clauses:\n",
                f"   {answers.get('special_clauses','')}\n\n",
            ])
        if answers.get('guardian'):
            clauses.extend([
                "5. Guardian for Minors:\n",
                f"   {answers.get('guardian','')}\n\n",
            ])
        clauses.extend([
            "Witnesses:\n",
            f"   1) {answers.get('witness1','')}\n",
            f"   2) {answers.get('witness2','')}\n",
        ])
        body = "".join(clauses)
    # FIR - Government of India Format
    elif doc_type == "FIR":
        body = (
            "=" * 80 + "\n"
            "FIRST INFORMATION REPORT\n"
            "UNDER SECTION 154, CODE OF CRIMINAL PROCEDURE, 1973\n"
            "=" * 80 + "\n\n"
            f"Police Station: {answers.get('police_station','_____________________________')}\n"
            f"FIR No.: _____________\n"
            f"Date: {answers.get('signature_date', datetime.datetime.now().strftime('%d/%m/%Y'))}\n\n"
            "PARTICULARS OF COMPLAINANT:\n"
            "-" * 80 + "\n"
            f"Name: {answers.get('complainant_name','')}\n"
            f"Address: {answers.get('complainant_address','')}\n\n"
            "PARTICULARS OF INCIDENT:\n"
            "-" * 80 + "\n"
            f"Date and Time of Occurrence: {answers.get('date_time_of_incident','')}\n"
            f"Place of Occurrence: {answers.get('incident_location','')}\n\n"
            "DETAILS OF INCIDENT:\n"
            "-" * 80 + "\n"
            f"{answers.get('incident_details','')}\n\n"
            "PARTICULARS OF ACCUSED (If Known):\n"
            "-" * 80 + "\n"
            f"{answers.get('accused','Not Known')}\n\n"
            "PARTICULARS OF WITNESSES (If Any):\n"
            "-" * 80 + "\n"
            f"{answers.get('witnesses','None')}\n\n"
            "LOSS/DAMAGE SUFFERED:\n"
            "-" * 80 + "\n"
            f"{answers.get('loss_details','None')}\n\n"
            "SECTIONS OF LAW APPLICABLE:\n"
            "-" * 80 + "\n"
            f"{answers.get('sections','To be determined')}\n\n"
            "=" * 80 + "\n"
            "DECLARATION:\n"
            "-" * 80 + "\n"
            "I hereby declare that the information furnished above is true and correct to the best of my knowledge and belief.\n\n"
            f"Signature of Complainant: _____________________________\n"
            f"Date: {answers.get('signature_date', datetime.datetime.now().strftime('%d/%m/%Y'))}\n\n"
            "Received by:\n"
            "Station House Officer / Duty Officer\n"
            "Signature: _____________________________\n"
            "=" * 80 + "\n"
        )
    # RTI - Government of India Format (RTI Act 2005)
    elif doc_type == "RTI":
        body = (
            "=" * 80 + "\n"
            "APPLICATION UNDER THE RIGHT TO INFORMATION ACT, 2005\n"
            "(Section 6(1) of the Right to Information Act, 2005)\n"
            "=" * 80 + "\n\n"
            "To,\n"
            "The Public Information Officer (PIO) / Assistant Public Information Officer (APIO)\n"
            f"{answers.get('public_authority','')}\n\n"
            "Subject: Request for Information under Section 6(1) of the RTI Act, 2005\n\n"
            "PARTICULARS OF APPLICANT:\n"
            "-" * 80 + "\n"
            f"Name: {answers.get('applicant_name','')}\n"
            f"Address: {answers.get('applicant_address','')}\n\n"
            "INFORMATION REQUESTED:\n"
            "-" * 80 + "\n"
            f"{answers.get('detailed_questions','')}\n\n"
            "PERIOD FOR WHICH INFORMATION IS SOUGHT:\n"
            "-" * 80 + "\n"
            f"{answers.get('period','Not specified')}\n\n"
            "FORMAT IN WHICH INFORMATION IS REQUIRED:\n"
            "-" * 80 + "\n"
            f"{answers.get('preferred_format','Paper copy')}\n\n"
            "FEE DETAILS:\n"
            "-" * 80 + "\n"
            f"{answers.get('fee_details','As per RTI Rules')}\n\n"
            "DECLARATION:\n"
            "-" * 80 + "\n"
            f"{answers.get('declaration','I hereby declare that the information sought is not exempted from disclosure under the RTI Act, 2005.')}\n\n"
            "=" * 80 + "\n"
            f"Signature of Applicant: _____________________________\n"
            f"Date: {answers.get('application_date', datetime.datetime.now().strftime('%d/%m/%Y'))}\n"
            "=" * 80 + "\n"
        )
    # AFFIDAVIT - Government of India Format
    elif doc_type == "AFFIDAVIT":
        body = (
            "=" * 80 + "\n"
            "AFFIDAVIT\n"
            "(As per Oaths Act, 1969)\n"
            "=" * 80 + "\n\n"
            "BEFORE ME, the undersigned authority, on this day personally appeared:\n\n"
            "PARTICULARS OF DEPONENT:\n"
            "-" * 80 + "\n"
            f"Name: {answers.get('deponent_name','')}\n"
            f"Son/Daughter/Wife of: {answers.get('father_or_husband','')}\n"
            f"Age / Date of Birth: {answers.get('age_dob','')}\n"
            f"Occupation: {answers.get('occupation','')}\n"
            f"Residential Address: {answers.get('deponent_address','')}\n\n"
            "AFFIDAVIT:\n"
            "-" * 80 + "\n"
            f"I, {answers.get('deponent_name','')}, son/daughter/wife of {answers.get('father_or_husband','')}, "
            f"aged {answers.get('age_dob','')}, residing at {answers.get('deponent_address','')}, "
            "do hereby solemnly affirm and state on oath as under:\n\n"
            f"{answers.get('statements','')}\n\n"
            f"This affidavit is made for the purpose of {answers.get('purpose','')}.\n\n"
            "=" * 80 + "\n"
            f"Place: {answers.get('place_date','').split(',')[0] if ',' in answers.get('place_date','') else '________________'}\n"
            f"Date: {answers.get('place_date','').split(',')[1] if ',' in answers.get('place_date','') else datetime.datetime.now().strftime('%d/%m/%Y')}\n\n"
            "SIGNATURE OF DEPONENT:\n"
            "-" * 80 + "\n"
            f"Signature: _____________________________\n"
            f"Name: {answers.get('deponent_name','')}\n\n"
            "VERIFICATION BY OATH ADMINISTERING AUTHORITY:\n"
            "-" * 80 + "\n"
            f"{answers.get('notary_details','')}\n\n"
            "Signature & Seal of Notary / Oath Officer:\n"
            "_____________________________\n"
            "=" * 80 + "\n"
        )
    # LEGAL NOTICE - Government of India Format
    elif doc_type == "LEGAL_NOTICE":
        body = (
            "=" * 80 + "\n"
            "LEGAL NOTICE\n"
            "(Under Section 80 of Code of Civil Procedure, 1908)\n"
            "=" * 80 + "\n\n"
            "FROM:\n"
            "-" * 80 + "\n"
            f"{answers.get('sender_name','')}\n"
            f"{answers.get('sender_address','')}\n\n"
            "TO:\n"
            "-" * 80 + "\n"
            f"{answers.get('recipient_name','')}\n"
            f"{answers.get('recipient_address','')}\n\n"
            f"Date: {answers.get('notice_date', datetime.datetime.now().strftime('%d/%m/%Y'))}\n"
            f"Subject: {answers.get('subject_nature','')}\n\n"
            "SIR / MADAM,\n\n"
            "Under instructions from and on behalf of my client, I hereby serve upon you the following notice:\n\n"
            "FACTS OF THE CASE:\n"
            "-" * 80 + "\n"
            f"{answers.get('facts_chronology','')}\n\n"
            "LEGAL BASIS:\n"
            "-" * 80 + "\n"
            f"{answers.get('legal_basis','')}\n\n"
            "DEMAND / RELIEF SOUGHT:\n"
            "-" * 80 + "\n"
            f"{answers.get('demand_relief','')}\n\n"
            "NOTICE:\n"
            "-" * 80 + "\n"
            f"You are hereby called upon to comply with the above-mentioned demands within {answers.get('deadline_days','15')} days "
            "from the date of receipt of this notice, failing which my client shall be constrained to initiate appropriate "
            "legal proceedings against you in a court of competent jurisdiction at your risk as to costs and consequences, "
            "without any further notice to you.\n\n"
            "=" * 80 + "\n"
            "Yours faithfully,\n\n"
            f"{answers.get('sender_name','')}\n"
            f"{answers.get('sender_address','')}\n"
            "=" * 80 + "\n"
        )
    # GRIEVANCE LETTER - Government of India Format
    elif doc_type == "GRIEVANCE_LETTER":
        body = (
            "=" * 80 + "\n"
            "GRIEVANCE / COMPLAINT LETTER\n"
            "(As per Grievance Redressal Mechanism)\n"
            "=" * 80 + "\n\n"
            "To,\n"
            f"{answers.get('recipient_org','')}\n"
            f"{answers.get('recipient_designation','')}\n\n"
            "Subject: Grievance / Complaint regarding _____________________________\n\n"
            "PARTICULARS OF COMPLAINANT:\n"
            "-" * 80 + "\n"
            f"Name: {answers.get('complainant_name','')}\n"
            f"Address: {answers.get('complainant_address','')}\n"
            f"Designation / Relation: {answers.get('designation','')}\n\n"
            "DETAILS OF GRIEVANCE / INCIDENT:\n"
            "-" * 80 + "\n"
            f"Date & Place of Incident: {answers.get('incident_date_place','')}\n\n"
            f"{answers.get('incident_details','')}\n\n"
            "PREVIOUS STEPS TAKEN (If Any):\n"
            "-" * 80 + "\n"
            f"{answers.get('previous_steps','None')}\n\n"
            "RELIEF / RESOLUTION SOUGHT:\n"
            "-" * 80 + "\n"
            f"{answers.get('desired_resolution','')}\n\n"
            "DECLARATION:\n"
            "-" * 80 + "\n"
            "I hereby declare that the information provided above is true and correct to the best of my knowledge and belief.\n\n"
            "=" * 80 + "\n"
            f"Signature of Complainant: _____________________________\n"
            f"Name: {answers.get('complainant_name','')}\n"
            f"Date: {answers.get('signature_date', datetime.datetime.now().strftime('%d/%m/%Y'))}\n"
            "=" * 80 + "\n"
        )
    # BUSINESS LICENSE - Government of India Format
    elif doc_type == "BUSINESS_LICENSE":
        body = (
            "=" * 80 + "\n"
            "APPLICATION FOR BUSINESS / TRADE LICENSE\n"
            "(As per Municipal Corporation / Local Authority Rules)\n"
            "=" * 80 + "\n\n"
            "To,\n"
            "The Licensing Authority\n"
            "Municipal Corporation / Local Authority\n"
            "_____________________________\n\n"
            "Subject: Application for Grant of Business / Trade License\n\n"
            "PARTICULARS OF APPLICANT:\n"
            "-" * 80 + "\n"
            f"Name: {answers.get('applicant_name','')}\n"
            f"Contact: {answers.get('contact_info','')}\n\n"
            "PARTICULARS OF BUSINESS:\n"
            "-" * 80 + "\n"
            f"Business / Trade Name: {answers.get('business_name','')}\n"
            f"Business Address: {answers.get('business_address','')}\n"
            f"Nature of Business Activities: {answers.get('nature_business','')}\n\n"
            "LICENSE DETAILS:\n"
            "-" * 80 + "\n"
            f"Type of License Requested: {answers.get('license_type','')}\n"
            f"Duration of License: {answers.get('duration_period','')}\n\n"
            "DOCUMENTS ATTACHED:\n"
            "-" * 80 + "\n"
            f"{answers.get('documents_attached','')}\n\n"
            "DECLARATION:\n"
            "-" * 80 + "\n"
            f"{answers.get('compliance_declaration','I hereby declare that all information provided is true and correct. I undertake to comply with all applicable laws, rules, and regulations.')}\n\n"
            "=" * 80 + "\n"
            f"Signature of Applicant: _____________________________\n"
            f"Name: {answers.get('applicant_name','')}\n"
            f"Date: {answers.get('application_date', datetime.datetime.now().strftime('%d/%m/%Y'))}\n"
            "=" * 80 + "\n"
        )
    # LEGAL LETTER (generic)
    else:
        body = (
            f"Date: {answers.get('letter_date',answers.get('letter_date',''))}\n\n"
            f"From: {answers.get('sender','')}\n"
            f"To: {answers.get('recipient','')}\n\n"
            f"Subject: {answers.get('subject','')}\n\n"
            "Background Facts:\n"
            f"{answers.get('background_facts',answers.get('background_facts',''))}\n\n"
            "Legal Position:\n"
            f"{answers.get('legal_position',answers.get('legal_position',''))}\n\n"
            "Request / Relief Sought:\n"
            f"{answers.get('request_action',answers.get('request_action',''))}\n\n"
            + (f"Response Deadline (in days): {answers.get('response_deadline','')}\n\n" if answers.get('response_deadline') else "")
            + (f"Further Action if Ignored: {answers.get('further_action','')}\n" if answers.get('further_action') else "")
        )
    disclaimer = (
        "\n\n" + "=" * 80 + "\n"
        "NOTE: This document is auto-generated based on user inputs and follows standard Government of India formats. "
        "Please review with a qualified legal professional and adapt to local jurisdictional requirements before official submission.\n"
        "=" * 80
    )
    draft = body + disclaimer
    return draft

# Helper function to categorize fields into basic info vs descriptions
def categorize_fields(doc_type):
    """Separate fields into basic information and descriptive fields"""
    fields = DOC_FIELDS.get(doc_type, [])
    basic_fields = []
    description_fields = []
    
    # Keywords that indicate descriptive fields
    desc_keywords = ['details', 'describe', 'chronology', 'statements', 'questions', 'facts', 'background', 'incident', 'grievance', 'steps', 'resolution', 'relief', 'demand', 'basis', 'position', 'action']
    
    for key, desc in fields:
        is_description = any(keyword in desc.lower() or keyword in key.lower() for keyword in desc_keywords)
        if is_description:
            description_fields.append((key, desc))
        else:
            basic_fields.append((key, desc))
    
    return basic_fields, description_fields

# --- NEW: System prompt for the Ollama model ---
SYSTEM_PROMPT = """
You are 'LegalGen', a professional AI assistant specialized in drafting Government of India approved legal documents.

CRITICAL PROCESS - Follow this EXACT order:

PHASE 1: COLLECT BASIC INFORMATION
1. Greet the user and ask which document they want to create. Options: Will, FIR, RTI, Affidavit, Legal Notice, Grievance Letter, Business License, Legal Letter.
2. Once document is selected, CONFIRM the selection and say: "I'll help you create a [document type]. Let me collect the necessary information step by step."
3. Ask for ALL basic information fields FIRST (names, addresses, dates, locations, contact details, police station names, etc.). Ask ONE question at a time. Be clear and specific.
4. For each field, ask exactly what is needed. Examples:
   - For FIR: "What is the name of the police station where you want to file the FIR?"
   - For FIR: "What is your full name as the complainant?"
   - For FIR: "What is your complete address and contact number?"
   - For FIR: "What was the date and time when the incident occurred?"
   - For FIR: "Where did the incident take place? (Location/Address)"
   - Continue asking for ALL basic fields one by one until complete.
5. DO NOT ask for descriptions (incident details, chronology, etc.) until ALL basic fields are collected.

PHASE 2: COLLECT DESCRIPTIONS (You will formalize them)
6. After ALL basic information is collected, say: "Thank you. Now I need you to describe the details. You can provide the information in your own words - I will convert it into formal, official language suitable for Government of India documentation."
7. Ask for descriptive fields ONE at a time. Tell the user they can describe it informally, and you will formalize it.
8. Guide them: "Please describe [field description]. You can explain it in your own words - I will convert it into formal, chronological, and official language as required for government documentation."
9. When the user provides a description (even if informal), acknowledge it and say: "Thank you. I've noted that and will format it appropriately for the official document."
10. Wait for their response before asking the next description.

PHASE 3: COMPLETION
11. After collecting ALL fields (both basic info AND descriptions), summarize what you've collected.
12. Ask: "Is all the information correct? Please confirm with 'YES' or 'PREVIEW'."
13. Once confirmed, you MUST end your message with the exact token: `###ALL_FIELDS_COLLECTED###`

IMPORTANT RULES:
- NEVER ask for descriptions before collecting all basic information
- ALWAYS ask for one field at a time but collect all the information first user provide you
- ACCEPT informal descriptions from users - you will convert them to formal language later
- Tell users they can describe things in their own words, and you'll formalize it
- For descriptions, accept any format but acknowledge you'll make it formal
- Do NOT use the token `###ALL_FIELDS_COLLECTED###` until ALL fields are collected and user confirms
- Be professional and helpful throughout
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
        
        # Check if document type was just selected and provide field guidance
        if user_msg and not session.get('doc_type_selected'):
            user_msg_upper = user_msg.upper().strip()
            for doc_key in DOC_FIELDS.keys():
                if doc_key.replace('_', ' ') in user_msg_upper or doc_key in user_msg_upper:
                    session['doc_type_selected'] = doc_key
                    basic_fields, desc_fields = categorize_fields(doc_key)
                    field_guidance = f"\n\nDOCUMENT TYPE SELECTED: {doc_key}\n"
                    field_guidance += f"BASIC INFORMATION FIELDS TO COLLECT FIRST ({len(basic_fields)} fields):\n"
                    for key, desc in basic_fields:
                        field_guidance += f"- {desc}\n"
                    field_guidance += f"\nDESCRIPTION FIELDS TO COLLECT AFTER ({len(desc_fields)} fields):\n"
                    for key, desc in desc_fields:
                        field_guidance += f"- {desc} (Ask for this in formal, official language)\n"
                    # Add guidance to the last assistant message or create a system message
                    if session.get('messages'):
                        session['messages'].append({
                            'role': 'system',
                            'content': field_guidance
                        })
                    break

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
        fields_collected = '###ALL_FIELDS_COLLECTED###' in bot_response
        
        # Fallback: Check if user confirmed and wants preview
        user_wants_preview = False
        if user_msg:
            user_msg_upper = user_msg.upper().strip()
            # Check for confirmation keywords
            confirmation_keywords = ['YES', 'PREVIEW', 'CONFIRM', 'OK', 'CORRECT', 'RIGHT', 'PROCEED', 'GENERATE', 'CREATE']
            user_wants_preview = any(keyword in user_msg_upper for keyword in confirmation_keywords)
            
            # Also check if bot asked for confirmation in recent messages
            recent_bot_messages = [msg.get('content', '') for msg in session.get('messages', []) if msg.get('role') == 'assistant'][-3:]
            bot_asked_confirmation = any('correct' in msg.lower() or 'confirm' in msg.lower() or 'proceed' in msg.lower() for msg in recent_bot_messages)
            
            if user_wants_preview and bot_asked_confirmation:
                # User confirmed, trigger extraction
                fields_collected = True
                # Modify bot response to indicate we're proceeding
                bot_response = "Thank you for confirming. Generating your document now...\n\n###ALL_FIELDS_COLLECTED###"
                # Update the last message in session
                if session.get('messages'):
                    session['messages'][-1]['content'] = bot_response
        
        if fields_collected:
            # Clean the token from the response
            clean_response = bot_response.replace('###ALL_FIELDS_COLLECTED###', '').strip()
            if not clean_response or clean_response == "Thank you for confirming. Generating your document now...":
                clean_response = "All information collected! Generating your document..."
            # Immediately proceed to extraction instead of waiting for next request
            session['stage'] = 'EXTRACT_DATA'
            session.modified = True
            stage = 'EXTRACT_DATA'  # Update local variable to trigger extraction in same request
            # Store the cleaned bot response to show it along with preview button
            session['final_bot_message'] = clean_response
            # Fall through to extraction logic below
        else:
            return jsonify({'type':'text','response': bot_response})
    
    # Handle extraction (either from immediate trigger or from EXTRACT_DATA stage)
    if stage == 'EXTRACT_DATA':
        # --- Data Extraction Step ---
        doc_type_prompt = "Based on the conversation history, which of the following document types was selected? Answer with the single, most likely key. Options: " + ", ".join(DOC_FIELDS.keys())
        doc_type_response = ollama.chat(model='llama3:8b', messages=session['messages'] + [{'role': 'user', 'content': doc_type_prompt}])
        doc_type_raw = doc_type_response['message']['content'].strip().upper()
        
        # Extract doc_type from response (handle cases where model adds extra text)
        doc_type = None
        for key in DOC_FIELDS.keys():
            if key in doc_type_raw:
                doc_type = key
                break
        
        # If no match found, try to clean and match
        if doc_type is None:
            # Remove common prefixes/suffixes and try again
            cleaned = doc_type_raw.split()[0] if doc_type_raw.split() else doc_type_raw
            if cleaned in DOC_FIELDS:
                doc_type = cleaned
            else:
                # Last resort: try to find partial match
                for key in DOC_FIELDS.keys():
                    if key.startswith(cleaned[:3]) or cleaned[:3] in key:
                        doc_type = key
                        break

        if doc_type not in DOC_FIELDS:
            # Fallback if the model returns an invalid doc type
            return jsonify({'type':'text', 'response': f'Sorry, I couldn\'t determine the document type from our conversation. Received: {doc_type_raw}. Please refresh to start over.'})

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
            model='llama3:8b',
            messages=[{'role': 'user', 'content': extraction_prompt}],
            options={'temperature': 0.0},
            format='json' # Ollama's JSON mode is perfect for this
        )

        try:
            answers = json.loads(extracted_data_response['message']['content'])
            
            # Formalize descriptions - convert informal descriptions to formal language
            basic_fields, desc_fields = categorize_fields(doc_type)
            desc_field_keys = [key for key, _ in desc_fields]
            
            # Formalize each description field
            for field_key in desc_field_keys:
                if field_key in answers and answers[field_key]:
                    informal_desc = str(answers[field_key]).strip()
                    if informal_desc and informal_desc.lower() not in ['n/a', 'none', 'not applicable', 'unknown']:
                        formalization_prompt = f"""
Convert the following informal description into formal, official language suitable for Government of India legal documentation.

Field: {field_keys.get(field_key, field_key)}
Document Type: {doc_type}
Original (informal) description: {informal_desc}

Requirements:
- Use formal, professional language
- Maintain chronological order if applicable
- Use proper legal terminology
- Make it suitable for official government documentation
- Keep all factual information intact
- Write in third person or formal first person as appropriate

Return ONLY the formalized description, nothing else:
"""
                        try:
                            formalized_response = ollama.chat(
                                model='llama3:8b',
                                messages=[{'role': 'user', 'content': formalization_prompt}],
                                options={'temperature': 0.3}  # Slightly creative for better formalization
                            )
                            formalized_desc = formalized_response['message']['content'].strip()
                            # Clean up any extra text the model might add
                            if 'formalized' in formalized_desc.lower() or 'description:' in formalized_desc.lower():
                                # Extract just the description part
                                lines = formalized_desc.split('\n')
                                formalized_desc = '\n'.join([line for line in lines if not any(word in line.lower() for word in ['formalized', 'description:', 'here is', 'converted'])])
                            answers[field_key] = formalized_desc
                        except Exception as e:
                            # If formalization fails, use original but log it
                            print(f"Formalization failed for {field_key}: {e}")
                            # Keep original answer
            
            session['answers'] = answers
            # Basic validation for required fields; if missing, route back to conversation to collect them
            required_keys = [key for key, _ in fields]
            missing_keys = [key for key in required_keys if not str(answers.get(key, '')).strip()]
            if missing_keys:
                session['stage'] = 'CONVERSATION'
                # Politely ask for the first missing field to keep 1-by-1 flow
                first_missing = missing_keys[0]
                missing_desc = field_keys.get(first_missing, first_missing.replace('_', ' ').title())
                # Guide the assistant by appending a system note
                session['messages'].append({
                    'role': 'system',
                    'content': f"Please ask the user for the missing field '{first_missing}' ({missing_desc}) in a formal tone, one question at a time."
                })
                return jsonify({'type': 'text', 'response': f"Before generating the draft, I still need: {missing_desc}. Please provide it."})
            draft = format_draft(doc_type, answers)
            session['last_draft'] = draft
            session['stage'] = 'COMPLETED'
            preview = draft.replace('\n','<br>')
            pdf_url = url_for('download_pdf')
            preview_url = f"{pdf_url}?mode=preview"
            preview_page_url = url_for('preview_page')
            
            # Get the bot's final message if it exists
            final_message = session.get('final_bot_message', 'All information collected! Your document has been generated successfully.')
            # Clear it from session after use
            if 'final_bot_message' in session:
                del session['final_bot_message']
            
            return jsonify({
                'type': 'preview',
                'response': preview,
                'bot_message': final_message,  # Include bot's message
                'pdf_url': pdf_url,
                'preview_url': preview_url,
                'preview_page_url': preview_page_url,
                'doc_type': doc_type
            })
        except (json.JSONDecodeError, KeyError) as e:
            return jsonify({'type':'text', 'response': f'Sorry, I had trouble structuring the data. Error: {e}. Please refresh to try again.'})


    # Completed or fallback
    return jsonify({'type':'text','response':'Session ended. Refresh page to start a new draft.'})


@app.route('/preview')
def preview_page():
    """Render the preview page"""
    if not session.get('last_draft'):
        return "No draft available. Please go back and generate a document first.", 400
    return render_template('preview.html')

@app.route('/api/get_preview', methods=['GET'])
def get_preview():
    """API endpoint to get preview data"""
    draft = session.get('last_draft', '')
    doc_type = session.get('doc_type', '')
    if not draft:
        return jsonify({'success': False, 'error': 'No draft available'}), 400
    
    preview = draft.replace('\n', '<br>')
    pdf_url = url_for('download_pdf')
    preview_url = f"{pdf_url}?mode=preview"
    
    return jsonify({
        'success': True,
        'preview': preview,
        'pdf_url': pdf_url,
        'preview_url': preview_url,
        'doc_type': doc_type
    })

@app.route('/download_pdf', methods=['GET'])
def download_pdf():
    try:
        draft = session.get('last_draft','')
        if not draft: 
            return "No draft available.", 400
        
        # Remove ALL duplicate content lines and separator lines
        # This ensures each unique content line appears only once, and removes separators
        lines = draft.split('\n')
        cleaned_lines = []
        seen_content = set()  # Track content lines we've seen
        
        for line in lines:
            line_stripped = line.strip()
            # Check if line is a separator (contains only = or - characters)
            is_separator = (line_stripped and 
                          (all(c == '=' for c in line_stripped) or 
                           all(c == '-' for c in line_stripped)))
            is_empty = not line_stripped
            
            # Skip separator lines completely
            if is_separator:
                continue
            # For empty lines, limit to max 1 consecutive
            elif is_empty:
                # Only add if last line wasn't empty
                if not cleaned_lines or cleaned_lines[-1].strip():
                    cleaned_lines.append(line)
            else:
                # For content lines, only add if we haven't seen this exact line before
                if line not in seen_content:
                    cleaned_lines.append(line)
                    seen_content.add(line)
        
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        left_margin = 40
        top = height - 50
        line_height = 14
        y_position = top
        
        # Set font once
        c.setFont('Times-Roman', 11)
        
        # Calculate max width for text
        max_width = width - 2 * left_margin
        # Approximate characters per line (Times-Roman 11pt is about 6.5 points per char)
        max_chars_per_line = int(max_width / 6.5)
        
        # Process each line exactly once - use drawString to write directly
        for line in cleaned_lines:
            # Check if we need a new page
            if y_position < 50:
                c.showPage()
                y_position = height - 50
                c.setFont('Times-Roman', 11)  # Reset font on new page
            
            # Handle empty lines
            if not line.strip():
                y_position -= line_height
                continue
            
            # Process line - wrap if necessary
            remaining = line
            while remaining:
                # Check if we need a new page before writing
                if y_position < 50:
                    c.showPage()
                    y_position = height - 50
                    c.setFont('Times-Roman', 11)
                
                # Check if line fits
                if len(remaining) <= max_chars_per_line:
                    # Write the entire line directly at coordinates
                    c.drawString(left_margin, y_position, remaining)
                    y_position -= line_height
                    remaining = ''
                else:
                    # Need to wrap - find break point
                    chunk = remaining[:max_chars_per_line]
                    last_space = chunk.rfind(' ')
                    
                    if last_space > max_chars_per_line * 0.5:
                        # Break at space
                        chunk = remaining[:last_space]
                        remaining = remaining[last_space:].lstrip()
                    else:
                        # Break at max_chars
                        chunk = remaining[:max_chars_per_line]
                        remaining = remaining[max_chars_per_line:].lstrip()
                    
                    # Write the chunk directly at coordinates
                    c.drawString(left_margin, y_position, chunk)
                    y_position -= line_height
        
        # Final page
        c.showPage()
        c.save()
        buffer.seek(0)
        mode = request.args.get('mode', 'download')
        as_attachment = mode != 'preview'
        
        # Generate appropriate filename based on document type
        doc_type = session.get('doc_type', 'Document')
        doc_type_clean = doc_type.replace('_', ' ').title()
        filename = f"{doc_type_clean}_Legal_Document.pdf"
        
        return send_file(
            buffer,
            as_attachment=as_attachment,
            download_name=filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        import traceback
        return f"Error generating PDF: {str(e)}\n{traceback.format_exc()}", 500

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
