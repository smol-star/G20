import json
import os
from datetime import datetime
from fpdf import FPDF
import requests

DATA_FILE = "current_trends.json"
ARCHIVE_DIR = "archive"
FONT_PATH = "NanumGothic.ttf"

def ensure_font_exists():
    if not os.path.exists(FONT_PATH):
        print("Downloading NanumGothic font...")
        url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
        r = requests.get(url)
        with open(FONT_PATH, "wb") as f:
            f.write(r.content)

def load_current_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_current_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def reset_and_archive():
    data = load_current_data()
    if not data:
        return
        
    date_str = datetime.now().strftime("%Y-%m-%d")
    month_dir = datetime.now().strftime("%Y-%m")
    save_dir = os.path.join(ARCHIVE_DIR, month_dir)
    os.makedirs(save_dir, exist_ok=True)
    
    pdf_path = os.path.join(save_dir, f"{date_str}.pdf")
    
    ensure_font_exists()
    
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("NanumGothic", "", FONT_PATH, uni=True)
    pdf.set_font("NanumGothic", size=16)
    
    pdf.cell(200, 10, txt=f"G20 트렌드 리포트 ({date_str})", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("NanumGothic", size=10)
    
    # data structure we expect: 
    # data['logs'][timestamp] = list of trends
    # or just data = list of latest trends
    for country, tr_list in data.items():
        pdf.set_font("NanumGothic", size=14)
        pdf.cell(200, 10, txt=f"[{country}]", ln=True)
        pdf.set_font("NanumGothic", size=10)
        
        for idx, t in enumerate(tr_list):
            # Write wrapped text instead of cell
            issue_text = f"{idx+1}. {t['title']} (언급량: {t.get('volume', '알수없음')})"
            pdf.multi_cell(0, 8, txt=issue_text)
            
            # Write 3-line summary
            summary = t.get('summary', [])
            for s_line in summary:
                pdf.multi_cell(0, 6, txt=f"  - {s_line}")
            pdf.ln(2)
        pdf.ln(5)

    pdf.output(pdf_path)
    print(f"Archived to PDF: {pdf_path}")
    
    # Reset data
    save_current_data({})
