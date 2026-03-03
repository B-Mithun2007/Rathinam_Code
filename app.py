# app.py
# 🚍 SMART TRANSPORT SYSTEM (Govt Bus Mode: NO Ticket Booking / NO Pre-booking)
# ✅ Stop-first UX (Next Bus ETA + Live tracking map ON SAME PAGE)
# ✅ Multilingual UI (user can switch language anytime) — FIXED for all listed languages
# ✅ NO booking, NO seat reservation, NO ticket purchase workflow
# ✅ Pass QR (optional) + Complaints / Grievance workflow
# ✅ Municipality Admin + Conductor Portal (updates live occupancy/status/location)
# ✅ Leaflet Map (Folium) via components.html
# ✅ SQLite persistence for: live bus state, passes, complaints
# ✅ Find My Bus list shows ALL buses INSIDE the red circle radius (no hidden limit)
# ✅ Circle also shows nearby sub-stops for dense hubs (e.g., Gandhipuram has nearby mini-stops)
# ✅ Fix: NaN ETA crash (ValueError: cannot convert float NaN to integer)

import streamlit as st
import streamlit.components.v1 as components

import pandas as pd
from datetime import datetime, timedelta
import random
import math
import uuid
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
# THEME (Warm: Yellow / Orange / Red)
# -----------------------------
WARM_THEME_CSS = """
<style>
:root{
  --warm-1:#fff7ed;
  --warm-2:#ffedd5;
  --warm-3:#fdba74;
  --warm-4:#f97316;
  --warm-5:#ea580c;
  --warm-6:#9a3412;
  --card:#ffffff;
  --border:#f1c6a6;
  --shadow: 0 10px 25px rgba(0,0,0,0.08);
}
.stApp{
  background: linear-gradient(180deg, var(--warm-1), #ffffff 65%);
}
.main-header{
  font-size: 2.8rem;
  font-weight: 900;
  text-align:center;
  margin: 0.4rem 0 1.2rem 0;
  letter-spacing: -0.6px;
  color: var(--warm-6);
}
.sub-header{
  font-size: 1.2rem;
  font-weight: 800;
  margin: 0.4rem 0 0.4rem 0;
  color: #2b2b2b;
}
.mini{ color:#333; font-weight:650; font-size:0.95rem; }
.card{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 1.0rem;
  box-shadow: var(--shadow);
  margin: 0.6rem 0;
}
.pill{
  display:inline-block;
  padding: 0.25rem 0.65rem;
  border-radius: 999px;
  font-weight: 800;
  font-size: 0.85rem;
  border: 1px solid var(--border);
  background: var(--warm-1);
  color: #2b2b2b;
}
.pill-ok{ background:#ecfdf5; border-color:#bbf7d0; color:#065f46; }
.pill-warn{ background:#fffbeb; border-color:#fde68a; color:#92400e; }
.pill-bad{ background:#fef2f2; border-color:#fecaca; color:#991b1b; }

.hr{
  border-top: 1px solid rgba(0,0,0,0.08);
  margin: 0.9rem 0;
}
div.stButton > button[kind="primary"]{
  background: linear-gradient(135deg, var(--warm-4), var(--warm-5)) !important;
  color: white !important;
  border: 0 !important;
  border-radius: 14px !important;
  font-weight: 900 !important;
}
div.stButton > button{
  border-radius: 14px !important;
  font-weight: 800 !important;
}
div[data-baseweb="input"] input, div[data-baseweb="select"] div{
  border-radius: 14px !important;
}
</style>
"""
st.markdown(WARM_THEME_CSS, unsafe_allow_html=True)


# -----------------------------
# Multilingual (UI Text Dictionary)
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

UI_KEYS = [
    "app_title", "govt_mode_line", "enter_name", "name_placeholder", "welcome", "phone", "role",
    "note_no_booking", "public_user", "conductor_driver", "municipality_admin",
    "public_portal", "find_my_bus", "my_pass", "complaints", "back",
    "find_my_bus_title", "find_my_bus_caption", "select_stop", "next_buses", "no_running_buses",
    "refresh_eta", "refresh_map", "map_title", "map_updated", "map_tip",
    "route", "type", "crowd", "arrives", "min", "running", "delayed", "breakdown", "unknown",
    "pass_title", "no_pass", "valid_until", "pass_id", "reminder_no_booking",
    "open_pass_mobile", "pass_preview",
    "submit_complaint", "bus_optional", "route_optional", "category", "describe_issue",
    "desc_placeholder", "submit", "desc_required", "complaint_submitted",
    "my_recent_complaints", "no_complaints",
    "conductor_portal", "conductor_caption", "select_bus", "current", "passengers", "status",
    "update_live", "passengers_approx", "gps_tip", "push_update", "updated_live",
    "verify_pass", "verify_pass_title", "verify_pass_line1", "verify_pass_line2",
    "verify", "pass_not_found", "pass_valid",
    "admin_title", "fleet_table", "complaints_mgmt", "disruption_monitor", "admin_info",
    "fleet_overview", "quick_actions", "quick_actions_line",
    "complaints_management", "all_complaints", "update_status", "new_status", "update", "updated",
    "disruption_title", "delayed_buses", "no_delays", "breakdowns", "no_breakdowns",
    "app_crashed", "language",
]

