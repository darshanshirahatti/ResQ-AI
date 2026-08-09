"""
ResQ-AI Admin Dashboard
=======================
Live vehicle tracking dashboard for the admin/control room.

Features:
  - See which vehicles are reporting live.
  - Track a selected vehicle's live location on a map (auto-refresh).
  - View the movement trail / history.
  - View live sensor metrics (speed, temp, heart, smoke).
  - View emergency alerts.
  - Email the current location to the admin's registered email.
  - Accept location requests by reading admin Gmail via the Gmail API (OAuth).
  - Generate AI location insights with Gemini.

The car dashboard pushes its live location to the ADMIN backend (port 5002),
and this dashboard reads it from there.

Run:  streamlit run Admin_Dashboard.py
"""
import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False

st.set_page_config(
    page_title='ResQ-AI Admin Dashboard',
    page_icon='🛰️',
    layout='wide',
    initial_sidebar_state='expanded',
)

ADMIN_BACKEND_URL = 'http://127.0.0.1:5002'
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

css = '''
<style>
body {
    background: #020617;
    color: #e2e8f0;
}
.admin-card {
    background: #0f172a;
    border-radius: 20px;
    padding: 18px;
    color: #e2e8f0;
}
.admin-card h3 {
    margin: 0 0 10px;
}
.hero {
    background: linear-gradient(90deg, #2563eb, #38bdf8);
    border-radius: 22px;
    padding: 24px;
    color: white;
    text-align: center;
}
</style>
'''
st.markdown(css, unsafe_allow_html=True)


def fetch_json(url, method='GET', **kwargs):
    try:
        if method == 'GET':
            r = requests.get(url, timeout=8)
        else:
            r = requests.post(url, json=kwargs.get('json'), timeout=8)
        return r.status_code, r.json()
    except Exception as e:
        return None, {'success': False, 'message': f'Cannot reach backend at {url}: {str(e)}'}


def get_vehicles():
    code, data = fetch_json(f'{ADMIN_BACKEND_URL}/vehicles')
    if data and data.get('success'):
        return data.get('vehicles', [])
    return []


def get_current_location(vehicle_number):
    code, data = fetch_json(f'{ADMIN_BACKEND_URL}/current-location?vehicle={requests.utils.quote(vehicle_number)}')
    if data and data.get('success'):
        return data.get('location'), data.get('driver_name'), data.get('last_update')
    return None, None, None


def get_history(vehicle_number):
    code, data = fetch_json(f'{ADMIN_BACKEND_URL}/location-history?vehicle={requests.utils.quote(vehicle_number)}')
    if data and data.get('success'):
        return data.get('history', [])
    return []


def get_alerts(vehicle_number=None):
    url = f'{ADMIN_BACKEND_URL}/emergency-alerts'
    if vehicle_number:
        url += f'?vehicle={requests.utils.quote(vehicle_number)}'
    code, data = fetch_json(url)
    if data and data.get('success'):
        return data.get('alerts', [])
    return []


def send_location_email(to_email, vehicle_number, driver_name, lat, lon):
    code, data = fetch_json(
        f'{ADMIN_BACKEND_URL}/send-location-request',
        method='POST',
        json={
            'to_email': to_email,
            'vehicle_number': vehicle_number,
            'driver_name': driver_name,
            'latitude': lat,
            'longitude': lon,
        },
    )
    if data:
        return data.get('success', False), data.get('message', 'Unknown response')
    return False, 'No response from backend.'


def get_gmail_location_requests(max_results=10):
    """
    Fetch the latest location-request emails from the admin's Gmail inbox via the
    Gmail API (OAuth). Returns (success, data_or_message).
    """
    code, data = fetch_json(
        f'{ADMIN_BACKEND_URL}/gmail-requests?max={max_results}'
    )
    if data and data.get('success'):
        return True, data.get('requests', [])
    return False, data.get('message', 'Unknown response') if data else 'No response from backend.'


