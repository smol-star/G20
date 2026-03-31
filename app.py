import streamlit as st
import pandas as pd
from data_manager import load_current_data, ARCHIVE_DIR
from datetime import datetime, timedelta
import os
import json

st.set_page_config(page_title="G20 실시간 뉴스 헤드라인 보드", layout="wide")

FLAG_CODES = {
    'United States': 'us', 'China': 'cn', 'Germany': 'de', 'Japan': 'jp',
    'India': 'in', 'United Kingdom': 'gb', 'France': 'fr', 'Italy': 'it',
    'Brazil': 'br', 'Canada': 'ca', 'Russia': 'ru', 'Mexico': 'mx',
    'Australia': 'au', 'South Korea': 'kr', 'Indonesia': 'id', 'Turkey': 'tr',
    'Saudi Arabia': 'sa', 'Argentina': 'ar', 'South Africa': 'za'
}

def render_dashboard(data, kst_now):
    st.divider()
    for country, info in data.items():
        score = info.get("spike_score", 0.0)
        rank = info.get("gdp_rank", 99)
        current_rank = info.get("current_rank", 99)
        previous_rank = info.get("previous_rank", current_rank)
        updated = info.get("last_updated", "N/A")
        
        rank_change = previous_rank - current_rank
        if rank_change > 0:
            change_badge = f"<span style='color: #ff4bc6; font-size: 0.8em; margin-left: 10px;'>▲ {rank_change}</span>"
        elif rank_change < 0:
            change_badge = f"<span style='color: #4b88ff; font-size: 0.8em; margin-left: 10px;'>▼ {abs(rank_change)}</span>"
        else:
            change_badge = f"<span style='color: #888; font-size: 0.8em; margin-left: 10px;'>-</span>"
            
        flag_code = FLAG_CODES.get(country, 'kr')
        
        st.markdown(f'''
            <div style="display: flex; align-items: center; margin-top: 20px; margin-bottom: 5px;">
                <span style="font-size: 1.2em; font-weight: bold; margin-right: 12px; color: #555;">{current_rank}위</span>
                <img src="https://flagcdn.com/w40/{flag_code}.png" width="36" style="border: 1px solid #e0e0e0; border-radius: 4px; margin-right: 12px; box-shadow: 0px 2px 4px rgba(0,0,0,0.1);">
                <h3 style="margin: 0; padding: 0;">{country} <span style="font-size: 0.7em; font-weight: normal; color: #888;">(GDP: {rank}위)</span> {change_badge}</h3>
            </div>
        ''', unsafe_allow_html=True)
        
        with st.expander(f"👉 이 곳을 눌러서 {country} 주요 뉴스 펼쳐보기", expanded=False):
            st.caption(f"🔄 최근 데이터 갱신 시간: {updated} (UTC) &nbsp;|&nbsp; ⏰ 기록 시간: {kst_now}")
            
            trends = info.get("trends", [])
            if not trends:
                st.write("수집된 트렌드가 없거나 Google 지원 대상 국가가 아닙니다.")
            
            for idx, t in enumerate(trends):
                category = t.get('category', '서브 이슈')
                category_color = "#ff4bc6" if category == "메인 이슈" else "#4b88ff"
                
                # HOT 뱃지: 발행 시점이 3시간 미만인 경우
                hot_badge = ""
                pub_dt_str = t.get('pub_datetime_utc')
                if pub_dt_str:
                    try:
                        from datetime import timezone
                        pub_dt = datetime.strptime(pub_dt_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                        diff_hours = (datetime.now(timezone.utc) - pub_dt).total_seconds() / 3600
                        if diff_hours < 3:
                            hot_badge = "<span style='background: linear-gradient(135deg, #ff4500, #ff8c00); color: white; font-size: 0.6em; font-weight: bold; border-radius: 4px; padding: 2px 6px; vertical-align: middle; margin-right: 6px; letter-spacing: 0.5px;'>🔥 HOT</span>"
                    except:
                        pass
                
                st.markdown(f"<p style='font-size: 1.2em; font-weight: bold; margin: 6px 0 2px 0;'>{idx+1}. <span style='color: {category_color}; font-size: 0.65em; border: 1px solid {category_color}; border-radius: 4px; padding: 2px 6px; vertical-align: middle; margin-right: 8px;'>{category}</span>{hot_badge}{t['title']}</p>", unsafe_allow_html=True)
                
                st.markdown(f"*(원문 뉴스 제목: {t['original_title']})*")
                
                pub_date = t.get('pub_date', '보도 시간 없음')
                st.markdown(f"🕒 **보도 시간:** {pub_date}")
                
                link_url = t.get('link', '#')
                st.markdown(f"🔗 [[기사 원문 보기]({link_url})]")
                
                if idx < len(trends) - 1:
                    st.markdown("<div style='border-top: 1px solid #e0e0e0; margin: 6px 0;'></div>", unsafe_allow_html=True)


page = st.sidebar.radio("메뉴", ["실시간 뉴스 보드", "과거 기록 보기"])

if page == "실시간 뉴스 보드":
    st.title("🌐 G20 실시간 글로벌 뉴스 헤드라인 브리핑")
    st.markdown("GDP 상위 G20 국가들의 구글 뉴스 메인 속보들을 수집하여 한국어로 제공합니다.")
    st.markdown("💡 **정렬 기준**: 기본적으로 GDP 순위로 정렬되지만, 전 세계 포털에 '새로운 속보'가 다수 등장한 국가는 위로 자동 배치됩니다.")
    st.markdown("🔥 **HOT 뱃지**: 기사가 발행된 지 **3시간 이내**인 따끈따끈한 최신 속보에만 부여됩니다.")
    
    data = load_current_data()
    if not data:
        st.info("데이터를 수집 중입니다. 백그라운드 수집기가 실행될 때까지 잠시만 대기해 주세요.")
    else:
        from datetime import datetime, timezone, timedelta
        kst = timezone(timedelta(hours=9))
        now_kst = datetime.now(kst)
        today_str = now_kst.strftime("%Y-%m-%d")
        history_dir = os.path.join("hourly_archive", today_str)
        
        options = ["⚡ 실시간 최신 (현재)"]
        snapshot_files = {}
        if os.path.exists(history_dir):
            for file in sorted(os.listdir(history_dir), reverse=True):
                if file.endswith(".json"):
                    hour_str = file.replace(".json", "")
                    label = f"🕒 오늘 {hour_str}시 기록"
                    options.append(label)
                    snapshot_files[label] = os.path.join(history_dir, file)
                    
        if len(options) > 1:
            selected_time = st.selectbox("⏳ 시간대 선택 (오늘의 과거 기록 열람):", options)
        else:
            selected_time = options[0]
            
        if selected_time == "⚡ 실시간 최신 (현재)":
            display_data = data
            time_label = now_kst.strftime("%Y-%m-%d %H:%M:%S (KST)")
        else:
            with open(snapshot_files[selected_time], "r", encoding="utf-8") as f:
                display_data = json.load(f)
            time_label = f"{today_str} {selected_time.replace('🕒 오늘 ', '').replace('시 기록', '')}:00:00 (KST)"
            st.info(f"선택하신 시간 단위({time_label})의 뉴스 트렌드입니다. 실시간과 순위나 내용이 다를 수 있습니다.")
            
        render_dashboard(display_data, time_label)

else:
    st.title("📜 G20 과거 뉴스 기록 보관소")
    st.markdown("이전에 저장된 G20 뉴스 트렌드 데이터를 다시 확인하거나 PDF를 다운로드할 수 있습니다.")
    
    if not os.path.exists(ARCHIVE_DIR):
        st.info("아직 저장된 과거 기록이 없습니다.")
    else:
        archives = []
        for month_dir in sorted(os.listdir(ARCHIVE_DIR), reverse=True):
            month_path = os.path.join(ARCHIVE_DIR, month_dir)
            if os.path.isdir(month_path):
                for file in sorted(os.listdir(month_path), reverse=True):
                    if file.endswith(".json") or file.endswith(".pdf"):
                        date_str = file.split('.')[0]
                        if date_str not in archives:
                            archives.append(date_str)
                            
        if not archives:
            st.info("아직 저장된 과거 기록이 없습니다.")
        else:
            selected_date = st.selectbox("📅 확인하고 싶은 날짜를 선택하세요:", archives)
            
            month_str = selected_date[:7]
            json_path = os.path.join(ARCHIVE_DIR, month_str, f"{selected_date}.json")
            pdf_path = os.path.join(ARCHIVE_DIR, month_str, f"{selected_date}.pdf")
            
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label="📄 이 날짜의 PDF 리포트 파일 다운로드",
                        data=f.read(),
                        file_name=f"{selected_date}_G20_Report.pdf",
                        mime="application/pdf"
                    )
                    
            if os.path.exists(json_path):
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        archive_data = json.load(f)
                    st.success(f"{selected_date} 일자의 상세 데이터를 불러왔습니다.")
                    render_dashboard(archive_data, f"{selected_date} (과거 보존 데이터)")
                except Exception as e:
                    st.error("데이터를 불러오는 중 오류가 발생했습니다.")
            else:
                st.warning("해당 날짜의 상세 JSON 데이터가 존재하지 않아 화면에 표시할 수 없습니다. (PDF 다운로드 기능만 제공됩니다)")
