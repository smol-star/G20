import os
import google.generativeai as genai
from dotenv import load_dotenv
import json
import re

load_dotenv()

def init_gemini():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("[AI] GEMINI_API_KEY가 환경변수에 없습니다. GitHub Secrets 또는 .env 파일을 확인하세요.")
    genai.configure(api_key=api_key)

def clean_text(text):
    """토큰 절약을 위한 텍스트 정규화"""
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
    init_gemini()
    
    # 국가명을 프롬프트에 명시하여 AI가 동일한 키를 반환하도록 강제
    country_names = ", ".join(bundle_dict.keys())
    
    prompt = f"""너는 GDELT 및 Google News RSS 뉴스를 분석하는 글로벌 뉴스 에디터 시스템이다.

[출력 규칙 — 최우선]
- 응답의 첫 번째 문자는 반드시 {{ 이어야 한다.
- JSON 앞뒤로 어떤 텍스트도, 마크다운 코드블록도 추가하지 마라.
- "안녕하세요", "요약입니다", "알겠습니다" 같은 문구는 절대 출력하지 마라.

[국가명 키 규칙]
- 반드시 아래 영문 이름을 JSON 키로 그대로 사용할 것: {country_names}

[출력 형식]
{{
  "Country Name": {{
    "headline": "한글 헤드라인 (3단어 내외)",
    "hook": "시청자의 스크롤을 멈추게 하는 강렬한 1줄 문장",
    "script": "쇼츠 대본 (30초, 3~4문장). 첫 단어부터 사건 핵심으로 직진."
  }},
  ...
}}

[분석 지침]
- 단순 뉴스 나열이 아닌, 3시간치 기사들의 공통 흐름이나 가장 큰 사건을 하나로 통합해서 표현해라.
- 한국어로 답변해라.

[분석할 뉴스 목록]
"""
    for country, items in bundle_dict.items():
        prompt += f"\n### {country}\n"
        for i, item in enumerate(items[:10]):
            title = clean_text(item.get('original_title', ''))
            prompt += f"{i+1}. {title}\n"

    try:
        try:
            model = genai.GenerativeModel('gemini-3-flash')
            response = model.generate_content(prompt)
        except Exception:
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            
        result_text = response.text.strip()
        start = result_text.find('{')
        end = result_text.rfind('}')
        if start != -1 and end != -1:
            return json.loads(result_text[start:end+1])
        return {}
    except Exception as e:
        print(f"[AI RSS Error] {e}")
        return {}
