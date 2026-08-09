"""
ResQ-AI 2.0 - Machine Learning Enhanced Version
Smart Accident & Health Detection System with ML Predictions
Alerts ONLY when vehicle crashes AND person is in danger
"""

import streamlit as st
from streamlit_javascript import st_javascript
import random
import time
from datetime import datetime
import requests
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title='ResQ-AI Car Dashboard',
    page_icon='🚘',
    layout='wide',
    initial_sidebar_state='expanded'
)

css = '''
<style>
body {
    background: #020617;
    color: #e2e8f0;
}
.dashboard-card {
    background: #0f172a;
    border-radius: 20px;
    padding: 18px;
    color: #e2e8f0;
}
.dashboard-card h3 {
    margin: 0 0 10px;
}
.speed-box {
    background: linear-gradient(90deg, #2563eb, #38bdf8);
    border-radius: 22px;
    padding: 20px;
    color: white;
    text-align: center;
}
.speed-meter {
    margin-top: 18px;
    background: #111827;
    padding: 18px;
    border-radius: 18px;
}
.speed-meter-bar {
    background: #1f2937;
    border-radius: 999px;
    height: 18px;
    overflow: hidden;
}
.speed-meter-fill {
    height: 100%;
    border-radius: 999px;
}
</style>
'''

st.markdown(css, unsafe_allow_html=True)

