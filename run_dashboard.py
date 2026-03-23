import multiprocessing
import os
import sys
import time
import schedule
from fetcher import fetch_and_update_trends
from data_manager import reset_and_archive
from datetime import datetime

LOG_FILE = "scheduler.log"

def log(msg):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def job_hourly():
    log("⏰ 1시간 경과 — 뉴스 트렌드 갱신 시작")
    try:
        fetch_and_update_trends()
        log("✅ 갱신 완료")
    except Exception as e:
        log(f"❌ 갱신 중 오류 발생: {e}")

def job_midnight():
    log("🌙 자정 도달 — PDF 아카이브 저장 및 데이터 초기화 시작")
    try:
        reset_and_archive()
        log("✅ PDF 저장 및 초기화 완료")
        fetch_and_update_trends()
        log("✅ 새 날 초기 뉴스 수집 완료")
    except Exception as e:
        log(f"❌ 자정 처리 중 오류: {e}")

def start_scheduler():
    log("🚀 스케줄러 시작 — 초기 뉴스 수집 중...")
    try:
        fetch_and_update_trends()
        log("✅ 초기 수집 완료")
    except Exception as e:
        log(f"❌ 초기 수집 오류: {e}")

    schedule.every().hour.do(job_hourly)
    schedule.every().day.at("00:00").do(job_midnight)

    log("📅 스케줄 등록 완료: 매시 정각 갱신 + 자정 PDF 아카이브")

    while True:
        schedule.run_pending()
        time.sleep(30)

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

    import streamlit.web.cli as stcli
    sys.exit(stcli.main())
