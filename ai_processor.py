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
    
    prompt = """
너는 전 세계 G20 국가의 실시간 RSS 뉴스 트렌드를 분석하여 가장 강렬한 '유튜브 쇼츠(Shorts) 대본'을 작성하는 베테랑 뉴스 에디터다.

[입력 데이터]
- 각 국가별로 최근 3시간 동안 수집된 주요 뉴스 헤드라인들이 제공된다.

[분석 포인트]
- 단순히 뉴스 하나하나를 요약하지 마라.
- 해당 국가에서 '현재 가장 뜨겁게 논의되고 있는 하나의 큰 흐름'이나 '가장 충격적인 사건'을 중심으로 입체적으로 재구성해라.

[출력 형식: JSON]
{
  "Country Name": {
    "headline": "한글 뉴스 헤드라인 (3단어 내외)",
    "hook": "시청자의 스크롤을 멈추게 하는 강렬한 1줄 문장",
    "script": "쇼츠 아나운서 리딩용 대본 (30초 분량, 3~4문장)"
  },
  ...
}

[절대 규칙]
1. 인사말 절대 금지: "안녕하세요", "요약입니다" 등은 쓰지 마라.
2. 강력한 훅(Hook)으로 시작: 대본 첫 문장부터 본론으로 돌진해라.
3. 한국어로 답변해라.

[분석할 뉴스 목록]
"""
    for country, items in bundle_dict.items():
        prompt += f"\n### COUNTRY: {country}\n"
        for i, item in enumerate(items[:10]): # 분석 질을 위해 최대 10개 참고
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
