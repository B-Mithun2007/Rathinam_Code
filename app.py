# app.py
# 🚍 SMART TRANSPORT SYSTEM (Govt Bus Mode: NO Ticket Booking / NO Pre-booking)
# ✅ Stop-first UX (Next buses list + Live map together)
# ✅ Public + Conductor + Municipality portals
# ✅ Complaints + Pass QR deep link
# ✅ Multilingual UI (ALL listed languages now have real translations)
#
# ✅ FIXES DONE (your issues):
# 1) "Next Buses Arriving (ETA)" now shows the EXACT number of buses inside the red circle (no hidden limit).
#    - It lists ALL buses inside the circle (even delayed/breakdown) so count matches map.
#    - ETA is shown only when meaningful (Active/Delayed). Otherwise, it shows "—".
#    - A count header shows: "Buses inside zone: X"
#
# 2) Stops can have multiple nearby sub-stops inside the same circle:
#    - Added sub-stops (platforms/stands) for big hubs like Gandhipuram, Chennai, Coimbatore, etc.
#    - Map shows ALL stops that fall inside the selected stop’s circle.
#
# 3) Languages fixed:
#    - English + Hindi + Tamil + Telugu + Malayalam + Kannada + Bengali + Urdu + Marathi + Gujarati + Punjabi
#    - No “blank” languages anymore.

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
# THEME
# -----------------------------
WARM_THEME_CSS = """
<style>
:root{
  --warm-1:#fff7ed;
  --warm-2:#ffedd5;
  --warm-4:#f97316;
  --warm-5:#ea580c;
  --warm-6:#9a3412;
  --card:#ffffff;
  --border:#f1c6a6;
  --shadow: 0 10px 25px rgba(0,0,0,0.08);
}
.stApp{ background: linear-gradient(180deg, var(--warm-1), #ffffff 65%); }
.main-header{
  font-size: 2.6rem; font-weight: 900; text-align:center;
  margin: 0.4rem 0 1.0rem 0; letter-spacing: -0.6px; color: var(--warm-6);
}
.sub-header{ font-size: 1.12rem; font-weight: 900; margin: 0.2rem 0; color: #2b2b2b; }
.card{
  background: var(--card); border: 1px solid var(--border); border-radius: 18px;
  padding: 1.0rem; box-shadow: var(--shadow); margin: 0.6rem 0;
}
.pill{
  display:inline-block; padding: 0.25rem 0.65rem; border-radius: 999px;
  font-weight: 900; font-size: 0.85rem; border: 1px solid var(--border);
  background: var(--warm-1); color: #2b2b2b;
}
.pill-ok{ background:#ecfdf5; border-color:#bbf7d0; color:#065f46; }
.pill-warn{ background:#fffbeb; border-color:#fde68a; color:#92400e; }
.pill-bad{ background:#fef2f2; border-color:#fecaca; color:#991b1b; }
.hr{ border-top: 1px solid rgba(0,0,0,0.08); margin: 0.9rem 0; }
div.stButton > button[kind="primary"]{
  background: linear-gradient(135deg, var(--warm-4), var(--warm-5)) !important;
  color: white !important; border: 0 !important; border-radius: 14px !important;
  font-weight: 900 !important;
}
div.stButton > button{ border-radius: 14px !important; font-weight: 900 !important; }
</style>
"""
st.markdown(WARM_THEME_CSS, unsafe_allow_html=True)

# -----------------------------
# STOP ZONE (same as red circle)
# -----------------------------
STOP_RADIUS_M = 900
STOP_RADIUS_KM = STOP_RADIUS_M / 1000.0


# -----------------------------
# Multilingual UI
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
    "find_my_bus_title", "find_my_bus_caption", "select_stop",
    "next_buses", "buses_in_zone", "zone_includes_stops", "no_buses_in_zone",
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

T = {}

# --- English (base truth) ---
T["en"] = {
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
    "find_my_bus_caption": "Select your stop → see buses inside the zone + ETA, and the live bus map on the same screen. No booking exists here.",
    "select_stop": "Select your current stop",
    "next_buses": "Next Buses Arriving (ETA)",
    "buses_in_zone": "Buses inside zone",
    "zone_includes_stops": "Zone includes nearby stops",
    "no_buses_in_zone": "No buses found inside the stop zone.",
    "refresh_eta": "Refresh List",
    "refresh_map": "Refresh Map",
    "map_title": "Live Bus Map (All Buses + Your Stop Zone)",
    "map_updated": "Map updated",
    "map_tip": "Tip: Click bus markers for bus number, route, occupancy and last update time.",
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
    "admin_info": "Public map is inside 'Find My Bus'. Admin uses fleet tables + complaints + disruption monitor.",
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
}

# --- Hindi ---
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
    "complaints": "शिकायतें / निवारण",
    "back": "वापस",
    "find_my_bus_title": "मेरी बस ढूँढें (ETA + लाइव मैप)",
    "find_my_bus_caption": "स्टॉप चुनें → ज़ोन के भीतर बसें + ETA देखें, और उसी स्क्रीन पर लाइव मैप। यहाँ बुकिंग नहीं है।",
    "select_stop": "अपना वर्तमान स्टॉप चुनें",
    "next_buses": "अगली बसें (ETA)",
    "buses_in_zone": "ज़ोन के भीतर बसें",
    "zone_includes_stops": "ज़ोन में पास के स्टॉप शामिल हैं",
    "no_buses_in_zone": "स्टॉप ज़ोन के भीतर कोई बस नहीं मिली।",
    "refresh_eta": "सूची रीफ्रेश",
    "refresh_map": "मैप रीफ्रेश",
    "map_title": "लाइव बस मैप (सभी बसें + आपका स्टॉप ज़ोन)",
    "map_updated": "मैप अपडेट हुआ",
    "map_tip": "टिप: बस मार्कर पर क्लिक करके बस नंबर, रूट, भीड़ और अपडेट समय देखें।",
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
    "verify_pass": "पास सत्यापित करें",
    "verify_pass_title": "पास सत्यापन",
    "verify_pass_line1": "वास्तविक सिस्टम में QR स्कैन → यहाँ लिंक खुलता है।",
    "verify_pass_line2": "डेमो/टेस्ट: नीचे पास आईडी पेस्ट करें।",
    "verify": "सत्यापित करें",
    "pass_not_found": "पास नहीं मिला।",
    "pass_valid": "पास मान्य है (डेमो)।",
    "admin_title": "नगरपालिका प्रशासक",
    "fleet_table": "फ्लीट टेबल",
    "complaints_mgmt": "शिकायतें",
    "disruption_monitor": "बाधा मॉनिटर",
    "admin_info": "पब्लिक मैप 'मेरी बस' के अंदर है। Admin: fleet + complaints + disruption monitor.",
    "fleet_overview": "फ्लीट अवलोकन",
    "quick_actions": "त्वरित क्रियाएँ",
    "quick_actions_line": "वास्तविक संचालन: डिपो, शेड्यूल, रोस्टर आदि।",
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

# --- Tamil ---
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
    "find_my_bus_caption": "ஸ்டாப் தேர்வு → மண்டலத்திற்குள் உள்ள பேருந்துகள் + ETA, அதே திரையில் லைவ் மேப். இங்கே புக்கிங் இல்லை.",
    "select_stop": "உங்கள் தற்போதைய ஸ்டாப் தேர்வு செய்யவும்",
    "next_buses": "அடுத்த பேருந்துகள் (ETA)",
    "buses_in_zone": "மண்டலத்திற்குள் பேருந்துகள்",
    "zone_includes_stops": "மண்டலம் அருகிலுள்ள ஸ்டாப்களையும் உள்ளடக்கும்",
    "no_buses_in_zone": "ஸ்டாப் மண்டலத்திற்குள் பேருந்துகள் இல்லை.",
    "refresh_eta": "பட்டியல் புதுப்பிக்க",
    "refresh_map": "மேப் புதுப்பிக்க",
    "map_title": "லைவ் பேருந்து மேப் (அனைத்து பேருந்துகள் + உங்கள் ஸ்டாப் மண்டலம்)",
    "map_updated": "மேப் புதுப்பிக்கப்பட்டது",
    "map_tip": "டிப்: பேருந்து மார்க்கரை கிளிக் செய்து எண், ரூட், கூட்டம், அப்டேட் நேரம் காணலாம்.",
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
    "verify_pass": "பாஸ் சரிபார்க்க",
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
    "admin_info": "பொது மேப் 'என் பேருந்து' பக்கத்தில் உள்ளது. Admin: fleet + complaints + disruption monitor.",
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

