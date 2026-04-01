import json
import os
from datetime import datetime, timezone, timedelta
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
    # 1. 항상 메인 파일 저장 (최우선, 절대 실패 불가)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    # 2. 시간별 스냅샷 저장: hourly_archive/YYYY-MM-DD/HH.json
    try:
        kst = timezone(timedelta(hours=9))
        now_kst = datetime.now(kst)
        date_str = now_kst.strftime("%Y-%m-%d")
        hour_str = now_kst.strftime("%H")
        
        snapshot_dir = os.path.join("hourly_archive", date_str)
        os.makedirs(snapshot_dir, exist_ok=True)
        
        snapshot_file = os.path.join(snapshot_dir, f"{hour_str}.json")
        with open(snapshot_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"[Archive] 스냅샷 저장 완료: {snapshot_file}")
    except Exception as e:
        print(f"[Archive] 스냅샷 저장 실패 (메인 파일은 정상 저장됨): {e}")

def reset_and_archive():
    data = load_current_data()
    if not data:
        return
        
    kst = timezone(timedelta(hours=9))
    # Archive the day that just ended (if run at midnight), or same day if run later. 
    archive_time = datetime.now(kst) - timedelta(hours=1)
    
    date_str = archive_time.strftime("%Y-%m-%d")
    month_dir = archive_time.strftime("%Y-%m")
    save_dir = os.path.join(ARCHIVE_DIR, month_dir)
    os.makedirs(save_dir, exist_ok=True)
    
    pdf_path = os.path.join(save_dir, f"{date_str}.pdf")
    
    json_path = os.path.join(save_dir, f"{date_str}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    ensure_font_exists()
    
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("NanumGothic", "", FONT_PATH)
    pdf.set_font("NanumGothic", size=16)
    
    pdf.cell(200, 10, txt=f"G20 트렌드 리포트 ({date_str})", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("NanumGothic", size=10)
    
    for country, info in data.items():
        # info는 dict: {"gdp_rank": ..., "trends": [...], ...}
        if not isinstance(info, dict):
            continue
        trends = info.get("trends", [])
        if not trends:
            continue
            
        pdf.set_font("NanumGothic", size=14)
        pdf.cell(200, 10, txt=f"[{country}]", ln=True)
        pdf.set_font("NanumGothic", size=10)
        
        for idx, t in enumerate(trends):
            # 구 데이터('title')와 신 데이터('keyword') 모두 지원
            issue_label = t.get('keyword', t.get('title', '이슈'))
            hook_text = t.get('hook', '')
            issue_text = f"{idx+1}. {issue_label}"
            pdf.multi_cell(0, 8, txt=issue_text)
            
            if hook_text:
                pdf.multi_cell(0, 6, txt=f"  → {hook_text[:100]}")

        pdf.ln(5)

    pdf.output(pdf_path)
    print(f"Archived to PDF: {pdf_path}")
    
    # Reset data
    save_current_data({})
