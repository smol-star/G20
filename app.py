import streamlit as st
import pandas as pd
from data_manager import load_current_data
from datetime import datetime

st.set_page_config(page_title="G20 실시간 뉴스 헤드라인 보드", layout="wide")
st.title("🌐 G20 실시간 글로벌 뉴스 헤드라인 브리핑")
st.markdown("GDP 상위 G20 국가들의 구글 뉴스 메인 속보 5개를 1시간 간격으로 수집하여 한국어 3줄 요약본으로 제공합니다.")
st.markdown("💡 **정렬 기준**: 기본적으로 GDP 순위로 정렬되지만, 전 세계 포털에 '새로운 속보'가 다수 등장한 국가는 **최상단(🔥 속보 집중)**으로 자동 배치됩니다.")

FLAG_EMOJIS = {
    'United States': '🇺🇸', 'China': '🇨🇳', 'Germany': '🇩🇪', 'Japan': '🇯🇵',
    'India': '🇮🇳', 'United Kingdom': '🇬🇧', 'France': '🇫🇷', 'Italy': '🇮🇹',
    'Brazil': '🇧🇷', 'Canada': '🇨🇦', 'Russia': '🇷🇺', 'Mexico': '🇲🇽',
    'Australia': '🇦🇺', 'South Korea': '🇰🇷', 'Indonesia': '🇮🇩', 'Turkey': '🇹🇷',
    'Saudi Arabia': '🇸🇦', 'Argentina': '🇦🇷', 'South Africa': '🇿🇦'
}

data = load_current_data()

if not data:
    st.info("데이터를 수집 중입니다. 백그라운드 수집기가 실행될 때까지 잠시만 대기해 주세요.")
else:
    st.divider()
    
    # data is already sorted by fetcher.py
    for country, info in data.items():
        score = info.get("spike_score", 0.0)
        rank = info.get("gdp_rank", 99)
        updated = info.get("last_updated", "N/A")
        
        spike_badge = "🔥 **속보 집중(상승)!**" if score > 0 else ""
        emoji = FLAG_EMOJIS.get(country, '🏳️')
        
        # 기본적으로 최상위 급상승 혹은 G3 국가는 열어둠
        with st.expander(f"[{emoji} {country}] 실시간 뉴스 헤드라인 Top 5 (GDP 순위: {rank}위) {spike_badge}", expanded=(score > 0 or rank <= 3)):
            st.caption(f"최근 데이터 갱신 시간: {updated}")
            
            trends = info.get("trends", [])
            if not trends:
                st.write("수집된 트렌드가 없거나 Google 지원 대상 국가가 아닙니다.")
            
            for idx, t in enumerate(trends):
                st.markdown(f"### {idx+1}. {t['title']}")
                st.markdown(f"*(원문 뉴스 제목: {t['original_title']})*")
                link_url = t.get('link', '#')
                st.markdown(f"🔗 [[기사 원문 보기]({link_url})]")
                
                # 3-line summary
                for line in t.get('summary', []):
                    st.markdown(f"- {line}")
                
                if idx < len(trends) - 1:
                    st.markdown("---")
