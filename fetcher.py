import requests
import xml.etree.ElementTree as ET
from deep_translator import GoogleTranslator
from data_manager import load_current_data, save_current_data
from datetime import datetime
import time

# G20 Countries mapped to geo codes for RSS parsing
G20_COUNTRIES = {
    'United States': ('US', 1),
    'China': ('CN', 2),
    'Germany': ('DE', 3),
    'Japan': ('JP', 4),
    'India': ('IN', 5),
    'United Kingdom': ('GB', 6),
    'France': ('FR', 7),
    'Italy': ('IT', 8),
    'Brazil': ('BR', 9),
    'Canada': ('CA', 10),
    'Russia': ('RU', 11),
    'Mexico': ('MX', 12),
    'Australia': ('AU', 13),
    'South Korea': ('KR', 14),
    'Indonesia': ('ID', 15),
    'Turkey': ('TR', 16),
    'Saudi Arabia': ('SA', 17),
    'Argentina': ('AR', 18),
    'South Africa': ('ZA', 20)
}

translator = GoogleTranslator(source='auto', target='ko')

def fetch_rss_trends(geo_code):
    url = f"https://trends.google.com/trends/trendingsearches/daily/rss?geo={geo_code}"
    # Adding a standard browser User-Agent
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return []
            
        root = ET.fromstring(resp.content)
        items = root.findall('.//item')
        
        trends = []
        for item in items[:3]: # top 3
            title = item.find('title').text
            ht_approx = item.find('{https://trends.google.com/trends/trendingsearches/daily}approx_traffic')
            traffic = ht_approx.text if ht_approx is not None else "관심도 상승"
            
            trends.append({
                "original_title": title,
                "traffic": traffic
            })
        return trends
    except Exception as e:
        print(f"Error fetching {geo_code}: {e}")
        return []

def fetch_and_update_trends():
    print(f"[{datetime.now()}] Fetching new hourly trends via RSS...")
    data = load_current_data()
    
    for country, (code, gdp_rank) in G20_COUNTRIES.items():
        top_trends = fetch_rss_trends(code)
        
        if not top_trends:
            continue
            
        country_trends = []
        for t in top_trends:
            trend_str = t['original_title']
            traffic_str = t['traffic']
            
            try:
                translated_title = translator.translate(trend_str)
            except:
                translated_title = trend_str
                
            summary_lines = [
                f"'{translated_title}' 관련 이슈가 급부상하고 있습니다.",
                f"해당 키워드는 현재 {country} 지역의 핵심 검색어입니다.",
                f"예상 검색량/언급량: {traffic_str}"
            ]
            
            country_trends.append({
                "title": translated_title,
                "volume": traffic_str,
                "summary": summary_lines,
                "original_title": trend_str
            })
            
        if country not in data:
            data[country] = {
                "gdp_rank": gdp_rank,
                "spike_score": 0.0,
                "trends": []
            }
        
        previous_trends = [t["original_title"] for t in data.get(country, {}).get("trends", [])]
        new_issues_count = len([t for t in country_trends if t["original_title"] not in previous_trends])
        
        data[country]["spike_score"] = data[country]["spike_score"] * 0.5 + (new_issues_count * 5.0)
        data[country]["trends"] = country_trends
        data[country]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        time.sleep(1)
        
    data = sort_countries(data)
    save_current_data(data)
    print("Trends updated.")

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
