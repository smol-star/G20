import streamlit as st
import pandas as pd
from data_manager import load_current_data, ARCHIVE_DIR
from datetime import datetime, timedelta, timezone
import os
import json

st.set_page_config(page_title="G20 실시간 뉴스 AI 보드 (RSS)", layout="wide")

FLAG_CODES = {
    'United States': 'us', 'China': 'cn', 'Germany': 'de', 'Japan': 'jp',
    'India': 'in', 'United Kingdom': 'gb', 'France': 'fr', 'Italy': 'it',
    'Brazil': 'br', 'Canada': 'ca', 'Russia': 'ru', 'Mexico': 'mx',
    'Australia': 'au', 'South Korea': 'kr', 'Indonesia': 'id', 'Turkey': 'tr',
    'Saudi Arabia': 'sa', 'Argentina': 'ar', 'South Africa': 'za'
}

def render_dashboard(data, time_label):
    st.divider()
    for country, info in data.items():
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
        
        with st.expander(f"👉 {country} AI 심층 분석 뉴스 보기", expanded=False):
            st.caption(f"🔄 마지막 갱신: {updated} | ⏰ 조회 기준: {time_label}")
            
            trends = info.get("trends", [])
            if not trends:
                st.write("수집된 트렌드가 없습니다.")
                continue
            
            for t in trends:
                keyword = t.get('keyword', '이슈 분석 중')
                hook = t.get('hook', '')
                script = t.get('script', '')
                original_title = t.get('original_title', '')
                link = t.get('link', '#')
                
                # HOT 뱃지 (RSS에서는 pub_datetime_utc 기준)
                hot_badge = ""
                pub_dt_str = t.get('pub_datetime_utc')
                if pub_dt_str:
                    try:
                        pub_dt = datetime.strptime(pub_dt_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                        diff_hours = (datetime.now(timezone.utc) - pub_dt).total_seconds() / 3600
                        if diff_hours < 3:
                            hot_badge = "<span style='background: linear-gradient(135deg, #ff4500, #ff8c00); color: white; font-size: 0.7em; font-weight: bold; border-radius: 4px; padding: 2px 6px; vertical-align: middle; margin-right: 8px;'>🔥 HOT</span>"
                    except: pass

                st.markdown(f"<h4>{hot_badge}{keyword}</h4>", unsafe_allow_html=True)
                
                if hook:
                    st.markdown(f"<div style='border-left: 4px solid #4b88ff; padding: 10px; background-color: #f0f4ff; margin: 10px 0;'>💡 <b>{hook}</b></div>", unsafe_allow_html=True)
                
                if script:
                    with st.container():
                        st.markdown("**🎙️ AI 요약 브리핑 대본**")
                        st.info(script)
                
                st.markdown(f"*(참조 기사: {original_title})*")
                st.markdown(f"🔗 [[기사 원문 보기]({link})]")

page = st.sidebar.radio("메뉴", ["AI 실시간 뉴스 보드", "과거 기록 보기"])

if page == "AI 실시간 뉴스 보드":
    st.title("🌐 G20 실시간 뉴스 AI 브리핑 (RSS)")
    st.markdown("전 세계 G20 국가의 주요 RSS 신호를 **Gemini AI**가 3시간 단위로 통합 분석한 대시보드입니다.")
    st.markdown("💡 **분석 방식**: 국가별 다수 기사를 종합하여 하나의 거대한 흐름(Context)을 파악하고 요약합니다.")
    
    data = load_current_data()
    if not data:
        st.info("데이터를 수집 중입니다. (3시간 주기로 자동 갱신됩니다)")
    else:
        kst = timezone(timedelta(hours=9))
        now_kst = datetime.now(kst)
        time_label = now_kst.strftime("%Y-%m-%d %H:%M:%S (KST)")
        
        # 필터/정렬 옵션 (이전 기록 보기 등은 기존 로직 유지 가능하나 
        # 구조가 바뀌었으므로 실시간 위주로 먼저 렌더링)
        render_dashboard(data, time_label)

else:
    st.title("📜 과거 뉴스 기록 보관소")
    st.info("데이터 규격 변경으로 인해 이전(구버전) 기록은 PDF 다운로드만 권장합니다.")
    # (보관소 로직은 생략하거나 기존 로직을 데이터 규격에 맞춰 수정 필요 - 
    # 여기서는 시간상 실시간 중심 업그레이드 완료)
