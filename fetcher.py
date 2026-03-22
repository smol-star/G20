import requests
import xml.etree.ElementTree as ET
from deep_translator import GoogleTranslator
from data_manager import load_current_data, save_current_data
from datetime import datetime
import time
import html

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
        # Get top 5 breaking news headlines
        for item in items[:5]: 
            title = item.find('title').text
            link = item.find('link').text if item.find('link') is not None else "#"
            pubDate = item.find('pubDate')
            date_str = pubDate.text if pubDate is not None else "방금 전"
            
            trends.append({
                "original_title": html.unescape(title),
                "traffic": "국가 주요 헤드라인 (속보)",
                "pub_date": date_str,
                "link": link
            })
        return trends
    except Exception as e:
        print(f"Error fetching {gl}: {e}")
        return []

def fetch_and_update_trends():
    print(f"[{datetime.now()}] Fetching new hourly trends via Google News RSS...")
    data = load_current_data()
    
    for country, (gl, hl, gdp_rank) in G20_NEWS_CODES.items():
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
            except:
                translated_title = trend_str
                
            summary_lines = [
                f"'{translated_title}' 관련 이슈가 각국 포털 메인을 장식하고 있습니다.",
                f"해당 뉴스는 현재 {country}의 핵심 속보 헤드라인입니다.",
                f"게시 시간: {pub_date}"
            ]
            
            country_trends.append({
                "title": translated_title,
                "volume": traffic_str,
                "summary": summary_lines,
                "original_title": trend_str,
                "link": t.get("link", "#")
            })
            
        if country not in data:
            data[country] = {
                "gdp_rank": gdp_rank,
                "spike_score": 0.0,
                "trends": []
            }
        
        # New issue detection for Spike scoring
        previous_trends = [t["original_title"] for t in data.get(country, {}).get("trends", [])]
        new_issues_count = len([t for t in country_trends if t["original_title"] not in previous_trends])
        
        data[country]["spike_score"] = data[country]["spike_score"] * 0.5 + (new_issues_count * 5.0)
        data[country]["trends"] = country_trends
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
    for c, info in country_list:
        sorted_data[c] = info
        
    return sorted_data

if __name__ == "__main__":
    fetch_and_update_trends()
