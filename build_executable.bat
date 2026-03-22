@echo off
echo ===========================================
echo Building G20 Dashboard Executable...
echo ===========================================

echo Installing required Python packages...
.\conda\Scripts\pip install pyinstaller streamlit pandas pytrends deep-translator schedule fpdf2 requests

echo Compiling Application...
.\conda\Scripts\pyinstaller --noconfirm --onefile --windowed --add-data "conda\Lib\site-packages\streamlit\static;streamlit\static" run_dashboard.py

echo Done! The executable is located in the 'dist' folder.
