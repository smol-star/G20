import os
import json
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

_client = None

def get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("[AI Error] GEMINI_API_KEY가 환경 변수에 없습니다.")
            return None
        _client = genai.Client(api_key=api_key)
    return _client

def get_available_model():
    """2026년 4월 표준: Gemini 3.1 시리즈 위주로 모델 탐색"""
    client = get_client()
    if not client: return "gemini-3.1-flash-lite"
    
    try:
        models = [m.name for m in client.models.list()]
        print(f"   [AI] RSS 프로젝트 가용 모델: {models}")
        
        preferences = [
            'gemini-3.1-flash-lite', 
            'gemini-3.1-flash',
            '3.1-flash',
            '2.0-flash'
        ]
        
        selected = None
        for pref in preferences:
            for m in models:
                if pref in m:
                    selected = m
                    break
            if selected: break
            
        if selected:
            print(f"   [AI] RSS 표준 모델 선택: {selected}")
            return selected
        elif models:
            return models[0]
            
    except Exception as e:
        print(f"   [AI Model List Error] {e}")
        
    return "gemini-3.1-flash-lite"

def clean_text(text):
    if not text: return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\?[^ ]*', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:400]

def summarize_rss_batch(bundle_dict):
    """
    RSS 뉴스 데이터를 배치로 묶어서 심층 요약
    bundle_dict: { "South Korea": [item1, item2, ...], ... }
    """
    client = get_client()
    if not client: return {}
    
    model_id = get_available_model()
    
    country_names = ", ".join(bundle_dict.keys())
    
    system_instruction = f"""너는 GDELT 및 Google News RSS 뉴스를 분석하는 글로벌 뉴스 에디터 시스템이다.

[출력 규칙 — 최우선]
- 응답은 오직 JSON 객체(Dictionary)여야 한다.
- JSON 앞뒤에 복제된 텍스트나 포맷 문자(마크다운 등)를 넣지 마라.
- 어떠한 언어의 뉴스라도 응답(headline, hook, script)은 반드시 **한국어(Korean)**로 작성하라.

[출력 형식]
{{
  "Country Name": {{
    "headline": "한국어 헤드라인 (3단어 내외)",
    "hook": "시청자의 스크롤을 멈추게 하는 강렬한 1줄 문장 (한국어)",
    "script": "쇼츠 대본 (30초, 3~4문장). 첫 단어부터 사건 핵심으로 직진. (한국어)"
  }}
}}
- 허용되는 JSON 키: {country_names}"""

    prompt = "[분석할 뉴스 목록]\n"
    for country, items in bundle_dict.items():
        prompt += f"\n### {country}\n"
        for i, item in enumerate(items[:10]):
            title = clean_text(item.get('original_title', ''))
            prompt += f"{i+1}. {title}\n"
            
    try:
        response = client.models.generate_content(
            model=model_id,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
                response_mime_type="application/json"
            )
        )
        # response_mime_type 설정으로 순수 JSON 텍스트 보장
        res_text = response.text.strip()
        return json.loads(res_text)
    except Exception as e:
        print(f"[AI RSS Error] {e}")
        return {}