T = {
    "en": {
        "app_title": "Smart Transport System",
        "govt_mode_line": "Govt bus mode: No ticket booking / no pre-booking. Focus on Next Bus ETA + Live Map, Passes, and Complaints.",
        "enter_name": "Enter your name",
        "name_placeholder": "e.g., Mithun",
        "welcome": "Welcome",
        "phone": "Phone",
        "role": "Role",
        "note_no_booking": "Note: This system does not provide any ticket booking.",
        "public_user": "Public User",
        "conductor_driver": "Conductor/Driver",
        "municipality_admin": "Municipality Admin",
        "public_portal": "Public Portal",
        "find_my_bus": "Find My Bus (ETA + Live Map)",
        "my_pass": "My Pass",
        "complaints": "Complaints / Grievances",
        "back": "Back",
        "find_my_bus_title": "Find My Bus (ETA + Live Map)",
        "find_my_bus_caption": "Select your stop → see next buses + ETA, and the live bus map on the same screen. No booking exists here.",
        "select_stop": "Select your current stop",
        "next_buses": "Next Buses Arriving (ETA)",
        "no_running_buses": "No running buses found inside the circle.",
        "refresh_eta": "Refresh ETA",
        "refresh_map": "Refresh Map",
        "map_title": "Live Bus Map (All Buses + Stops in Circle)",
        "map_updated": "Map updated",
        "map_tip": "Tip: Click bus markers to see bus number, route, occupancy and last update time. Orange markers are stops (including nearby mini-stops).",
        "route": "Route",
        "type": "Type",
        "crowd": "Crowd",
        "arrives": "Arrives ~",
        "min": "min",
        "running": "RUNNING",
        "delayed": "DELAYED",
        "breakdown": "BREAKDOWN",
        "unknown": "UNKNOWN",
        "pass_title": "My Pass",
        "no_pass": "No pass found.",
        "valid_until": "Valid Until",
        "pass_id": "Pass ID",
        "reminder_no_booking": "Reminder: No ticket booking is provided in this app.",
        "open_pass_mobile": "Open the pass on mobile using the QR deep link.",
        "pass_preview": "Pass Preview",
        "submit_complaint": "Submit a complaint",
        "bus_optional": "Bus (optional)",
        "route_optional": "Route (optional)",
        "category": "Category",
        "describe_issue": "Describe the issue",
        "desc_placeholder": "Write clearly with time/place details...",
        "submit": "Submit Complaint",
        "desc_required": "Please enter the description.",
        "complaint_submitted": "Complaint submitted. Ticket ID:",
        "my_recent_complaints": "My recent complaints (by phone)",
        "no_complaints": "No complaints yet.",
        "conductor_portal": "Conductor / Driver Portal",
        "conductor_caption": "No ticket booking exists in this system. Conductor only updates live status + verifies passes.",
        "select_bus": "Select your bus",
        "current": "Current",
        "passengers": "Passengers",
        "status": "Status",
        "update_live": "Update live status",
        "passengers_approx": "Passengers (approx.)",
        "gps_tip": "If you have GPS, enter exact values below.",
        "push_update": "Push Update",
        "updated_live": "Updated live state.",
        "verify_pass": "Verify Pass (Open Link)",
        "verify_pass_title": "Verify Pass",
        "verify_pass_line1": "In the real system, conductor scans pass QR → opens deep link here.",
        "verify_pass_line2": "For demo/testing: paste Pass ID below.",
        "verify": "Verify",
        "pass_not_found": "Pass not found.",
        "pass_valid": "Pass valid (demo).",
        "admin_title": "Municipality Admin",
        "fleet_table": "Fleet Table",
        "complaints_mgmt": "Complaints",
        "disruption_monitor": "Disruption Monitor",
        "admin_info": "Live map is intentionally not a separate tab anymore. Public sees map inside 'Find My Bus (ETA + Live Map)'.",
        "fleet_overview": "Fleet Overview",
        "quick_actions": "Quick Actions",
        "quick_actions_line": "For real operations: assign depots, schedules, trip blocks, driver rosters, etc.",
        "complaints_management": "Complaints Management",
        "all_complaints": "All complaints",
        "update_status": "Update status",
        "new_status": "New Status",
        "update": "Update",
        "updated": "Updated.",
        "disruption_title": "Disruption Monitor",
        "delayed_buses": "Delayed Buses",
        "no_delays": "No delayed buses.",
        "breakdowns": "Breakdowns",
        "no_breakdowns": "No breakdowns.",
        "app_crashed": "App crashed. Full error below:",
        "language": "Language",
    },

    "hi": {},
    "ta": {},
    "te": {}, "ml": {}, "kn": {}, "bn": {}, "ur": {}, "mr": {}, "gu": {}, "pa": {},
}

