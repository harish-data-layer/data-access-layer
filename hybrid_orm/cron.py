import time
import schedule
from datetime import datetime
import pull_service

def scheduled_job():
    """The task that runs when the schedule triggers."""
    print("\n" + "="*60)
    print(f"[CRON TRIGGERED] Running Automated SAP Sync at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        # Calls your main logic directly from pull_service.py
        pull_service.fetch_and_store()
    except Exception as e:
        print(f"[CRON ERROR] Sync failed with error: {e}")

# =====================================================================
# CRON SCHEDULE CONFIGURATION
# =====================================================================
# This script will wait in the background and pull data AUTOMATICALLY
# ONLY when the clock strikes the EXACT time you configure below. 

# 24-hour time format ("HH:MM")
# 10:00 PM = "22:00"
schedule.every().day.at("22:00").do(scheduled_job)   # Runs at exactly 10:00 PM every night!

# If you want to add more times, just copy the line above.
# Example: schedule.every().day.at("04:30").do(scheduled_job)  # 4:30 AM



# =====================================================================
# START CRON ENGINE
# =====================================================================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  AUTOMATED CRON STARTED")
    print("  Leave this terminal window open for continuous syncing.")
    print("="*60)
    
    # Optional: Run immediately once when you start the terminal
    # scheduled_job() 

    # Infinite loop to keep the python script alive and checking the clock
    while True:
        schedule.run_pending()
        time.sleep(1) # Check the clock every 1 second
