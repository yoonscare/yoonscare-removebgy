import streamlit as st
import replicate
import requests
import cloudinary
import cloudinary.uploader
from PIL import Image
import io
import os
from io import BytesIO
import time

# 페이지 설정
st.set_page_config(
    page_title="배경 제거 도구",
    page_icon="🖼️",
    layout="wide"
)

# Cloudinary 설정
cloudinary.config( 
    cloud_name = "demo", 
    api_key = "YOUR_CLOUDINARY_API_KEY", 
    api_secret = "YOUR_CLOUDINARY_API_SECRET" 
)

# 세션 상태 초기화
if 'api_key' not in st.session_state:
    st.session_state.api_key = ''
if 'processed_image' not in st.session_state:
    st.session_state.processed_image = None

# 메인 페이지 제목
st.title("🖼️ 이미지 배경 제거 도구")
st.markdown("간단하게 이미지의 배경을 제거해보세요!")

# 사이드바에 API 키 입력 필드 추가
with st.sidebar:
    st.title("설정")
    api_key_input = st.text_input(
        "Replicate API 키를 입력하세요", 
        type="password",
        value=st.session_state.api_key,
        help="https://replicate.com에서 API 키를 발급받을 수 있습니다."
    )
    
    if api_key_input != st.session_state.api_key:
        st.session_state.api_key = api_key_input
        if api_key_input:
            st.success("API 키가 저장되었습니다!")

    st.markdown("""
    ### 사용 방법
    1. Replicate API 키를 입력하세요
    2. 이미지를 업로드하세요
    3. '배경 제거' 버튼을 클릭하세요
    """)

def upload_to_cloudinary(file_data):
    """Cloudinary에 이미지 업로드"""
    try:
        response = cloudinary.uploader.upload(file_data)
        return response['secure_url']
    except Exception as e:
        st.error(f"이미지 업로드 중 오류 발생: {str(e)}")
        return None

def process_uploaded_file(uploaded_file):
    try:
        # 파일을 바이트로 읽기
        file_bytes = uploaded_file.getvalue()
        
        # Cloudinary에 업로드
        image_url = upload_to_cloudinary(file_bytes)
        
        if image_url:
            return image_url
        else:
            st.error("이미지 업로드에 실패했습니다. 다시 시도해주세요.")
            return None
    except Exception as e:
        st.error(f"이미지 처리 중 오류 발생: {str(e)}")
        return None

def remove_background(image_url, api_key):
    try:
        os.environ["REPLICATE_API_TOKEN"] = api_key
        for attempt in range(3):  # 최대 3번 재시도
            try:
                output = replicate.run(
                    "fottoai/remove-bg:d20cb34668e219d0a0785a9f61c212f5b8650ebe0f0d0c74812c39ee52ae7ba9",
                    input={"image_url": image_url}
                )
                return output
            except Exception as e:
                if attempt == 2:  # 마지막 시도였다면
                    raise e
                time.sleep(1)  # 재시도 전 대기
    except Exception as e:
        st.error(f"배경 제거 중 오류 발생: {str(e)}")
        return None

# 파일 업로더 생성
uploaded_file = st.file_uploader(
    "이미지를 선택하세요", 
    type=["png", "jpg", "jpeg"],
    help="최대 200MB까지 업로드 가능합니다"
)

if uploaded_file is not None:
    # 이미지 표시를 위한 컨테이너
    with st.container():
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("원본 이미지")
            st.image(uploaded_file, use_container_width=True)
        
        # 배경 제거 버튼
        if st.button("배경 제거", key="remove_bg_button"):
            if not st.session_state.api_key:
                st.error("Replicate API 키를 입력해주세요!")
            else:
                try:
                    with st.spinner("배경을 제거하는 중..."):
                        # 이미지 업로드 처리
                        image_url = process_uploaded_file(uploaded_file)
                        
                        if image_url:
                            # 배경 제거 실행
                            result = remove_background(image_url, st.session_state.api_key)
                            
                            if result:
                                with col2:
                                    st.subheader("결과 이미지")
                                    st.image(result, use_container_width=True)
                                    
                                    # 결과 이미지 다운로드
                                    try:
                                        response = requests.get(result, timeout=30)
                                        if response.status_code == 200:
                                            st.download_button(
                                                label="결과 이미지 다운로드",
                                                data=response.content,
                                                file_name="removed_background.png",
                                                mime="image/png"
                                            )
                                    except requests.exceptions.RequestException:
                                        st.error("이미지 다운로드 중 오류가 발생했습니다. 다시 시도해주세요.")
                except Exception as e:
                    st.error(f"처리 중 오류가 발생했습니다: {str(e)}")