def gemini_analyze_location(lat, lon, vehicle_number, driver_name, speed, temp, heart, smoke):
    """
    Uses the Gemini API to generate a human-readable insight/analysis of the
    vehicle's received location. Returns (success, message).
    """
    if not GEMINI_AVAILABLE:
        return False, 'The "google-generativeai" package is not installed. Run: pip install google-generativeai'
    if not GEMINI_API_KEY:
        return False, 'GEMINI_API_KEY is not set. Add it to ResQ-AI_Admin/.env'
    if GEMINI_API_KEY == 'YOUR_GEMINI_API_KEY_HERE':
        return False, 'GEMINI_API_KEY is still the placeholder. Set your real Gemini API key in ResQ-AI_Admin/.env'

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = (
            f"You are a vehicle fleet-safety analyst. The vehicle '{vehicle_number}' "
            f"(driver: {driver_name}) is currently located at latitude {lat}, longitude {lon}. "
            f"Live telemetry: speed={speed} km/h, engine temp={temp}°C, driver heart rate={heart} bpm, "
            f"smoke level={smoke}.\n\n"
            "Provide a concise 3-5 sentence location safety insight. Mention the general area type "
            "implied by the coordinates, any safety concerns implied by the telemetry, and a recommended "
            "action. Do not make up specific street names or landmarks you are not sure about."
        )
        response = model.generate_content(prompt)
        text = response.text.strip()
        return True, text
    except Exception as e:
        return False, f'Gemini API error: {str(e)}'