# --- Other languages (full coverage; concise but complete) ---
T["te"] = {
    "app_title":"స్మార్ట్ రవాణా వ్యవస్థ","govt_mode_line":"ప్రభుత్వ బస్ మోడ్: టికెట్ బుకింగ్/ప్రీ-బుకింగ్ లేదు. ఫోకస్: Next Bus ETA + Live Map, పాసులు, ఫిర్యాదులు.",
    "enter_name":"మీ పేరు నమోదు చేయండి","name_placeholder":"ఉదా., Mithun","welcome":"స్వాగతం","phone":"ఫోన్","role":"పాత్ర",
    "note_no_booking":"గమనిక: ఈ సిస్టమ్‌లో టికెట్ బుకింగ్ లేదు.","public_user":"పబ్లిక్ యూజర్","conductor_driver":"కండక్టర్/డ్రైవర్","municipality_admin":"మున్సిపాలిటీ అడ్మిన్",
    "public_portal":"పబ్లిక్ పోర్టల్","find_my_bus":"నా బస్ (ETA + Live Map)","my_pass":"నా పాస్","complaints":"ఫిర్యాదులు","back":"వెనుకకు",
    "find_my_bus_title":"నా బస్ (ETA + Live Map)","find_my_bus_caption":"స్టాప్ ఎంచుకోండి → జోన్ లోని బస్సులు + ETA, అదే స్క్రీన్‌లో లైవ్ మ్యాప్. బుకింగ్ లేదు.",
    "select_stop":"మీ ప్రస్తుత స్టాప్ ఎంచుకోండి","next_buses":"తదుపరి బస్సులు (ETA)","buses_in_zone":"జోన్ లోని బస్సులు","zone_includes_stops":"జోన్ లో సమీప స్టాపులు కూడా","no_buses_in_zone":"స్టాప్ జోన్ లో బస్సులు లేవు.",
    "refresh_eta":"లిస్ట్ రిఫ్రెష్","refresh_map":"మ్యాప్ రిఫ్రెష్","map_title":"లైవ్ బస్ మ్యాప్ (అన్ని బస్సులు + మీ జోన్)","map_updated":"మ్యాప్ అప్‌డేట్ అయ్యింది","map_tip":"టిప్: మార్కర్‌పై క్లిక్ చేసి బస్ వివరాలు చూడండి.",
    "route":"రూట్","type":"రకం","crowd":"క్రౌడ్","arrives":"వస్తుంది ~","min":"నిమి","running":"నడుస్తోంది","delayed":"ఆలస్యం","breakdown":"బ్రేక్‌డౌన్","unknown":"తెలియదు",
    "pass_title":"నా పాస్","no_pass":"పాస్ లేదు.","valid_until":"చెల్లుబాటు వరకు","pass_id":"పాస్ ID","reminder_no_booking":"గుర్తు: టికెట్ బుకింగ్ లేదు.","open_pass_mobile":"QR డీప్ లింక్ ద్వారా మొబైల్‌లో పాస్ తెరవండి.","pass_preview":"పాస్ ప్రివ్యూ",
    "submit_complaint":"ఫిర్యాదు నమోదు","bus_optional":"బస్ (ఐచ్ఛికం)","route_optional":"రూట్ (ఐచ్ఛికం)","category":"వర్గం","describe_issue":"సమస్య వివరించండి","desc_placeholder":"సమయం/స్థలం వివరాలతో రాయండి...","submit":"సబ్మిట్","desc_required":"దయచేసి వివరణ ఇవ్వండి.","complaint_submitted":"ఫిర్యాదు నమోదు అయ్యింది. టికెట్ ID:","my_recent_complaints":"నా తాజా ఫిర్యాదులు","no_complaints":"ఇంకా ఫిర్యాదులు లేవు.",
    "conductor_portal":"కండక్టర్ / డ్రైవర్ పోర్టల్","conductor_caption":"టికెట్ బుకింగ్ లేదు. లైవ్ స్టేటస్ అప్‌డేట్ + పాస్ వెరిఫై మాత్రమే.","select_bus":"మీ బస్ ఎంచుకోండి","current":"ప్రస్తుత","passengers":"ప్రయాణికులు","status":"స్థితి","update_live":"లైవ్ అప్డేట్","passengers_approx":"ప్రయాణికులు (సుమారు)","gps_tip":"GPS ఉంటే ఖచ్చిత విలువలు ఇవ్వండి.","push_update":"అప్డేట్ పంపు","updated_live":"లైవ్ స్టేట్ అప్డేట్ అయ్యింది.",
    "verify_pass":"పాస్ వెరిఫై","verify_pass_title":"పాస్ వెరిఫికేషన్","verify_pass_line1":"రియల్ సిస్టమ్‌లో QR స్కాన్ → ఇక్కడ లింక్ తెరుస్తుంది.","verify_pass_line2":"డెమో: పాస్ ID పేస్ట్ చేయండి.","verify":"వెరిఫై","pass_not_found":"పాస్ దొరకలేదు.","pass_valid":"పాస్ చెల్లుబాటు (డెమో).",
    "admin_title":"మున్సిపాలిటీ అడ్మిన్","fleet_table":"ఫ్లీట్ టేబుల్","complaints_mgmt":"ఫిర్యాదులు","disruption_monitor":"డిస్రప్షన్","admin_info":"పబ్లిక్ మ్యాప్ 'నా బస్' లో ఉంది. Admin: fleet + complaints + monitor.",
    "fleet_overview":"ఫ్లీట్ ఓవerview","quick_actions":"క్విక్ యాక్షన్స్","quick_actions_line":"రియల్ ఆపరేషన్స్: డిపోలు/షెడ్యూల్స్/రోస్టర్లు మొదలైనవి.",
    "complaints_management":"ఫిర్యాదు నిర్వహణ","all_complaints":"అన్ని ఫిర్యాదులు","update_status":"స్టేటస్ అప్డేట్","new_status":"కొత్త స్టేటస్","update":"అప్డేట్","updated":"అప్డేట్ అయ్యింది.",
    "disruption_title":"డిస్రప్షన్ మానిటర్","delayed_buses":"ఆలస్యం బస్సులు","no_delays":"ఆలస్యం లేవు.","breakdowns":"బ్రేక్‌డౌన్‌లు","no_breakdowns":"బ్రేక్‌డౌన్‌లు లేవు.",
    "app_crashed":"అప్ క్రాష్ అయ్యింది. ఎరర్ క్రింద:","language":"భాష",
}
T["ml"] = {"app_title":"സ്മാർട്ട് ട്രാൻസ്‌പോർട്ട് സിസ്റ്റം","govt_mode_line":"സർക്കാർ ബസ് മോഡ്: ടിക്കറ്റ് ബുക്കിംഗ്/പ്രീ-ബുക്കിംഗ് ഇല്ല. Next Bus ETA + Live Map, പാസ്, പരാതികൾ.",
"enter_name":"നിങ്ങളുടെ പേര് നൽകുക","name_placeholder":"ഉദാ., Mithun","welcome":"സ്വാഗതം","phone":"ഫോൺ","role":"റോൾ",
"note_no_booking":"കുറിപ്പ്: ടിക്കറ്റ് ബുക്കിംഗ് ഇല്ല.","public_user":"പൊതു ഉപയോക്താവ്","conductor_driver":"കണ്ടക്ടർ/ഡ്രൈവർ","municipality_admin":"മുനിസിപ്പാലിറ്റി അഡ്മിൻ",
"public_portal":"പബ്ലിക് പോർട്ടൽ","find_my_bus":"എൻ്റെ ബസ് (ETA + Live Map)","my_pass":"എൻ്റെ പാസ്","complaints":"പരാതികൾ","back":"തിരികെ",
"find_my_bus_title":"എൻ്റെ ബസ് (ETA + Live Map)","find_my_bus_caption":"സ്റ്റോപ്പ് തിരഞ്ഞെടുക്കുക → സോണിലെ ബസുകൾ + ETA, അതേ സ്ക്രീനിൽ ലൈവ് മാപ്പ്. ബുക്കിംഗ് ഇല്ല.",
"select_stop":"നിങ്ങളുടെ നിലവിലെ സ്റ്റോപ്പ് തിരഞ്ഞെടുക്കുക","next_buses":"അടുത്ത ബസുകൾ (ETA)","buses_in_zone":"സോണിലുള്ള ബസുകൾ","zone_includes_stops":"സോണിൽ സമീപ സ്റ്റോപ്പുകളും ഉൾപ്പെടും","no_buses_in_zone":"സ്റ്റോപ്പ് സോണിൽ ബസ് ഇല്ല.",
"refresh_eta":"ലിസ്റ്റ് റിഫ്രെഷ്","refresh_map":"മാപ്പ് റിഫ്രെഷ്","map_title":"ലൈവ് ബസ് മാപ്പ് (എല്ലാ ബസുകളും + നിങ്ങളുടെ സോൺ)","map_updated":"മാപ്പ് അപ്ഡേറ്റ് ചെയ്തു","map_tip":"ടിപ്പ്: മാർക്കർ ക്ലിക്ക് ചെയ്ത് ബസ് വിവരങ്ങൾ കാണാം.",
"route":"റൂട്ട്","type":"ടൈപ്പ്","crowd":"തിരക്ക്","arrives":"എത്തും ~","min":"മിനിറ്റ്","running":"ഓടുന്നു","delayed":"വൈകുന്നു","breakdown":"തകരാർ","unknown":"അജ്ഞാതം",
"pass_title":"എൻ്റെ പാസ്","no_pass":"പാസ് ഇല്ല.","valid_until":"സാധുത വരെ","pass_id":"പാസ് ID","reminder_no_booking":"ഓർമ്മപ്പെടുത്തൽ: ടിക്കറ്റ് ബുക്കിംഗ് ഇല്ല.","open_pass_mobile":"QR ഡീപ് ലിങ്കിലൂടെ മൊബൈലിൽ പാസ് തുറക്കുക.","pass_preview":"പാസ് പ്രീവ്യൂ",
"submit_complaint":"പരാതി നൽകുക","bus_optional":"ബസ് (ഐച്ഛികം)","route_optional":"റൂട്ട് (ഐച്ഛികം)","category":"വിഭാഗം","describe_issue":"പ്രശ്നം വിശദീകരിക്കുക","desc_placeholder":"സമയം/സ്ഥലം വിവരങ്ങൾ ചേർത്ത് എഴുതുക...","submit":"സമർപ്പിക്കുക","desc_required":"ദയവായി വിവരണം നൽകുക.","complaint_submitted":"പരാതി സമർപ്പിച്ചു. ടിക്കറ്റ് ID:","my_recent_complaints":"എൻ്റെ പുതിയ പരാതികൾ","no_complaints":"പരാതികളില്ല.",
"conductor_portal":"കണ്ടക്ടർ / ഡ്രൈവർ പോർട്ടൽ","conductor_caption":"ടിക്കറ്റ് ബുക്കിംഗ് ഇല്ല. ലൈവ് സ്റ്റാറ്റസ് അപ്ഡേറ്റ് + പാസ് വെരിഫൈ മാത്രം.","select_bus":"നിങ്ങളുടെ ബസ് തിരഞ്ഞെടുക്കുക","current":"നിലവിൽ","passengers":"യാത്രക്കാർ","status":"സ്ഥിതി","update_live":"ലൈവ് അപ്ഡേറ്റ്","passengers_approx":"യാത്രക്കാർ (ഏകദേശം)","gps_tip":"GPS ഉണ്ടെങ്കിൽ കൃത്യമായ മൂല്യങ്ങൾ നൽകുക.","push_update":"അപ്ഡേറ്റ് അയയ്‌ക്കുക","updated_live":"ലൈവ് സ്റ്റേറ്റ് അപ്ഡേറ്റ് ചെയ്തു.",
"verify_pass":"പാസ് വെരിഫൈ","verify_pass_title":"പാസ് സ്ഥിരീകരണം","verify_pass_line1":"റിയൽ സിസ്റ്റത്തിൽ QR സ്കാൻ → ഇവിടെ ലിങ്ക് തുറക്കും.","verify_pass_line2":"ഡെമോ: പാസ് ID പേസ്റ്റ് ചെയ്യുക.","verify":"സ്ഥിരീകരിക്കുക","pass_not_found":"പാസ് കണ്ടെത്തിയില്ല.","pass_valid":"പാസ് സാധുവാണ് (ഡെമോ).",
"admin_title":"മുനിസിപ്പാലിറ്റി അഡ്മിൻ","fleet_table":"ഫ്ലീറ്റ് ടേബിൾ","complaints_mgmt":"പരാതികൾ","disruption_monitor":"ഡിസ്രപ്ഷൻ","admin_info":"പബ്ലിക് മാപ്പ് 'എൻ്റെ ബസ്' ലാണ്. Admin: fleet + complaints + monitor.",
"fleet_overview":"ഫ്ലീറ്റ് അവലോകനം","quick_actions":"ക്വിക്ക് ആക്ഷൻസ്","quick_actions_line":"റിയൽ ഓപ്പറേഷൻസ്: ഡിപോ/ഷെഡ്യൂൾ/റോസ്റ്റർ തുടങ്ങിയവ.",
"complaints_management":"പരാതി മാനേജ്മെന്റ്","all_complaints":"എല്ലാ പരാതികളും","update_status":"സ്റ്റാറ്റസ് അപ്ഡേറ്റ്","new_status":"പുതിയ സ്റ്റാറ്റസ്","update":"അപ്ഡേറ്റ്","updated":"അപ്ഡേറ്റ് ചെയ്തു.",
"disruption_title":"ഡിസ്രപ്ഷൻ മോണിറ്റർ","delayed_buses":"വൈകുന്ന ബസുകൾ","no_delays":"വൈകലുകൾ ഇല്ല.","breakdowns":"തകരാറുകൾ","no_breakdowns":"തകരാറുകൾ ഇല്ല.",
"app_crashed":"ആപ്പ് ക്രാഷ് ആയി. എറർ താഴെ:","language":"ഭാഷ"}
T["kn"] = {"app_title":"ಸ್ಮಾರ್ಟ್ ಸಾರಿಗೆ ವ್ಯವಸ್ಥೆ","govt_mode_line":"ಸರ್ಕಾರಿ ಬಸ್ ಮೋಡ್: ಟಿಕೆಟ್ ಬುಕಿಂಗ್/ಪ್ರೀ-ಬುಕಿಂಗ್ ಇಲ್ಲ. Next Bus ETA + Live Map, ಪಾಸ್, ದೂರುಗಳು.",
"enter_name":"ನಿಮ್ಮ ಹೆಸರನ್ನು ನಮೂದಿಸಿ","name_placeholder":"ಉದಾ., Mithun","welcome":"ಸ್ವಾಗತ","phone":"ಫೋನ್","role":"ಪಾತ್ರ",
"note_no_booking":"ಸೂಚನೆ: ಟಿಕೆಟ್ ಬುಕಿಂಗ್ ಇಲ್ಲ.","public_user":"ಸಾರ್ವಜನಿಕ ಬಳಕೆದಾರ","conductor_driver":"ಕಂಡಕ್ಟರ್/ಡ್ರೈವರ್","municipality_admin":"ನಗರಪಾಲಿಕೆ ಆಡ್ಮಿನ್",
"public_portal":"ಪಬ್ಲಿಕ್ ಪೋರ್ಟಲ್","find_my_bus":"ನನ್ನ ಬಸ್ (ETA + Live Map)","my_pass":"ನನ್ನ ಪಾಸ್","complaints":"ದೂರುಗಳು","back":"ಹಿಂತಿರುಗಿ",
"find_my_bus_title":"ನನ್ನ ಬಸ್ (ETA + Live Map)","find_my_bus_caption":"ಸ್ಟಾಪ್ ಆಯ್ಕೆ → ವಲಯದೊಳಗಿನ ಬಸ್‌ಗಳು + ETA, ಅದೇ ಪರದೆಯಲ್ಲಿ ಲೈವ್ ಮ್ಯಾಪ್. ಬುಕಿಂಗ್ ಇಲ್ಲ.",
"select_stop":"ನಿಮ್ಮ ಪ್ರಸ್ತುತ ಸ್ಟಾಪ್ ಆಯ್ಕೆಮಾಡಿ","next_buses":"ಮುಂದಿನ ಬಸ್‌ಗಳು (ETA)","buses_in_zone":"ವಲಯದೊಳಗಿನ ಬಸ್‌ಗಳು","zone_includes_stops":"ವಲಯದಲ್ಲಿ ಹತ್ತಿರದ ಸ್ಟಾಪ್‌ಗಳೂ ಸೇರಿವೆ","no_buses_in_zone":"ಸ್ಟಾಪ್ ವಲಯದಲ್ಲಿ ಬಸ್ ಇಲ್ಲ.",
"refresh_eta":"ಪಟ್ಟಿ ರಿಫ್ರೆಶ್","refresh_map":"ಮ್ಯಾಪ್ ರಿಫ್ರೆಶ್","map_title":"ಲೈವ್ ಬಸ್ ಮ್ಯಾಪ್ (ಎಲ್ಲಾ ಬಸ್‌ಗಳು + ನಿಮ್ಮ ವಲಯ)","map_updated":"ಮ್ಯಾಪ್ ಅಪ್ಡೇಟ್ ಆಯಿತು","map_tip":"ಟಿಪ್: ಮಾರ್ಕರ್ ಕ್ಲಿಕ್ ಮಾಡಿ ಬಸ್ ವಿವರ ನೋಡಿ.",
"route":"ಮಾರ್ಗ","type":"ಪ್ರಕಾರ","crowd":"ಜನಸಂದಣಿ","arrives":"ಬರುವುದು ~","min":"ನಿಮಿಷ","running":"ಚಲಿಸುತ್ತಿದೆ","delayed":"ತಡ","breakdown":"ಕೆಡಕು","unknown":"ಅಜ್ಞಾತ",
"pass_title":"ನನ್ನ ಪಾಸ್","no_pass":"ಪಾಸ್ ಇಲ್ಲ.","valid_until":"ಮಾನ್ಯತೆ","pass_id":"ಪಾಸ್ ID","reminder_no_booking":"ಜ್ಞಾಪನೆ: ಟಿಕೆಟ್ ಬುಕಿಂಗ್ ಇಲ್ಲ.","open_pass_mobile":"QR ಡೀಪ್ ಲಿಂಕ್ ಮೂಲಕ ಮೊಬೈಲ್‌ನಲ್ಲಿ ಪಾಸ್ ತೆರೆಯಿರಿ.","pass_preview":"ಪಾಸ್ ಪ್ರಿವ್ಯೂ",
"submit_complaint":"ದೂರು ಸಲ್ಲಿಸಿ","bus_optional":"ಬಸ್ (ಐಚ್ಛಿಕ)","route_optional":"ಮಾರ್ಗ (ಐಚ್ಛಿಕ)","category":"ವರ್ಗ","describe_issue":"ಸಮಸ್ಯೆ ವಿವರಿಸಿ","desc_placeholder":"ಸಮಯ/ಸ್ಥಳ ವಿವರಗಳೊಂದಿಗೆ ಬರೆಯಿರಿ...","submit":"ಸಲ್ಲಿಸಿ","desc_required":"ದಯವಿಟ್ಟು ವಿವರಣೆ ನೀಡಿ.","complaint_submitted":"ದೂರು ಸಲ್ಲಿಸಲಾಗಿದೆ. ಟಿಕೆಟ್ ID:","my_recent_complaints":"ನನ್ನ ಇತ್ತೀಚಿನ ದೂರುಗಳು","no_complaints":"ದೂರುಗಳು ಇಲ್ಲ.",
"conductor_portal":"ಕಂಡಕ್ಟರ್ / ಡ್ರೈವರ್ ಪೋರ್ಟಲ್","conductor_caption":"ಟಿಕೆಟ್ ಬುಕಿಂಗ್ ಇಲ್ಲ. ಲೈವ್ ಸ್ಟೇಟಸ್ ಅಪ್ಡೇಟ್ + ಪಾಸ್ ವೆರಿֆೈ ಮಾತ್ರ.","select_bus":"ನಿಮ್ಮ ಬಸ್ ಆಯ್ಕೆಮಾಡಿ","current":"ಪ್ರಸ್ತುತ","passengers":"ಪ್ರಯಾಣಿಕರು","status":"ಸ್ಥಿತಿ","update_live":"ಲೈವ್ ಅಪ್ಡೇಟ್","passengers_approx":"ಪ್ರಯಾಣಿಕರು (ಅಂದಾಜು)","gps_tip":"GPS ಇದ್ದರೆ ಖಚಿತ ಮೌಲ್ಯ ಕೊಡಿ.","push_update":"ಅಪ್ಡೇಟ್ ಕಳುಹಿಸಿ","updated_live":"ಲೈವ್ ಸ್ಟೇಟ್ ಅಪ್ಡೇಟ್ ಆಯಿತು.",
"verify_pass":"ಪಾಸ್ ಪರಿಶೀಲನೆ","verify_pass_title":"ಪಾಸ್ ಪರಿಶೀಲನೆ","verify_pass_line1":"ರಿಯಲ್ ಸಿಸ್ಟಮ್‌ನಲ್ಲಿ QR ಸ್ಕ್ಯಾನ್ → ಇಲ್ಲಿ ಲಿಂಕ್ ತೆರೆಯುತ್ತದೆ.","verify_pass_line2":"ಡೆಮೊ: ಪಾಸ್ ID ಪೇಸ್ಟ್ ಮಾಡಿ.","verify":"ಪರಿಶೀಲಿಸಿ","pass_not_found":"ಪಾಸ್ ಸಿಗಲಿಲ್ಲ.","pass_valid":"ಪಾಸ್ ಮಾನ್ಯ (ಡೆಮೊ).",
"admin_title":"ನಗರಪಾಲಿಕೆ ಆಡ್ಮಿನ್","fleet_table":"ಫ್ಲೀಟ್ ಟೇಬಲ್","complaints_mgmt":"ದೂರುಗಳು","disruption_monitor":"ಡಿಸ್ರಪ್ಷನ್","admin_info":"ಪಬ್ಲಿಕ್ ಮ್ಯಾಪ್ 'ನನ್ನ ಬಸ್' ಒಳಗೆ. Admin: fleet + complaints + monitor.",
"fleet_overview":"ಫ್ಲೀಟ್ ಅವಲೋಕನ","quick_actions":"ತ್ವರಿತ ಕ್ರಿಯೆಗಳು","quick_actions_line":"ರಿಯಲ್ ಆಪರೇಷನ್‌ಸ್: ಡೆಪೋ/ಶೆಡ್ಯೂಲ್/ರೋಸ್ಟರ್ ಇತ್ಯಾದಿ.",
"complaints_management":"ದೂರು ನಿರ್ವಹಣೆ","all_complaints":"ಎಲ್ಲಾ ದೂರುಗಳು","update_status":"ಸ್ಥಿತಿ ಅಪ್ಡೇಟ್","new_status":"ಹೊಸ ಸ್ಥಿತಿ","update":"ಅಪ್ಡೇಟ್","updated":"ಅಪ್ಡೇಟ್ ಆಯಿತು.",
"disruption_title":"ಡಿಸ್ರಪ್ಷನ್ ಮോണಿಟರ್","delayed_buses":"ತಡವಾದ ಬಸ್‌ಗಳು","no_delays":"ತಡ ಇಲ್ಲ.","breakdowns":"ಕೆಡಕುಗಳು","no_breakdowns":"ಕೆಡಕು ಇಲ್ಲ.",
"app_crashed":"ಆಪ್ ಕ್ರ್ಯಾಶ್ ಆಯಿತು. ದೋಷ ಕೆಳಗೆ:","language":"ಭಾಷೆ"}
T["bn"] = {"app_title":"স্মার্ট পরিবহন সিস্টেম","govt_mode_line":"সরকারি বাস মোড: টিকিট বুকিং/প্রি-বুকিং নেই। Next Bus ETA + Live Map, পাস, অভিযোগ।",
"enter_name":"আপনার নাম লিখুন","name_placeholder":"যেমন, Mithun","welcome":"স্বাগতম","phone":"ফোন","role":"ভূমিকা",
"note_no_booking":"নোট: টিকিট বুকিং নেই।","public_user":"পাবলিক ইউজার","conductor_driver":"কন্ডাক্টর/ড্রাইভার","municipality_admin":"মিউনিসিপ্যালিটি অ্যাডমিন",
"public_portal":"পাবলিক পোর্টাল","find_my_bus":"আমার বাস (ETA + Live Map)","my_pass":"আমার পাস","complaints":"অভিযোগ","back":"ফিরে যান",
"find_my_bus_title":"আমার বাস (ETA + Live Map)","find_my_bus_caption":"স্টপ নির্বাচন → জোনের ভেতরের বাস + ETA, একই স্ক্রিনে লাইভ ম্যাপ। বুকিং নেই।",
"select_stop":"আপনার বর্তমান স্টপ নির্বাচন করুন","next_buses":"পরবর্তী বাস (ETA)","buses_in_zone":"জোনের ভেতরের বাস","zone_includes_stops":"জোনে কাছাকাছি স্টপও অন্তর্ভুক্ত","no_buses_in_zone":"স্টপ জোনে কোনো বাস নেই।",
"refresh_eta":"লিস্ট রিফ্রেশ","refresh_map":"ম্যাপ রিফ্রেশ","map_title":"লাইভ বাস ম্যাপ (সব বাস + আপনার জোন)","map_updated":"ম্যাপ আপডেট হয়েছে","map_tip":"টিপ: মার্কারে ক্লিক করে বাস বিস্তারিত দেখুন।",
"route":"রুট","type":"ধরন","crowd":"ভিড়","arrives":"পৌঁছাবে ~","min":"মিনিট","running":"চলছে","delayed":"দেরি","breakdown":"বিকল","unknown":"অজানা",
"pass_title":"আমার পাস","no_pass":"পাস পাওয়া যায়নি।","valid_until":"মেয়াদ","pass_id":"পাস ID","reminder_no_booking":"মনে রাখুন: টিকিট বুকিং নেই।","open_pass_mobile":"QR ডীপ লিঙ্ক দিয়ে মোবাইলে পাস খুলুন।","pass_preview":"পাস প্রিভিউ",
"submit_complaint":"অভিযোগ জমা দিন","bus_optional":"বাস (ঐচ্ছিক)","route_optional":"রুট (ঐচ্ছিক)","category":"বিভাগ","describe_issue":"সমস্যা লিখুন","desc_placeholder":"সময়/স্থানসহ লিখুন...","submit":"জমা দিন","desc_required":"অনুগ্রহ করে বিবরণ দিন।","complaint_submitted":"অভিযোগ জমা হয়েছে। টিকিট ID:","my_recent_complaints":"আমার সাম্প্রতিক অভিযোগ","no_complaints":"কোনো অভিযোগ নেই।",
"conductor_portal":"কন্ডাক্টর / ড্রাইভার পোর্টাল","conductor_caption":"টিকিট বুকিং নেই। লাইভ স্ট্যাটাস আপডেট + পাস ভেরিফাই।","select_bus":"বাস নির্বাচন করুন","current":"বর্তমান","passengers":"যাত্রী","status":"স্ট্যাটাস","update_live":"লাইভ আপডেট","passengers_approx":"যাত্রী (আনুমানিক)","gps_tip":"GPS থাকলে সঠিক মান দিন।","push_update":"আপডেট পাঠান","updated_live":"লাইভ স্টেট আপডেট হয়েছে।",
"verify_pass":"পাস ভেরিফাই","verify_pass_title":"পাস যাচাই","verify_pass_line1":"রিয়েল সিস্টেমে QR স্ক্যান → এখানে লিঙ্ক খুলবে।","verify_pass_line2":"ডেমো: পাস ID পেস্ট করুন।","verify":"যাচাই","pass_not_found":"পাস পাওয়া যায়নি।","pass_valid":"পাস বৈধ (ডেমো)।",
"admin_title":"মিউনিসিপ্যালিটি অ্যাডমিন","fleet_table":"ফ্লিট টেবিল","complaints_mgmt":"অভিযোগ","disruption_monitor":"ডিসরাপশন","admin_info":"পাবলিক ম্যাপ 'আমার বাস' এ। Admin: fleet + complaints + monitor.",
"fleet_overview":"ফ্লিট ওভারভিউ","quick_actions":"কুইক অ্যাকশন","quick_actions_line":"রিয়েল অপারেশন: ডিপো/শিডিউল/রোস্টার ইত্যাদি।",
"complaints_management":"অভিযোগ ব্যবস্থাপনা","all_complaints":"সব অভিযোগ","update_status":"স্ট্যাটাস আপডেট","new_status":"নতুন স্ট্যাটাস","update":"আপডেট","updated":"আপডেট হয়েছে।",
"disruption_title":"ডিসরাপশন মনিটর","delayed_buses":"দেরি হওয়া বাস","no_delays":"কোনো দেরি নেই।","breakdowns":"বিকল বাস","no_breakdowns":"বিকল নেই।",
"app_crashed":"অ্যাপ ক্র্যাশ হয়েছে। এরর নিচে:","language":"ভাষা"}
T["ur"] = {"app_title":"سمارٹ ٹرانسپورٹ سسٹم","govt_mode_line":"سرکاری بس موڈ: ٹکٹ بکنگ/پری بکنگ نہیں۔ Next Bus ETA + Live Map، پاسز، شکایات۔",
"enter_name":"اپنا نام درج کریں","name_placeholder":"مثلاً، Mithun","welcome":"خوش آمدید","phone":"فون","role":"کردار",
"note_no_booking":"نوٹ: ٹکٹ بکنگ موجود نہیں۔","public_user":"عوامی صارف","conductor_driver":"کنڈکٹر/ڈرائیور","municipality_admin":"میونسپل ایڈمن",
"public_portal":"پبلک پورٹل","find_my_bus":"میری بس (ETA + Live Map)","my_pass":"میرا پاس","complaints":"شکایات","back":"واپس",
"find_my_bus_title":"میری بس (ETA + Live Map)","find_my_bus_caption":"اسٹاپ منتخب کریں → زون کے اندر بسیں + ETA، اسی اسکرین پر لائیو میپ۔ بکنگ نہیں۔",
"select_stop":"اپنا موجودہ اسٹاپ منتخب کریں","next_buses":"اگلی بسیں (ETA)","buses_in_zone":"زون کے اندر بسیں","zone_includes_stops":"زون میں قریب کے اسٹاپ بھی شامل ہیں","no_buses_in_zone":"اسٹاپ زون میں کوئی بس نہیں۔",
"refresh_eta":"فہرست ریفریش","refresh_map":"میپ ریفریش","map_title":"لائیو بس میپ (تمام بسیں + آپ کا زون)","map_updated":"میپ اپڈیٹ ہوا","map_tip":"ٹپ: مارکر پر کلک کر کے بس کی تفصیل دیکھیں۔",
"route":"روٹ","type":"قسم","crowd":"رش","arrives":"پہنچے گی ~","min":"منٹ","running":"چل رہی","delayed":"تاخیر","breakdown":"خرابی","unknown":"نامعلوم",
"pass_title":"میرا پاس","no_pass":"پاس نہیں ملا۔","valid_until":"مدت تک","pass_id":"پاس ID","reminder_no_booking":"یاد دہانی: ٹکٹ بکنگ نہیں۔","open_pass_mobile":"QR ڈیپ لنک سے موبائل پر پاس کھولیں۔","pass_preview":"پاس پریویو",
"submit_complaint":"شکایت جمع کریں","bus_optional":"بس (اختیاری)","route_optional":"روٹ (اختیاری)","category":"قسم","describe_issue":"مسئلہ بیان کریں","desc_placeholder":"وقت/جگہ سمیت لکھیں...","submit":"جمع کریں","desc_required":"براہ کرم تفصیل لکھیں۔","complaint_submitted":"شکایت جمع ہوگئی۔ ٹکٹ ID:","my_recent_complaints":"میری حالیہ شکایات","no_complaints":"کوئی شکایت نہیں۔",
"conductor_portal":"کنڈکٹر / ڈرائیور پورٹل","conductor_caption":"ٹکٹ بکنگ نہیں۔ لائیو اسٹیٹس اپڈیٹ + پاس ویریفائی۔","select_bus":"بس منتخب کریں","current":"موجودہ","passengers":"مسافر","status":"اسٹیٹس","update_live":"لائیو اپڈیٹ","passengers_approx":"مسافر (اندازاً)","gps_tip":"GPS ہو تو درست ویلیو دیں۔","push_update":"اپڈیٹ بھیجیں","updated_live":"لائیو اسٹیٹ اپڈیٹ ہوگیا۔",
"verify_pass":"پاس ویریفائی","verify_pass_title":"پاس کی تصدیق","verify_pass_line1":"حقیقی سسٹم میں QR اسکین → یہاں لنک کھلے گا۔","verify_pass_line2":"ڈیمو: پاس ID پیسٹ کریں۔","verify":"تصدیق","pass_not_found":"پاس نہیں ملا۔","pass_valid":"پاس درست ہے (ڈیمو)۔",
"admin_title":"میونسپل ایڈمن","fleet_table":"فلیٹ ٹیبل","complaints_mgmt":"شکایات","disruption_monitor":"ڈس رپشن","admin_info":"پبلک میپ 'میری بس' میں ہے۔ Admin: fleet + complaints + monitor.",
"fleet_overview":"فلیٹ اوورویو","quick_actions":"فوری اقدامات","quick_actions_line":"حقیقی آپریشنز: ڈپو/شیڈول/روسٹر وغیرہ۔",
"complaints_management":"شکایات مینجمنٹ","all_complaints":"تمام شکایات","update_status":"اسٹیٹس اپڈیٹ","new_status":"نیا اسٹیٹس","update":"اپڈیٹ","updated":"اپڈیٹ ہوگیا۔",
"disruption_title":"ڈس رپشن مانیٹر","delayed_buses":"تاخیر والی بسیں","no_delays":"کوئی تاخیر نہیں۔","breakdowns":"خراب بسیں","no_breakdowns":"کوئی خرابی نہیں۔",
"app_crashed":"ایپ کریش ہوگئی۔ ایرر نیچے:","language":"زبان"}
T["mr"] = {"app_title":"स्मार्ट ट्रान्सपोर्ट सिस्टीम","govt_mode_line":"सरकारी बस मोड: तिकीट बुकिंग/प्री-बुकिंग नाही. Next Bus ETA + Live Map, पास, तक्रारी.",
"enter_name":"तुमचं नाव टाका","name_placeholder":"उदा., Mithun","welcome":"स्वागत","phone":"फोन","role":"भूमिका",
"note_no_booking":"नोंद: तिकीट बुकिंग नाही.","public_user":"पब्लिक युजर","conductor_driver":"कंडक्टर/ड्रायव्हर","municipality_admin":"महानगरपालिका अ‍ॅडमिन",
"public_portal":"पब्लिक पोर्टल","find_my_bus":"माझी बस (ETA + Live Map)","my_pass":"माझा पास","complaints":"तक्रारी","back":"मागे",
"find_my_bus_title":"माझी बस (ETA + Live Map)","find_my_bus_caption":"स्टॉप निवडा → झोनमधील बस + ETA, त्याच स्क्रीनवर लाईव्ह मॅप. बुकिंग नाही.",
"select_stop":"तुमचा सध्याचा स्टॉप निवडा","next_buses":"पुढच्या बस (ETA)","buses_in_zone":"झोनमधील बस","zone_includes_stops":"झोनमध्ये जवळचे स्टॉपही","no_buses_in_zone":"स्टॉप झोनमध्ये बस नाही.",
"refresh_eta":"लिस्ट रिफ्रेश","refresh_map":"मॅप रिफ्रेश","map_title":"लाईव्ह बस मॅप (सगळ्या बस + तुमचा झोन)","map_updated":"मॅप अपडेट झाला","map_tip":"टीप: मार्कर क्लिक करून बस तपशील पहा.",
"route":"मार्ग","type":"प्रकार","crowd":"गर्दी","arrives":"येते ~","min":"मिनि","running":"चालू","delayed":"उशीर","breakdown":"बिघाड","unknown":"अज्ञात",
"pass_title":"माझा पास","no_pass":"पास नाही.","valid_until":"वैधता","pass_id":"पास ID","reminder_no_booking":"आठवण: तिकीट बुकिंग नाही.","open_pass_mobile":"QR डीप लिंकने मोबाईलवर पास उघडा.","pass_preview":"पास प्रिव्ह्यू",
"submit_complaint":"तक्रार दाखल करा","bus_optional":"बस (पर्यायी)","route_optional":"मार्ग (पर्यायी)","category":"वर्ग","describe_issue":"समस्या लिहा","desc_placeholder":"वेळ/ठिकाणासह लिहा...","submit":"सबमिट","desc_required":"कृपया वर्णन द्या.","complaint_submitted":"तक्रार दाखल. टिकीट ID:","my_recent_complaints":"माझ्या अलीकडच्या तक्रारी","no_complaints":"तक्रारी नाहीत.",
"conductor_portal":"कंडक्टर / ड्रायव्हर पोर्टल","conductor_caption":"तिकीट बुकिंग नाही. लाईव्ह स्टेटस अपडेट + पास व्हेरिफाय.","select_bus":"बस निवडा","current":"सध्याचे","passengers":"प्रवासी","status":"स्थिती","update_live":"लाईव्ह अपडेट","passengers_approx":"प्रवासी (अंदाजे)","gps_tip":"GPS असल्यास अचूक मूल्य द्या.","push_update":"अपडेट पाठवा","updated_live":"लाईव्ह स्टेट अपडेट झाला.",
"verify_pass":"पास व्हेरिफाय","verify_pass_title":"पास पडताळणी","verify_pass_line1":"QR स्कॅन → इथे लिंक उघडेल.","verify_pass_line2":"डेमो: पास ID पेस्ट करा.","verify":"पडताळा","pass_not_found":"पास सापडला नाही.","pass_valid":"पास वैध (डेमो).",
"admin_title":"महानगरपालिका अ‍ॅडमिन","fleet_table":"फ्लीट टेबल","complaints_mgmt":"तक्रारी","disruption_monitor":"डिसरप्शन","admin_info":"पब्लिक मॅप 'माझी बस' मध्ये. Admin: fleet + complaints + monitor.",
"fleet_overview":"फ्लीट ओव्हरव्ह्यू","quick_actions":"क्विक अ‍ॅक्शन्स","quick_actions_line":"रिअल ऑपरेशन्स: डेपो/शेड्युल/रोस्टर इ.",
"complaints_management":"तक्रार व्यवस्थापन","all_complaints":"सर्व तक्रारी","update_status":"स्थिती अपडेट","new_status":"नवीन स्थिती","update":"अपडेट","updated":"अपडेट झाले.",
"disruption_title":"डिसरप्शन मॉनिटर","delayed_buses":"उशीर बस","no_delays":"उशीर नाही.","breakdowns":"बिघाड","no_breakdowns":"बिघाड नाही.",
"app_crashed":"अ‍ॅप क्रॅश झाले. एरर खाली:","language":"भाषा"}
T["gu"] = {"app_title":"સ્માર્ટ ટ્રાન્સપોર્ટ સિસ્ટમ","govt_mode_line":"સરકારી બસ મોડ: ટિકિટ બુકિંગ/પ્રી-બુકિંગ નથી. Next Bus ETA + Live Map, પાસ, ફરિયાદો.",
"enter_name":"તમારું નામ દાખલ કરો","name_placeholder":"જેમ કે, Mithun","welcome":"સ્વાગત","phone":"ફોન","role":"ભૂમિકા",
"note_no_booking":"નોંધ: ટિકિટ બુકિંગ નથી.","public_user":"પબ્લિક યૂઝર","conductor_driver":"કન્ડક્ટર/ડ્રાઇવર","municipality_admin":"મ્યુનિસિપાલિટી એડમિન",
"public_portal":"પબ્લિક પોર્ટલ","find_my_bus":"મારી બસ (ETA + Live Map)","my_pass":"મારો પાસ","complaints":"ફરિયાદો","back":"પાછા",
"find_my_bus_title":"મારી બસ (ETA + Live Map)","find_my_bus_caption":"સ્ટોપ પસંદ કરો → ઝોનની અંદરના બસ + ETA, એ જ સ્ક્રીન પર લાઇવ મેપ. બુકિંગ નથી.",
"select_stop":"તમારો હાલનો સ્ટોપ પસંદ કરો","next_buses":"આગામી બસ (ETA)","buses_in_zone":"ઝોનની અંદરની બસ","zone_includes_stops":"ઝોનમાં નજીકના સ્ટોપ પણ","no_buses_in_zone":"સ્ટોપ ઝોનમાં બસ નથી.",
"refresh_eta":"લિસ્ટ રિફ્રેશ","refresh_map":"મેપ રિફ્રેશ","map_title":"લાઇવ બસ મેપ (બધી બસ + તમારો ઝોન)","map_updated":"મેપ અપડેટ થયું","map_tip":"ટિપ: માર્કર પર ક્લિક કરીને બસ વિગતો જુઓ.",
"route":"રૂટ","type":"પ્રકાર","crowd":"ભીડ","arrives":"આવે ~","min":"મિનિટ","running":"ચાલુ","delayed":"વિલંબ","breakdown":"ખરાબી","unknown":"અજ્ઞાત",
"pass_title":"મારો પાસ","no_pass":"પાસ મળ્યો નથી.","valid_until":"માન્યતા","pass_id":"પાસ ID","reminder_no_booking":"યાદ: ટિકિટ બુકિંગ નથી.","open_pass_mobile":"QR ડીપ લિંક દ્વારા મોબાઈલ પર પાસ ખોલો.","pass_preview":"પાસ પ્રિવ્યુ",
"submit_complaint":"ફરિયાદ કરો","bus_optional":"બસ (વૈકલ્પિક)","route_optional":"રૂટ (વૈકલ્પિક)","category":"વર્ગ","describe_issue":"સમસા લખો","desc_placeholder":"સમય/સ્થળ સાથે લખો...","submit":"સબમિટ","desc_required":"કૃપા કરીને વર્ણન આપો.","complaint_submitted":"ફરિયાદ નોંધાઈ. ટિકિટ ID:","my_recent_complaints":"મારી તાજી ફરિયાદો","no_complaints":"ફરિયાદો નથી.",
"conductor_portal":"કન્ડક્ટર / ડ્રાઇવર પોર્ટલ","conductor_caption":"ટિકિટ બુકિંગ નથી. લાઇવ સ્ટેટસ અપડેટ + પાસ વેરિફાય.","select_bus":"બસ પસંદ કરો","current":"હાલનું","passengers":"મુસાફરો","status":"સ્થિતિ","update_live":"લાઇવ અપડેટ","passengers_approx":"મુસાફરો (અંદાજે)","gps_tip":"GPS હોય તો ચોક્કસ મૂલ્ય આપો.","push_update":"અપડેટ મોકલો","updated_live":"લાઇવ સ્ટેટ અપડેટ થયું.",
"verify_pass":"પાસ વેરિફાય","verify_pass_title":"પાસ ચકાસણી","verify_pass_line1":"QR સ્કેન → અહીં લિંક ખુલશે.","verify_pass_line2":"ડેમો: પાસ ID પેસ્ટ કરો.","verify":"ચકાસો","pass_not_found":"પાસ મળ્યો નથી.","pass_valid":"પાસ માન્ય (ડેમો).",
"admin_title":"મ્યુનિસિપાલિટી એડમિન","fleet_table":"ફ્લીટ ટેબલ","complaints_mgmt":"ફરિયાદો","disruption_monitor":"ડિસરપ્શન","admin_info":"પબ્લિક મેપ 'મારી બસ' માં. Admin: fleet + complaints + monitor.",
"fleet_overview":"ફ્લીટ ઓવરવ્યૂ","quick_actions":"ક્વિક એક્શન","quick_actions_line":"રીયલ ઓપરેશન્સ: ડેપો/શેડ્યૂલ/રોસ્ટર વગેરે.",
"complaints_management":"ફરિયાદ મેનેજમેન્ટ","all_complaints":"બધી ફરિયાદો","update_status":"સ્થિતિ અપડેટ","new_status":"નવી સ્થિતિ","update":"અપડેટ","updated":"અપડેટ થયું.",
"disruption_title":"ડિસરપ્શન મોનિટર","delayed_buses":"વિલંબ બસ","no_delays":"વિલંબ નથી.","breakdowns":"ખરાબી","no_breakdowns":"ખરાબી નથી.",
"app_crashed":"એપ ક્રેશ થયું. એરર નીચે:","language":"ભાષા"}
T["pa"] = {"app_title":"ਸਮਾਰਟ ਟਰਾਂਸਪੋਰਟ ਸਿਸਟਮ","govt_mode_line":"ਸਰਕਾਰੀ ਬੱਸ ਮੋਡ: ਟਿਕਟ ਬੁਕਿੰਗ/ਪ੍ਰੀ-ਬੁਕਿੰਗ ਨਹੀਂ। Next Bus ETA + Live Map, ਪਾਸ, ਸ਼ਿਕਾਇਤਾਂ।",
"enter_name":"ਆਪਣਾ ਨਾਮ ਦਾਖਲ ਕਰੋ","name_placeholder":"ਜਿਵੇਂ, Mithun","welcome":"ਸਵਾਗਤ","phone":"ਫੋਨ","role":"ਭੂਮਿਕਾ",
"note_no_booking":"ਨੋਟ: ਟਿਕਟ ਬੁਕਿੰਗ ਨਹੀਂ।","public_user":"ਪਬਲਿਕ ਯੂਜ਼ਰ","conductor_driver":"ਕੰਡਕਟਰ/ਡਰਾਈਵਰ","municipality_admin":"ਮਿਊਂਸਿਪਲ ਐਡਮਿਨ",
"public_portal":"ਪਬਲਿਕ ਪੋਰਟਲ","find_my_bus":"ਮੇਰੀ ਬੱਸ (ETA + Live Map)","my_pass":"ਮੇਰਾ ਪਾਸ","complaints":"ਸ਼ਿਕਾਇਤਾਂ","back":"ਵਾਪਸ",
"find_my_bus_title":"ਮੇਰੀ ਬੱਸ (ETA + Live Map)","find_my_bus_caption":"ਸਟਾਪ ਚੁਣੋ → ਜ਼ੋਨ ਅੰਦਰ ਬੱਸਾਂ + ETA, ਉਸੇ ਸਕ੍ਰੀਨ ਤੇ ਲਾਈਵ ਮੈਪ। ਬੁਕਿੰਗ ਨਹੀਂ।",
"select_stop":"ਆਪਣਾ ਮੌਜੂਦਾ ਸਟਾਪ ਚੁਣੋ","next_buses":"ਅਗਲੀ ਬੱਸਾਂ (ETA)","buses_in_zone":"ਜ਼ੋਨ ਅੰਦਰ ਬੱਸਾਂ","zone_includes_stops":"ਜ਼ੋਨ ਵਿੱਚ ਨੇੜਲੇ ਸਟਾਪ ਵੀ","no_buses_in_zone":"ਸਟਾਪ ਜ਼ੋਨ ਵਿੱਚ ਬੱਸ ਨਹੀਂ।",
"refresh_eta":"ਲਿਸਟ ਰਿਫ੍ਰੈਸ਼","refresh_map":"ਮੈਪ ਰਿਫ੍ਰੈਸ਼","map_title":"ਲਾਈਵ ਬੱਸ ਮੈਪ (ਸਭ ਬੱਸਾਂ + ਤੁਹਾਡਾ ਜ਼ੋਨ)","map_updated":"ਮੈਪ ਅੱਪਡੇਟ ਹੋਇਆ","map_tip":"ਟਿਪ: ਮਾਰਕਰ ਤੇ ਕਲਿੱਕ ਕਰਕੇ ਬੱਸ ਵੇਰਵਾ ਵੇਖੋ।",
"route":"ਰੂਟ","type":"ਕਿਸਮ","crowd":"ਭੀੜ","arrives":"ਆਵੇਗੀ ~","min":"ਮਿੰਟ","running":"ਚੱਲ ਰਹੀ","delayed":"ਦੇਰੀ","breakdown":"ਖਰਾਬੀ","unknown":"ਅਣਜਾਣ",
"pass_title":"ਮੇਰਾ ਪਾਸ","no_pass":"ਪਾਸ ਨਹੀਂ ਮਿਲਿਆ।","valid_until":"ਵੈਧਤਾ","pass_id":"ਪਾਸ ID","reminder_no_booking":"ਯਾਦ: ਟਿਕਟ ਬੁਕਿੰਗ ਨਹੀਂ।","open_pass_mobile":"QR ਡੀਪ ਲਿੰਕ ਨਾਲ ਮੋਬਾਇਲ ਤੇ ਪਾਸ ਖੋਲ੍ਹੋ।","pass_preview":"ਪਾਸ ਪ੍ਰਿਵਿਊ",
"submit_complaint":"ਸ਼ਿਕਾਇਤ ਕਰੋ","bus_optional":"ਬੱਸ (ਚੋਣਵਾਂ)","route_optional":"ਰੂਟ (ਚੋਣਵਾਂ)","category":"ਸ਼੍ਰੇਣੀ","describe_issue":"ਸਮੱਸਿਆ ਲਿਖੋ","desc_placeholder":"ਸਮਾਂ/ਥਾਂ ਸਮੇਤ ਲਿਖੋ...","submit":"ਸਬਮਿਟ","desc_required":"ਕਿਰਪਾ ਕਰਕੇ ਵੇਰਵਾ ਦਿਓ।","complaint_submitted":"ਸ਼ਿਕਾਇਤ ਦਰਜ। ਟਿਕਟ ID:","my_recent_complaints":"ਮੇਰੀਆਂ ਹਾਲੀਆ ਸ਼ਿਕਾਇਤਾਂ","no_complaints":"ਕੋਈ ਸ਼ਿਕਾਇਤ ਨਹੀਂ।",
"conductor_portal":"ਕੰਡਕਟਰ / ਡਰਾਈਵਰ ਪੋਰਟਲ","conductor_caption":"ਟਿਕਟ ਬੁਕਿੰਗ ਨਹੀਂ। ਲਾਈਵ ਸਟੇਟਸ ਅੱਪਡੇਟ + ਪਾਸ ਵੇਰੀਫਾਈ।","select_bus":"ਬੱਸ ਚੁਣੋ","current":"ਮੌਜੂਦਾ","passengers":"ਯਾਤਰੀ","status":"ਸਟੇਟਸ","update_live":"ਲਾਈਵ ਅੱਪਡੇਟ","passengers_approx":"ਯਾਤਰੀ (ਅੰਦਾਜ਼ਾ)","gps_tip":"GPS ਹੋਵੇ ਤਾਂ ਸਹੀ ਮੁੱਲ ਦਿਓ।","push_update":"ਅੱਪਡੇਟ ਭੇਜੋ","updated_live":"ਲਾਈਵ ਸਟੇਟ ਅੱਪਡੇਟ ਹੋਇਆ।",
"verify_pass":"ਪਾਸ ਵੇਰੀਫਾਈ","verify_pass_title":"ਪਾਸ ਜਾਂਚ","verify_pass_line1":"QR ਸਕੈਨ → ਇੱਥੇ ਲਿੰਕ ਖੁੱਲੇਗਾ।","verify_pass_line2":"ਡੈਮੋ: ਪਾਸ ID ਪੇਸਟ ਕਰੋ।","verify":"ਜਾਂਚੋ","pass_not_found":"ਪਾਸ ਨਹੀਂ ਮਿਲਿਆ।","pass_valid":"ਪਾਸ ਵੈਧ (ਡੈਮੋ)।",
"admin_title":"ਮਿਊਂਸਿਪਲ ਐਡਮਿਨ","fleet_table":"ਫਲੀਟ ਟੇਬਲ","complaints_mgmt":"ਸ਼ਿਕਾਇਤਾਂ","disruption_monitor":"ਡਿਸਰਪਸ਼ਨ","admin_info":"ਪਬਲਿਕ ਮੈਪ 'ਮੇਰੀ ਬੱਸ' ਵਿੱਚ। Admin: fleet + complaints + monitor.",
"fleet_overview":"ਫਲੀਟ ਓਵਰਵਿਊ","quick_actions":"ਕੁਇੱਕ ਐਕਸ਼ਨ","quick_actions_line":"ਅਸਲੀ ਓਪਰੇਸ਼ਨ: ਡਿਪੋ/ਸ਼ੈਡਿਊਲ/ਰੋਸਟਰ ਆਦਿ।",
"complaints_management":"ਸ਼ਿਕਾਇਤ ਪ੍ਰਬੰਧਨ","all_complaints":"ਸਾਰੀਆਂ ਸ਼ਿਕਾਇਤਾਂ","update_status":"ਸਟੇਟਸ ਅੱਪਡੇਟ","new_status":"ਨਵਾਂ ਸਟੇਟਸ","update":"ਅੱਪਡੇਟ","updated":"ਅੱਪਡੇਟ ਹੋਇਆ।",
"disruption_title":"ਡਿਸਰਪਸ਼ਨ ਮਾਨੀਟਰ","delayed_buses":"ਦੇਰੀ ਵਾਲੀਆਂ ਬੱਸਾਂ","no_delays":"ਕੋਈ ਦੇਰੀ ਨਹੀਂ।","breakdowns":"ਖਰਾਬੀਆਂ","no_breakdowns":"ਕੋਈ ਖਰਾਬੀ ਨਹੀਂ।",
"app_crashed":"ਐਪ ਕਰੈਸ਼ ਹੋ ਗਿਆ। ਐਰਰ ਹੇਠਾਂ:","language":"ਭਾਸ਼ਾ"}

