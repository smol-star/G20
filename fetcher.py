import requests
import xml.etree.ElementTree as ET
import ai_processor
from data_manager import load_current_data, save_current_data
from datetime import datetime, timezone, timedelta
import time
import html
import re
import email.utils

# G20 Countries mapped to Google News codes
G20_NEWS_CODES = {
    'United States': ('US', 'en-US', 1),
    'China': ('CN', 'zh-CN', 2),
    'Germany': ('DE', 'de', 3),
    'Japan': ('JP', 'ja', 4),
    'India': ('IN', 'en-IN', 5),
    'United Kingdom': ('GB', 'en-GB', 6),
    'France': ('FR', 'fr', 7),
    'Italy': ('IT', 'it', 8),
    'Brazil': ('BR', 'pt-BR', 9),
    'Canada': ('CA', 'en-CA', 10),
    'Russia': ('RU', 'ru', 11),
    'Mexico': ('MX', 'es-419', 12),
    'Australia': ('AU', 'en-AU', 13),
    'South Korea': ('KR', 'ko', 14),
    'Indonesia': ('ID', 'id', 15),
    'Turkey': ('TR', 'tr', 16),
    'Saudi Arabia': ('SA', 'ar', 17),
    'Argentina': ('AR', 'es-419', 18),
    'South Africa': ('ZA', 'en-ZA', 20)
}

def fetch_rss_news(gl, hl):
    url = f"https://news.google.com/rss?gl={gl}&hl={hl}&ceid={gl}:{hl}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200: return []
        root = ET.fromstring(resp.content)
        items = root.findall('.//item')
        
        trends = []
        for item in items[:15]:
            title = html.unescape(item.find('title').text)
            link = item.find('link').text if item.find('link') is not None else "#"
            pubDate = item.find('pubDate')
            pub_dt_utc = None
            if pubDate is not None and pubDate.text:
                try:
                    dt = email.utils.parsedate_to_datetime(pubDate.text)
                    pub_dt_utc = dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                except: pass
            trends.append({
                "original_title": title,
                "link": link,
                "pub_datetime_utc": pub_dt_utc
            })
        return trends
    except Exception as e:
        print(f"Error fetching {gl}: {e}")
        return []

