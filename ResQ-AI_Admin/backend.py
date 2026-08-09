"""
ResQ-AI Admin Backend - Live Location Store + Gmail API Reader
==============================================================
Separate backend for the ADMIN dashboard.

Responsibilities:
  1. Receive live location/sensor updates pushed by the car dashboard.
  2. Store the latest position + movement history + emergency alerts in memory.
  3. Serve the latest location, history, and alerts to the admin dashboard.
  4. Read incoming "location request" emails from the admin's Gmail inbox via the
     Gmail API (OAuth) so the admin can ACCEPT the tracking request.
  5. Send the current location to the admin's registered email via Gmail SMTP.

Run:  python backend.py        (serves on port 5002)
"""
import os
import re
import time
import smtplib
import base64
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Gmail API (OAuth) imports
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Load credentials from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)  # Allow both the car dashboard and admin dashboard to call this API

# ---------------------------------------------------------------------------
# In-memory data store
# ---------------------------------------------------------------------------
vehicles = {}
MAX_HISTORY = 200        # keep last 200 movement points per vehicle
MAX_ALERTS = 50          # keep last 50 emergency alerts per vehicle

# Gmail API scope: read emails + send as
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
]


def get_or_create_vehicle(vehicle_number, driver_name=None):
    """Return the vehicle record, creating a new one if it does not exist."""
    if vehicle_number not in vehicles:
        vehicles[vehicle_number] = {
            "vehicle_number": vehicle_number,
            "driver_name": driver_name or "Unknown Driver",
            "last_update": None,
            "latest": None,
            "history": [],
            "alerts": [],
        }
    elif driver_name:
        vehicles[vehicle_number]["driver_name"] = driver_name
    return vehicles[vehicle_number]


# ---------------------------------------------------------------------------
# Gmail API (OAuth) helpers - for READING the admin's inbox
# ---------------------------------------------------------------------------
def get_gmail_service():
    """
    Builds an authenticated Gmail API service using OAuth.

    On first run this will print a URL and ask you to paste an authorization
    code (console flow). Afterwards the token is cached in token.json.
    """
    token_file = os.getenv('GMAIL_TOKEN_FILE', 'token.json')
    client_secret_file = os.getenv('GMAIL_CLIENT_SECRET_FILE', 'client_secret.json')

    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(client_secret_file):
                raise FileNotFoundError(
                    f'{client_secret_file} not found. Download your OAuth client JSON '
                    f'from Google Cloud Console and save it as {client_secret_file}.'
                )
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
            # Opens a browser for the admin to authorize. token.json is saved afterwards.
            creds = flow.run_local_server(port=0)
        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)


def decode_body(payload):
    """Extract plain text or html body from a Gmail message payload."""
    if payload.get('mimeType') == 'text/plain' and 'data' in payload.get('body', {}):
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', 'ignore')
    if payload.get('mimeType') == 'text/html' and 'data' in payload.get('body', {}):
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', 'ignore')
    # Multipart: recurse into parts
    for part in payload.get('parts', []):
        text = decode_body(part)
        if text:
            return text
    return ''


def read_latest_location_requests(max_results=10):
    """
    Reads the most recent emails whose subject contains the location-request
    keyword. Returns (success, requests_list_or_error_message).
    """
    try:
        service = get_gmail_service()
    except FileNotFoundError as e:
        return False, str(e)
    except Exception as e:
        return False, f'Gmail API auth error: {str(e)}'

    try:
        # Search for location request emails (from the car dashboard backend)
        query = 'subject:(Live Location Request) OR subject:(Location Request) OR subject:(ResQ-AI)'
        results = service.users().messages().list(
            userId='me', q=query, maxResults=max_results
        ).execute()

        messages = results.get('messages', [])
        location_requests = []

        for msg_meta in messages:
            msg = service.users().messages().get(
                userId='me', id=msg_meta['id'], format='full'
            ).execute()
            headers = {h['name'].lower(): h['value'] for h in msg.get('payload', {}).get('headers', [])}
            subject = headers.get('subject', '')
            from_addr = headers.get('from', '')
            date = msg.get('internalDate')
            date_str = datetime.fromtimestamp(int(date) / 1000).strftime('%Y-%m-%d %H:%M:%S') if date else ''

            body = decode_body(msg.get('payload', {}))

            # Try to extract lat/lon from the email body
            lat = lon = None
            m = re.search(r'Latitude[:\s<]*(-?\d+\.\d+)', body)
            if m:
                lat = m.group(1)
            m = re.search(r'Longitude[:\s<]*(-?\d+\.\d+)', body)
            if m:
                lon = m.group(1)

            # Try to extract vehicle number
            vm = re.search(r'(Vehicle)[:\s<]*([A-Z]{2}-[0-9]{2}-[A-Z]{2}-\d{4})', body)
            vehicle_number = vm.group(2) if vm else 'Unknown Vehicle'

            location_requests.append({
                'id': msg_meta['id'],
                'subject': subject,
                'from': from_addr,
                'date': date_str,
                'message_preview': body[:300],
                'latitude': lat,
                'longitude': lon,
                'vehicle_number': vehicle_number,
            })

        return True, location_requests
    except Exception as e:
        return False, f'Gmail API read error: {str(e)}'