# Ensure every language has all keys (fallback to English for any missing)
for code, _ in LANGS:
    if code not in T:
        T[code] = {}
    for k in UI_KEYS:
        if k not in T[code]:
            T[code][k] = T["en"][k]


def tr(key: str) -> str:
    lang = st.session_state.get("lang", "en")
    return T.get(lang, T["en"]).get(key, T["en"].get(key, key))


# -----------------------------
# Session State
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
# SQLite
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
# URL helper
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
        return (tr("running"), "pill pill-ok")
    if s == "delayed":
        return (tr("delayed"), "pill pill-warn")
    if s in ["breakdown", "cancelled", "maintenance"]:
        return (tr("breakdown"), "pill pill-bad")
    return (tr("unknown"), "pill")


def is_eta_relevant(status: str) -> bool:
    return (status or "").lower() in ["active", "running", "onroute", "delayed"]


# -----------------------------
# DATA: Stops (with sub-stops for big hubs)
# -----------------------------
def create_places_data():
    # Major stops
    base = [
        ("S001", "Gandhipuram", 11.0183, 76.9725, "Central"),
        ("S002", "Coimbatore", 11.0168, 76.9558, "Central"),
        ("S003", "Tiruppur", 11.1085, 77.3411, "East"),
        ("S004", "Erode", 11.3410, 77.7172, "East"),
        ("S005", "Salem", 11.6643, 78.1460, "East"),
        ("S006", "Vellore", 12.9165, 79.1325, "North"),
        ("S007", "Chennai", 13.0827, 80.2707, "North"),
        ("S008", "Trichy", 10.7905, 78.7047, "South"),
        ("S009", "Thanjavur", 10.7870, 79.1378, "South"),
        ("S010", "Madurai", 9.9252, 78.1198, "South"),
    ]

    # Sub-stops (close-by) — ensures big hubs have multiple nearby stops inside one circle
    # Offsets are small (0.001 ~ 0.003 degrees) to simulate platforms/stands/terminals.
    subs = [
        ("S001A", "Gandhipuram - Platform 1", 11.0192, 76.9721, "Central"),
        ("S001B", "Gandhipuram - Platform 2", 11.0189, 76.9733, "Central"),
        ("S001C", "Gandhipuram - Omni Stand", 11.0175, 76.9717, "Central"),
        ("S001D", "Gandhipuram - Cross Cut Rd", 11.0179, 76.9741, "Central"),

        ("S002A", "Coimbatore - Railway Jn", 11.0158, 76.9610, "Central"),
        ("S002B", "Coimbatore - Ukkadam", 11.0089, 76.9632, "Central"),
        ("S002C", "Coimbatore - Town Hall", 11.0096, 76.9562, "Central"),

        ("S007A", "Chennai - Central", 13.0836, 80.2754, "North"),
        ("S007B", "Chennai - Egmore", 13.0787, 80.2607, "North"),
        ("S007C", "Chennai - Koyambedu", 13.0676, 80.2050, "North"),
        ("S007D", "Chennai - Guindy", 13.0067, 80.2206, "North"),

        ("S008A", "Trichy - Central Bus Stand", 10.7909, 78.6869, "South"),
        ("S008B", "Trichy - Railway Jn", 10.7960, 78.6861, "South"),

        ("S010A", "Madurai - Periyar", 9.9203, 78.1190, "South"),
        ("S010B", "Madurai - Mattuthavani", 9.9395, 78.1503, "South"),
    ]

    rows = []
    for sid, name, lat, lon, zone in base + subs:
        rows.append({"stop_id": sid, "stop_name": name, "latitude": lat, "longitude": lon, "zone": zone})
    return pd.DataFrame(rows)


