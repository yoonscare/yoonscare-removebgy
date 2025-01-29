import streamlit as st
import replicate
import requests
from PIL import Image
import io
import os

# 페이지 설정
st.set_page_config(
    page_title="배경 제거 도구",
    page_icon="🖼️",
    layout="wide"
)

# 사이드바에 API 키 입력 필드 추가
with st.sidebar:
    st.title("설정")
    api_key = st.text_input("Replicate API 키를 입력하세요", type="password")
    st.markdown("""
    ### 사용 방법
    1. Replicate API 키를 입력하세요
    2. 이미지를 업로드하세요
    3. '배경 제거' 버튼을 클릭하세요
    """)

# 메인 페이지 제목
st.title("🖼️ 이미지 배경 제거 도구")
st.markdown("간단하게 이미지의 배경을 제거해보세요!")

# ImgBB에 이미지 업로드하는 함수
def upload_to_imgbb(image_bytes):
    try:
        response = requests.post(
            "https://api.imgbb.com/1/upload",
            params={"key": "e2b77b1380511b353288b7b436927a6c"},
            files={"image": image_bytes}
        )
        response_data = response.json()
        if response.status_code == 200:
            return response_data["data"]["url"]
        else:
            st.error("이미지 업로드 실패")
            return None
    except Exception as e:
        st.error(f"이미지 업로드 중 오류 발생: {str(e)}")
        return None

# 배경 제거 함수
def remove_background(image_url, api_key):
    try:
        os.environ["REPLICATE_API_TOKEN"] = api_key
        output = replicate.run(
            "fottoai/remove-bg:d20cb34668e219d0a0785a9f61c212f5b8650ebe0f0d0c74812c39ee52ae7ba9",
            input={"image_url": image_url}
        )
        return output
    except Exception as e:
        st.error(f"배경 제거 중 오류 발생: {str(e)}")
        return None

# 파일 업로더 생성
uploaded_file = st.file_uploader("이미지를 선택하세요", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # 업로드된 이미지 표시
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("원본 이미지")
        st.image(uploaded_file, use_column_width=True)
    
    # 배경 제거 버튼
    if st.button("배경 제거"):
        if not api_key:
            st.error("Replicate API 키를 입력해주세요!")
        else:
            with st.spinner("배경을 제거하는 중..."):
                # 이미지를 ImgBB에 업로드
                image_url = upload_to_imgbb(uploaded_file.getvalue())
                
                if image_url:
                    # 배경 제거 실행
                    result = remove_background(image_url, api_key)
                    
                    if result:
                        with col2:
                            st.subheader("결과 이미지")
                            st.image(result, use_column_width=True)
                            
                            # 다운로드 버튼 추가
                            response = requests.get(result)
                            if response.status_code == 200:
                                st.download_button(
                                    label="결과 이미지 다운로드",
                                    data=response.content,
                                    file_name="removed_background.png",
                                    mime="image/png"
                                )