def main():
    st.markdown(
        "<div class='hero'><h1 style='margin:0;'>🛰️ ResQ-AI Admin Dashboard</h1>"
        "<p style='margin:8px 0 0; opacity:.9;'>Live vehicle tracking · Emergency monitoring · Location emailing</p></div>",
        unsafe_allow_html=True,
    )
    st.markdown('---')

    # ---- Sidebar ----
    with st.sidebar:
        st.header('Admin Panel')
        st.text_input('Admin Registered Email', key='admin_email',
                      placeholder='admin@example.com',
                      help='This is where location update emails will be sent.')
        st.markdown('---')

        vehicles = get_vehicles()
        if not vehicles:
            st.info('No vehicles reporting yet. Start the car dashboard so it can push its location here.')
            vehicle_number = None
        else:
            options = [v['vehicle_number'] for v in vehicles]
            labels = {v['vehicle_number']: f"{v['vehicle_number']} ({v['driver_name']})" for v in vehicles}
            display = [labels[v] for v in options]
            selected = st.selectbox('Select Vehicle', options, format_func=lambda v: labels[v])
            vehicle_number = selected

        st.markdown('---')
        st.checkbox('Auto Refresh', value=True, key='admin_auto_refresh')
        st.slider('Refresh Interval (seconds)', 1, 10, 2, key='admin_refresh_interval')
        st.markdown('---')
        if st.button('🗑️ Refresh Vehicle List'):
            st.rerun()

    if st.session_state.admin_auto_refresh:
        st.markdown(
            f"<script>setTimeout(function() {{ window.location.reload(); }}, {st.session_state.admin_refresh_interval * 1000});</script>",
            unsafe_allow_html=True,
        )

    # ---- Main content ----
    if not vehicle_number:
        st.info('👈 Select a vehicle from the sidebar to begin tracking. Start the car dashboard first.')
        return

    location, driver_name, last_update = get_current_location(vehicle_number)

    # Status card
    live_status = 'LIVE' if location else 'NO DATA'
    color = '#22c55e' if location else '#ef4444'
    st.markdown(
        f"<div class='admin-card'><h3>🚗 {vehicle_number}</h3>"
        f"<strong>Driver:</strong> {driver_name or 'N/A'} &nbsp;|&nbsp; "
        f"<strong>Last update:</strong> {last_update or 'Never'} &nbsp;|&nbsp; "
        f"<span style='color:{color}; font-weight:700;'>● {live_status}</span></div>",
        unsafe_allow_html=True,
    )

    if not location:
        st.warning('No live location received yet. Ensure the car dashboard is running and monitoring.')
        return

    lat, lon = location['lat'], location['lon']
    speed = location.get('speed', 0)
    temp = location.get('temp', 0)
    heart = location.get('heart', 0)
    smoke = location.get('smoke', 0)
    impact = location.get('impact', False)

    # ---- Live metrics ----
    metric_cols = st.columns(4)
    metric_cols[0].metric('Speed', f'{speed} km/h')
    metric_cols[1].metric('Engine Temp', f'{temp} °C')
    metric_cols[2].metric('Heart Rate', f'{heart} bpm')
    metric_cols[3].metric('Smoke Level', smoke)

    left, right = st.columns([3, 2])
    with left:
        st.subheader('📍 Live Location')
        st.markdown(
            f"<iframe src='https://maps.google.com/maps?q={lat},{lon}&z=18&output=embed' "
            f"width='100%' height='380' style='border:0; border-radius:14px;' allowfullscreen='' loading='lazy'></iframe>",
            unsafe_allow_html=True,
        )
        st.write(f'**Coordinates:** {lat:.6f}, {lon:.6f}')

        st.markdown('---')
        st.subheader('🤖 Gemini AI Location Insight')
        gemini_status = 'API Ready' if (GEMINI_AVAILABLE and GEMINI_API_KEY and GEMINI_API_KEY != 'YOUR_GEMINI_API_KEY_HERE') else 'Not configured'
        st.caption(f'Gemini status: {gemini_status}')
        if st.button('🧠 Generate AI Location Insight', key='gemini_analyze'):
            with st.spinner('Asking Gemini to analyze this location...'):
                ok, msg = gemini_analyze_location(
                    lat, lon, vehicle_number, driver_name or 'Unknown', speed, temp, heart, smoke
                )
            if ok:
                st.success('✅ Gemini analysis:')
                st.write(msg)
            else:
                st.error(f'❌ {msg}')

        history = get_history(vehicle_number)
        if history:
            st.subheader('🛣️ Movement Trail')
            trail_df = pd.DataFrame(history)
            st.map(trail_df[['lat', 'lon']])
        else:
            st.info('No movement history yet.')

    with right:
        st.subheader('Vehicle Status')
        if impact:
            st.error('🚨 Impact detected!')
        elif speed > 80:
            st.warning('⚠️ High speed detected.')
        else:
            st.success('✅ Vehicle operating normally.')

        st.markdown('---')
        st.subheader('📤 Email Location to Admin')
        if st.session_state.admin_email:
            if st.button('📩 Send Current Location', key='admin_send_email'):
                ok, msg = send_location_email(
                    st.session_state.admin_email, vehicle_number, driver_name or 'Unknown', lat, lon
                )
                if ok:
                    st.success(f'✅ {msg}')
                else:
                    st.error(f'❌ {msg}')
        else:
            st.info('Enter your admin email in the sidebar to enable location emails.')

        st.markdown('---')
        st.subheader('📥 Accept Location Requests (Gmail API)')
        st.caption('Reads "Live Location Request" emails from the admin Gmail inbox and lets you accept the tracking request.')
        if st.button('📥 Check Gmail for Location Requests', key='check_gmail_requests'):
            with st.spinner('Reading admin Gmail inbox via Gmail API...'):
                ok, result = get_gmail_location_requests(max_results=10)
            if not ok:
                st.error(f'❌ {result}')
            else:
                if not result:
                    st.info('No location request emails found in the inbox yet.')
                else:
                    st.success(f'✅ Found {len(result)} location request email(s).')
                    for req in result:
                        with st.expander(f"📧 {req['subject']} — {req['date']}"):
                            st.write(f"**From:** {req['from']}")
                            st.write(f"**Vehicle:** {req['vehicle_number']}")
                            if req['latitude'] and req['longitude']:
                                st.write(f"**Coordinates:** {req['latitude']}, {req['longitude']}")
                                st.markdown(
                                    f"<iframe src='https://maps.google.com/maps?q={req['latitude']},{req['longitude']}&z=18&output=embed' "
                                    f"width='100%' height='250' style='border:0; border-radius:12px;' allowfullscreen='' loading='lazy'></iframe>",
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.write('**Coordinates:** not embedded in the email body.')
                            st.write(f"**Preview:** {req['message_preview']}")
                            if st.button('✅ Accept & Track This Request', key=f"accept_{req['id']}"):
                                st.session_state.accepted_request = req
                                st.success(f'Accepted tracking request for {req["vehicle_number"]}. Switch to a vehicle in the sidebar to view its live location.')

        st.markdown('---')
        st.subheader('🚨 Emergency Alerts')
        alerts = get_alerts(vehicle_number)
        if alerts:
            for alert in alerts[:5]:
                st.error(f"**{alert['timestamp']} — {alert['crash_type']}**")
                st.write(f"Location: {alert['gps'][0]:.6f}, {alert['gps'][1]:.6f}")
                st.write(f"Speed: {alert['speed']} km/h | Temp: {alert['temp']} °C | Heart: {alert['heart']} bpm | Smoke: {alert['smoke']}")
        else:
            st.info('No emergency alerts.')


if __name__ == '__main__':
    main()
