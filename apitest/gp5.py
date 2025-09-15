import os
import time
import pandas as pd
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# 1️⃣ 환경변수에서 API 키 읽기
load_dotenv()
API_KEY = os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY")
if not API_KEY or "your-api-key" in API_KEY:
    print("❌ API 키를 설정해주세요!")
    exit()

client = OpenAI(api_key=API_KEY)

# 2️⃣ 테스트 설정
MODEL = "gpt-5"
TEST_QUERY = "서울시 종로구 맛집 추천"

SEARCH_TYPES = {
    "non_reasoning": {"reasoning": {"effort": "low"}},
    "agentic": {"reasoning": {"effort": "medium"}},
    "deep_research": {"reasoning": {"effort": "high"}}
}

# 3️⃣ 응답 추출 함수
def extract_response_text(response):
    try:
        if hasattr(response, 'output_text'):
            return response.output_text or ""
        if hasattr(response, 'output'):
            for out in response.output:
                for content in out.content:
                    if hasattr(content, 'text'):
                        return content.text
        return ""
    except:
        return ""

def extract_citations(response):
    urls, titles = [], []
    try:
        if hasattr(response, 'output'):
            for out in response.output:
                for content in out.content:
                    if hasattr(content, 'annotations'):
                        for ann in content.annotations:
                            if getattr(ann, 'type', '') == "url_citation":
                                urls.append(getattr(ann, 'url', ''))
                                titles.append(getattr(ann, 'title', ''))
        return urls, titles
    except:
        return [], []

# 4️⃣ 웹 검색 실행 함수
def run_web_search(query, search_type_name, reasoning_params):
    print(f"🔹 [{search_type_name}] 검색 시작...")
    start_time = time.time()
    
    response = client.responses.create(
        model=MODEL,
        tools=[{"type": "web_search"}],
        reasoning=reasoning_params,
        input=query
    )
    
    duration = time.time() - start_time
    response_text = extract_response_text(response)
    urls, titles = extract_citations(response)
    
    result = {
        "search_type": search_type_name,
        "query": query,
        "duration_seconds": round(duration, 2),
        "response_text": response_text,
        "citation_count": len(urls),
        "citation_urls": urls,
        "citation_titles": titles
    }
    print(f"✅ [{search_type_name}] 완료! ({round(duration,2)}초)")
    return result

# 5️⃣ 결과 저장 함수
def save_results(results):
    df = pd.DataFrame(results)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = f"gpt5_web_search_results_{timestamp}.csv"
    excel_file = f"gpt5_web_search_results_{timestamp}.xlsx"
    
    df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Results', index=False)
    
    return csv_file, excel_file

# 6️⃣ 메인 실행
def main():
    results = []
    for name, params in SEARCH_TYPES.items():
        res = run_web_search(TEST_QUERY, name, params["reasoning"])
        results.append(res)
        print("\n출력 예시:", res["response_text"][:300], "...")  # 최대 300자
    
    csv_path, excel_path = save_results(results)
    print(f"\n 결과 저장:\n- CSV: {csv_path}\n- Excel: {excel_path}")

if __name__ == "__main__":
    main()