# app.py
# 🚍 SMART TRANSPORT SYSTEM (Govt Bus Mode: NO Ticket Booking / NO Pre-booking)
# ✅ Stop-first UX (Find My Bus shows ETA + Live map together)
# ✅ Public + Conductor + Municipality portals
# ✅ Municipality has Live Map page too
# ✅ Complaints + Pass QR deep link (no ticket booking)
# ✅ Multilingual UI (Robust: fallback-to-English so every language "works")
# ✅ Better Orange/Amber UI palette
# ✅ Home button (back to Role Selection) added on all portals

import streamlit as st
import streamlit.components.v1 as components

import pandas as pd
from datetime import datetime, timedelta
import random
import math
import uuid
import json
import io
import socket
import sqlite3
from urllib.parse import urlencode

import qrcode
import folium
from folium.plugins import MarkerCluster


# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Smart Transport System — Govt Bus",
    layout="wide",
    page_icon="🚍",
)

# -----------------------------
# ORANGE/AMBER THEME (Clean)
# -----------------------------
THEME_CSS = """
<style>
:root{
  --bg1:#fff7ed;   /* orange-50 */
  --bg2:#fffbeb;   /* amber-50 */
  --accent:#f97316; /* orange-500 */
  --accent2:#fb923c; /* orange-400 */
  --accentDark:#9a3412; /* orange-800 */
  --ink:#0f172a;   /* slate-900 */
  --muted:#475569; /* slate-600 */
  --card:#ffffff;
  --border:#fed7aa; /* orange-200 */
  --shadow: 0 10px 22px rgba(0,0,0,0.08);
}

/* Background */
.stApp{
  background: linear-gradient(180deg, var(--bg1), #ffffff 60%);
}

/* Titles */
.main-header{
  font-size: 2.8rem;
  font-weight: 900;
  text-align:center;
  margin: 0.4rem 0 1.2rem 0;
  letter-spacing: -0.6px;
  color: var(--accentDark);
}
.sub-header{
  font-size: 1.2rem;
  font-weight: 900;
  margin: 0.6rem 0 0.4rem 0;
  color: var(--ink);
}
.mini{ font-size: 0.95rem; color: var(--muted); }

/* Cards */
.card{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 1.0rem;
  box-shadow: var(--shadow);
  margin: 0.6rem 0;
}

/* Divider */
.hr{
  border-top: 1px solid rgba(0,0,0,0.08);
  margin: 0.9rem 0;
}

/* Pills */
.pill{
  display:inline-block;
  padding: 0.25rem 0.65rem;
  border-radius: 999px;
  font-weight: 900;
  font-size: 0.85rem;
  border: 1px solid var(--border);
  background: #fff;
  color: var(--muted);
}
.pill-ok{ background:#ecfdf5; border-color:#bbf7d0; color:#065f46; }
.pill-warn{ background:#fffbeb; border-color:#fde68a; color:#92400e; }
.pill-bad{ background:#fef2f2; border-color:#fecaca; color:#991b1b; }

/* KPI */
.kpi{
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  color: white;
  border-radius: 18px;
  padding: 1.0rem;
  box-shadow: var(--shadow);
  border: 1px solid rgba(255,255,255,0.25);
}
.kpi h2{ margin:0; font-size: 2.0rem; }
.kpi p{ margin:0.2rem 0 0; opacity:0.95; font-weight:800; }

/* Buttons */
div.stButton > button[kind="primary"]{
  background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
  color: white !important;
  border: 0 !important;
  border-radius: 14px !important;
  font-weight: 900 !important;
}
div.stButton > button{
  border-radius: 14px !important;
  font-weight: 800 !important;
}
</style>
"""
st.markdown(THEME_CSS, unsafe_allow_html=True)


# -----------------------------
# MULTILINGUAL (ROBUST)
# -----------------------------
LANGS = [
    ("en", "English"),
    ("hi", "हिंदी"),
    ("ta", "தமிழ்"),
    ("te", "తెలుగు"),
    ("ml", "മലയാളം"),
    ("kn", "ಕನ್ನಡ"),
    ("bn", "বাংলা"),
    ("ur", "اردو"),
    ("mr", "मराठी"),
    ("gu", "ગુજરાતી"),
    ("pa", "ਪੰਜਾਬੀ"),
]

