import multiprocessing
import os
import sys
import time
import run_scheduler
import streamlit.web.cli as stcli

def start_scheduler():
    run_scheduler.fetch_and_update_trends()
    import schedule
    schedule.every().hour.do(run_scheduler.job_hourly)
    schedule.every().day.at("00:00").do(run_scheduler.job_midnight)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    multiprocessing.freeze_support()
    
    # Start scheduler in a background process
    p = multiprocessing.Process(target=start_scheduler)
    p.daemon = True
    p.start()
    
    # Resolve the path to app.py when bundled
    if getattr(sys, 'frozen', False):
        app_path = os.path.join(sys._MEIPASS, 'app.py')
    else:
        app_path = 'app.py'
        
    sys.argv = ["streamlit", "run", app_path, "--global.developmentMode=false"]
    sys.exit(stcli.main())