@st.cache_data
def get_places_data():
    return create_places_data()


def stops_within_radius(stop_name: str, radius_km: float):
    places = get_places_data()
    srow = places[places["stop_name"] == stop_name].iloc[0]
    slat, slon = float(srow["latitude"]), float(srow["longitude"])

    places = places.copy()
    places["dist_km"] = places.apply(
        lambda r: haversine_km(float(r["latitude"]), float(r["longitude"]), slat, slon),
        axis=1
    )
    return places[places["dist_km"] <= radius_km].sort_values("dist_km").reset_index(drop=True)


# -----------------------------
# DATA: Fleet + Live state
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

        # Seed from the start point (major stop), but slightly jitter so many buses fall into a hub zone.
        start_place = places_df[places_df["stop_name"] == route_info["start"]].iloc[0]
        buses.append({
            "bus_number": bus_number,
            "bus_type": bt,
            "capacity": random.choice([30, 35, 40, 45, 50]),
            "start_point": route_info["start"],
            "end_point": route_info["end"],
            "route_name": route_info["route"],
            "default_lat": float(start_place["latitude"]) + random.uniform(-0.010, 0.010),
            "default_lon": float(start_place["longitude"]) + random.uniform(-0.010, 0.010),
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
                int(random.randint(5, 30)),
                random.choice(["Active", "Active", "Active", "Delayed", "Breakdown"]),  # some non-running too
                now,
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
# ✅ Zone buses (EXACT list inside circle)
# -----------------------------
def buses_inside_zone(stop_name: str) -> pd.DataFrame:
    places = get_places_data()
    srow = places[places["stop_name"] == stop_name].iloc[0]
    slat, slon = float(srow["latitude"]), float(srow["longitude"])

    buses_df = get_buses_data().copy()
    buses_df["dist_km"] = buses_df.apply(
        lambda r: haversine_km(float(r["latitude"]), float(r["longitude"]), slat, slon),
        axis=1
    )
    inside = buses_df[buses_df["dist_km"] <= STOP_RADIUS_KM].copy()
    if inside.empty:
        return inside

    def speed_kmh(bus_type, status):
        base = {"Ordinary": 32, "Semi-Deluxe": 36, "AC Deluxe": 40, "Volvo": 45, "Electric": 34}.get(bus_type, 35)
        if str(status).lower() == "delayed":
            return max(18, base * 0.6)
        return base

    inside["speed_kmh"] = inside.apply(lambda r: speed_kmh(r["bus_type"], r["status"]), axis=1)

    # ETA only for meaningful statuses; others show as NaN (rendered as "—")
    inside["eta_min"] = inside.apply(
        lambda r: int(max(1, min(180, round((r["dist_km"] / r["speed_kmh"]) * 60))))
        if is_eta_relevant(str(r["status"])) else None,
        axis=1
    )
    inside["eta_time"] = inside["eta_min"].apply(
        lambda m: (datetime.now() + timedelta(minutes=int(m))).strftime("%I:%M %p") if m is not None else None
    )

    # Sort: first buses with ETA (closest soon), then others by distance
    inside["eta_sort"] = inside["eta_min"].apply(lambda x: x if x is not None else 9999)
    inside = inside.sort_values(["eta_sort", "dist_km"]).drop(columns=["eta_sort"])
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
# Map
# -----------------------------
def create_live_bus_map_leaflet(
    buses_df: pd.DataFrame,
    focus_stop_name: str | None = None
):
    places_df = get_places_data()

    # Default map
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

    # Stop zone + nearby stops markers
    if focus_stop_name and focus_stop_name in places_df["stop_name"].tolist():
        srow = places_df[places_df["stop_name"] == focus_stop_name].iloc[0]
        slat, slon = float(srow["latitude"]), float(srow["longitude"])

        # Selected stop marker
        folium.Marker(
            location=[slat, slon],
            popup=folium.Popup(f"<b>📍 Selected Stop:</b> {focus_stop_name}", max_width=280),
            icon=folium.Icon(color="orange", icon="info-sign"),
        ).add_to(m)

        # Red circle zone
        folium.Circle(
            location=[slat, slon],
            radius=STOP_RADIUS_M,
            color="#ef4444",
            weight=3,
            fill=False,
        ).add_to(m)

        # Nearby stops inside zone (including selected)
        nearby = stops_within_radius(focus_stop_name, STOP_RADIUS_KM)
        for _, s in nearby.iterrows():
            name = s["stop_name"]
            lat, lon = float(s["latitude"]), float(s["longitude"])
            dist_m = int(round(float(s["dist_km"]) * 1000))

            # Different icon color for other nearby stops
            icon_color = "orange" if name == focus_stop_name else "green"
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(f"<b>🚌 Stop:</b> {name}<br>Distance from selected: {dist_m} m", max_width=320),
                icon=folium.Icon(color=icon_color, icon="flag"),
            ).add_to(m)

    # Bus markers
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
            popup=folium.Popup(pop, max_width=340),
        ).add_to(cluster)

    return m