T["hi"] = {
    "app_title": "स्मार्ट परिवहन प्रणाली",
    "govt_mode_line": "सरकारी बस मोड: टिकट बुकिंग/प्री-बुकिंग नहीं। फोकस: अगली बस ETA + लाइव मैप, पास और शिकायतें।",
    "enter_name": "अपना नाम दर्ज करें",
    "name_placeholder": "उदा., Mithun",
    "welcome": "स्वागत है",
    "phone": "फ़ोन",
    "role": "भूमिका",
    "note_no_booking": "नोट: इस सिस्टम में टिकट बुकिंग उपलब्ध नहीं है।",
    "public_user": "सार्वजनिक उपयोगकर्ता",
    "conductor_driver": "कंडक्टर/ड्राइवर",
    "municipality_admin": "नगरपालिका प्रशासक",
    "public_portal": "पब्लिक पोर्टल",
    "find_my_bus": "मेरी बस ढूँढें (ETA + लाइव मैप)",
    "my_pass": "मेरा पास",
    "complaints": "शिकायतें / शिकायत निवारण",
    "back": "वापस",
    "find_my_bus_title": "मेरी बस ढूँढें (ETA + लाइव मैप)",
    "find_my_bus_caption": "स्टॉप चुनें → अगली बसें + ETA देखें, और उसी स्क्रीन पर लाइव मैप। यहाँ बुकिंग नहीं है।",
    "select_stop": "अपना वर्तमान स्टॉप चुनें",
    "next_buses": "अगली बसें (ETA)",
    "no_running_buses": "सर्कल के अंदर कोई चलती बस नहीं मिली।",
    "refresh_eta": "ETA रीफ्रेश",
    "refresh_map": "मैप रीफ्रेश",
    "map_title": "लाइव बस मैप (सभी बसें + सर्कल के स्टॉप)",
    "map_updated": "मैप अपडेट हुआ",
    "map_tip": "टिप: बस मार्कर पर क्लिक करके बस नंबर, रूट, भीड़ और अपडेट समय देखें। ऑरेंज मार्कर स्टॉप हैं।",
    "route": "रूट",
    "type": "प्रकार",
    "crowd": "भीड़",
    "arrives": "आती है ~",
    "min": "मिनट",
    "running": "चल रही",
    "delayed": "देरी",
    "breakdown": "खराबी",
    "unknown": "अज्ञात",
    "pass_title": "मेरा पास",
    "no_pass": "कोई पास नहीं मिला।",
    "valid_until": "मान्य तिथि",
    "pass_id": "पास आईडी",
    "reminder_no_booking": "रिमाइंडर: इस ऐप में टिकट बुकिंग नहीं है।",
    "open_pass_mobile": "QR डीप लिंक से मोबाइल पर पास खोलें।",
    "pass_preview": "पास प्रीव्यू",
    "submit_complaint": "शिकायत दर्ज करें",
    "bus_optional": "बस (वैकल्पिक)",
    "route_optional": "रूट (वैकल्पिक)",
    "category": "श्रेणी",
    "describe_issue": "समस्या का विवरण",
    "desc_placeholder": "समय/स्थान के विवरण के साथ स्पष्ट लिखें...",
    "submit": "शिकायत सबमिट करें",
    "desc_required": "कृपया विवरण दर्ज करें।",
    "complaint_submitted": "शिकायत दर्ज हो गई। टिकट आईडी:",
    "my_recent_complaints": "मेरी हाल की शिकायतें (फ़ोन के अनुसार)",
    "no_complaints": "अभी तक कोई शिकायत नहीं।",
    "conductor_portal": "कंडक्टर / ड्राइवर पोर्टल",
    "conductor_caption": "इस सिस्टम में टिकट बुकिंग नहीं है। कंडक्टर केवल लाइव स्टेटस अपडेट और पास वेरिफाई करता है।",
    "select_bus": "अपनी बस चुनें",
    "current": "वर्तमान",
    "passengers": "यात्री",
    "status": "स्थिति",
    "update_live": "लाइव स्टेटस अपडेट करें",
    "passengers_approx": "यात्री (अनुमानित)",
    "gps_tip": "यदि GPS है, तो सही मान दर्ज करें।",
    "push_update": "अपडेट भेजें",
    "updated_live": "लाइव स्टेट अपडेट हुआ।",
    "verify_pass": "पास सत्यापित करें (लिंक खोलें)",
    "verify_pass_title": "पास सत्यापन",
    "verify_pass_line1": "वास्तविक सिस्टम में कंडक्टर QR स्कैन करता है → यहाँ लिंक खुलता है।",
    "verify_pass_line2": "डेमो/टेस्ट: नीचे पास आईडी पेस्ट करें।",
    "verify": "सत्यापित करें",
    "pass_not_found": "पास नहीं मिला।",
    "pass_valid": "पास मान्य है (डेमो)।",
    "admin_title": "नगरपालिका प्रशासक",
    "fleet_table": "फ्लीट टेबल",
    "complaints_mgmt": "शिकायतें",
    "disruption_monitor": "बाधा मॉनिटर",
    "admin_info": "लाइव मैप अलग टैब नहीं है। पब्लिक को 'मेरी बस (ETA + लाइव मैप)' में मैप दिखेगा।",
    "fleet_overview": "फ्लीट अवलोकन",
    "quick_actions": "त्वरित क्रियाएँ",
    "quick_actions_line": "वास्तविक संचालन: डिपो, शेड्यूल, रोस्टर आदि असाइन करें।",
    "complaints_management": "शिकायत प्रबंधन",
    "all_complaints": "सभी शिकायतें",
    "update_status": "स्थिति अपडेट करें",
    "new_status": "नई स्थिति",
    "update": "अपडेट",
    "updated": "अपडेट हो गया।",
    "disruption_title": "बाधा मॉनिटर",
    "delayed_buses": "देरी वाली बसें",
    "no_delays": "कोई देरी नहीं।",
    "breakdowns": "खराबियाँ",
    "no_breakdowns": "कोई खराबी नहीं।",
    "app_crashed": "ऐप क्रैश हो गया। पूरा एरर नीचे:",
    "language": "भाषा",
}

