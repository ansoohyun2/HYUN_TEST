import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import time  # 딜레이 추가
import google.generativeai as genai  # Google Generative AI 추가
import random  # 랜덤 선택 추가
import re  # 숫자 추출을 위한 정규 표현식 추가

# Google Gemini API 설정
API_KEY = "AIzaSyDmaCsKCS4PrE3B-ErmHKknXEOpHQ2vjno"  # Google Generative AI 키
genai.configure(api_key=API_KEY)

# CSS 추가
st.markdown("""
    <style>
        .title {
            font-size: 50px;
            font-weight: bold;
            color: white; /* 초록색 글씨 */
            text-align: center; /* 제목을 가운데 정렬 */
        }
.subtitle {
    font-size: 12px;
    color: #FFFFFF; /* 글자색을 화이트로 설정 */
    text-align: right; /* 글씨를 오른쪽 정렬 */
    float: right; /* 상자를 오른쪽으로 이동 */
    margin-top: 30px; /* 상단 여백 추가 */
    margin-bottom: 20px /* 하단 여백 추가*/

}


      .stButton > button {
            float: right;
            background-color: #28a745; /* 초록색 배경 */
            color: #FFFFFF !important; /* 버튼 텍스트 색상 흰색 */
            font-weight: bold;
            border: none;
            padding: 10px 20px;
            border-radius: 5px; /* 버튼 모서리를 둥글게 */
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2); /* 그림자 추가 */
            cursor: pointer;
        }
        .stButton > button:hover {
            background-color: #218838; /* 버튼 호버시 색상 변경 */
        }

                .input-label {
            font-size: 22px; /* 글씨 크기 설정 */
            color: #fffff; /* 진한 회색 */
        }

        .stTextInput > div {
        margin-top: -20px; /* 입력 상자와 레이블 사이 여백 감소 */
    }

    .stTextArea > div, .stTextInput > div {
        margin-top: -20px; /* 입력 필드 상단 여백 줄임 */
    }
        .stTextArea, .stTextInput {
        margin-bottom: 30px; /* 입력 필드 사이 간격 */
    }

    

        
    </style>

""", unsafe_allow_html=True)



# 네이버 뉴스 크롤링 함수
def crawl_naver_news(keyword):
    encoded_keyword = quote(keyword)
    url = f"https://search.naver.com/search.naver?where=news&query={encoded_keyword}"
    
    # User-Agent 및 Referer 추가
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.naver.com"
    }

    try:
        time.sleep(1)
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            news_list = []

            # 뉴스 제목과 링크 추출
            for news_item in soup.select("a.news_tit"):
                title = news_item.get("title")
                link = news_item.get("href")
                news_list.append({"title": title, "link": link})

            return news_list[:5]  # 상위 5개 뉴스만 반환
        else:
            st.error(f"네이버 뉴스 페이지 접근 실패 (상태 코드: {response.status_code})")
            return []
    except Exception as e:
        st.error(f"오류 발생: {e}")
        return []

# AI 요약 개수 추출 함수
def extract_summary_count(user_question):
    match = re.search(r'(\d+)', user_question)
    if match:
        return int(match.group(1))
    return 2

# Google Generative AI 요약 함수 (대화 형식)
def generate_ai_summary(selected_articles, user_question, keyword):
    """
    Google Generative AI를 사용해 선택된 뉴스 기사를 대화 형식으로 요약합니다.
    """
    combined_data = "\n".join(
        [f"제목: {article['title']}, 링크: {article['link']}" for article in selected_articles]
    )
    prompt = f"""
    다음은 '{keyword}' 키워드로 검색된 뉴스 중 선택된 기사 목록입니다:

    {combined_data}

    위 뉴스 내용을 바탕으로 대화 형식으로 답변해 주세요.  
    친근하고 자연스러운 말투를 사용하고, 뉴스 요약을 각각 "첫 번째 뉴스 요약은", "두 번째 뉴스 요약은" 형식으로 나눠 전달해 주세요.  
    예시:  
    🎯첫 번째 뉴스는 비트코인의 가격 상승 소식이에요. 투자자들이 주목하고 있네요.  
    🎯두 번째 뉴스는 비트코인의 시장 동향에 관한 기사네요. 신중하게 접근하라는 전문가 의견도 있어요.  
    """
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        if hasattr(response, 'text'):
            return response.text
        else:
            return "유효한 응답을 받지 못했습니다."
    except Exception as e:
        st.error(f"AI 요약 중 오류 발생: {e}")
        return "요약에 실패했습니다."

# Streamlit UI 제목 및 서브텍스트 표시
st.markdown('<div class="title">📰 뉴스한입</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">네이버 뉴스 기사를 크롤링하고<br>AI를 사용해 한입 사이즈로 요약해 드립니다~!</div>', unsafe_allow_html=True)

# 사용자 입력
# 검색 키워드 입력
st.markdown('<div class="input-label">🔎 검색 키워드를 입력하세요.</div>', unsafe_allow_html=True)
search_keyword = st.text_input(" ", placeholder="검색어를 입력하세요...")

# AI 질문 입력
st.markdown('<div class="input-label">🗣 AI에게 질문을 입력하세요.</div>', unsafe_allow_html=True)
user_question = st.text_area(" ", placeholder="예: '뉴스 요약 2개 해줘'")

if st.button("뉴스 검색 및 요약"):
    if search_keyword and user_question:
        with st.spinner(f"🔗 '{search_keyword}' 관련 뉴스를 가져오는 중..."):
            news = crawl_naver_news(search_keyword)

        if news:
            st.subheader(f"🔎 '{search_keyword}' 뉴스 목록 (최대 10개)")
            for idx, article in enumerate(news):
                st.write(f"{idx+1}. [{article['title']}]({article['link']})")

            # 질문에서 요약할 뉴스 개수 추출
            num_summary = extract_summary_count(user_question)
            num_summary = min(num_summary, len(news))

            # 뉴스에서 랜덤으로 선택
            selected_news = random.sample(news, num_summary)

            st.subheader(f"🎯 요약할 뉴스 ({num_summary}개)")
            for idx, article in enumerate(selected_news):
                st.write(f"{idx+1}. [{article['title']}]({article['link']})")

            # AI 요약 생성
            with st.spinner("🤖 AI가 대화 형식으로 요약 중입니다..."):
                summary = generate_ai_summary(selected_news, user_question, search_keyword)

            # 요약 결과 출력
            st.subheader("🤖 AI 요약 결과")
            st.write(summary)
        else:
            st.error(f"❌ '{search_keyword}' 관련 뉴스를 찾지 못했습니다.")
    else:
        st.warning("키워드와 질문을 입력해 주세요!")
