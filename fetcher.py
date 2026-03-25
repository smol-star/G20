import requests
import xml.etree.ElementTree as ET
from deep_translator import GoogleTranslator
from data_manager import load_current_data, save_current_data
from datetime import datetime
import time
import html
import re
from collections import Counter

# G20 Countries mapped to Google News (gl) and Language (hl) codes
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

translator = GoogleTranslator(source='auto', target='ko')

def fetch_rss_news(gl, hl):
    url = f"https://news.google.com/rss?gl={gl}&hl={hl}&ceid={gl}:{hl}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return []
            
        root = ET.fromstring(resp.content)
        items = root.findall('.//item')
        
        trends = []
        # Get top 15 breaking news headlines
        for item in items[:15]: 
            title = item.find('title').text
            link = item.find('link').text if item.find('link') is not None else "#"
            pubDate = item.find('pubDate')
            
            date_str = "방금 전"
            pub_datetime_utc = None
            if pubDate is not None and pubDate.text:
                try:
                    import email.utils
                    from datetime import timezone, timedelta
                    dt = email.utils.parsedate_to_datetime(pubDate.text)
                    dt_utc = dt.astimezone(timezone.utc)
                    pub_datetime_utc = dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
                    kst_dt = dt_utc + timedelta(hours=9)
                    date_str = f"{pubDate.text} ➡️ 한국시간 {kst_dt.strftime('%m월 %d일 %H:%M')}"
                except:
                    date_str = pubDate.text

            trends.append({
                "original_title": html.unescape(title),
                "traffic": "국가 주요 헤드라인 (속보)",
                "pub_date": date_str,
                "pub_datetime_utc": pub_datetime_utc,
                "link": link
            })
        return trends
    except Exception as e:
        print(f"Error fetching {gl}: {e}")
        return []

def extract_keywords(text):
    text = re.sub(r'[^가-힣a-zA-Z0-9\s]', '', text)
    words = text.split()
    cleaned = []
    for w in words:
        if len(w) > 1:
            for suffix in ['은', '는', '이', '가', '을', '를', '의', '에', '에게', '에서', '로', '으로', '과', '와', '도', '만', '까지', '부터', '이다', '하다', '합니다', '입니다', '한다']:
                if w.endswith(suffix):
                    w = w[:-len(suffix)]
                    break
            if len(w) > 1:
                cleaned.append(w)
    return cleaned

def fetch_and_update_trends():
    print(f"[{datetime.now()}] Fetching new hourly trends via Google News RSS...")
    data = load_current_data()
    
    for country, (gl, hl, gdp_rank) in G20_NEWS_CODES.items():
        if country in data:
            data[country]["previous_rank"] = data[country].get("current_rank", data[country].get("gdp_rank", 99))
            
        top_trends = fetch_rss_news(gl, hl)
        
        if not top_trends:
            continue
            
        country_trends = []
        for t in top_trends:
            trend_str = t['original_title']
            traffic_str = t['traffic']
            pub_date = t['pub_date']
            
            try:
                # To avoid translate failing completely, we use translation
                translated_title = translator.translate(trend_str)
            except Exception:
                translated_title = trend_str
                
            country_trends.append({
                "title": translated_title,
                "volume": traffic_str,
                "original_title": trend_str,
                "link": t.get("link", "#"),
                "pub_date": pub_date,
                "pub_datetime_utc": t.get("pub_datetime_utc")
            })
            
        all_keywords = []
        for t in country_trends:
            all_keywords.extend(extract_keywords(t['title']))
            
        keyword_counts = Counter(all_keywords)
        main_issue_keywords = {k for k, v in keyword_counts.items() if v >= 3}
        
        main_issues = []
        sub_issues = []
        
        for t in country_trends:
            t_keywords = set(extract_keywords(t['title']))
            if t_keywords & main_issue_keywords:
                t['category'] = '메인 이슈'
                main_issues.append(t)
            else:
                t['category'] = '서브 이슈'
                sub_issues.append(t)
                
        # Keep all main issues and top 5 sub issues
        final_trends = main_issues + sub_issues[:5]
            
        if country not in data:
            data[country] = {
                "gdp_rank": gdp_rank,
                "spike_score": 0.0,
                "trends": [],
                "previous_rank": gdp_rank
            }
        
        # New issue detection for Spike scoring
        previous_trends = [t["original_title"] for t in data.get(country, {}).get("trends", [])]
        new_issues_count = len([t for t in final_trends if t["original_title"] not in previous_trends])
        
        data[country]["spike_score"] = data[country]["spike_score"] * 0.5 + (new_issues_count * 5.0)
        data[country]["trends"] = final_trends
        data[country]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Prevent Google Translate API rate limit
        time.sleep(1.5)
        
    data = sort_countries(data)
    save_current_data(data)
    print("News Trends updated successfully.")

def sort_countries(data):
    country_list = []
    for c, info in data.items():
        country_list.append((c, info))
        
    country_list.sort(key=lambda x: (-x[1]["spike_score"], x[1]["gdp_rank"]))
    
    sorted_data = {}
    for i, (c, info) in enumerate(country_list):
        info["current_rank"] = i + 1
        sorted_data[c] = info
        
    return sorted_data

if __name__ == "__main__":
    fetch_and_update_trends()