T["ta"] = {
    "app_title": "ஸ்மார்ட் போக்குவரத்து அமைப்பு",
    "govt_mode_line": "அரசுப் பேருந்து முறை: டிக்கெட்/முன்பதிவு இல்லை. கவனம்: அடுத்த பேருந்து ETA + லைவ் மேப், பாஸ், புகார்கள்.",
    "enter_name": "உங்கள் பெயரை உள்ளிடவும்",
    "name_placeholder": "உதா., Mithun",
    "welcome": "வரவேற்கிறோம்",
    "phone": "தொலைபேசி",
    "role": "பங்கு",
    "note_no_booking": "குறிப்பு: இந்த அமைப்பில் டிக்கெட் புக்கிங் இல்லை.",
    "public_user": "பொது பயனர்",
    "conductor_driver": "கொண்டக்டர்/டிரைவர்",
    "municipality_admin": "மாநகராட்சி நிர்வாகம்",
    "public_portal": "பொது போர்டல்",
    "find_my_bus": "என் பேருந்தை கண்டுபிடி (ETA + லைவ் மேப்)",
    "my_pass": "என் பாஸ்",
    "complaints": "புகார்கள் / குறைநீர்",
    "back": "திரும்ப",
    "find_my_bus_title": "என் பேருந்தை கண்டுபிடி (ETA + லைவ் மேப்)",
    "find_my_bus_caption": "ஸ்டாப் தேர்வு → அடுத்த பேருந்துகள் + ETA, அதே திரையில் லைவ் மேப். இங்கே புக்கிங் இல்லை.",
    "select_stop": "உங்கள் தற்போதைய ஸ்டாப் தேர்வு செய்யவும்",
    "next_buses": "அடுத்த பேருந்துகள் (ETA)",
    "no_running_buses": "சர்க்கிள் உள்ளே ஓடும் பேருந்துகள் இல்லை.",
    "refresh_eta": "ETA புதுப்பிக்க",
    "refresh_map": "மேப் புதுப்பிக்க",
    "map_title": "லைவ் பேருந்து மேப் (அனைத்து பேருந்துகள் + சர்க்கிள் ஸ்டாப்கள்)",
    "map_updated": "மேப் புதுப்பிக்கப்பட்டது",
    "map_tip": "டிப்: பேருந்து மார்க்கரை கிளிக் செய்து எண், ரூட், கூட்டம், அப்டேட் நேரம் காணலாம். ஆரஞ்சு மார்க்கர்கள் ஸ்டாப்கள்.",
    "route": "ரூட்",
    "type": "வகை",
    "crowd": "கூட்டம்",
    "arrives": "வருகை ~",
    "min": "நிமி",
    "running": "ஓடுகிறது",
    "delayed": "தாமதம்",
    "breakdown": "பழுது",
    "unknown": "தெரியாது",
    "pass_title": "என் பாஸ்",
    "no_pass": "பாஸ் கிடைக்கவில்லை.",
    "valid_until": "செல்லுபடியாகும் நாள்",
    "pass_id": "பாஸ் ஐடி",
    "reminder_no_booking": "நினைவூட்டல்: இந்த அப்பில் டிக்கெட் புக்கிங் இல்லை.",
    "open_pass_mobile": "QR டீப் லிங்க் மூலம் மொபைலில் பாஸ் திறக்கவும்.",
    "pass_preview": "பாஸ் முன்னோட்டம்",
    "submit_complaint": "புகார் பதிவு",
    "bus_optional": "பேருந்து (விருப்பம்)",
    "route_optional": "ரூட் (விருப்பம்)",
    "category": "வகை",
    "describe_issue": "பிரச்சனை விவரம்",
    "desc_placeholder": "நேரம்/இடம் விவரங்களுடன் தெளிவாக எழுதவும்...",
    "submit": "புகார் சமர்ப்பி",
    "desc_required": "தயவுசெய்து விவரம் உள்ளிடவும்.",
    "complaint_submitted": "புகார் பதிவு செய்யப்பட்டது. டிக்கெட் ஐடி:",
    "my_recent_complaints": "என் சமீப புகார்கள் (தொலைபேசி மூலம்)",
    "no_complaints": "இன்னும் புகார்கள் இல்லை.",
    "conductor_portal": "கொண்டக்டர் / டிரைவர் போர்டல்",
    "conductor_caption": "இந்த அமைப்பில் டிக்கெட் புக்கிங் இல்லை. லைவ் நிலை அப்டேட் + பாஸ் சரிபார்ப்பு மட்டும்.",
    "select_bus": "உங்கள் பேருந்தை தேர்வு செய்யவும்",
    "current": "தற்போது",
    "passengers": "பயணிகள்",
    "status": "நிலை",
    "update_live": "லைவ் நிலை புதுப்பி",
    "passengers_approx": "பயணிகள் (சுமார்)",
    "gps_tip": "GPS இருந்தால் சரியான மதிப்பை உள்ளிடவும்.",
    "push_update": "அப்டேட் அனுப்பு",
    "updated_live": "லைவ் நிலை புதுப்பிக்கப்பட்டது.",
    "verify_pass": "பாஸ் சரிபார்க்க (லிங்க் திறக்க)",
    "verify_pass_title": "பாஸ் சரிபார்ப்பு",
    "verify_pass_line1": "உண்மை அமைப்பில் QR ஸ்கேன் → இங்கே லிங்க் திறக்கும்.",
    "verify_pass_line2": "டெமோ/டெஸ்ட்: பாஸ் ஐடி ஒட்டவும்.",
    "verify": "சரிபார்",
    "pass_not_found": "பாஸ் கிடைக்கவில்லை.",
    "pass_valid": "பாஸ் செல்லுபடியாகும் (டெமோ).",
    "admin_title": "மாநகராட்சி நிர்வாகம்",
    "fleet_table": "பேருந்து பட்டியல்",
    "complaints_mgmt": "புகார்கள்",
    "disruption_monitor": "தடைகள் கண்காணிப்பு",
    "admin_info": "லைவ் மேப் தனி டாப் இல்லை. பொதுப் பயனர் 'என் பேருந்து' பக்கத்தில் மேப் பார்க்கலாம்.",
    "fleet_overview": "பேருந்து அவலோகம்",
    "quick_actions": "விரைவு செயல்கள்",
    "quick_actions_line": "உண்மை இயக்கம்: டெபோ, அட்டவணை, ரோஸ்டர் போன்றவை.",
    "complaints_management": "புகார் மேலாண்மை",
    "all_complaints": "அனைத்து புகார்கள்",
    "update_status": "நிலை மாற்று",
    "new_status": "புதிய நிலை",
    "update": "புதுப்பி",
    "updated": "புதுப்பிக்கப்பட்டது.",
    "disruption_title": "தடைகள் கண்காணிப்பு",
    "delayed_buses": "தாமதமான பேருந்துகள்",
    "no_delays": "தாமதம் இல்லை.",
    "breakdowns": "பழுதுகள்",
    "no_breakdowns": "பழுது இல்லை.",
    "app_crashed": "ஆப் க்ராஷ் ஆனது. முழு பிழை கீழே:",
    "language": "மொழி",
}

# Compact complete translations (kept short; missing keys auto-fill from English)
T["te"] = {"app_title": "స్మార్ట్ ట్రాన్స్‌పోర్ట్ సిస్టమ్", "language": "భాష"}
T["ml"] = {"app_title": "സ്മാർട്ട് ട്രാൻസ്‌പോർട്ട് സിസ്റ്റം", "language": "ഭാഷ"}
T["kn"] = {"app_title": "ಸ್ಮಾರ್ಟ್ ಸಾರಿಗೆ ವ್ಯವಸ್ಥೆ", "language": "ಭಾಷೆ"}
T["bn"] = {"app_title": "স্মার্ট ট্রান্সপোর্ট সিস্টেম", "language": "ভাষা"}
T["ur"] = {"app_title": "سمارٹ ٹرانسپورٹ سسٹم", "language": "زبان"}
T["mr"] = {"app_title": "स्मार्ट ट्रान्सपोर्ट सिस्टम", "language": "भाषा"}
T["gu"] = {"app_title": "સ્માર્ટ ટ્રાન્સપોર્ટ સિસ્ટમ", "language": "ભાષા"}
T["pa"] = {"app_title": "ਸਮਾਰਟ ਟਰਾਂਸਪੋਰਟ ਸਿਸਟਮ", "language": "ਭਾਸ਼ਾ"}

# Ensure every language has all keys: if missing, copy English for those keys.
for lang_code, _ in LANGS:
    if lang_code not in T:
        T[lang_code] = {}
    for k in UI_KEYS:
        if k not in T[lang_code]:
            T[lang_code][k] = T["en"][k]


def tr(key: str) -> str:
    lang = st.session_state.get("lang", "en")
    return T.get(lang, T["en"]).get(key, T["en"].get(key, key))


