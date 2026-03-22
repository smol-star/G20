@echo off
echo ==============================================
echo G20 Trends Dashboard Launcher
echo ==============================================
echo 시스템의 Python 환경을 확인하고 프로그램을 실행합니다...

:: 백그라운드에서 스케줄러 실행
start /B python run_scheduler.py

:: 프론트엔드 대시보드 실행
python -m streamlit run app.py

pause