# ---------------------------------------------------------------------------
# Email helper (Gmail SMTP) - for SENDING location emails
# ---------------------------------------------------------------------------
def send_location_email(to_email, latitude, longitude, vehicle_number, driver_name):
    """
    Sends an email via Gmail SMTP (App Password) containing the vehicle's live location.
    Returns (success: bool, message: str)
    """
    gmail_user = os.getenv('GMAIL_USER')
    gmail_app_password = os.getenv('GMAIL_APP_PASSWORD')

    if not gmail_user:
        return False, 'GMAIL_USER is not set in the .env file.'
    if not gmail_app_password:
        return False, 'GMAIL_APP_PASSWORD is not set in the .env file.'
    if gmail_app_password == 'your_16_char_app_password':
        return False, 'GMAIL_APP_PASSWORD is still the placeholder. Open the .env file and paste your real App Password.'

    maps_link = f'https://www.google.com/maps?q={latitude},{longitude}&z=18'

    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;
                border: 1px solid #e0e0e0; border-radius: 12px; overflow: hidden;">
        <div style="background: #2563eb; color: white; padding: 16px; text-align: center;">
            <h2 style="margin: 0;">🚘 ResQ-AI Live Location Update</h2>
        </div>
        <div style="padding: 20px;">
            <p>Hello Admin,</p>
            <p>The <strong>{vehicle_number}</strong> ({driver_name}) has just shared its live location.</p>
            <table style="border-collapse: collapse; width: 100%; margin: 16px 0;">
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Vehicle</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{vehicle_number}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Latitude</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{latitude}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Longitude</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{longitude}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Time</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                </tr>
            </table>
            <p>
                <a href="{maps_link}" style="background:#22c55e; color:white; padding:12px 24px;
                   text-decoration:none; border-radius:8px; display:inline-block;">
                   📍 View Live Location on Google Maps
                </a>
            </p>
            <p style="color:#666; font-size:13px;">This is an automated message from the ResQ-AI emergency system.</p>
        </div>
    </div>
    """

    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = gmail_user
        msg['To'] = to_email
        msg['Subject'] = f'🚘 Live Location Request - {vehicle_number} (ResQ-AI)'
        msg.attach(MIMEText(html_content, 'html'))

        with smtplib.SMTP('smtp.gmail.com', 587, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(gmail_user, gmail_app_password)
            server.sendmail(gmail_user, to_email, msg.as_string())

        return True, 'Email sent successfully via Gmail SMTP.'
    except Exception as e:
        return False, f'Failed to send email: {str(e)}'


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'vehicles': len(vehicles)})


@app.route('/update-location', methods=['POST', 'OPTIONS'])
def update_location():
    """Car dashboard pushes its live location + sensor data here."""
    if request.method == 'OPTIONS':
        return ('', 200)

    data = request.get_json(silent=True) or {}
    vehicle_number = (data.get('vehicle_number') or '').strip()
    if not vehicle_number:
        return jsonify({'success': False, 'message': 'vehicle_number is required.'}), 400

    vehicle = get_or_create_vehicle(vehicle_number, data.get('driver_name'))

    lat = data.get('latitude')
    lon = data.get('longitude')
    if lat is None or lon is None:
        return jsonify({'success': False, 'message': 'latitude and longitude are required.'}), 400

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    now_epoch = time.time()

    vehicle['latest'] = {
        'lat': float(lat),
        'lon': float(lon),
        'speed': data.get('speed', 0),
        'temp': data.get('temp', 0),
        'heart': data.get('heart', 0),
        'smoke': data.get('smoke', 0),
        'impact': bool(data.get('impact', False)),
        'timestamp': now_epoch,
        'time': now_str,
    }
    vehicle['last_update'] = now_str

    vehicle['history'].append({
        'lat': float(lat),
        'lon': float(lon),
        'time': now_str,
        'speed': data.get('speed', 0),
    })
    if len(vehicle['history']) > MAX_HISTORY:
        vehicle['history'] = vehicle['history'][-MAX_HISTORY:]

    # If this is flagged as an emergency, store it as an alert too
    if data.get('is_emergency'):
        vehicle['alerts'].insert(0, {
            'timestamp': now_str,
            'crash_type': data.get('crash_type', 'EMERGENCY'),
            'danger_reasons': data.get('danger_reasons', []),
            'gps': [float(lat), float(lon)],
            'speed': data.get('speed', 0),
            'temp': data.get('temp', 0),
            'heart': data.get('heart', 0),
            'smoke': data.get('smoke', 0),
        })
        if len(vehicle['alerts']) > MAX_ALERTS:
            vehicle['alerts'] = vehicle['alerts'][:MAX_ALERTS]

    return jsonify({'success': True, 'message': 'Location updated.'})


@app.route('/vehicles', methods=['GET', 'OPTIONS'])
def list_vehicles():
    """Return the list of vehicles that have pushed data."""
    if request.method == 'OPTIONS':
        return ('', 200)
    result = []
    for vn, v in vehicles.items():
        result.append({
            'vehicle_number': vn,
            'driver_name': v['driver_name'],
            'last_update': v['last_update'],
            'has_location': v['latest'] is not None,
        })
    return jsonify({'success': True, 'vehicles': result})


@app.route('/current-location', methods=['GET', 'OPTIONS'])
def current_location():
    """Return the latest live location for a vehicle."""
    if request.method == 'OPTIONS':
        return ('', 200)
    vehicle_number = request.args.get('vehicle', '').strip()
    if not vehicle_number:
        return jsonify({'success': False, 'message': 'vehicle query param is required.'}), 400

    vehicle = vehicles.get(vehicle_number)
    if not vehicle or vehicle['latest'] is None:
        return jsonify({'success': False, 'message': 'No location data for this vehicle yet.'}), 404

    return jsonify({
        'success': True,
        'vehicle': vehicle_number,
        'driver_name': vehicle['driver_name'],
        'last_update': vehicle['last_update'],
        'location': vehicle['latest'],
    })


@app.route('/location-history', methods=['GET', 'OPTIONS'])
def location_history():
    """Return the movement history (trail) for a vehicle."""
    if request.method == 'OPTIONS':
        return ('', 200)
    vehicle_number = request.args.get('vehicle', '').strip()
    if not vehicle_number:
        return jsonify({'success': False, 'message': 'vehicle query param is required.'}), 400

    vehicle = vehicles.get(vehicle_number)
    if not vehicle:
        return jsonify({'success': False, 'message': 'No data for this vehicle yet.'}), 404

    return jsonify({
        'success': True,
        'vehicle': vehicle_number,
        'history': vehicle['history'],
    })


@app.route('/emergency-alerts', methods=['GET', 'OPTIONS'])
def emergency_alerts():
    """Return the emergency alerts for a vehicle (or all vehicles)."""
    if request.method == 'OPTIONS':
        return ('', 200)
    vehicle_number = request.args.get('vehicle', '').strip()
    if vehicle_number:
        vehicle = vehicles.get(vehicle_number)
        alerts = vehicle['alerts'] if vehicle else []
    else:
        alerts = []
        for v in vehicles.values():
            alerts.extend(v['alerts'])
        alerts.sort(key=lambda a: a['timestamp'], reverse=True)
    return jsonify({'success': True, 'alerts': alerts})


@app.route('/send-location-request', methods=['POST', 'OPTIONS'])
def send_location_request():
    """Send the current location of a vehicle to a recipient email (admin)."""
    if request.method == 'OPTIONS':
        return ('', 200)

    data = request.get_json(silent=True) or {}
    to_email = (data.get('to_email') or '').strip()
    vehicle_number = (data.get('vehicle_number') or '').strip()

    if not to_email:
        return jsonify({'success': False, 'message': 'Recipient email is required.'}), 400

    # Use provided lat/lon, or pull the latest stored location for the vehicle
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    driver_name = data.get('driver_name', 'Unknown Driver')

    if (latitude is None or longitude is None) and vehicle_number:
        vehicle = vehicles.get(vehicle_number)
        if vehicle and vehicle['latest']:
            latitude = vehicle['latest']['lat']
            longitude = vehicle['latest']['lon']
            driver_name = vehicle['driver_name']

    if latitude is None or longitude is None:
        return jsonify({'success': False, 'message': 'No location available. The car has not pushed any data yet, or provide latitude/longitude.'}), 400

    success, message = send_location_email(
        to_email, latitude, longitude, vehicle_number, driver_name
    )
    status_code = 200 if success else 500
    return jsonify({'success': success, 'message': message}), status_code


@app.route('/gmail-requests', methods=['GET', 'OPTIONS'])
def gmail_requests():
    """
    Read the latest location-request emails from the admin's Gmail inbox via the
    Gmail API. This is how the admin ACCEPTS a tracking request.
    """
    if request.method == 'OPTIONS':
        return ('', 200)

    max_results = request.args.get('max', default=10, type=int)
    success, result = read_latest_location_requests(max_results=max_results)

    if success:
        return jsonify({'success': True, 'requests': result})
    return jsonify({'success': False, 'message': result}), 500


if __name__ == '__main__':
    # Admin backend runs on port 5002 (car backend uses 5001)
    app.run(host='0.0.0.0', port=5002, debug=True)