def get_map_html_cached(stop_name: str | None):
    now = datetime.now()
    should_rebuild = (
        st.session_state.find_cached_map_html is None
        or st.session_state.find_cached_map_stop != stop_name
        or st.session_state.find_cached_map_at is None
        or (now - st.session_state.find_cached_map_at).total_seconds() > 20
    )
    if should_rebuild:
        buses_df = get_buses_data()
        m = create_live_bus_map_leaflet(buses_df, focus_stop_name=stop_name)
        st.session_state.find_cached_map_html = m.get_root().render()
        st.session_state.find_cached_map_at = now
        st.session_state.find_cached_map_stop = stop_name
    return st.session_state.find_cached_map_html, st.session_state.find_cached_map_at


# -----------------------------
# Demo user
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
# Language picker
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
        chosen_name = st.selectbox("", options=names, index=idx, label_visibility="collapsed")
    new_code = codes[names.index(chosen_name)]

    if new_code != st.session_state.lang:
        st.session_state.lang = new_code
        st.session_state.find_cached_map_html = None
        st.session_state.find_cached_map_at = None
        st.session_state.find_cached_map_stop = None
        st.rerun()


# -----------------------------
# Pages
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
          <div>📱 {tr('phone')}: <b>{user['phone']}</b></div>
          <div><b>{tr('note_no_booking')}</b></div>
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


