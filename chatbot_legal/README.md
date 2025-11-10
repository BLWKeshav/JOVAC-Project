# Legal Document Chatbot (Local Flask App)

## Overview
This project is a local, offline-capable Flask chatbot that guides a user through drafting 8 types of legal documents (Will, FIR, RTI, Affidavit, Legal Notice, Grievance Letter, Business License Application, Legal Letter). It follows a conversational interview flow (greeting -> choose document -> ask fields one-by-one -> generate preview -> downloadable PDF).

## Run locally
1. Create a Python virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # on Windows: venv\Scripts\activate
   ```
2. Install requirements:
   ```
   pip install -r requirements.txt
   ```
3. Run the app:
   ```
   python app.py
   ```
4. Open your browser at `http://127.0.0.1:5000`

## Notes
- The generated PDF uses `reportlab` and will be saved to `/mnt/data/generated_document.pdf` when you click "Download PDF".
- The drafts are auto-generated templates and include a legal disclaimer. Please review with a qualified legal professional before using.