T = {
    "en": {
        "language": "Language",
        "home": "Home",
        "back": "Back",
        "app_title": "Smart Transport System",
        "govt_mode": "Govt bus version: No ticket booking. Focus on Next Bus ETA, Live Tracking, Passes, and Complaints.",
        "enter_name": "Enter your name",
        "name_ph": "e.g., Mithun",
        "welcome": "Welcome",
        "phone": "Phone",
        "role": "Role",

        "public_user": "Public User",
        "conductor_driver": "Conductor/Driver",
        "municipality_admin": "Municipality Admin",

        "public_portal": "Public Portal",
        "find_my_bus": "Find My Bus (ETA + Live Map)",
        "my_pass": "My Pass",
        "complaints": "Complaints / Grievances",

        "select_stop": "Select your current stop",
        "next_buses": "Next Buses Arriving (ETA)",
        "no_running_buses": "No running buses found.",
        "live_map": "Live Tracking Map",
        "refresh": "Refresh",
        "last_refreshed": "Last refreshed",

        "route": "Route",
        "type": "Type",
        "crowd": "Crowd",
        "status": "Status",
        "arrives": "Arrives ~",

        "total_buses": "Total Buses",
        "running": "Running",
        "delayed": "Delayed",
        "breakdowns": "Breakdowns",
        "onboard": "On-board (approx.)",

        "submit_complaint": "Submit a complaint",
        "bus_optional": "Bus (optional)",
        "route_optional": "Route (optional)",
        "category": "Category",
        "describe_issue": "Describe the issue",
        "desc_ph": "Write clearly with time/place details...",
        "submit": "Submit Complaint",
        "desc_required": "Please enter the description.",
        "complaint_submitted": "Complaint submitted. Ticket ID:",
        "my_recent": "My recent complaints (by phone)",
        "no_complaints": "No complaints yet.",

        "pass_preview": "Pass Preview",
        "no_pass": "No pass found.",
        "open_mobile": "Open the pass on mobile using QR deep link.",
        "scan_mobile": "Scan to open pass on mobile",

        "conductor_portal": "Conductor / Driver Portal",
        "select_bus": "Select your bus",
        "update_live": "Update live status",
        "passengers": "Passengers (approx.)",
        "gps_tip": "If you have GPS, enter exact values below.",
        "push_update": "Push Update",
        "updated_live": "Updated live state.",

        "verify_pass": "Verify Pass (Open Link)",
        "verify_pass_title": "Verify Pass",
        "verify": "Verify",
        "pass_not_found": "Pass not found.",
        "pass_valid": "Pass valid (demo).",

        "admin_title": "Municipality Admin",
        "admin_live_map": "Live Map",
        "admin_live_map_title": "Municipality Live Map (Fleet Monitoring)",
        "fleet_table": "Fleet Table",
        "complaints_mgmt": "Complaints",
        "disruption_monitor": "Disruption Monitor",

        "app_crashed": "App crashed. Full error below:",
        "note_no_booking": "Note: Ticket booking does not exist in this system."
    },

    "hi": {
        "language": "भाषा",
        "home": "होम",
        "back": "वापस",
        "app_title": "स्मार्ट परिवहन प्रणाली",
        "govt_mode": "सरकारी बस संस्करण: टिकट बुकिंग नहीं। अगली बस ETA, लाइव ट्रैकिंग, पास और शिकायतों पर फोकस।",
        "enter_name": "अपना नाम दर्ज करें",
        "name_ph": "उदा., मिथुन",
        "welcome": "स्वागत है",
        "phone": "फोन",
        "role": "भूमिका",
        "public_user": "सार्वजनिक उपयोगकर्ता",
        "conductor_driver": "कंडक्टर/ड्राइवर",
        "municipality_admin": "नगरपालिका प्रशासन",
        "public_portal": "सार्वजनिक पोर्टल",
        "find_my_bus": "मेरी बस खोजें (ETA + लाइव मैप)",
        "my_pass": "मेरा पास",
        "complaints": "शिकायतें / शिकायत निवारण",
        "select_stop": "अपना वर्तमान स्टॉप चुनें",
        "next_buses": "अगली बसें (ETA)",
        "no_running_buses": "कोई चलती बस नहीं मिली।",
        "live_map": "लाइव ट्रैकिंग मैप",
        "refresh": "रीफ्रेश",
        "last_refreshed": "अंतिम अपडेट",
        "route": "रूट",
        "type": "प्रकार",
        "crowd": "भीड़",
        "status": "स्थिति",
        "arrives": "आने का समय ~",
        "total_buses": "कुल बसें",
        "running": "चल रही",
        "delayed": "देरी",
        "breakdowns": "खराब",
        "onboard": "यात्रियों की संख्या (लगभग)",
        "submit_complaint": "शिकायत दर्ज करें",
        "bus_optional": "बस (वैकल्पिक)",
        "route_optional": "रूट (वैकल्पिक)",
        "category": "श्रेणी",
        "describe_issue": "समस्या लिखें",
        "desc_ph": "समय/स्थान सहित स्पष्ट लिखें...",
        "submit": "शिकायत सबमिट करें",
        "desc_required": "कृपया विवरण दर्ज करें।",
        "complaint_submitted": "शिकायत दर्ज हुई। टिकट आईडी:",
        "my_recent": "मेरी हाल की शिकायतें (फोन द्वारा)",
        "no_complaints": "अभी तक कोई शिकायत नहीं।",
        "pass_preview": "पास पूर्वावलोकन",
        "no_pass": "कोई पास नहीं मिला।",
        "open_mobile": "QR डीप लिंक से मोबाइल पर पास खोलें।",
        "scan_mobile": "मोबाइल पर खोलने के लिए स्कैन करें",
        "conductor_portal": "कंडक्टर / ड्राइवर पोर्टल",
        "select_bus": "अपनी बस चुनें",
        "update_live": "लाइव स्थिति अपडेट करें",
        "passengers": "यात्री (लगभग)",
        "gps_tip": "यदि GPS है, तो सटीक मान दर्ज करें।",
        "push_update": "अपडेट भेजें",
        "updated_live": "लाइव स्थिति अपडेट हो गई।",
        "verify_pass": "पास सत्यापन (लिंक खोलें)",
        "verify_pass_title": "पास सत्यापन",
        "verify": "सत्यापित करें",
        "pass_not_found": "पास नहीं मिला।",
        "pass_valid": "पास मान्य है (डेमो)।",
        "admin_title": "नगरपालिका प्रशासन",
        "admin_live_map": "लाइव मैप",
        "admin_live_map_title": "नगरपालिका लाइव मैप (फ्लीट मॉनिटरिंग)",
        "fleet_table": "फ्लीट तालिका",
        "complaints_mgmt": "शिकायतें",
        "disruption_monitor": "विघ्न मॉनिटर",
        "app_crashed": "ऐप क्रैश हो गया। नीचे पूरा एरर:",
        "note_no_booking": "नोट: इस सिस्टम में टिकट बुकिंग नहीं है।"
    },
    "ta": {
        "language": "மொழி",
        "home": "முகப்பு",
        "back": "பின்செல்",
        "app_title": "ஸ்மார்ட் போக்குவரத்து அமைப்பு",
        "govt_mode": "அரசு பேருந்து: டிக்கெட் முன்பதிவு இல்லை. அடுத்த பேருந்து ETA, நேரடி கண்காணிப்பு, பாஸ், புகார்கள்.",
        "enter_name": "உங்கள் பெயரை உள்ளிடவும்",
        "name_ph": "எ.கா., மிதுன்",
        "welcome": "வரவேற்கிறோம்",
        "phone": "தொலைபேசி",
        "role": "பங்கு",
        "public_user": "பொது பயனர்",
        "conductor_driver": "கண்டக்டர்/டிரைவர்",
        "municipality_admin": "நகராட்சி நிர்வாகம்",
        "public_portal": "பொது போர்டல்",
        "find_my_bus": "என் பேருந்தை காண்க (ETA + Live Map)",
        "my_pass": "என் பாஸ்",
        "complaints": "புகார்கள் / முறையீடு",
        "select_stop": "உங்கள் தற்போதைய நிறுத்தத்தை தேர்ந்தெடுக்கவும்",
        "next_buses": "அடுத்த பேருந்துகள் (ETA)",
        "no_running_buses": "ஓடும் பேருந்துகள் இல்லை.",
        "live_map": "நேரடி கண்காணிப்பு வரைபடம்",
        "refresh": "புதுப்பி",
        "last_refreshed": "கடைசி புதுப்பிப்பு",
        "route": "பாதை",
        "type": "வகை",
        "crowd": "நெரிசல்",
        "status": "நிலை",
        "arrives": "வருகை ~",
        "total_buses": "மொத்த பேருந்துகள்",
        "running": "ஓடுகிறது",
        "delayed": "தாமதம்",
        "breakdowns": "பழுது",
        "onboard": "பயணிகள் (சுமார்)",
        "submit_complaint": "புகார் பதிவு",
        "bus_optional": "பேருந்து (விருப்பம்)",
        "route_optional": "பாதை (விருப்பம்)",
        "category": "வகை",
        "describe_issue": "பிரச்சனையை எழுதவும்",
        "desc_ph": "நேரம்/இடம் உட்பட தெளிவாக எழுதவும்...",
        "submit": "புகார் சமர்ப்பி",
        "desc_required": "விவரத்தை உள்ளிடவும்.",
        "complaint_submitted": "புகார் பதிவு செய்யப்பட்டது. டிக்கெட் ஐடி:",
        "my_recent": "என் சமீபத்திய புகார்கள் (எண் மூலம்)",
        "no_complaints": "புகார்கள் இல்லை.",
        "pass_preview": "பாஸ் முன்னோட்டம்",
        "no_pass": "பாஸ் இல்லை.",
        "open_mobile": "QR மூலம் மொபைலில் பாஸ் திறக்கவும்.",
        "scan_mobile": "மொபைலில் திறக்க ஸ்கேன் செய்யவும்",
        "conductor_portal": "கண்டக்டர் / டிரைவர் போர்டல்",
        "select_bus": "உங்கள் பேருந்தை தேர்வு செய்க",
        "update_live": "நேரடி நிலை புதுப்பி",
        "passengers": "பயணிகள் (சுமார்)",
        "gps_tip": "GPS இருந்தால் சரியான மதிப்புகளை உள்ளிடவும்.",
        "push_update": "புதுப்பிப்பு அனுப்பு",
        "updated_live": "நேரடி நிலை புதுப்பிக்கப்பட்டது.",
        "verify_pass": "பாஸ் சரிபார்ப்பு",
        "verify_pass_title": "பாஸ் சரிபார்ப்பு",
        "verify": "சரிபார்",
        "pass_not_found": "பாஸ் கிடைக்கவில்லை.",
        "pass_valid": "பாஸ் செல்லுபடியாகும் (டெமோ).",
        "admin_title": "நகராட்சி நிர்வாகம்",
        "admin_live_map": "நேரடி வரைபடம்",
        "admin_live_map_title": "நகராட்சி நேரடி வரைபடம் (Fleet Monitoring)",
        "fleet_table": "Fleet அட்டவணை",
        "complaints_mgmt": "புகார்கள்",
        "disruption_monitor": "பிரச்சனை கண்காணிப்பு",
        "app_crashed": "ஆப் பிழை. முழு பிழை கீழே:",
        "note_no_booking": "குறிப்பு: டிக்கெட் புக்கிங் இல்லை."
    },
}

