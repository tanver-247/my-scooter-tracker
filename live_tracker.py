import json
import os
from datetime import datetime

HISTORY_FILE = "location_history.json"
MAP_FILE = "live_map.html"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

def update_map(history):
    if not history:
        print("No history available to plot.")
        return

    last_point = history[-1]
    center_lat = last_point["lat"]
    center_lon = last_point["lon"]

    history_json = json.dumps(history)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scooter Live Tracking Dashboard</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body, html {{ margin: 0; padding: 0; width: 100%; height: 100%; font-family: sans-serif; }}
        #map {{ width: 100%; height: 100%; }}
        .hud {{
            position: absolute;
            top: 15px;
            left: 55px;
            z-index: 1000;
            background: rgba(15, 23, 42, 0.85);
            color: #ffffff;
            padding: 12px 18px;
            border-radius: 8px;
            backdrop-filter: blur(6px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .hud h2 {{ margin: 0 0 5px 0; font-size: 15px; font-weight: 600; color: #38bdf8; }}
        .hud p {{ margin: 3px 0; font-size: 13px; color: #e2e8f0; }}
        .hud .live-badge {{
            display: inline-block;
            width: 8px;
            height: 8px;
            background-color: #22c55e;
            border-radius: 50%;
            margin-right: 6px;
        }}
    </style>
</head>
<body>
    <div class="hud">
        <h2><span class="live-badge"></span>Scooter Tracker (Google FMD)</h2>
        <p><strong>Last Seen:</strong> {last_point["time"]}</p>
        <p><strong>Coordinates:</strong> {center_lat:.6f}, {center_lon:.6f}</p>
        <p><strong>Total Points:</strong> {len(history)}</p>
    </div>

    <div id="map"></div>

    <script>
        const historyData = {history_json};
        const centerLat = {center_lat};
        const centerLon = {center_lon};

        const map = L.map('map').setView([centerLat, centerLon], 16);

        // Google Hybrid Satellite Layer
        const googleSat = L.tileLayer('https://mt1.google.com/vt/lyrs=y&x={{x}}&y={{y}}&z={{z}}', {{
            maxZoom: 20,
            subdomains: ['mt0', 'mt1', 'mt2', 'mt3']
        }});

        // Google Streets Layer
        const googleStreets = L.tileLayer('https://mt1.google.com/vt/lyrs=m&x={{x}}&y={{y}}&z={{z}}', {{
            maxZoom: 20,
            subdomains: ['mt0', 'mt1', 'mt2', 'mt3']
        }});

        // Esri Satellite Layer
        const esriSat = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
            maxZoom: 19
        }});

        googleSat.addTo(map);

        const baseLayers = {{
            "Google Satellite": googleSat,
            "Google Streets": googleStreets,
            "Esri HD Satellite": esriSat
        }};
        L.control.layers(baseLayers).addTo(map);

        const latlngs = [];
        historyData.forEach((point, index) => {{
            const pos = [point.lat, point.lon];
            latlngs.push(pos);

            if (index === 0 && historyData.length > 1) {{
                L.circleMarker(pos, {{
                    radius: 7,
                    color: '#22c55e',
                    fillColor: '#22c55e',
                    fillOpacity: 1
                }}).addTo(map).bindPopup("<b>Trip Start:</b> " + point.time);
            }} else if (index === historyData.length - 1) {{
                L.circleMarker(pos, {{
                    radius: 9,
                    color: '#ffffff',
                    weight: 2,
                    fillColor: '#ef4444',
                    fillOpacity: 1
                }}).addTo(map).bindPopup("<b>Current Location:</b> " + point.time).openPopup();
            }} else {{
                L.circleMarker(pos, {{
                    radius: 3,
                    color: '#38bdf8',
                    fillColor: '#38bdf8',
                    fillOpacity: 0.8
                }}).addTo(map).bindPopup(point.time);
            }}
        }});

        if (latlngs.length > 1) {{
            L.polyline(latlngs, {{
                color: '#38bdf8',
                weight: 4,
                opacity: 0.85,
                smoothFactor: 1
            }}).addTo(map);
        }}

        // ২০ সেকেন্ড পর পর ব্রাউজার অটো রিফ্রেশ
        setTimeout(() => {{
            window.location.reload();
        }}, 20000);
    </script>
</body>
</html>"""

    with open(MAP_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Map file generated -> {MAP_FILE}")

def record_new_point(lat, lon, timestamp=None):
    history = load_history()
    if not timestamp:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # একই স্থানে থাকলেও টাইমস্ট্যাম্প আপডেট হবে কিন্তু পয়েন্ট লিস্ট বড় না করে ম্যাপটি রি-রাইট করবে
    if history and history[-1]["lat"] == lat and history[-1]["lon"] == lon:
        print("Device is stationary. Updating timestamp & rewriting map...")
        history[-1]["time"] = timestamp
    else:
        history.append({
            "lat": lat,
            "lon": lon,
            "time": timestamp
        })
        print(f"New position recorded: {lat}, {lon}")

    save_history(history)
    update_map(history)

if __name__ == "__main__":
    record_new_point(23.8174147, 90.5352147, "2026-09-26 20:14:45")
