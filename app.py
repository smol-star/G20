import streamlit as st
import pandas as pd
from data_manager import load_current_data
from datetime import datetime, timedelta

st.set_page_config(page_title="G20 실시간 뉴스 헤드라인 보드", layout="wide")
st.title("🌐 G20 실시간 글로벌 뉴스 헤드라인 브리핑")
st.markdown("GDP 상위 G20 국가들의 구글 뉴스 메인 속보 5개를 1시간 간격으로 수집하여 한국어 개괄 요약본으로 제공합니다.")
st.markdown("💡 **정렬 기준**: 기본적으로 GDP 순위로 정렬되지만, 전 세계 포털에 '새로운 속보'가 다수 등장한 국가는 **최상단(🔥 속보 집중)**으로 자동 배치됩니다.")

FLAG_CODES = {
    'United States': 'us', 'China': 'cn', 'Germany': 'de', 'Japan': 'jp',
    'India': 'in', 'United Kingdom': 'gb', 'France': 'fr', 'Italy': 'it',
    'Brazil': 'br', 'Canada': 'ca', 'Russia': 'ru', 'Mexico': 'mx',
    'Australia': 'au', 'South Korea': 'kr', 'Indonesia': 'id', 'Turkey': 'tr',
    'Saudi Arabia': 'sa', 'Argentina': 'ar', 'South Africa': 'za'
}

data = load_current_data()

if not data:
    st.info("데이터를 수집 중입니다. 백그라운드 수집기가 실행될 때까지 잠시만 대기해 주세요.")
else:
    st.divider()
    kst_now = (datetime.utcnow() + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S")
    
    # data is already sorted by fetcher.py
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
            st.caption(f"🔄 최근 데이터 갱신 시간: {updated} (UTC) &nbsp;|&nbsp; ⏰ 대한민국 현재 시간: {kst_now} (KST)")
            
            trends = info.get("trends", [])
            if not trends:
                st.write("수집된 트렌드가 없거나 Google 지원 대상 국가가 아닙니다.")
            
            for idx, t in enumerate(trends):
                category = t.get('category', '서브 이슈')
                category_color = "#ff4bc6" if category == "메인 이슈" else "#4b88ff"
                
                st.markdown(f"### {idx+1}. <span style='color: {category_color}; font-size: 0.6em; border: 1px solid {category_color}; border-radius: 4px; padding: 2px 6px; vertical-align: middle; margin-right: 8px;'>{category}</span>{t['title']}", unsafe_allow_html=True)
                
                st.markdown(f"*(원문 뉴스 제목: {t['original_title']})*")
                
                pub_date = t.get('pub_date', '보도 시간 없음')
                st.markdown(f"🕒 **보도 시간:** {pub_date}")
                
                link_url = t.get('link', '#')
                st.markdown(f"🔗 [[기사 원문 보기]({link_url})]")
                
                if idx < len(trends) - 1:
                    st.markdown("---")
