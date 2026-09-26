import subprocess
import sys
import re
import time
from datetime import datetime
from live_tracker import record_new_point

# আপনার ট্র্যাকারের নম্বর (মেনুতে ২ নম্বরে ছিল)
TRACKER_OPTION = "2\n"
POLL_INTERVAL_SECONDS = 120  # প্রতি ২ মিনিট পর পর গুগল সার্ভার থেকে চেক করবে

def query_google_fmd():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Querying Google FMD Network...")
    
    # main.py স্ক্রিপ্ট সাবপ্রসেসে রান করা
    process = subprocess.Popen(
        [sys.executable, "main.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    # ট্র্যাকার নম্বর সিলেক্ট করে কমান্ড পাঠানো
    try:
        stdout, _ = process.communicate(input=TRACKER_OPTION, timeout=60)
    except subprocess.TimeoutExpired:
        process.kill()
        print("Request timed out. Google servers or FCM took too long.")
        return

    # আউটপুট থেকে ডেটা খোঁজা
    lat_match = re.search(r"Latitude:\s*([-+]?\d*\.?\d+)", stdout)
    lon_match = re.search(r"Longitude:\s*([-+]?\d*\.?\d+)", stdout)
    time_match = re.search(r"Time:\s*([^\r\n]+)", stdout)

    if lat_match and lon_match:
        lat = float(lat_match.group(1))
        lon = float(lon_match.group(1))
        report_time = time_match.group(1).strip() if time_match else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"-> Location Received!")
        print(f"   Latitude : {lat}")
        print(f"   Longitude: {lon}")
        print(f"   Seen Time: {report_time}")

        # লাইভ ম্যাপে রেকর্ড যোগ ও স্যাটেলাইট রেন্ডার
        record_new_point(lat, lon, report_time)
    else:
        print("No decrypted location block found in output.")
        # সমস্যা ডায়াগনসিস করার সুবিধার্থে স্ক্রিপ্ট রেসপন্স
        for line in stdout.splitlines():
            if "LocationRequest" in line or "DecryptLocations" in line or "Error" in line:
                print(f"   [Debug Log] {line}")

if __name__ == "__main__":
    print("=" * 55)
    print("Google Find My Device - Real-Time Background Daemon")
    print("=" * 55)
    
    while True:
        try:
            query_google_fmd()
        except KeyboardInterrupt:
            print("\nDaemon terminated by user.")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")

        print(f"Next query in {POLL_INTERVAL_SECONDS} seconds...")
        time.sleep(POLL_INTERVAL_SECONDS)

        import subprocess

def git_auto_sync():
    try:
        subprocess.run(["git", "add", "location_history.json"], check=True)
        subprocess.run(["git", "commit", "-m", "Auto-update live scooter location"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("Successfully synced location history to GitHub & Vercel!")
    except Exception as e:
        print(f"Git sync skipped or failed: {e}")