def tr(key: str) -> str:
    lang = st.session_state.get("lang", "en")
    if lang not in T:
        lang = "en"
    return T.get(lang, {}).get(key, T["en"].get(key, key))


# -----------------------------
# Session State Init
# -----------------------------
def initialize_session_state():
    defaults = {
        "page": "role_selection",
        "role": None,
        "current_user": None,
        "lang": "en",

        "cached_buses_df": None,
        "cached_leaflet_html": None,
        "last_refresh_time": None,

        # which stop the map/eta is focused on
        "selected_stop": None,
        "cached_stop": None,

        # Admin map cache
        "admin_cached_leaflet_html": None,
        "admin_last_refresh_time": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

initialize_session_state()


# -----------------------------
# SQLite (Persistent Store)
# -----------------------------
def get_db():
    conn = sqlite3.connect("transport.db", check_same_thread=False)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS bus_live (
            bus_number TEXT PRIMARY KEY,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            passengers INTEGER NOT NULL,
            status TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS passes (
            pass_id TEXT PRIMARY KEY,
            phone TEXT NOT NULL,
            pass_type TEXT NOT NULL,
            valid_until TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            complaint_id TEXT PRIMARY KEY,
            phone TEXT NOT NULL,
            bus_number TEXT,
            route_name TEXT,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    return conn


# -----------------------------
# URL helpers (QR deep links)
# -----------------------------
def get_lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


def get_base_url():
    try:
        base = st.secrets.get("BASE_URL", "")
        if base:
            return base.rstrip("/")
    except Exception:
        pass

    ip = get_lan_ip()
    if ip:
        return f"http://{ip}:8501"
    return "http://localhost:8501"


# -----------------------------
# Geo helpers
# -----------------------------
def haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return 6371 * c


def crowd_level(passengers: int, capacity: int):
    if capacity <= 0:
        return ("Unknown", "pill")
    ratio = passengers / capacity
    if ratio < 0.45:
        return ("LOW", "pill pill-ok")
    if ratio < 0.80:
        return ("MED", "pill pill-warn")
    return ("HIGH", "pill pill-bad")


def status_pill(status: str):
    s = (status or "").lower()
    if s in ["active", "onroute", "running"]:
        return ("RUNNING", "pill pill-ok")
    if s in ["delayed"]:
        return ("DELAYED", "pill pill-warn")
    if s in ["breakdown", "cancelled", "maintenance"]:
        return ("BREAKDOWN", "pill pill-bad")
    return ("UNKNOWN", "pill")


# -----------------------------
# DATA: Places / Stops
# -----------------------------
def create_places_data():
    places = [
        {"stop_id": "S001", "stop_name": "Gandhipuram", "latitude": 11.0183, "longitude": 76.9725, "zone": "Central"},
        {"stop_id": "S002", "stop_name": "Coimbatore", "latitude": 11.0168, "longitude": 76.9558, "zone": "Central"},
        {"stop_id": "S003", "stop_name": "Tiruppur", "latitude": 11.1085, "longitude": 77.3411, "zone": "East"},
        {"stop_id": "S004", "stop_name": "Erode", "latitude": 11.3410, "longitude": 77.7172, "zone": "East"},
        {"stop_id": "S005", "stop_name": "Salem", "latitude": 11.6643, "longitude": 78.1460, "zone": "East"},
        {"stop_id": "S006", "stop_name": "Vellore", "latitude": 12.9165, "longitude": 79.1325, "zone": "North"},
        {"stop_id": "S007", "stop_name": "Chennai", "latitude": 13.0827, "longitude": 80.2707, "zone": "North"},
        {"stop_id": "S008", "stop_name": "Trichy", "latitude": 10.7905, "longitude": 78.7047, "zone": "South"},
        {"stop_id": "S009", "stop_name": "Thanjavur", "latitude": 10.7870, "longitude": 79.1378, "zone": "South"},
        {"stop_id": "S010", "stop_name": "Madurai", "latitude": 9.9252, "longitude": 78.1198, "zone": "South"},
    ]
    return pd.DataFrame(places)


@st.cache_data
def get_places_data():
    return create_places_data()


# -----------------------------
# Fleet + Live state
# -----------------------------
@st.cache_data
def get_static_fleet():
    places_df = get_places_data()
    bus_types = ["Ordinary", "Semi-Deluxe", "AC Deluxe", "Volvo", "Electric"]

    predefined_routes = [
        {"start": "Gandhipuram", "end": "Chennai", "route": "Gandhipuram-Chennai Express"},
        {"start": "Coimbatore", "end": "Madurai", "route": "Coimbatore-Madurai Direct"},
        {"start": "Salem", "end": "Chennai", "route": "Salem-Chennai Highway"},
        {"start": "Erode", "end": "Trichy", "route": "Erode-Trichy Local"},
        {"start": "Tiruppur", "end": "Salem", "route": "Tiruppur-Salem Connect"},
        {"start": "Vellore", "end": "Chennai", "route": "Vellore-Chennai Metro"},
        {"start": "Trichy", "end": "Madurai", "route": "Trichy-Madurai Express"},
        {"start": "Gandhipuram", "end": "Tiruppur", "route": "Gandhipuram-Tiruppur Local"},
    ]

    buses = []
    for i in range(120):
        route_info = predefined_routes[i % len(predefined_routes)]
        bt = bus_types[i % len(bus_types)]
        bus_number = f"TN38{random.choice(['A','B','C'])}{100 + i:03d}"

        start_place = places_df[places_df["stop_name"] == route_info["start"]].iloc[0]
        buses.append({
            "bus_number": bus_number,
            "bus_type": bt,
            "capacity": random.choice([30, 35, 40, 45, 50]),
            "start_point": route_info["start"],
            "end_point": route_info["end"],
            "route_name": route_info["route"],
            "default_lat": float(start_place["latitude"]) + random.uniform(-0.01, 0.01),
            "default_lon": float(start_place["longitude"]) + random.uniform(-0.01, 0.01),
        })

    return pd.DataFrame(buses)


def ensure_live_state_seeded():
    conn = get_db()
    cur = conn.execute("SELECT COUNT(*) FROM bus_live")
    n = cur.fetchone()[0]
    if n and int(n) > 0:
        return

    static_df = get_static_fleet()
    now = datetime.now().isoformat(timespec="seconds")
    for _, b in static_df.iterrows():
        conn.execute(
            "INSERT OR REPLACE INTO bus_live (bus_number, latitude, longitude, passengers, status, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                b["bus_number"],
                float(b["default_lat"]),
                float(b["default_lon"]),
                int(random.randint(5, 25)),
                "Active",
                now
            )
        )
    conn.commit()


def get_buses_data():
    ensure_live_state_seeded()
    static_df = get_static_fleet()

    conn = get_db()
    live_df = pd.read_sql_query(
        "SELECT bus_number, latitude, longitude, passengers, status, updated_at FROM bus_live",
        conn
    )

    df = static_df.merge(live_df, on="bus_number", how="left")
    df["passengers"] = df["passengers"].fillna(0).astype(int)
    df["status"] = df["status"].fillna("Unknown")
    df["latitude"] = df["latitude"].fillna(df["default_lat"]).astype(float)
    df["longitude"] = df["longitude"].fillna(df["default_lon"]).astype(float)

    df["crowd"] = df.apply(lambda r: crowd_level(int(r["passengers"]), int(r["capacity"]))[0], axis=1)
    return df


# -----------------------------
# Next Bus ETA (ONLY buses inside the red circle)
# -----------------------------
def buses_in_circle_eta(stop_name: str, radius_m=900):
    places = get_places_data()
    srow = places[places["stop_name"] == stop_name].iloc[0]
    slat, slon = float(srow["latitude"]), float(srow["longitude"])

    buses_df = get_buses_data()
    running = buses_df[buses_df["status"].str.lower().isin(["active", "running", "onroute", "delayed"])].copy()
    if running.empty:
        return pd.DataFrame()

    running["dist_km"] = running.apply(
        lambda r: haversine_km(float(r["latitude"]), float(r["longitude"]), slat, slon),
        axis=1
    )

    # keep ONLY buses inside circle
    r_km = float(radius_m) / 1000.0
    inside = running[running["dist_km"] <= r_km].copy()
    if inside.empty:
        return pd.DataFrame()

    def speed_kmh(bus_type, status):
        base = {"Ordinary": 32, "Semi-Deluxe": 36, "AC Deluxe": 40, "Volvo": 45, "Electric": 34}.get(bus_type, 35)
        if str(status).lower() == "delayed":
            return max(18, base * 0.6)
        return base

    inside["speed_kmh"] = inside.apply(lambda r: speed_kmh(r["bus_type"], r["status"]), axis=1)
    inside["eta_min"] = (inside["dist_km"] / inside["speed_kmh"] * 60).round().astype(int)
    inside["eta_min"] = inside["eta_min"].clip(lower=1, upper=180)

    out = inside.sort_values(["eta_min", "dist_km"]).copy()
    out["eta_time"] = out["eta_min"].apply(lambda m: (datetime.now() + timedelta(minutes=int(m))).strftime("%I:%M %p"))
    return out


# -----------------------------
# Passes
# -----------------------------
def ensure_demo_pass(phone: str):
    conn = get_db()
    cur = conn.execute("SELECT COUNT(*) FROM passes WHERE phone=?", (phone,))
    n = cur.fetchone()[0]
    if n and int(n) > 0:
        return

    pid = f"PASS-{uuid.uuid4().hex[:8].upper()}"
    valid = (datetime.now() + timedelta(days=30)).date().isoformat()
    now = datetime.now().isoformat(timespec="seconds")
    conn.execute(
        "INSERT INTO passes (pass_id, phone, pass_type, valid_until, created_at) VALUES (?, ?, ?, ?, ?)",
        (pid, phone, "Monthly Pass", valid, now)
    )
    conn.commit()


def get_user_passes(phone: str):
    conn = get_db()
    return pd.read_sql_query(
        "SELECT * FROM passes WHERE phone=? ORDER BY created_at DESC",
        conn,
        params=(phone,)
    )


def load_pass(pass_id: str):
    conn = get_db()
    cur = conn.execute(
        "SELECT pass_id, phone, pass_type, valid_until, created_at FROM passes WHERE pass_id=?",
        (pass_id,)
    )
    row = cur.fetchone()
    if not row:
        return None
    return {"pass_id": row[0], "phone": row[1], "pass_type": row[2], "valid_until": row[3], "created_at": row[4]}


def render_pass_qr(pass_row: dict):
    base_url = get_base_url()
    pass_url = f"{base_url}/?{urlencode({'pass': pass_row['pass_id']})}"

    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(pass_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    st.image(buf.getvalue(), width=220)
    st.caption(tr("scan_mobile"))


def render_pass_card(p: dict):
    html = f"""
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <style>
        body {{ font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial; background:#fff7ed; padding:12px; }}
        .wrap {{ max-width: 520px; margin: 0 auto; }}
        .card {{ background:#fff; border:1px solid #fed7aa; border-radius:16px; padding:16px; box-shadow: 0 10px 22px rgba(0,0,0,0.10); }}
        .title {{ text-align:center; font-weight:900; font-size:18px; margin:0; color:#9a3412; }}
        .sub {{ text-align:center; margin-top:6px; font-size:13px; color:#444; }}
        .dash {{ border-top:1px dashed #999; margin:12px 0; }}
        .row {{ display:flex; justify-content:space-between; gap:12px; font-size:13px; margin:6px 0; }}
        .label {{ color:#333; font-weight:900; }}
        .value {{ color:#111; text-align:right; word-break:break-word; }}
        .ok {{ display:inline-block; padding:4px 10px; border-radius:999px; background:#ecfdf5; border:1px solid #bbf7d0; color:#065f46; font-weight:900; font-size:12px; }}
      </style>
    </head>
    <body>
      <div class="wrap">
        <div class="card">
          <h2 class="title">🪪 GOVT BUS PASS</h2>
          <div class="sub">{tr("note_no_booking")}</div>
          <div class="dash"></div>

          <div class="row"><div class="label">Pass ID</div><div class="value">{p['pass_id']}</div></div>
          <div class="row"><div class="label">{tr("type")}</div><div class="value">{p['pass_type']}</div></div>
          <div class="row"><div class="label">{tr("phone")}</div><div class="value">{p['phone']}</div></div>
          <div class="row"><div class="label">Valid</div><div class="value"><span class="ok">{p['valid_until']}</span></div></div>
        </div>
      </div>
    </body>
    </html>
    """
    components.html(html, height=460, scrolling=True)


# -----------------------------
# Complaints
# -----------------------------
def create_complaint(phone, bus_number, route_name, category, description):
    cid = f"CMP-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now().isoformat(timespec="seconds")
    conn = get_db()
    conn.execute(
        """INSERT INTO complaints
           (complaint_id, phone, bus_number, route_name, category, description, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (cid, phone, bus_number, route_name, category, description, "OPEN", now, now)
    )
    conn.commit()
    return cid


def list_complaints(status=None):
    conn = get_db()
    if status:
        return pd.read_sql_query(
            "SELECT * FROM complaints WHERE status=? ORDER BY created_at DESC",
            conn,
            params=(status,)
        )
    return pd.read_sql_query("SELECT * FROM complaints ORDER BY created_at DESC", conn)


def update_complaint_status(complaint_id, new_status):
    conn = get_db()
    now = datetime.now().isoformat(timespec="seconds")
    conn.execute(
        "UPDATE complaints SET status=?, updated_at=? WHERE complaint_id=?",
        (new_status, now, complaint_id)
    )
    conn.commit()


# -----------------------------
# Map (Folium) — show circle + clickable nearby stops (3–4)
# -----------------------------
def _nearby_stops_within_circle(focus_stop: str, radius_m=900, pick_n=4):
    places = get_places_data()
    if focus_stop not in places["stop_name"].tolist():
        return pd.DataFrame()

    srow = places[places["stop_name"] == focus_stop].iloc[0]
    slat, slon = float(srow["latitude"]), float(srow["longitude"])
    r_km = float(radius_m) / 1000.0

    tmp = places.copy()
    tmp["dist_km"] = tmp.apply(lambda r: haversine_km(float(r["latitude"]), float(r["longitude"]), slat, slon), axis=1)
    inside = tmp[tmp["dist_km"] <= r_km].sort_values("dist_km").copy()

    if inside.empty:
        return pd.DataFrame()

    # always include focus stop + up to 3 others (total 4)
    focus_df = inside[inside["stop_name"] == focus_stop]
    others = inside[inside["stop_name"] != focus_stop].head(max(0, pick_n - 1))
    out = pd.concat([focus_df, others], ignore_index=True)
    return out


def create_live_bus_map_leaflet(
    buses_df: pd.DataFrame,
    focus_stop=None,
    show_clickable_stops=False,
    radius_m=900
):
    places = get_places_data()

    if focus_stop and focus_stop in places["stop_name"].tolist():
        srow = places[places["stop_name"] == focus_stop].iloc[0]
        center_lat, center_lon = float(srow["latitude"]), float(srow["longitude"])
        zoom = 14
    else:
        # fallback center if no focus
        if buses_df is None or buses_df.empty:
            center_lat, center_lon, zoom = 11.0, 78.0, 7
        else:
            center_lat = float(buses_df["latitude"].mean())
            center_lon = float(buses_df["longitude"].mean())
            zoom = 7

    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom, tiles="OpenStreetMap")

    # Focus circle + stops first
    if focus_stop and focus_stop in places["stop_name"].tolist():
        srow = places[places["stop_name"] == focus_stop].iloc[0]

        folium.Marker(
            location=[float(srow["latitude"]), float(srow["longitude"])],
            popup=folium.Popup(f"<b>📍 Stop:</b> {focus_stop}", max_width=260),
            icon=folium.Icon(color="orange", icon="info-sign"),
        ).add_to(m)

        folium.Circle(
            location=[float(srow["latitude"]), float(srow["longitude"])],
            radius=float(radius_m),
            color="#f97316",
            fill=False
        ).add_to(m)

        if show_clickable_stops:
            base_url = get_base_url()
            nearby = _nearby_stops_within_circle(focus_stop, radius_m=radius_m, pick_n=4)
            for _, r in nearby.iterrows():
                stop_nm = str(r["stop_name"])
                # clicking marker => reload app with ?stop=...
                stop_url = f"{base_url}/?{urlencode({'stop': stop_nm})}"
                pop = f"""
                <div style="font-family: Arial; font-size: 12px;">
                  <b>📍 {stop_nm}</b><br>
                  <a href="{stop_url}" style="font-weight:900; color:#9a3412; text-decoration:none;">
                    Tap to view buses arriving
                  </a>
                </div>
                """
                icon_color = "orange" if stop_nm == focus_stop else "blue"
                folium.Marker(
                    location=[float(r["latitude"]), float(r["longitude"])],
                    popup=folium.Popup(pop, max_width=320),
                    icon=folium.Icon(color=icon_color, icon="info-sign"),
                ).add_to(m)

    # Bus markers
    if buses_df is not None and not buses_df.empty:
        cluster = MarkerCluster().add_to(m)

        def color_for_type(bt):
            return {"Ordinary": "blue", "Semi-Deluxe": "green", "AC Deluxe": "orange", "Volvo": "red", "Electric": "purple"}.get(bt, "blue")

        for _, bus in buses_df.iterrows():
            crowd, _ = crowd_level(int(bus["passengers"]), int(bus["capacity"]))
            pop = f"""
            <div style="font-family: Arial; font-size: 12px;">
                <b>🚌 {bus['bus_number']}</b><br>
                {tr('type')}: {bus['bus_type']}<br>
                {tr('route')}: {bus['route_name']}<br>
                {bus['start_point']} → {bus['end_point']}<br>
                {tr('crowd')}: {bus['passengers']}/{bus['capacity']} ({crowd})<br>
                {tr('status')}: {bus['status']}<br>
                Updated: {bus.get('updated_at','-')}
            </div>
            """
            folium.CircleMarker(
                location=[float(bus["latitude"]), float(bus["longitude"])],
                radius=6,
                color=color_for_type(bus["bus_type"]),
                fill=True,
                fill_opacity=0.9,
                popup=folium.Popup(pop, max_width=320),
            ).add_to(cluster)

    return m


# -----------------------------
# Users (demo)
# -----------------------------
def find_user_by_name(name: str):
    return {
        "user_id": 1,
        "first_name": name.split()[0] if " " in name else name,
        "last_name": name.split()[-1] if " " in name else "User",
        "full_name": name,
        "age": 25,
        "phone": f"9{random.randint(100000000, 999999999)}",
    }


# -----------------------------
# Language Picker (WORKS ALWAYS)
# -----------------------------
def language_bar():
    codes = [c for c, _ in LANGS]
    names = [n for _, n in LANGS]
    cur = st.session_state.get("lang", "en")
    if cur not in codes:
        cur = "en"
    idx = codes.index(cur)

    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown(f"**🌐 {tr('language')}**")
    with col2:
        chosen = st.selectbox("", names, index=idx, label_visibility="collapsed")

    new_code = codes[names.index(chosen)]
    if new_code != st.session_state.lang:
        st.session_state.lang = new_code
        st.rerun()


# -----------------------------
# Navigation Helpers
# -----------------------------
def goto_home():
    st.session_state.page = "role_selection"
    st.session_state.role = None
    st.rerun()


def home_button():
    if st.button(f"🏠 {tr('home')}", use_container_width=True):
        goto_home()


def back_button(target_page: str):
    if st.button(f"← {tr('back')}", use_container_width=True):
        st.session_state.page = target_page
        st.rerun()


# -----------------------------
# PAGES
# -----------------------------
def role_selection_page():
    st.markdown(f"<div class='main-header'>🚍 {tr('app_title')}</div>", unsafe_allow_html=True)
    st.write(tr("govt_mode"))

    user_name = st.text_input(tr("enter_name"), placeholder=tr("name_ph"))
    if not user_name:
        return

    user = find_user_by_name(user_name)
    st.session_state.current_user = user

    st.markdown(
        f"""
        <div class="card">
          <div class="sub-header">👋 {tr('welcome')}, {user['full_name']}</div>
          <div class="mini">📱 <b>{tr('phone')}:</b> {user['phone']}</div>
          <div class="mini"><b>{tr('note_no_booking')}</b></div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(f"👥 {tr('public_user')}", type="primary", use_container_width=True):
            st.session_state.role = "public"
            st.session_state.page = "public_home"
            st.rerun()
    with col2:
        if st.button(f"🧑‍✈️ {tr('conductor_driver')}", use_container_width=True):
            st.session_state.role = "conductor"
            st.session_state.page = "conductor_portal"
            st.rerun()
    with col3:
        if st.button(f"🏛 {tr('municipality_admin')}", use_container_width=True):
            st.session_state.role = "municipality"
            st.session_state.page = "admin_home"
            st.rerun()


def top_bar():
    if st.session_state.page == "role_selection" or not st.session_state.current_user:
        return
    u = st.session_state.current_user
    role = st.session_state.role
    st.markdown(f"**👤 {u['full_name']}** | **📱 {tr('phone')}: {u['phone']}** | **{tr('role')}:** {role}")
    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)


def public_home():
    u = st.session_state.current_user
    ensure_demo_pass(u["phone"])

    st.markdown(f"<div class='main-header'>👥 {tr('public_portal')}</div>", unsafe_allow_html=True)

    # back + home
    colA, colB = st.columns([1, 1])
    with colA:
        back_button("role_selection")
    with colB:
        home_button()

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(f"📍 {tr('find_my_bus')}", type="primary", use_container_width=True):
            st.session_state.page = "find_my_bus"
            st.rerun()
    with col2:
        if st.button(f"🪪 {tr('my_pass')}", use_container_width=True):
            st.session_state.page = "my_pass"
            st.rerun()
    with col3:
        if st.button(f"📝 {tr('complaints')}", use_container_width=True):
            st.session_state.page = "complaints_public"
            st.rerun()


def find_my_bus_page():
    st.markdown(f"<div class='main-header'>📍 {tr('find_my_bus')}</div>", unsafe_allow_html=True)

    # back + home
    colA, colB = st.columns([1, 1])
    with colA:
        back_button("public_home")
    with colB:
        home_button()

    places = get_places_data()
    stop_names = places["stop_name"].tolist()

    # pick a default focus stop for the "map first" experience
    if st.session_state.selected_stop is None:
        st.session_state.selected_stop = stop_names[0] if stop_names else None

    # Stop selector (still available) but map is shown first
    stop = st.selectbox(tr("select_stop"), stop_names, index=stop_names.index(st.session_state.selected_stop))

    if stop != st.session_state.selected_stop:
        st.session_state.selected_stop = stop
        # invalidate cache when stop changes
        st.session_state.cached_buses_df = None
        st.session_state.cached_leaflet_html = None
        st.session_state.last_refresh_time = None

    # Refresh buttons
    r1, r2 = st.columns([1, 1])
    with r1:
        refresh_clicked = st.button(f"🔄 {tr('refresh')}", type="primary", use_container_width=True)
    with r2:
        st.caption(tr("note_no_booking"))

    # refresh data/map
    if refresh_clicked or st.session_state.cached_buses_df is None or st.session_state.cached_stop != stop:
        with st.spinner("Refreshing..."):
            buses_df = get_buses_data()
            leaflet = create_live_bus_map_leaflet(
                buses_df=buses_df,
                focus_stop=stop,
                show_clickable_stops=True,
                radius_m=900
            )
            st.session_state.cached_buses_df = buses_df
            st.session_state.cached_leaflet_html = leaflet.get_root().render()
            st.session_state.last_refresh_time = datetime.now()
            st.session_state.cached_stop = stop

    buses_df = st.session_state.cached_buses_df
    if buses_df is None or buses_df.empty:
        st.error("No bus data available.")
        return

    # --- MAP FIRST (requested) ---
    st.markdown(f"### 🗺 {tr('live_map')}")
    if st.session_state.cached_leaflet_html:
        components.html(st.session_state.cached_leaflet_html, height=560, scrolling=False)
    else:
        st.warning("Map not ready. Click refresh.")

    if st.session_state.last_refresh_time:
        st.info(f"{tr('last_refreshed')}: {st.session_state.last_refresh_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # KPI row (fleet-wide; unchanged)
    total = len(buses_df)
    running_n = len(buses_df[buses_df["status"].str.lower().isin(["active", "running", "onroute", "delayed"])])
    delayed_n = len(buses_df[buses_df["status"].str.lower().eq("delayed")])
    breakdown_n = len(buses_df[buses_df["status"].str.lower().eq("breakdown")])
    pax = int(buses_df["passengers"].sum())

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"<div class='kpi'><h2>{total}</h2><p>{tr('total_buses')}</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='kpi'><h2>{running_n}</h2><p>{tr('running')}</p></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='kpi'><h2>{delayed_n}</h2><p>{tr('delayed')}</p></div>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div class='kpi'><h2>{breakdown_n}</h2><p>{tr('breakdowns')}</p></div>", unsafe_allow_html=True)
    with c5:
        st.markdown(f"<div class='kpi'><h2>{pax}</h2><p>{tr('onboard')}</p></div>", unsafe_allow_html=True)

    # --- BUSES FOR THE STOP (ONLY inside circle; show ALL, not capped at 10) ---
    st.markdown(f"### 🚌 {tr('next_buses')}")
    buses = buses_in_circle_eta(stop, radius_m=900)
    if buses.empty:
        st.warning(tr("no_running_buses"))
    else:
        # show every bus found inside circle (no artificial limit)
        for _, b in buses.iterrows():
            crowd_lbl, crowd_cls = crowd_level(int(b["passengers"]), int(b["capacity"]))
            st_lbl, st_cls = status_pill(str(b["status"]))

            st.markdown(
                f"""
                <div class="card">
                  <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:14px;">
                    <div>
                      <div class="sub-header">🚌 {b['bus_number']} <span class="{st_cls}">{st_lbl}</span></div>
                      <div class="mini"><b>{tr('route')}:</b> {b['route_name']} ({b['start_point']} → {b['end_point']})</div>
                      <div class="mini"><b>{tr('type')}:</b> {b['bus_type']} • <b>{tr('crowd')}:</b> <span class="{crowd_cls}">{crowd_lbl}</span> • {b['passengers']}/{b['capacity']}</div>
                    </div>
                    <div style="text-align:right;">
                      <div style="font-size:1.6rem; font-weight:900; color:#9a3412;">{int(b['eta_min'])} min</div>
                      <div class="mini">{tr('arrives')} {b['eta_time']}</div>
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True
            )


def my_pass_page():
    st.markdown(f"<div class='main-header'>🪪 {tr('my_pass')}</div>", unsafe_allow_html=True)

    colA, colB = st.columns([1, 1])
    with colA:
        back_button("public_home")
    with colB:
        home_button()

    u = st.session_state.current_user
    ensure_demo_pass(u["phone"])
    passes = get_user_passes(u["phone"])

    if passes.empty:
        st.warning(tr("no_pass"))
        return

    p = passes.iloc[0].to_dict()

    st.markdown(
        f"""
        <div class="card">
          <div class="sub-header">{p['pass_type']}</div>
          <div class="mini"><b>Valid Until:</b> {p['valid_until']}</div>
          <div class="mini"><b>Pass ID:</b> {p['pass_id']}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([1, 2])
    with col1:
        render_pass_qr(p)
    with col2:
        st.write(tr("open_mobile"))
        base_url = get_base_url()
        pass_url = f"{base_url}/?{urlencode({'pass': p['pass_id']})}"
        st.code(pass_url)

    st.markdown(f"### {tr('pass_preview')}")
    render_pass_card(p)


def complaints_public_page():
    st.markdown(f"<div class='main-header'>📝 {tr('complaints')}</div>", unsafe_allow_html=True)

    colA, colB = st.columns([1, 1])
    with colA:
        back_button("public_home")
    with colB:
        home_button()

    u = st.session_state.current_user
    buses_df = get_buses_data()

    st.markdown(f"### {tr('submit_complaint')}")
    col1, col2 = st.columns(2)
    with col1:
        bus_number = st.selectbox(tr("bus_optional"), ["—"] + buses_df["bus_number"].tolist(), index=0)
    with col2:
        route_name = st.selectbox(tr("route_optional"), ["—"] + sorted(buses_df["route_name"].unique().tolist()), index=0)

    category = st.selectbox(tr("category"), ["Delay", "Overcrowding", "Rash Driving", "Cleanliness", "Misbehavior", "Other"])
    desc = st.text_area(tr("describe_issue"), placeholder=tr("desc_ph"), height=120)

    if st.button(tr("submit"), type="primary"):
        if not desc.strip():
            st.error(tr("desc_required"))
        else:
            cid = create_complaint(
                phone=u["phone"],
                bus_number=None if bus_number == "—" else bus_number,
                route_name=None if route_name == "—" else route_name,
                category=category,
                description=desc.strip()
            )
            st.success(f"{tr('complaint_submitted')} {cid}")

    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
    st.markdown(f"### {tr('my_recent')}")
    allc = list_complaints()
    mine = allc[allc["phone"] == u["phone"]].copy()
    if mine.empty:
        st.info(tr("no_complaints"))
    else:
        st.dataframe(mine[["complaint_id", "category", "bus_number", "route_name", "status", "created_at"]].head(30),
                     use_container_width=True)


def conductor_portal():
    st.markdown(f"<div class='main-header'>🧑‍✈️ {tr('conductor_portal')}</div>", unsafe_allow_html=True)

    colA, colB = st.columns([1, 1])
    with colA:
        back_button("role_selection")
    with colB:
        home_button()

    buses_df = get_buses_data()
    bus_number = st.selectbox(tr("select_bus"), buses_df["bus_number"].tolist())
    current = buses_df[buses_df["bus_number"] == bus_number].iloc[0].to_dict()

    st.markdown(
        f"""
        <div class="card">
          <div class="sub-header">🚌 {bus_number} <span class="pill">{current['bus_type']}</span></div>
          <div class="mini"><b>{tr('route')}:</b> {current['route_name']} ({current['start_point']} → {current['end_point']})</div>
          <div class="mini"><b>Current:</b> {current['latitude']:.5f}, {current['longitude']:.5f} • <b>{tr('status')}:</b> {current['status']}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(f"### {tr('update_live')}")
    col1, col2, col3 = st.columns(3)
    with col1:
        new_status = st.selectbox(tr("status"), ["Active", "Delayed", "Breakdown"], index=0)
    with col2:
        new_pass = st.number_input(tr("passengers"), min_value=0, max_value=int(current["capacity"]), value=int(current["passengers"]))
    with col3:
        st.caption(tr("gps_tip"))
        lat = st.number_input("Latitude", value=float(current["latitude"]), format="%.6f")
        lon = st.number_input("Longitude", value=float(current["longitude"]), format="%.6f")

    if st.button(f"✅ {tr('push_update')}", type="primary"):
        conn = get_db()
        now = datetime.now().isoformat(timespec="seconds")
        conn.execute(
            "INSERT OR REPLACE INTO bus_live (bus_number, latitude, longitude, passengers, status, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (bus_number, float(lat), float(lon), int(new_pass), new_status, now)
        )
        conn.commit()
        st.success(tr("updated_live"))
        # invalidate public/admin map caches
        st.session_state.cached_buses_df = None
        st.session_state.cached_leaflet_html = None
        st.session_state.admin_cached_leaflet_html = None


def admin_home():
    st.markdown(f"<div class='main-header'>🏛 {tr('admin_title')}</div>", unsafe_allow_html=True)

    colA, colB = st.columns([1, 1])
    with colA:
        back_button("role_selection")
    with colB:
        home_button()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button(f"🗺 {tr('admin_live_map')}", type="primary", use_container_width=True):
            st.session_state.page = "admin_live_map"
            st.rerun()
    with col2:
        if st.button(f"🚌 {tr('fleet_table')}", use_container_width=True):
            st.session_state.page = "fleet_admin"
            st.rerun()
    with col3:
        if st.button(f"📝 {tr('complaints_mgmt')}", use_container_width=True):
            st.session_state.page = "complaints_admin"
            st.rerun()
    with col4:
        if st.button(f"🔧 {tr('disruption_monitor')}", use_container_width=True):
            st.session_state.page = "disruption_admin"
            st.rerun()


def admin_live_map_page():
    st.markdown(f"<div class='main-header'>🗺 {tr('admin_live_map_title')}</div>", unsafe_allow_html=True)

    colA, colB = st.columns([1, 1])
    with colA:
        back_button("admin_home")
    with colB:
        home_button()

    refresh_clicked = st.button(f"🔄 {tr('refresh')}", type="primary", use_container_width=True)

    if refresh_clicked or st.session_state.admin_cached_leaflet_html is None:
        with st.spinner("Refreshing..."):
            buses_df = get_buses_data()
            leaflet = create_live_bus_map_leaflet(buses_df, focus_stop=None)
            st.session_state.admin_cached_leaflet_html = leaflet.get_root().render()
            st.session_state.admin_last_refresh_time = datetime.now()

    if st.session_state.admin_last_refresh_time:
        st.info(f"{tr('last_refreshed')}: {st.session_state.admin_last_refresh_time.strftime('%Y-%m-%d %H:%M:%S')}")

    components.html(st.session_state.admin_cached_leaflet_html, height=650, scrolling=False)


def fleet_admin_page():
    st.markdown(f"<div class='main-header'>🚌 {tr('fleet_table')}</div>", unsafe_allow_html=True)

    colA, colB = st.columns([1, 1])
    with colA:
        back_button("admin_home")
    with colB:
        home_button()

    df = get_buses_data()
    st.dataframe(df[["bus_number","route_name","bus_type","status","passengers","capacity","latitude","longitude","updated_at"]],
                 use_container_width=True)


def complaints_admin_page():
    st.markdown(f"<div class='main-header'>📝 {tr('complaints_mgmt')}</div>", unsafe_allow_html=True)

    colA, colB = st.columns([1, 1])
    with colA:
        back_button("admin_home")
    with colB:
        home_button()

    allc = list_complaints()
    if allc.empty:
        st.info("No complaints.")
        return

    st.dataframe(allc[["complaint_id","phone","category","bus_number","route_name","status","created_at","updated_at"]],
                 use_container_width=True)

    st.markdown("### Update status")
    cid = st.selectbox("Complaint ID", allc["complaint_id"].tolist())
    new_status = st.selectbox("New Status", ["OPEN", "IN_PROGRESS", "RESOLVED", "REJECTED"])
    if st.button("Update", type="primary"):
        update_complaint_status(cid, new_status)
        st.success("Updated.")
        st.rerun()


def disruption_admin_page():
    st.markdown(f"<div class='main-header'>🔧 {tr('disruption_monitor')}</div>", unsafe_allow_html=True)

    colA, colB = st.columns([1, 1])
    with colA:
        back_button("admin_home")
    with colB:
        home_button()

    df = get_buses_data()
    delayed = df[df["status"].str.lower().eq("delayed")]
    breakdown = df[df["status"].str.lower().eq("breakdown")]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🟡 Delayed Buses")
        if delayed.empty:
            st.success("No delayed buses.")
        else:
            st.dataframe(delayed[["bus_number","route_name","passengers","capacity","updated_at"]].head(30),
                         use_container_width=True)
    with col2:
        st.markdown("### 🔴 Breakdowns")
        if breakdown.empty:
            st.success("No breakdowns.")
        else:
            st.dataframe(breakdown[["bus_number","route_name","passengers","capacity","updated_at"]].head(30),
                         use_container_width=True)


# -----------------------------
# Deep-link Pass Page
# -----------------------------
def pass_page(pass_id: str):
    st.markdown(f"<div class='main-header'>🪪 {tr('my_pass')}</div>", unsafe_allow_html=True)
    p = load_pass(pass_id)
    if not p:
        st.error(tr("pass_not_found"))
        return
    render_pass_card(p)


# -----------------------------
# MAIN
# -----------------------------
def main():
    language_bar()

    # Deep link support (both old/new streamlit)
    stop_from_link = None
    pass_id = None
    try:
        qp = st.query_params
        pass_id = qp.get("pass")
        stop_from_link = qp.get("stop")
    except Exception:
        qp = st.experimental_get_query_params()
        pass_id = (qp.get("pass") or [None])[0]
        stop_from_link = (qp.get("stop") or [None])[0]

    if pass_id:
        pass_page(pass_id)
        return

    # If a stop is clicked from the map, jump to Find My Bus and focus that stop
    if stop_from_link:
        places = get_places_data()
        if stop_from_link in places["stop_name"].tolist():
            st.session_state.selected_stop = stop_from_link
            st.session_state.page = "find_my_bus"
            # invalidate cache so buses/map match the clicked stop
            st.session_state.cached_buses_df = None
            st.session_state.cached_leaflet_html = None
            st.session_state.last_refresh_time = None
            st.session_state.cached_stop = None

    top_bar()

    page = st.session_state.page

    if page == "role_selection":
        role_selection_page()
    elif page == "public_home":
        public_home()
    elif page == "find_my_bus":
        find_my_bus_page()
    elif page == "my_pass":
        my_pass_page()
    elif page == "complaints_public":
        complaints_public_page()
    elif page == "conductor_portal":
        conductor_portal()
    elif page == "admin_home":
        admin_home()
    elif page == "admin_live_map":
        admin_live_map_page()
    elif page == "fleet_admin":
        fleet_admin_page()
    elif page == "complaints_admin":
        complaints_admin_page()
    elif page == "disruption_admin":
        disruption_admin_page()
    else:
        st.session_state.page = "role_selection"
        st.rerun()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(tr("app_crashed"))
        st.exception(e)
        raise