def fetch_and_update_trends():
    print(f"[{datetime.now()}] RSS AI 배치 수집 및 분석 시작 (3시간 주기)...")
    data = load_current_data()
    
    # 1. 뉴스 데이터 수집 및 중복 필터링
    country_news_payload = {}
    
    for country, (gl, hl, gdp_rank) in G20_NEWS_CODES.items():
        print(f"  Fetching {country} ({gl})...")
        raw_trends = fetch_rss_news(gl, hl)
        if not raw_trends:
            continue
        
        # 중복 제거 (URL 기준 + 제목 기준)
        existing_urls = {t.get("link") for t in data.get(country, {}).get("trends", [])}
        existing_titles = {t.get("original_title") for t in data.get(country, {}).get("trends", [])}
        
        filtered = [
            nt for nt in raw_trends
            if nt["link"] not in existing_urls and nt["original_title"] not in existing_titles
        ]
        
        if not filtered:
            print(f"  → {country}: 신규 기사 없음, 갱신 건너뜀.")
            continue
        
        country_news_payload[country] = filtered
        
    if not country_news_payload:
        print("모든 국가에서 신규 기사 없음. 기존 데이터 유지.")
        return
        
    # 2. AI 배치 요약 (6개국씩 분할 호출)
    all_countries = list(country_news_payload.keys())
    batch_size = 6
    
    print(f"\n총 {len(all_countries)}개국 → Gemini AI 배치 분석 시작 (배치당 최대 {batch_size}개국)...")
    
    for i in range(0, len(all_countries), batch_size):
        batch_keys = all_countries[i : i + batch_size]
        batch_dict = {k: country_news_payload[k] for k in batch_keys}
        batch_num = i // batch_size + 1
        
        print(f"  [배치 {batch_num}] {', '.join(batch_keys)}")
        ai_results = ai_processor.summarize_rss_batch(batch_dict)
        
        # 3. 결과 매핑: AI 응답 국가명과 실제 국가명 매칭 (완화된 매칭)
        for country_key in batch_keys:
            # AI 결과에서 일치하는 국가 찾기
            ai_info = {}
            for ai_country, ai_data in ai_results.items():
                matched = ai_country if ai_country == country_key else None
                if not matched:
                    for real_country in G20_NEWS_CODES:
                        if ai_country.lower() in real_country.lower() or real_country.lower() in ai_country.lower():
                            if real_country == country_key:
                                matched = real_country
                                break
                if matched:
                    ai_info = ai_data
                    break
            
            matched_country = country_key
            if matched_country not in country_news_payload:
                continue

            country, (gl, hl, gdp_rank) = matched_country, G20_NEWS_CODES[matched_country]
            kst = timezone(timedelta(hours=9))
            now_kst = datetime.now(kst)
            
            # 대표 기사 (가장 최신 기사)
            rep_item = country_news_payload[matched_country][0]
            
            # AI 실패 시 원본 제목을 Fallback으로 사용
            headline = ai_info.get("headline") or rep_item.get("original_title", "주요 이슈")[:30]
            hook = ai_info.get("hook") or f"{matched_country}의 최신 주요 뉴스입니다."
            script = ai_info.get("script") or headline
            
            data[country] = {
                "gdp_rank": gdp_rank,
                "spike_score": len(country_news_payload[matched_country]) * 5.0,
                "previous_rank": data.get(country, {}).get("current_rank", gdp_rank),
                "trends": [{
                    "keyword": headline,
                    "hook": hook,
                    "script": script,
                    "original_title": rep_item.get("original_title", ""),
                    "link": rep_item.get("link", "#"),
                    "pub_datetime_utc": rep_item.get("pub_datetime_utc")
                }],
                "last_updated": now_kst.strftime("%Y-%m-%d %H:%M:%S KST")
            }


    # 4. 정렬 및 저장
    country_list = sorted(
        data.items(),
        key=lambda x: (-x[1].get("spike_score", 0), x[1].get("gdp_rank", 99))
    )
    sorted_data = {}
    for i, (c, info) in enumerate(country_list):
        info["current_rank"] = i + 1
        sorted_data[c] = info
        
    save_current_data(sorted_data)
    print("\nRSS AI Trends 업데이트 완료!")

if __name__ == "__main__":
    try:
        fetch_and_update_trends()
    except Exception as e:
        import traceback
        from data_manager import load_current_data, save_current_data
        
        kst = timezone(timedelta(hours=9))
        now_str = datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S KST")
        
        print("=" * 60)
        print("[CRITICAL ERROR] 파이프라인 예외 발생. Fallback 데이터로 저장합니다.")
        traceback.print_exc()
        print("=" * 60)
        
        # 기존 데이터 유지, last_updated에만 지연 메시지 기록
        data = load_current_data()
        if not data:
            data = {
                "System Notice": {
                    "gdp_rank": 0, "current_rank": 0, "spike_score": 0.0,
                    "trends": [{"keyword": "갱신 일시 지연", "hook": f"파이프라인 오류로 이번 회차({now_str}) 갱신이 지연되었습니다.",
                                "script": f"[오류] {str(e)[:200]}", "original_title": "", "link": "#", "pub_datetime_utc": None}],
                    "last_updated": f"{now_str} (오류)"
                }
            }
        else:
            for country in data:
                if isinstance(data[country], dict):
                    data[country]["last_updated"] = f"{now_str} (갱신 일시 지연)"
        
        save_current_data(data)
        print("Fallback 데이터 저장 완료. 파이프라인 정상 종료(exit 0).")
