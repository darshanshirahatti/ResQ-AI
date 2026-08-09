"""
ResQ-AI Backend - Gmail SMTP Email Service
Sends the vehicle's live location request email to the registered recipient.

Uses Gmail SMTP with an App Password. Reads credentials from the .env file:
    GMAIL_USER          = your Gmail address (e.g. you@gmail.com)
    GMAIL_APP_PASSWORD  = the 16-character App Password (no spaces)

Run:  python backend.py
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)  # Allow the Streamlit app (on a different port) to call this API


def send_location_email(to_email, latitude, longitude, vehicle_number, driver_name):
    """
    Sends an email via Gmail SMTP (App Password) containing the vehicle's live location.
    Returns (success: bool, message: str)
    """
    gmail_user = os.getenv("GMAIL_USER")
    gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")

    if not gmail_user:
        return False, "GMAIL_USER is not set in the .env file."
    if not gmail_app_password:
        return False, "GMAIL_APP_PASSWORD is not set in the .env file."
    if gmail_app_password == "your_16_char_app_password":
        return False, "GMAIL_APP_PASSWORD is still the placeholder. Open the .env file and paste your real App Password."

    maps_link = (
        f"https://www.google.com/maps?q={latitude},{longitude}&z=18"
    )

    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;
                border: 1px solid #e0e0e0; border-radius: 12px; overflow: hidden;">
        <div style="background: #2563eb; color: white; padding: 16px; text-align: center;">
            <h2 style="margin: 0;">🚘 ResQ-AI Emergency Location Request</h2>
        </div>
        <div style="padding: 20px;">
            <p>Hello,</p>
            <p>A <strong>live location request</strong> has been issued from the ResQ-AI dashboard for the vehicle below.</p>
            <table style="border-collapse: collapse; width: 100%; margin: 16px 0;">
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Vehicle</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{vehicle_number}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Driver</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{driver_name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Latitude</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{latitude}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Longitude</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{longitude}</td>
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
        msg = MIMEMultipart("alternative")
        msg["From"] = gmail_user
        msg["To"] = to_email
        msg["Subject"] = f"🚘 Live Location Request - {vehicle_number} (ResQ-AI)"
        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(gmail_user, gmail_app_password)
            server.sendmail(gmail_user, to_email, msg.as_string())

        return True, "Email sent successfully via Gmail SMTP."
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/send-location-request", methods=["POST", "OPTIONS"])
def send_location_request():
    if request.method == "OPTIONS":
        return ("", 200)

    data = request.get_json(silent=True) or {}
    to_email = data.get("to_email", "").strip()
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    vehicle_number = data.get("vehicle_number", "KA-01-AB-1234")
    driver_name = data.get("driver_name", "John Doe")

    if not to_email:
        return jsonify({"success": False, "message": "Recipient email is required."}), 400
    if latitude is None or longitude is None:
        return jsonify({"success": False, "message": "Latitude and longitude are required."}), 400

    success, message = send_location_email(
        to_email, latitude, longitude, vehicle_number, driver_name
    )

    status_code = 200 if success else 500
    return jsonify({"success": success, "message": message}), status_code


if __name__ == "__main__":
    # Run on port 5001 (Streamlit commonly uses 8501)
    app.run(host="0.0.0.0", port=5001, debug=True)
