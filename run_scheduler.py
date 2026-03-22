import schedule
import time
from fetcher import fetch_and_update_trends
from data_manager import reset_and_archive

def job_hourly():
    fetch_and_update_trends()

def job_midnight():
    print("Executing Midnight Reset & PDF Archive...")
    reset_and_archive()
    # Fetch initial data for the new day
    fetch_and_update_trends()

if __name__ == "__main__":
    print("Starting Initial Fetch before entering schedule loop...")
    fetch_and_update_trends()

    # Schedule hourly job
    schedule.every().hour.do(job_hourly)
    
    # Schedule midnight archive job
    schedule.every().day.at("00:00").do(job_midnight)

    print("Scheduler activated. Listening for next job...")
    while True:
        schedule.run_pending()
        time.sleep(60)
