import subprocess
import sys
import re
import time
import os
import json
from datetime import datetime

# কনফিগারেশন
TRACKER_OPTION = "2\n"  # আপনার ট্র্যাকারের মেনু ইনডেক্স
POLL_INTERVAL_SECONDS = 30  # প্রতি 30 পর পর গুগল সার্ভার চেক করবে
HISTORY_FILE = "public/location_history.json"
MAP_FILE = "public/index.html"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_history(history):
    os.makedirs("public", exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)

def generate_dashboard_html(history):
    if not history:
        return
    
    last_point = history[-1]
    center_lat = last_point["lat"]
    center_lon = last_point["lon"]
    history_json = json.dumps(history)

    # পাইথনের ফরম্যাটিং এড়ানোর জন্য প্লেইন স্ট্রিং ব্যবহার করা হয়েছে
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scooter Live 3D Tracking Dashboard</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body, html {{ margin: 0; padding: 0; width: 100%; height: 100%; font-family: sans-serif; background: #0f172a; }}
        #map {{ width: 100%; height: 100%; }}
        .hud {{
            position: absolute;
            top: 15px;
            left: 55px;
            z-index: 1000;
            background: rgba(15, 23, 42, 0.9);
            color: #ffffff;
            padding: 14px 20px;
            border-radius: 10px;
            backdrop-filter: blur(8px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.4);
            border: 1px solid rgba(255,255,255,0.15);
        }}
        .hud h2 {{ margin: 0 0 6px 0; font-size: 16px; font-weight: 600; color: #38bdf8; display: flex; align-items: center; gap: 8px; }}
        .hud p {{ margin: 4px 0; font-size: 13px; color: #cbd5e1; }}
        .live-badge {{
            width: 9px;
            height: 9px;
            background-color: #22c55e;
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 8px #22c55e;
            animation: pulse 1.5s infinite;
        }}
        @keyframes pulse {{
            0% {{ transform: scale(0.95); opacity: 0.8; }}
            50% {{ transform: scale(1.2); opacity: 1; }}
            100% {{ transform: scale(0.95); opacity: 0.8; }}
        }}
    </style>
</head>
<body>
    <div class="hud">
        <h2><span class="live-badge"></span> Scooter Live Tracker</h2>
        <p><strong>Status:</strong> <span style="color: #22c55e;">Connected & Live</span></p>
        <p><strong>Last Seen:</strong> {last_point["time"]}</p>
        <p><strong>Coordinates:</strong> {center_lat:.6f}, {center_lon:.6f}</p>
        <p><strong>Total History Points:</strong> {len(history)}</p>
    </div>

    <div id="map"></div>

    <script>
        const historyData = {history_json};
        const map = L.map('map').setView([{center_lat}, {center_lon}], 16);

        L.tileLayer('https://mt1.google.com/vt/lyrs=y&x={{x}}&y={{y}}&z={{z}}', {{
            maxZoom: 20,
            subdomains: ['mt0', 'mt1', 'mt2', 'mt3']
        }}).addTo(map);

        const scooterIcon = L.divIcon({{
            className: 'custom-scooter-marker',
            html: '<div style="font-size: 28px; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.6)); transform: rotate(-25deg);">🛵</div>',
            iconSize: [35, 35],
            iconAnchor: [17, 17]
        }});

        const latlngs = [];
        historyData.forEach((point, index) => {{
            const pos = [point.lat, point.lon];
            latlngs.push(pos);

            if (index === historyData.length - 1) {{
                L.marker(pos, {{ icon: scooterIcon }}).addTo(map)
                    .bindPopup("<b>Scooter Live Location</b><br>Time: " + point.time).openPopup();
            }} else {{
                L.circleMarker(pos, {{
                    radius: 4,
                    color: '#38bdf8',
                    fillColor: '#38bdf8',
                    fillOpacity: 0.8
                }}).addTo(map).bindPopup("History: " + point.time);
            }}
        }});

        if (latlngs.length > 1) {{
            L.polyline(latlngs, {{
                color: '#38bdf8',
                weight: 5,
                opacity: 0.85,
                smoothFactor: 1
            }}).addTo(map);
        }}
    </script>
</body>
</html>"""

    os.makedirs("public", exist_ok=True)
    with open(MAP_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Master Dashboard Generated -> {MAP_FILE}")

def record_new_point(lat, lon, timestamp):
    history = load_history()
    if not timestamp:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if history and history[-1]["lat"] == lat and history[-1]["lon"] == lon:
        print("Device is stationary. Updating timestamp...")
        history[-1]["time"] = timestamp
    else:
        history.append({
            "lat": lat,
            "lon": lon,
            "time": timestamp
        })
        print(f"New position recorded -> Lat: {lat}, Lon: {lon}")

    save_history(history)
    generate_dashboard_html(history)

def git_auto_sync():
    try:
        subprocess.run(["git", "add", "public/"], check=True, capture_output=True)
        result = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
        if result.returncode != 0:
            subprocess.run(["git", "commit", "-m", "Auto-update live scooter data & dashboard"], check=True, capture_output=True)
            subprocess.run(["git", "push", "origin", "main"], check=True, capture_output=True)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Pushed to GitHub & Vercel successfully 🚀")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] No changes to push.")
    except Exception as e:
        print(f"Git sync notice: {e}")

def query_google_fmd():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Querying Google FMD Network...")
    
    process = subprocess.Popen(
        [sys.executable, "main.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    try:
        stdout, _ = process.communicate(input=TRACKER_OPTION, timeout=60)
    except subprocess.TimeoutExpired:
        process.kill()
        print("Request timed out.")
        return

    lat_match = re.search(r"Latitude:\s*([-+]?\d*\.?\d+)", stdout)
    lon_match = re.search(r"Longitude:\s*([-+]?\d*\.?\d+)", stdout)
    time_match = re.search(r"Time:\s*([^\r\n]+)", stdout)

    if lat_match and lon_match:
        lat = float(lat_match.group(1))
        lon = float(lon_match.group(1))
        report_time = time_match.group(1).strip() if time_match else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"-> Success! Lat: {lat} | Lon: {lon} | Time: {report_time}")
        record_new_point(lat, lon, report_time)
        git_auto_sync()
    else:
        print("No decrypted location block found in current response.")

if __name__ == "__main__":
    print("=" * 60)
    print(" Master Scooter Live Tracking Daemon Started ")
    print("=" * 60)
    
    while True:
        try:
            query_google_fmd()
        except KeyboardInterrupt:
            print("\nDaemon stopped by user.")
            break
        except Exception as e:
            print(f"Error: {e}")

        print(f"Next query in {POLL_INTERVAL_SECONDS} seconds...\n")
        time.sleep(POLL_INTERVAL_SECONDS)