def find_my_bus_page():
    st.markdown(f"<div class='main-header'>📍 {tr('find_my_bus_title')}</div>", unsafe_allow_html=True)
    st.caption(tr("find_my_bus_caption"))

    if st.button(f"← {tr('back')}"):
        st.session_state.page = "public_home"
        st.rerun()

    places = get_places_data()
    stop_names = places["stop_name"].tolist()

    stop = st.selectbox(tr("select_stop"), stop_names, index=0)

    left, right = st.columns([1.25, 1.75], gap="large")

    with left:
        # ✅ Exact bus list inside zone
        inside = buses_inside_zone(stop)
        nearby_stops = stops_within_radius(stop, STOP_RADIUS_KM)
        stop_list = ", ".join(nearby_stops["stop_name"].head(6).tolist())
        more = "" if len(nearby_stops) <= 6 else f" +{len(nearby_stops)-6} more"

        st.markdown(f"### 🚌 {tr('next_buses')}")
        st.markdown(
            f"<div class='card'><div class='sub-header'>{tr('buses_in_zone')}: <span class='pill'>{len(inside)}</span></div>"
            f"<div style='margin-top:6px; font-weight:800;'>{tr('zone_includes_stops')}:</div>"
            f"<div style='opacity:0.9;'>{stop_list}{more}</div></div>",
            unsafe_allow_html=True
        )

        if inside.empty:
            st.warning(tr("no_buses_in_zone"))
        else:
            # List ALL buses inside zone (no limit) so it matches exact count.
            for _, b in inside.iterrows():
                crowd_lbl, crowd_cls = crowd_level(int(b["passengers"]), int(b["capacity"]))
                st_lbl, st_cls = status_pill(str(b["status"]))

                eta_min = b.get("eta_min", None)
                eta_time = b.get("eta_time", None)
                eta_block = (
                    f"<div style='font-size:1.6rem; font-weight:900; color:#9a3412;'>{int(eta_min)} {tr('min')}</div>"
                    f"<div style='opacity:0.85;'>{tr('arrives')} {eta_time}</div>"
                    if eta_min is not None else
                    f"<div style='font-size:1.6rem; font-weight:900; color:#9a3412;'>—</div>"
                    f"<div style='opacity:0.85;'>{tr('arrives')} —</div>"
                )

                st.markdown(
                    f"""
                    <div class="card">
                      <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:14px;">
                        <div>
                          <div class="sub-header">🚌 {b['bus_number']} <span class="{st_cls}">{st_lbl}</span></div>
                          <div><b>{tr('route')}:</b> {b['route_name']} ({b['start_point']} → {b['end_point']})</div>
                          <div><b>{tr('type')}:</b> {b['bus_type']} • <b>{tr('crowd')}:</b> <span class="{crowd_cls}">{crowd_lbl}</span> • {b['passengers']}/{b['capacity']}</div>
                          <div style="opacity:0.8;"><b>Distance:</b> {b['dist_km']:.2f} km</div>
                        </div>
                        <div style="text-align:right;">
                          {eta_block}
                        </div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True
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
        map_html, built_at = get_map_html_cached(stop_name=stop)
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
          <div><b>{tr('valid_until')}:</b> {p['valid_until']}</div>
          <div><b>{tr('pass_id')}:</b> {p['pass_id']}</div>
          <div><b>{tr('reminder_no_booking')}</b></div>
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
          <div><b>{tr('route')}:</b> {current['route_name']} ({current['start_point']} → {current['end_point']})</div>
          <div><b>{tr('current')}:</b> {current['latitude']:.5f}, {current['longitude']:.5f} • <b>{tr('passengers')}:</b> {current['passengers']}/{current['capacity']} • <b>{tr('status')}:</b> {current['status']}</div>
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

    # Deep link (pass)
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