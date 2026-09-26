import time
from live_tracker import record_new_point

# 1. আপনার রেজিস্টার্ড ট্র্যাকারের ইনডেক্স বা ডিভাইস আইডি নিশ্চিত করুন
# 2. nbe_list_devices বা SpotApi থেকে ফেচ ফাংশন কল করার লুপ

INTERVAL_MINUTES = 3

print("Starting Auto Location Logger...")

while True:
    try:
        # TODO: আপনার রিপোর ফেচ ফাংশন কল করে lat, lon এবং report_time আনুন
        # উদাহরণ:
        # lat, lon, report_time = fetch_latest_location()
        # record_new_point(lat, lon, report_time)
        print("Checking for location updates from Google servers...")
        
        # পোলিং ব্যবধান
        time.sleep(INTERVAL_MINUTES * 60)
    except KeyboardInterrupt:
        print("Stopping Auto Logger.")
        break
    except Exception as e:
        print(f"Error fetching data: {e}")
        time.sleep(60)