class AccidentPredictor:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.train_initial_model()

    def train_initial_model(self):
        np.random.seed(42)
        n_samples = 1000
        normal_speed = np.random.normal(60, 20, n_samples // 2)
        normal_temp = np.random.normal(75, 10, n_samples // 2)
        normal_heart = np.random.normal(80, 10, n_samples // 2)
        normal_smoke = np.random.normal(200, 50, n_samples // 2)
        normal_impact = np.zeros(n_samples // 2)
        normal_labels = np.zeros(n_samples // 2)

        accident_speed = np.random.normal(90, 15, n_samples // 2)
        accident_temp = np.random.normal(85, 15, n_samples // 2)
        accident_heart = np.random.normal(130, 20, n_samples // 2)
        accident_smoke = np.random.normal(400, 100, n_samples // 2)
        accident_impact = np.random.binomial(1, 0.7, n_samples // 2)
        accident_labels = np.ones(n_samples // 2)

        X = np.column_stack([
            np.concatenate([normal_speed, accident_speed]),
            np.concatenate([normal_temp, accident_temp]),
            np.concatenate([normal_heart, accident_heart]),
            np.concatenate([normal_smoke, accident_smoke]),
            np.concatenate([normal_impact, accident_impact]),
        ])
        y = np.concatenate([normal_labels, accident_labels])

        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_trained = True

    def predict_accident_probability(self, speed, temp, heart, smoke, impact):
        if not self.is_trained:
            return 0.0
        features = np.array([[speed, temp, heart, smoke, int(impact)]])
        features_scaled = self.scaler.transform(features)
        return self.model.predict_proba(features_scaled)[0][1]

class AnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.history = []

    def update_and_predict(self, speed, temp, heart, smoke):
        self.history.append([speed, temp, heart, smoke])
        if len(self.history) > 100:
            self.history.pop(0)
        if len(self.history) >= 20 and not self.is_trained:
            X = np.array(self.history)
            X_scaled = self.scaler.fit_transform(X)
            self.model.fit(X_scaled)
            self.is_trained = True
        if self.is_trained:
            current = np.array([[speed, temp, heart, smoke]])
            current_scaled = self.scaler.transform(current)
            prediction = self.model.predict(current_scaled)[0]
            score = self.model.score_samples(current_scaled)[0]
            return prediction == -1, score
        return False, 0.0

class HealthPredictor:
    def __init__(self):
        self.heart_history = []
        self.window_size = 10

    def add_reading(self, heart_rate):
        self.heart_history.append(heart_rate)
        if len(self.heart_history) > self.window_size:
            self.heart_history.pop(0)

    def detect_trend(self):
        if len(self.heart_history) < 5:
            return 'INSUFFICIENT_DATA', 0
        recent = self.heart_history[-5:]
        x = np.arange(len(recent))
        z = np.polyfit(x, recent, 1)
        slope = z[0]
        if slope > 5:
            return 'RAPID_INCREASE', slope
        if slope < -5:
            return 'RAPID_DECREASE', slope
        std = np.std(recent)
        if std > 15:
            return 'HIGH_VARIABILITY', std
        return 'STABLE', slope


def get_speed():
    return random.randint(0, 120)


def get_impact():
    return random.random() < 0.08


def get_engine_temp():
    base = 70 + random.uniform(-5, 5)
    if random.random() < 0.05:
        base += random.uniform(25, 50)
    return round(base, 2)


def get_heart_rate():
    base = 80 + random.uniform(-15, 15)
    if random.random() < 0.05:
        base += random.uniform(40, 70)
    return round(base, 1)


def get_smoke_level():
    base = random.randint(50, 300)
    if random.random() < 0.03:
        base += random.randint(400, 700)
    return min(base, 1000)


def get_gps():
    lat = 15.0000 + random.uniform(-0.05, 0.05)
    lon = 75.0000 + random.uniform(-0.05, 0.05)
    return (round(lat, 5), round(lon, 5))


def init_state():
    defaults = {
        'monitoring': False,
        'auto_refresh': True,
        'refresh_interval': 2,
        'sensor_data': [],
        'location_history': [],
        'emergency_alerts': [],
        'vehicle_number': 'KA-01-AB-1234',
        'driver_name': ' ',
        'driver_phone': '+919876543210',
        'registered_email': '  ',
        'emergency_contact1': '+919876543211',
        'emergency_contact2': '+919876543212',
        'latest_gps': None,
        'browser_location': None,
        'browser_location_accuracy': None,
        'browser_location_timestamp': None,
        'browser_location_history': [],
        'browser_tracking': False,
        'browser_permission_requested': False,
        'location_request_sent': False,
        'accident_predictor': None,
        'anomaly_detector': None,
        'health_predictor': None,
        'test_emergency': False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    if 'accident_predictor' not in st.session_state or st.session_state.accident_predictor is None:
        st.session_state.accident_predictor = AccidentPredictor()
    if 'anomaly_detector' not in st.session_state or st.session_state.anomaly_detector is None:
        st.session_state.anomaly_detector = AnomalyDetector()
    if 'health_predictor' not in st.session_state or st.session_state.health_predictor is None:
        st.session_state.health_predictor = HealthPredictor()


def is_critical_emergency(speed, impact, temp, heart, smoke, thresholds):
    crash_detected = False
    crash_type = ''
    if speed > thresholds['accident_speed'] and impact:
        crash_detected = True
        crash_type = 'HIGH-SPEED COLLISION'
    elif thresholds['accident_speed_moderate'] < speed <= thresholds['accident_speed'] and impact:
        crash_detected = True
        crash_type = 'MODERATE COLLISION'
    person_in_danger = False
    danger_reasons = []
    if heart < thresholds['heart_min_critical']:
        person_in_danger = True
        danger_reasons.append(f'Critical Low Heart Rate ({heart} bpm)')
    if heart > thresholds['heart_max_critical']:
        person_in_danger = True
        danger_reasons.append(f'Critical High Heart Rate ({heart} bpm)')
    if smoke > thresholds['smoke_critical']:
        person_in_danger = True
        danger_reasons.append(f'Fire/Heavy Smoke ({smoke})')
    if temp > thresholds['temp_critical']:
        person_in_danger = True
        danger_reasons.append(f'Engine Fire Risk ({temp}°C)')
    if crash_detected and person_in_danger:
        return True, crash_type, danger_reasons
    return False, '', []


def get_monitoring_warnings(temp, heart, smoke, thresholds):
    warnings_list = []
    if thresholds['temp_warning'] < temp <= thresholds['temp_critical']:
        warnings_list.append(f'⚠️ Engine temperature elevated: {temp}°C')
    if thresholds['heart_min_warning'] <= heart < thresholds['heart_min_critical']:
        warnings_list.append(f'⚠️ Heart rate low: {heart} bpm')
    if thresholds['heart_max_warning'] < heart <= thresholds['heart_max_critical']:
        warnings_list.append(f'⚠️ Heart rate elevated: {heart} bpm')
    if thresholds['smoke_warning'] < smoke <= thresholds['smoke_critical']:
        warnings_list.append(f'⚠️ Smoke detected: {smoke}')
    return warnings_list


def get_ml_insights(speed, temp, heart, smoke, impact):
    insights = []
    accident_prob = st.session_state.accident_predictor.predict_accident_probability(
        speed, temp, heart, smoke, impact
    )
    if accident_prob > 0.75:
        insights.append(f'🤖 High accident risk: {accident_prob:.1%}')
    elif accident_prob > 0.5:
        insights.append(f'🤖 Elevated accident risk: {accident_prob:.1%}')
    is_anomaly, anomaly_score = st.session_state.anomaly_detector.update_and_predict(
        speed, temp, heart, smoke
    )
    if is_anomaly:
        insights.append(f'🤖 Anomaly detected (score: {anomaly_score:.3f})')
    st.session_state.health_predictor.add_reading(heart)
    trend, value = st.session_state.health_predictor.detect_trend()
    if trend == 'RAPID_INCREASE':
        insights.append(f'🤖 Heart rate rising rapidly (+{value:.1f} bpm/step)')
    elif trend == 'RAPID_DECREASE':
        insights.append(f'🤖 Heart rate dropping rapidly ({value:.1f} bpm/step)')
    elif trend == 'HIGH_VARIABILITY':
        insights.append(f'🤖 High heart variability ({value:.1f} bpm)')
    return insights, accident_prob, is_anomaly


def trigger_emergency_alert(crash_type, danger_reasons, gps, speed, temp, heart, smoke):
    st.session_state.emergency_alerts.insert(0, {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'crash_type': crash_type,
        'danger_reasons': danger_reasons,
        'gps': gps,
        'speed': speed,
        'temp': temp,
        'heart': heart,
        'smoke': smoke,
    })


BACKEND_URL = 'http://127.0.0.1:5001'
ADMIN_BACKEND_URL = 'http://127.0.0.1:5002'


def send_location_request_to_backend(email, gps, vehicle_number, driver_name):
    """
    Calls the Gmail-SMTP-backed Flask backend to email the live location request.
    Returns (success: bool, message: str).
    """
    try:
        response = requests.post(
            f'{BACKEND_URL}/send-location-request',
            json={
                'to_email': email,
                'latitude': gps[0],
                'longitude': gps[1],
                'vehicle_number': vehicle_number,
                'driver_name': driver_name,
            },
            timeout=20,
        )
        data = response.json()
        return data.get('success', False), data.get('message', 'Unknown response')
    except Exception as e:
        return False, f'Could not reach the backend. Is backend.py running? ({e})'


def push_location_to_admin(gps, speed, temp, heart, smoke, impact,
                           vehicle_number, driver_name, is_emergency=False,
                           crash_type='', danger_reasons=None):
    """
    Pushes the car's live location to the ADMIN backend so the admin
    dashboard can track it in real time.
    Returns (success: bool, message: str).
    """
    try:
        response = requests.post(
            f'{ADMIN_BACKEND_URL}/update-location',
            json={
                'vehicle_number': vehicle_number,
                'driver_name': driver_name,
                'latitude': gps[0],
                'longitude': gps[1],
                'speed': speed,
                'temp': temp,
                'heart': heart,
                'smoke': smoke,
                'impact': impact,
                'is_emergency': is_emergency,
                'crash_type': crash_type,
                'danger_reasons': danger_reasons or [],
            },
            timeout=10,
        )
        data = response.json()
        return data.get('success', False), data.get('message', 'Unknown response')
    except Exception as e:
        return False, f'Could not reach admin backend at {ADMIN_BACKEND_URL}. Is it running? ({e})'


def render_speedometer(speed):
    fill = min(max(speed, 0), 140) / 140 * 100
    color = '#22c55e' if speed < 80 else '#facc15' if speed < 110 else '#ef4444'
    return f"""
    <div class='speed-box'>
        <div style='font-size:16px; opacity:0.8;'>Live Speed</div>
        <div style='font-size:56px; font-weight:700; margin-top:8px;'>{speed} km/h</div>
        <div class='speed-meter'>
            <div class='speed-meter-bar'><div class='speed-meter-fill' style='width:{fill}%; background:{color};'></div></div>
            <div style='font-size:13px; color:#cbd5e1; margin-top:10px;'>Dashboard-style live speed gauge</div>
        </div>
    </div>
    """


def get_auto_refresh_script(interval):
    return f"<script>setTimeout(function() {{ window.location.reload(); }}, {interval * 1000});</script>"


def render_google_map_embed(lat, lon):
    src = f'https://maps.google.com/maps?q={lat},{lon}&z=18&output=embed'
    return (
        f"<iframe src='{src}' width='100%' height='320' style='border:0;' allowfullscreen='' loading='lazy'></iframe>"
    )


def render_browser_geolocation_component():
    js = """
        const getGeo = () => {
            return new Promise((resolve) => {
                if (!navigator.geolocation) {
                    resolve({ error: 'Geolocation is not supported in this browser.' });
                    return;
                }
                navigator.geolocation.getCurrentPosition(
                    (pos) => {
                        resolve({
                            lat: pos.coords.latitude,
                            lon: pos.coords.longitude,
                            accuracy: pos.coords.accuracy,
                            timestamp: pos.timestamp
                        });
                    },
                    (err) => {
                        resolve({ error: err.message || 'Unable to get location' });
                    },
                    {
                        enableHighAccuracy: true,
                        maximumAge: 1000,
                        timeout: 15000
                    }
                );
            });
        };
        return getGeo();
    """
    return st_javascript(js_code=js, key='browser_geolocation')


def main():
    init_state()
    st.title('🚘 ResQ-AI Car Dashboard')
    st.markdown('### Real-time vehicle monitoring with speed, engine, driver health, and emergency alerts')
    st.markdown('---')

    with st.sidebar:
        st.header('Control Panel')
        st.text_input('Vehicle Number', value=st.session_state.vehicle_number, key='vehicle_number')
        st.text_input('Driver Name', value=st.session_state.driver_name, key='driver_name')
        st.text_input('Driver Phone', value=st.session_state.driver_phone, key='driver_phone')
        st.text_input('Registered Email', value=st.session_state.registered_email, key='registered_email')
        st.markdown('---')
        if st.button('🟢 Start Monitoring' if not st.session_state.monitoring else '🔴 Stop Monitoring'):
            st.session_state.monitoring = not st.session_state.monitoring
        st.checkbox('Auto Refresh', value=st.session_state.auto_refresh, key='auto_refresh')
        st.slider('Refresh Interval (seconds)', 1, 10, st.session_state.refresh_interval, key='refresh_interval')
        st.markdown('---')
        st.subheader('Emergency Contacts')
        st.text_input('Contact 1', value=st.session_state.emergency_contact1, key='emergency_contact1')
        st.text_input('Contact 2', value=st.session_state.emergency_contact2, key='emergency_contact2')
        st.markdown('---')
        st.subheader('Alert Thresholds')
        accident_speed = st.slider('Crash Speed Threshold', 30, 100, 50, 5)
        accident_speed_moderate = st.slider('Moderate Crash Speed', 20, 50, 30, 5)
        heart_min_critical = st.slider('Critical Low HR', 30, 50, 40, 5)
        heart_max_critical = st.slider('Critical High HR', 120, 170, 145, 5)
        temp_warning = st.slider('Temp Warning (°C)', 80, 110, 90, 5)
        temp_critical = st.slider('Temp Critical (°C)', 95, 140, 110, 5)
        smoke_warning = st.slider('Smoke Warning', 300, 700, 500, 50)
        smoke_critical = st.slider('Smoke Critical', 500, 1000, 750, 50)
        thresholds = {
            'accident_speed': accident_speed,
            'accident_speed_moderate': accident_speed_moderate,
            'heart_min_critical': heart_min_critical,
            'heart_max_critical': heart_max_critical,
            'heart_min_warning': heart_min_critical + 10,
            'heart_max_warning': heart_max_critical - 20,
            'temp_warning': temp_warning,
            'temp_critical': temp_critical,
            'smoke_warning': smoke_warning,
            'smoke_critical': smoke_critical,
        }
        st.markdown('---')
        if st.button('⚠️ Simulate Crash + Emergency'):
            st.session_state.test_emergency = True
        if st.button('🧹 Reset History'):
            st.session_state.sensor_data = []
            st.session_state.emergency_alerts = []
            st.success('History reset.')

    st.markdown(
        f"<div class='dashboard-card'><h3>Vehicle</h3>"
        f"<strong>{st.session_state.vehicle_number}</strong> | "
        f"Driver: <strong>{st.session_state.driver_name}</strong> | "
        f"Status: <strong>{'Monitoring' if st.session_state.monitoring else 'Stopped'}</strong></div>",
        unsafe_allow_html=True,
    )

    if st.session_state.monitoring and st.session_state.auto_refresh:
        st.markdown(get_auto_refresh_script(st.session_state.refresh_interval), unsafe_allow_html=True)

    if st.session_state.monitoring or st.session_state.test_emergency:
        previous_speed = st.session_state.sensor_data[-1]['speed'] if st.session_state.sensor_data else None
        if st.session_state.test_emergency:
            speed = thresholds['accident_speed'] + 15
            impact = True
            temp = thresholds['temp_critical'] + 12
            heart = thresholds['heart_max_critical'] + 15
            smoke = thresholds['smoke_critical'] + 120
            st.session_state.test_emergency = False
        else:
            speed = get_speed()
            impact = get_impact()
            temp = get_engine_temp()
            heart = get_heart_rate()
            smoke = get_smoke_level()
        gps = get_gps()

        st.session_state.sensor_data.append({
            'time': datetime.now().strftime('%H:%M:%S'),
            'speed': speed,
            'temp': temp,
            'heart': heart,
            'smoke': smoke,
            'impact': impact,
        })
        st.session_state.latest_gps = gps
        st.session_state.location_history.append({
            'latitude': gps[0],
            'longitude': gps[1],
            'time': datetime.now().strftime('%H:%M:%S')
        })
        st.session_state.location_history = st.session_state.location_history[-50:]
        st.session_state.sensor_data = st.session_state.sensor_data[-50:]

        insights, accident_prob, is_anomaly = get_ml_insights(
            speed, temp, heart, smoke, impact
        )

        is_emergency, crash_type, danger_reasons = is_critical_emergency(
            speed, impact, temp, heart, smoke, thresholds
        )
        if is_emergency:
            trigger_emergency_alert(crash_type, danger_reasons, gps, speed, temp, heart, smoke)

        # Push live location to the admin backend for real-time tracking.
        push_location_to_admin(
            gps, speed, temp, heart, smoke, impact,
            st.session_state.vehicle_number,
            st.session_state.driver_name,
            is_emergency=is_emergency,
            crash_type=crash_type,
            danger_reasons=danger_reasons,
        )

        speed_delta = ''
        if previous_speed is not None:
            speed_delta = f'{speed - previous_speed:+d} km/h'

        left, right = st.columns([3, 2])
        with left:
            st.markdown(render_speedometer(speed), unsafe_allow_html=True)
            metric_cols = st.columns(4)
            metric_cols[0].metric('Speed', f'{speed} km/h', speed_delta)
            metric_cols[1].metric('Engine Temp', f'{temp} °C')
            metric_cols[2].metric('Heart Rate', f'{heart} bpm')
            metric_cols[3].metric('Smoke Level', smoke)

        with right:
            st.subheader('System Status')
            if is_emergency:
                st.error(f'🚨 EMERGENCY: {crash_type}')
                st.write('**Danger:** ' + ' | '.join(danger_reasons))
                st.write(f'**Location:** {gps[0]}, {gps[1]}')
            else:
                st.success('✅ Monitoring active. No crash + critical danger detected.')
            st.markdown('---')
            st.write(f'**Accident risk:** {accident_prob:.1%}')
            if is_anomaly:
                st.warning('⚠️ Environmental anomaly detected')
            for insight in insights:
                st.info(insight)

        st.subheader('Live Sensor Trends')
        chart_df = pd.DataFrame(st.session_state.sensor_data).set_index('time')
        st.line_chart(chart_df[['speed', 'temp', 'heart', 'smoke']])

        warnings = get_monitoring_warnings(temp, heart, smoke, thresholds)
        if warnings:
            st.subheader('Warnings')
            for warning in warnings:
                st.warning(warning)

        tracked_gps = st.session_state.browser_location or gps
        st.subheader('📍 Current Location')
        st.write(f"Latitude: {tracked_gps[0]:.6f}, Longitude: {tracked_gps[1]:.6f}")
        if st.session_state.browser_location_accuracy is not None:
            st.write(f"GPS accuracy: ±{st.session_state.browser_location_accuracy:.1f} meters")
        if st.session_state.browser_location_timestamp is not None:
            st.write(
                f"Last fix: {datetime.fromtimestamp(st.session_state.browser_location_timestamp / 1000).strftime('%H:%M:%S')}"
            )

        if st.session_state.registered_email:
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button('📍 Request Live Location Access', key='request_browser_location'):
                    st.session_state.browser_tracking = True
                    st.session_state.browser_permission_requested = True
                    st.session_state.location_request_sent = False
            with col2:
                if st.button('📩 Send Location Request', key='send_location_request'):
                    st.session_state.location_request_sent = True
                    if not st.session_state.browser_location:
                        st.session_state.browser_tracking = True
                        st.session_state.browser_permission_requested = True
                        st.warning('Requesting browser location permission so tracking can start.')

            if st.session_state.browser_tracking:
                browser_data = render_browser_geolocation_component()
                if isinstance(browser_data, dict):
                    if browser_data.get('error'):
                        st.warning(f"Browser location error: {browser_data['error']}")
                    elif 'lat' in browser_data and 'lon' in browser_data:
                        st.session_state.browser_location = (
                            float(browser_data['lat']), float(browser_data['lon'])
                        )
                        st.session_state.browser_location_accuracy = float(browser_data.get('accuracy', 0))
                        st.session_state.browser_location_timestamp = float(browser_data.get('timestamp', time.time() * 1000))
                        st.session_state.browser_location_history.append({
                            'latitude': float(browser_data['lat']),
                            'longitude': float(browser_data['lon']),
                            'time': datetime.now().strftime('%H:%M:%S')
                        })
                        st.session_state.browser_location_history = st.session_state.browser_location_history[-50:]
                        st.success('✅ Browser location tracking active.')

            if st.session_state.browser_location:
                st.markdown(render_google_map_embed(*st.session_state.browser_location), unsafe_allow_html=True)
                st.success('🟢 Tracking status: Active')
            elif st.session_state.browser_permission_requested:
                st.info('Waiting for browser location permission or GPS fix...')
            else:
                st.info('Click Request Live Location Access to allow this browser to share GPS coordinates.')

            if st.session_state.browser_location_history:
                location_df = pd.DataFrame(st.session_state.browser_location_history)
                st.map(location_df)
            elif st.session_state.location_history:
                location_df = pd.DataFrame(st.session_state.location_history)
                st.map(location_df)

            if st.session_state.location_request_sent:
                success, message = send_location_request_to_backend(
                    st.session_state.registered_email,
                    tracked_gps,
                    st.session_state.vehicle_number,
                    st.session_state.driver_name,
                )
                if success:
                    st.success(f'✅ Location request sent! {message}')
                else:
                    st.error(f'❌ {message}')
        else:
            st.info('Enter a registered email to enable precise location tracking and request support.')
    else:
        st.info('Monitoring is stopped. Press Start Monitoring to begin live tracking.')

    st.markdown('---')
    st.subheader('Recent Emergency Alerts')
    if st.session_state.emergency_alerts:
        for alert in st.session_state.emergency_alerts[:5]:
            st.error(f"**{alert['timestamp']} — {alert['crash_type']}**")
            st.write(f"Location: {alert['gps'][0]:.6f}, {alert['gps'][1]:.6f}")
            st.write(f"Speed: {alert['speed']} km/h | Temp: {alert['temp']} °C | Heart: {alert['heart']} bpm | Smoke: {alert['smoke']}")
    else:
        st.info('No emergency alerts yet.')

if __name__ == '__main__':
    main()
