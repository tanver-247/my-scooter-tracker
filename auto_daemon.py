import subprocess
import sys
import re
import time
from datetime import datetime
from live_tracker import record_new_point

# আপনার ট্র্যাকারের নম্বর (আপনার আগের কনফিগারেশন অনুযায়ী ২ নম্বর ট্র্যাকারের জন্য)
TRACKER_OPTION = "2\n"
POLL_INTERVAL_SECONDS = 120  # প্রতি ২ মিনিট পর পর চেক করবে

def git_auto_sync():
    """নতুন লোকেশন ফাইল গিটহাবে পুশ করার ফাংশন"""
    try:
        subprocess.run(["git", "add", "location_history.json"], check=True, capture_output=True)
        # যদি কোনো চেঞ্জ না থাকে তবে কমিট স্কিপ করার জন্য চেক
        result = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
        if result.returncode != 0:
            subprocess.run(["git", "commit", "-m", "Auto-update live scooter location"], check=True, capture_output=True)
            subprocess.run(["git", "push", "origin", "main"], check=True, capture_output=True)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Successfully synced to GitHub/Vercel 🚀")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Location unchanged, skipping git push.")
    except Exception as e:
        print(f"Git sync warning: {e}")

def query_google_fmd():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Querying Google FMD Network...")
    
    # main.py সাবপ্রসেসে রান করে ডেটা ফেচ করা
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
        print("Request timed out. Google servers or FCM took too long.")
        return

    # আউটপুট থেকে কোঅর্ডিনেট পার্স করা
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

        # লোকাল হিস্ট্রি ফাইলে রেকর্ড যোগ করা
        record_new_point(lat, lon, report_time)

        # সাথে সাথে গিটহাব ও ভেরসেলে পুশ করা
        git_auto_sync()
    else:
        print("No decrypted location block found in current response.")

if __name__ == "__main__":
    print("=" * 55)
    print(" Scooter Live Daemon Started (Local to Vercel Sync) ")
    print("=" * 55)
    
    while True:
        try:
            query_google_fmd()
        except KeyboardInterrupt:
            print("\nDaemon terminated by user.")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")

        print(f"Waiting {POLL_INTERVAL_SECONDS} seconds for next check...")
        time.sleep(POLL_INTERVAL_SECONDS)