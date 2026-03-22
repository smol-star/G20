import pandas as pd
from pytrends.request import TrendReq
from deep_translator import GoogleTranslator
from data_manager import load_current_data, save_current_data
from datetime import datetime
import time

# G20 Countries supported by pytrends trending_searches
G20_COUNTRIES = {
    'United States': ('united_states', 1),    # (pytrends_name, default_gdp_rank)
    'China': ('china', 2),                    # May not work due to google blocking
    'Germany': ('germany', 3),
    'Japan': ('japan', 4),
    'India': ('india', 5),
    'United Kingdom': ('united_kingdom', 6),
    'France': ('france', 7),
    'Italy': ('italy', 8),
    'Brazil': ('brazil', 9),
    'Canada': ('canada', 10),
    'Russia': ('russia', 11),
    'Mexico': ('mexico', 12),
    'Australia': ('australia', 13),
    'South Korea': ('south_korea', 14),
    'Indonesia': ('indonesia', 15),
    'Turkey': ('turkey', 16),
    'Saudi Arabia': ('saudi_arabia', 17),
    'Argentina': ('argentina', 18),
    'South Africa': ('south_africa', 20)      # 19 is EU
}

pytrends = TrendReq(hl='en-US', tz=360)
translator = GoogleTranslator(source='auto', target='ko')

def fetch_and_update_trends():
    print(f"[{datetime.now()}] Fetching new hourly trends...")
    data = load_current_data()
    
    # Structure of data:
    # {
    #   "CountryName": {
    #       "gdp_rank": int,
    #       "spike_score": float,
    #       "last_updated": str,
    #       "trends": [
    #           {"title": "translated_title", "volume": int, "summary": ["line1", "line2", "line3"], "is_new": bool, "original_title": "raw"}
    #       ]
    #   }
    # }
    
    for country, (code, gdp_rank) in G20_COUNTRIES.items():
        try:
            # We use realtime_trending_searches if possible, else trending_searches
            # trending_searches gives top 20 daily
            df = pytrends.trending_searches(pn=code)
            if df is None or df.empty:
                continue
                
            # Take top 3 for dashboard sanity
            top_trends = df[0].head(3).tolist()
            
            # Format translations
            country_trends = []
            for trend in top_trends:
                # 3-line summary format:
                # 1. Headline (Translated)
                # 2. Key context (e.g. Currently trending in {Country})
                # 3. Mention volume or rank info
                
                translated_title = translator.translate(trend)
                summary_lines = [
                    f"'{translated_title}' 관련 이슈가 급부상하고 있습니다.",
                    f"해당 키워드는 현재 {country} 지역의 핵심 검색어입니다.",
                    f"원문 검색어: {trend}"
                ]
                
                country_trends.append({
                    "title": translated_title,
                    "volume": 1000, # pytrends trending_searches doesn't give exact volume per hour easily without get_request, so we mock or use relative rank
                    "summary": summary_lines,
                    "original_title": trend
                })
                
            # Initialize or Update
            if country not in data:
                data[country] = {
                    "gdp_rank": gdp_rank,
                    "spike_score": 0.0,
                    "trends": []
                }
            
            # Simple Spike detection: if new trend wasn't in previous top 3, increase spike score!
            previous_trends = [t["original_title"] for t in data.get(country, {}).get("trends", [])]
            new_issues_count = len([t for t in top_trends if t not in previous_trends])
            
            # Decay old spike score slowly, add big boost for new issues
            data[country]["spike_score"] = data[country]["spike_score"] * 0.5 + (new_issues_count * 5.0)
            data[country]["trends"] = country_trends
            data[country]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Sleep to prevent rate limit
            time.sleep(2)
            
        except Exception as e:
            print(f"Skipping {country} due to error/unsupported: {e}")
            
    # Calculate final ranks
    data = sort_countries(data)
    save_current_data(data)
    print("Trends updated.")

def sort_countries(data):
    # Sort criteria: Spike Score (descending), then GDP Rank (ascending)
    # Countries with high spike score jump to the top
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