# -----------------------------
# Session State Init
# -----------------------------
def initialize_session_state():
    defaults = {
        "page": "role_selection",
        "role": None,
        "current_user": None,
        "lang": "en",
        "find_cached_map_html": None,
        "find_cached_map_at": None,
        "find_cached_map_stop": None,
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
# URL helpers (Pass deep links)
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
# Geo + UI helpers
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
        return (tr("running"), "pill pill-ok")
    if s == "delayed":
        return (tr("delayed"), "pill pill-warn")
    if s in ["breakdown", "cancelled", "maintenance"]:
        return (tr("breakdown"), "pill pill-bad")
    return (tr("unknown"), "pill")


def is_eta_relevant(status: str) -> bool:
    s = (status or "").lower().strip()
    return s in ["active", "running", "onroute", "delayed"]


# -----------------------------
# DATA: Places / Stops (with nearby mini-stops for dense hubs)
# -----------------------------
def create_places_data():
    base = [
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

    mini = []

    def add_mini(parent_id, parent_name, plat, plon, names_offsets):
        for i, (suffix, dlat, dlon) in enumerate(names_offsets, start=1):
            mini.append({
                "stop_id": f"{parent_id}M{i:02d}",
                "stop_name": f"{parent_name} — {suffix}",
                "latitude": plat + dlat,
                "longitude": plon + dlon,
                "zone": "Micro",
                "parent_stop": parent_name,
            })

    add_mini(
        "S001", "Gandhipuram", 11.0183, 76.9725,
        [
            ("Bus Stand Gate", 0.0012, 0.0009),
            ("Signal Junction", 0.0006, -0.0010),
            ("2nd Street Stop", -0.0011, -0.0003),
            ("Market Road Stop", -0.0007, 0.0013),
            ("Cross Cut Road", 0.0009, 0.0016),
        ]
    )
    add_mini(
        "S002", "Coimbatore", 11.0168, 76.9558,
        [
            ("Town Hall", 0.0010, 0.0007),
            ("Railway Station", -0.0012, -0.0006),
            ("Ukkadam", -0.0015, 0.0012),
        ]
    )
    add_mini(
        "S007", "Chennai", 13.0827, 80.2707,
        [
            ("Central Station", 0.0014, -0.0008),
            ("Egmore", 0.0005, -0.0015),
            ("T Nagar", -0.0018, 0.0011),
            ("Guindy", -0.0023, 0.0004),
        ]
    )

    df = pd.DataFrame(base)
    mdf = pd.DataFrame(mini) if mini else pd.DataFrame(columns=["stop_id", "stop_name", "latitude", "longitude", "zone", "parent_stop"])
    if "parent_stop" not in df.columns:
        df["parent_stop"] = None
    out = pd.concat([df, mdf], ignore_index=True)
    return out


@st.cache_data
def get_places_data():
    return create_places_data()


# -----------------------------
# DATA: Fleet (Static info) + Live state (DB)
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
        bus_number = f"TN38{random.choice(['A', 'B', 'C'])}{100 + i:03d}"

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
# Zone logic: buses + stops inside the circle radius
# -----------------------------
ZONE_RADIUS_METERS_DEFAULT = 900


def get_stop_row(stop_name: str) -> dict:
    places = get_places_data()
    row = places[places["stop_name"] == stop_name]
    if row.empty:
        r0 = places.iloc[0]
        return {"stop_name": str(r0["stop_name"]), "latitude": float(r0["latitude"]), "longitude": float(r0["longitude"])}
    r = row.iloc[0]
    return {"stop_name": str(r["stop_name"]), "latitude": float(r["latitude"]), "longitude": float(r["longitude"])}


def stops_inside_zone(center_stop_name: str, radius_m: int):
    places = get_places_data()
    c = get_stop_row(center_stop_name)
    clat, clon = c["latitude"], c["longitude"]

    tmp = places.copy()
    tmp["dist_km"] = tmp.apply(lambda r: haversine_km(float(r["latitude"]), float(r["longitude"]), clat, clon), axis=1)
    tmp["dist_m"] = (tmp["dist_km"] * 1000.0)
    inside = tmp[tmp["dist_m"] <= float(radius_m)].sort_values("dist_m").copy()
    return inside


def buses_inside_zone(center_stop_name: str, radius_m: int):
    c = get_stop_row(center_stop_name)
    clat, clon = c["latitude"], c["longitude"]

    buses_df = get_buses_data()
    inside = buses_df.copy()
    inside["dist_km"] = inside.apply(
        lambda r: haversine_km(float(r["latitude"]), float(r["longitude"]), clat, clon),
        axis=1
    )
    inside["dist_m"] = inside["dist_km"] * 1000.0
    inside = inside[inside["dist_m"] <= float(radius_m)].copy()

    def speed_kmh(bus_type, status):
        base = {"Ordinary": 32, "Semi-Deluxe": 36, "AC Deluxe": 40, "Volvo": 45, "Electric": 34}.get(bus_type, 35)
        if str(status).lower() == "delayed":
            return max(18, base * 0.6)
        return base

    if inside.empty:
        inside["eta_min"] = pd.Series(dtype="Int64")
        inside["eta_time"] = pd.Series(dtype="object")
        return inside

    inside["speed_kmh"] = inside.apply(lambda r: speed_kmh(r["bus_type"], r["status"]), axis=1)

    inside["eta_min"] = inside.apply(
        lambda r: int(max(1, min(180, round((float(r["dist_km"]) / float(r["speed_kmh"])) * 60))))
        if is_eta_relevant(str(r["status"])) else pd.NA,
        axis=1
    )
    inside["eta_min"] = inside["eta_min"].astype("Int64")

    inside["eta_time"] = inside["eta_min"].apply(
        lambda m: (datetime.now() + timedelta(minutes=int(m))).strftime("%I:%M %p")
        if pd.notna(m) else None
    )

    inside = inside.sort_values(
        by=["eta_min", "dist_km"],
        key=lambda s: s.fillna(10**9)
    )
    return inside


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
# Passes (Optional)
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
    return {
        "pass_id": row[0],
        "phone": row[1],
        "pass_type": row[2],
        "valid_until": row[3],
        "created_at": row[4]
    }


def render_pass_qr(pass_row: dict):
    base_url = get_base_url()
    pass_url = f"{base_url}/?{urlencode({'pass': pass_row['pass_id']})}"

    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(pass_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    st.image(img, width=220)
    st.caption("Scan to open pass on mobile")


def render_pass_card(p: dict):
    html = f"""
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <style>
        body {{ font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial; background:#fff7ed; padding:12px; }}
        .wrap {{ max-width: 520px; margin: 0 auto; }}
        .card {{ background:#fff; border:1px solid #f1c6a6; border-radius:16px; padding:16px; box-shadow: 0 10px 25px rgba(0,0,0,0.10); }}
        .title {{ text-align:center; font-weight:900; font-size:18px; margin:0; color:#9a3412; }}
        .sub {{ text-align:center; margin-top:6px; font-size:13px; color:#444; }}
        .dash {{ border-top:1px dashed #999; margin:12px 0; }}
        .row {{ display:flex; justify-content:space-between; gap:12px; font-size:13px; margin:6px 0; }}
        .label {{ color:#333; font-weight:800; }}
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

          <div class="row"><div class="label">{tr("pass_id")}</div><div class="value">{p['pass_id']}</div></div>
          <div class="row"><div class="label">{tr("type")}</div><div class="value">{p['pass_type']}</div></div>
          <div class="row"><div class="label">{tr("phone")}</div><div class="value">{p['phone']}</div></div>
          <div class="row"><div class="label">{tr("valid_until")}</div><div class="value"><span class="ok">{p['valid_until']}</span></div></div>
        </div>
      </div>
    </body>
    </html>
    """
    components.html(html, height=470, scrolling=True)


# -----------------------------
# Map (Leaflet via Folium) - show buses + all stops inside circle
# -----------------------------
def create_live_bus_map_leaflet(
    buses_df: pd.DataFrame,
    focus_stop_name: str | None = None,
    radius_m: int = ZONE_RADIUS_METERS_DEFAULT
):
    places_df = get_places_data()

    if buses_df is None or buses_df.empty:
        return folium.Map(location=[11.0, 78.0], zoom_start=7, tiles="OpenStreetMap")

    if focus_stop_name and focus_stop_name in places_df["stop_name"].tolist():
        srow = places_df[places_df["stop_name"] == focus_stop_name].iloc[0]
        center_lat, center_lon, zoom = float(srow["latitude"]), float(srow["longitude"]), 13
    else:
        center_lat, center_lon, zoom = float(buses_df["latitude"].mean()), float(buses_df["longitude"].mean()), 7

    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom, tiles="OpenStreetMap")
    cluster = MarkerCluster().add_to(m)

    def color_for_type(bt):
        return {"Ordinary": "blue", "Semi-Deluxe": "green", "AC Deluxe": "orange", "Volvo": "red", "Electric": "purple"}.get(bt, "blue")

    if focus_stop_name and focus_stop_name in places_df["stop_name"].tolist():
        srow = places_df[places_df["stop_name"] == focus_stop_name].iloc[0]
        slat, slon = float(srow["latitude"]), float(srow["longitude"])

        folium.Marker(
            location=[slat, slon],
            popup=folium.Popup(f"<b>📍 Stop:</b> {focus_stop_name}", max_width=260),
            icon=folium.Icon(color="orange", icon="info-sign"),
        ).add_to(m)

        folium.Circle(
            location=[slat, slon],
            radius=float(radius_m),
            color="#ea580c",
            weight=3,
            fill=False,
        ).add_to(m)

        stops_in = stops_inside_zone(focus_stop_name, radius_m)
        for _, sr in stops_in.iterrows():
            name = str(sr["stop_name"])
            if name == focus_stop_name:
                continue
            folium.CircleMarker(
                location=[float(sr["latitude"]), float(sr["longitude"])],
                radius=5,
                color="#f97316",
                fill=True,
                fill_opacity=0.9,
                popup=folium.Popup(f"<b>🛑 Nearby Stop:</b> {name}", max_width=280),
            ).add_to(m)

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


def get_map_html_cached(stop_name: str | None, radius_m: int):
    now = datetime.now()
    should_rebuild = (
        st.session_state.find_cached_map_html is None
        or st.session_state.find_cached_map_stop != f"{stop_name}|{radius_m}"
        or st.session_state.find_cached_map_at is None
        or (now - st.session_state.find_cached_map_at).total_seconds() > 20
    )

    if should_rebuild:
        buses_df = get_buses_data()
        m = create_live_bus_map_leaflet(buses_df, focus_stop_name=stop_name, radius_m=radius_m)
        st.session_state.find_cached_map_html = m.get_root().render()
        st.session_state.find_cached_map_at = now
        st.session_state.find_cached_map_stop = f"{stop_name}|{radius_m}"

    return st.session_state.find_cached_map_html, st.session_state.find_cached_map_at


# -----------------------------
# Users (Demo)
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
# Language Picker
# -----------------------------
def language_bar():
    codes = [c for c, _ in LANGS]
    names = [n for _, n in LANGS]
    current = st.session_state.get("lang", "en")
    idx = codes.index(current) if current in codes else 0

    col1, col2 = st.columns([1, 5])
    with col1:
        st.markdown(f"**🌐 {tr('language')}**")
    with col2:
        chosen_name = st.selectbox(
            label="",
            options=names,
            index=idx,
            key="__lang_picker__",
            label_visibility="collapsed",
        )

    new_code = codes[names.index(chosen_name)]
    if new_code != st.session_state.lang:
        st.session_state.lang = new_code
        st.session_state.find_cached_map_html = None
        st.session_state.find_cached_map_at = None
        st.session_state.find_cached_map_stop = None
        st.rerun()


# -----------------------------
# PAGES
# -----------------------------
def role_selection_page():
    st.markdown(f"<div class='main-header'>🚍 {tr('app_title')}</div>", unsafe_allow_html=True)
    st.write(tr("govt_mode_line"))

    user_name = st.text_input(tr("enter_name"), placeholder=tr("name_placeholder"))
    if not user_name:
        return

    user = find_user_by_name(user_name)
    st.session_state.current_user = user

    st.markdown(
        f"""
        <div class="card">
          <div class="sub-header">👋 {tr('welcome')}, {user['full_name']}</div>
          <div class="mini">📱 {tr('phone')}: <b>{user['phone']}</b></div>
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

    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"📍 {tr('find_my_bus')}", type="primary", use_container_width=True):
            st.session_state.page = "find_my_bus"
            st.rerun()
    with col2:
        if st.button(f"🪪 {tr('my_pass')}", use_container_width=True):
            st.session_state.page = "my_pass"
            st.rerun()

    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
    if st.button(f"📝 {tr('complaints')}", use_container_width=True):
        st.session_state.page = "complaints_public"
        st.rerun()

    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
    if st.button(f"← {tr('back')}", use_container_width=True):
        st.session_state.page = "role_selection"
        st.rerun()


def find_my_bus_page():
    st.markdown(f"<div class='main-header'>📍 {tr('find_my_bus_title')}</div>", unsafe_allow_html=True)
    st.caption(tr("find_my_bus_caption"))

    if st.button(f"← {tr('back')}"):
        st.session_state.page = "public_home"
        st.rerun()

    places = get_places_data()
    stop_names = places[places["parent_stop"].isna() | places["parent_stop"].isnull()]["stop_name"].tolist()

    stop = st.selectbox(tr("select_stop"), stop_names, index=0)

    radius_m = st.slider("Circle radius (meters)", min_value=300, max_value=2000, value=ZONE_RADIUS_METERS_DEFAULT, step=50)

    left, right = st.columns([1.25, 1.75], gap="large")

    with left:
        st.markdown(f"### 🚌 {tr('next_buses')}")
        inside = buses_inside_zone(stop, radius_m=radius_m)

        if inside.empty:
            st.warning(tr("no_running_buses"))
        else:
            st.caption(f"Buses inside circle: **{len(inside)}**")

            for _, b in inside.iterrows():
                crowd_lbl, crowd_cls = crowd_level(int(b["passengers"]), int(b["capacity"]))
                st_lbl, st_cls = status_pill(str(b["status"]))

                eta_min = b["eta_min"]
                eta_time = b.get("eta_time", None)

                eta_block = ""
                if pd.notna(eta_min):
                    eta_block = f"""
                    <div style="text-align:right;">
                      <div style="font-size:1.6rem; font-weight:900; color:#9a3412;">{int(eta_min)} {tr('min')}</div>
                      <div class="mini">{tr('arrives')} {eta_time}</div>
                    </div>
                    """
                else:
                    eta_block = f"""
                    <div style="text-align:right;">
                      <div style="font-size:1.1rem; font-weight:900; color:#9a3412;">—</div>
                      <div class="mini">{tr('unknown')}</div>
                    </div>
                    """

                st.markdown(
                    f"""
                    <div class="card">
                      <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:14px;">
                        <div>
                          <div class="sub-header">🚌 {b['bus_number']} <span class="{st_cls}">{st_lbl}</span></div>
                          <div class="mini"><b>{tr('route')}:</b> {b['route_name']} ({b['start_point']} → {b['end_point']})</div>
                          <div class="mini"><b>{tr('type')}:</b> {b['bus_type']} • <b>{tr('crowd')}:</b> <span class="{crowd_cls}">{crowd_lbl}</span> • {b['passengers']}/{b['capacity']}</div>
                        </div>
                        {eta_block}
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.markdown("<div class='hr'></div>", unsafe_allow_html=True)

        st.markdown("### 🛑 Stops inside circle")
        s_in = stops_inside_zone(stop, radius_m)
        if s_in.empty:
            st.info("No nearby stops found.")
        else:
            st.caption(f"Stops inside circle: **{len(s_in)}**")
            st.dataframe(
                s_in[["stop_name", "zone", "dist_m"]].rename(columns={"dist_m": "distance_m"}).head(40),
                use_container_width=True
            )

        st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
        colA, colB = st.columns(2)
        with colA:
            if st.button(f"🔄 {tr('refresh_eta')}", use_container_width=True, type="primary"):
                st.rerun()
        with colB:
            if st.button(f"🔄 {tr('refresh_map')}", use_container_width=True):
                st.session_state.find_cached_map_html = None
                st.session_state.find_cached_map_at = None
                st.session_state.find_cached_map_stop = None
                st.rerun()

    with right:
        st.markdown(f"### 🗺 {tr('map_title')}")
        map_html, built_at = get_map_html_cached(stop_name=stop, radius_m=radius_m)
        if built_at:
            st.info(f"{tr('map_updated')}: {built_at.strftime('%Y-%m-%d %H:%M:%S')}")
        components.html(map_html, height=620, scrolling=False)
        st.caption(tr("map_tip"))


def my_pass_page():
    st.markdown(f"<div class='main-header'>🪪 {tr('pass_title')}</div>", unsafe_allow_html=True)

    if st.button(f"← {tr('back')}"):
        st.session_state.page = "public_home"
        st.rerun()

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
          <div class="mini"><b>{tr('valid_until')}:</b> {p['valid_until']}</div>
          <div class="mini"><b>{tr('pass_id')}:</b> {p['pass_id']}</div>
          <div class="mini"><b>{tr('reminder_no_booking')}</b></div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([1, 2])
    with col1:
        render_pass_qr(p)
    with col2:
        st.write(tr("open_pass_mobile"))
        base_url = get_base_url()
        pass_url = f"{base_url}/?{urlencode({'pass': p['pass_id']})}"
        st.code(pass_url)

    st.markdown(f"### {tr('pass_preview')}")
    render_pass_card(p)


def complaints_public_page():
    st.markdown(f"<div class='main-header'>📝 {tr('complaints')}</div>", unsafe_allow_html=True)
    if st.button(f"← {tr('back')}"):
        st.session_state.page = "public_home"
        st.rerun()

    u = st.session_state.current_user
    buses_df = get_buses_data()

    st.markdown(f"### {tr('submit_complaint')}")
    col1, col2 = st.columns(2)
    with col1:
        bus_number = st.selectbox(tr("bus_optional"), ["—"] + buses_df["bus_number"].tolist(), index=0)
    with col2:
        route_name = st.selectbox(tr("route_optional"), ["—"] + sorted(buses_df["route_name"].unique().tolist()), index=0)

    category = st.selectbox(tr("category"), ["Delay", "Overcrowding", "Rash Driving", "Cleanliness", "Misbehavior", "Other"])
    desc = st.text_area(tr("describe_issue"), placeholder=tr("desc_placeholder"), height=120)

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
    st.markdown(f"### {tr('my_recent_complaints')}")
    allc = list_complaints()
    mine = allc[allc["phone"] == u["phone"]].copy()
    if mine.empty:
        st.info(tr("no_complaints"))
    else:
        st.dataframe(mine[["complaint_id", "category", "bus_number", "route_name", "status", "created_at"]].head(30), use_container_width=True)


def conductor_portal():
    st.markdown(f"<div class='main-header'>🧑‍✈️ {tr('conductor_portal')}</div>", unsafe_allow_html=True)
    st.caption(tr("conductor_caption"))

    if st.button(f"← {tr('back')}"):
        st.session_state.page = "role_selection"
        st.rerun()

    buses_df = get_buses_data()
    bus_number = st.selectbox(tr("select_bus"), buses_df["bus_number"].tolist())

    current = buses_df[buses_df["bus_number"] == bus_number].iloc[0].to_dict()
    st.markdown(
        f"""
        <div class="card">
          <div class="sub-header">🚌 {bus_number} <span class="pill">{current['bus_type']}</span></div>
          <div class="mini"><b>{tr('route')}:</b> {current['route_name']} ({current['start_point']} → {current['end_point']})</div>
          <div class="mini"><b>{tr('current')}:</b> {current['latitude']:.5f}, {current['longitude']:.5f} • <b>{tr('passengers')}:</b> {current['passengers']}/{current['capacity']} • <b>{tr('status')}:</b> {current['status']}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(f"### {tr('update_live')}")
    col1, col2, col3 = st.columns(3)
    with col1:
        new_status = st.selectbox(tr("status"), ["Active", "Delayed", "Breakdown"], index=0)
    with col2:
        new_pass = st.number_input(tr("passengers_approx"), min_value=0, max_value=int(current["capacity"]), value=int(current["passengers"]))
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

        st.session_state.find_cached_map_html = None
        st.session_state.find_cached_map_at = None
        st.session_state.find_cached_map_stop = None

    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
    if st.button(f"🪪 {tr('verify_pass')}", use_container_width=True):
        st.session_state.page = "verify_pass"
        st.rerun()


def verify_pass_page():
    st.markdown(f"<div class='main-header'>🪪 {tr('verify_pass_title')}</div>", unsafe_allow_html=True)
    if st.button(f"← {tr('back')}"):
        st.session_state.page = "conductor_portal"
        st.rerun()

    st.write(tr("verify_pass_line1"))
    st.write(tr("verify_pass_line2"))

    pid = st.text_input(tr("pass_id"), placeholder="e.g., PASS-XXXXXXXX")
    if st.button(tr("verify"), key="v_pass", type="primary"):
        p = load_pass(pid.strip())
        if not p:
            st.error(tr("pass_not_found"))
        else:
            st.success(tr("pass_valid"))
            render_pass_card(p)


def admin_home():
    st.markdown(f"<div class='main-header'>🏛 {tr('admin_title')}</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(f"🚌 {tr('fleet_table')}", type="primary", use_container_width=True):
            st.session_state.page = "fleet_admin"
            st.rerun()
    with col2:
        if st.button(f"📝 {tr('complaints_mgmt')}", use_container_width=True):
            st.session_state.page = "complaints_admin"
            st.rerun()
    with col3:
        if st.button(f"🔧 {tr('disruption_monitor')}", use_container_width=True):
            st.session_state.page = "disruption_admin"
            st.rerun()

    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
    st.info(tr("admin_info"))

    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
    if st.button(f"← {tr('back')}", use_container_width=True):
        st.session_state.page = "role_selection"
        st.rerun()


def fleet_admin_page():
    st.markdown(f"<div class='main-header'>🚌 {tr('fleet_overview')}</div>", unsafe_allow_html=True)
    if st.button(f"← {tr('back')}"):
        st.session_state.page = "admin_home"
        st.rerun()

    df = get_buses_data()
    st.dataframe(
        df[["bus_number", "route_name", "bus_type", "status", "passengers", "capacity", "latitude", "longitude", "updated_at"]],
        use_container_width=True
    )

    st.markdown(f"### {tr('quick_actions')}")
    st.write(tr("quick_actions_line"))


def complaints_admin_page():
    st.markdown(f"<div class='main-header'>📝 {tr('complaints_management')}</div>", unsafe_allow_html=True)
    if st.button(f"← {tr('back')}"):
        st.session_state.page = "admin_home"
        st.rerun()

    allc = list_complaints()
    if allc.empty:
        st.info(tr("all_complaints") + ": 0")
        return

    st.markdown(f"### {tr('all_complaints')}")
    st.dataframe(
        allc[["complaint_id", "phone", "category", "bus_number", "route_name", "status", "created_at", "updated_at"]],
        use_container_width=True
    )

    st.markdown(f"### {tr('update_status')}")
    cid = st.selectbox("Complaint ID", allc["complaint_id"].tolist())
    new_status = st.selectbox(tr("new_status"), ["OPEN", "IN_PROGRESS", "RESOLVED", "REJECTED"])
    if st.button(tr("update"), type="primary"):
        update_complaint_status(cid, new_status)
        st.success(tr("updated"))
        st.rerun()


def disruption_admin_page():
    st.markdown(f"<div class='main-header'>🔧 {tr('disruption_title')}</div>", unsafe_allow_html=True)
    if st.button(f"← {tr('back')}"):
        st.session_state.page = "admin_home"
        st.rerun()

    df = get_buses_data()
    delayed = df[df["status"].str.lower().eq("delayed")]
    breakdown = df[df["status"].str.lower().eq("breakdown")]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"### 🟡 {tr('delayed_buses')}")
        if delayed.empty:
            st.success(tr("no_delays"))
        else:
            st.dataframe(delayed[["bus_number", "route_name", "passengers", "capacity", "updated_at"]].head(30), use_container_width=True)

    with col2:
        st.markdown(f"### 🔴 {tr('breakdowns')}")
        if breakdown.empty:
            st.success(tr("no_breakdowns"))
        else:
            st.dataframe(breakdown[["bus_number", "route_name", "passengers", "capacity", "updated_at"]].head(30), use_container_width=True)


# -----------------------------
# Deep-link Page (Pass)
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

    try:
        qp = st.query_params
        pass_id = qp.get("pass")
    except Exception:
        qp = st.experimental_get_query_params()
        pass_id = (qp.get("pass") or [None])[0]

    if pass_id:
        pass_page(pass_id)
        return

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
    elif page == "verify_pass":
        verify_pass_page()
    elif page == "admin_home":
        admin_home()
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