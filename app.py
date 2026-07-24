#!/usr/bin/env python3
"""
HVAC Install Pipeline — Combined Form + Backend Server
Serves form and handles submissions on single port
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
import json

app = Flask(__name__, static_folder='/tmp/hvac_deploy')
CORS(app)

# Gmail configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "csperry@tbyrdhvac.com"
SENDER_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

# Recipients
# TEST MODE: Only send to Colten
FULL_DETAIL_RECIPIENTS = [
    "csperry@tbyrdhvac.com"
]

# TEST MODE: Disable Johnstone emails
EQUIPMENT_RECIPIENTS = [
    # "cody.stough@johnstonesupply.com",
    # "keith.hartsell@johnstonesupply.com",
    # "zach.ward@johnstonesupply.com"
]

def send_email(recipient, subject, body):
    """Send a single email"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email sent to {recipient}")
        return True
    except Exception as e:
        print(f"❌ Email error to {recipient}: {e}")
        return False

@app.route('/')
def serve_form():
    """Serve the HTML form"""
    return send_from_directory('/tmp/hvac_deploy', 'index.html')

@app.route('/logo.jpg')
def serve_logo():
    """Serve the logo image"""
    return send_from_directory('/tmp/hvac_deploy', 'logo.jpg')

@app.route('/submit', methods=['POST', 'OPTIONS'])
def submit_job():
    """Handle form submission"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['customerName', 'dateSold', 'installDate', 'address', 'phone', 
                   'jobNumber', 'equipment', 'leadSource', 'paymentMethod', 'amount']
        
        for field in required:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'error': f'Missing {field}'}), 400
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Full email body for Colten
        full_body = f"""
New Job Submitted - {timestamp}

Customer: {data['customerName']}
Date Sold: {data['dateSold']}
Install Date: {data['installDate']}
Address: {data['address']}
Phone: {data['phone']}
Job #: {data['jobNumber']}

Equipment:
{data['equipment']}

Lead Source: {data['leadSource']}
{f"Tech: {data['techName']}" if data.get('techName') else ""}
Payment Method: {data['paymentMethod']}
Amount: ${float(data['amount']):.2f}

Notes: {data['notes']}
        """
        
        # Equipment email body for suppliers
        equipment_body = f"""
NEW TBYRD HVAC EQUIPMENT ORDER

Customer: {data['customerName']}
Install Date: {data['installDate']}

Equipment to Order:
{data['equipment']}

---
Please pull and prepare this equipment for the scheduled install date above.
        """
        
        # Send full detail emails to you only for now
        for recipient in FULL_DETAIL_RECIPIENTS:
            send_email(recipient, f"New HVAC Job Entry: {data['customerName']}", full_body)
        
        # Send equipment emails to suppliers
        for recipient in EQUIPMENT_RECIPIENTS:
            send_email(recipient, "NEW TBYRD HVAC Equipment Order", equipment_body)
        
        return jsonify({
            'success': True,
            'message': 'Job submitted successfully',
            'timestamp': timestamp
        }), 200
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()}), 200

if __name__ == '__main__':
    print("🚀 HVAC Pipeline Server Starting...")
    print(f"📧 Sender: {SENDER_EMAIL}")
    print(f"🌐 Serving on http://0.0.0.0:8000")
    
    if not SENDER_PASSWORD:
        print("⚠️  WARNING: GMAIL_APP_PASSWORD not set!")
    
    app.run(host='0.0.0.0', port=8000, debug=False)
