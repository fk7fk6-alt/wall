import streamlit as st
import requests
import pandas as pd
import folium
from datetime import datetime, timedelta
from streamlit_folium import st_folium

# 1. 페이지 기본 설정 및 제목
st.set_page_config(page_title="지진 분포와 판 구조론 탐구", layout="wide")

st.title("🌍 실시간 지진 데이터로 찾는 지진대 탐구 앱")
st.markdown("""
### 🧑‍🔬 학생 탐구 질문: "지진은 왜 특정 지역에 몰려서 발생할까?"
이 앱은 미국지질조사국(USGS)의 실시간 데이터를 가져와 지도에 표시합니다. 
지진이 발생하는 위치를 관찰하고, 지진들이 어떤 모양을 이루며 연결되는지 찾아보세요!
""")

# 2. 사이드바 - 조건 변경 필터 구성
st.sidebar.header("🔍 탐구 조건 설정")

# 기간 선택 (1일, 7일, 30일)
period = st.sidebar.selectbox(
    "1. 데이터 분석 기간 선택",
    ["최근 1일", "최근 7일", "최근 30일"],
    index=1
)

# 규모(Magnitude) 필터 슬라이더
min_magnitude = st.sidebar.slider(
    "2. 최소 지진 규모(Magnitude) 설정",
    min_value=2.0,
    max_value=7.0,
    value=4.5,
    step=0.5,
    help="규모가 커질수록 에너지가 강한 지진입니다. 값이 클수록 주요 지진대 윤곽이 잘 보입니다."
)

# 기간 선택에 따른 날짜 계산
days_map = {"최근 1일": 1, "최근 7일": 7, "최근 30일": 30}
target_days = days_map[period]
start_time = (datetime.utcnow() - timedelta(days=target_days)).strftime('%Y-%m-%d')

# 3. USGS API 데이터 요청 함수
@st.cache_data(ttl=600)  # 10분간 데이터 캐싱하여 속도 향상 및 API 부하 감소
def fetch_earthquake_data(starttime, minmag):
    url = "https://earthquake.usgov/fdsnws/event/1/query" # 내부 수정을 방지하기 위해 원본 주소 유지
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "starttime": starttime,
        "minmagnitude": minmag,
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        # GeoJSON 데이터를 판다스 데이터프레임으로 변환
        features = data['features']
        earthquakes = []
        for f in features:
            props = f['properties']
            geom = f['geometry']
            earthquakes.append({
                "place": props['place'],
                "mag": props['mag'],
                "time": pd.to_datetime(props['time'], unit='ms'),
                "latitude": geom['coordinates'][1],
                "longitude": geom['coordinates'][0],
                "depth": geom['coordinates'][2]
            })
        return pd.DataFrame(earthquakes)
    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")
        return pd.DataFrame()

# 데이터 로딩 스피너
with st.spinner("🔄 USGS에서 실시간 지진 데이터를 가져오는 중입니다..."):
    df = fetch_earthquake_data(start_time, min_magnitude)

# 4. 데이터 요약 및 시각화 화면 구성
if not df.empty:
    # 대시보드 상단 통계 매트릭스
    col1, col2, col3 = st.columns(3)
    col1.metric("📊 감지된 총 지진 수", f"{len(df)} 건")
    col2.metric("💥 가장 강한 지진 규모", f"M {df['mag'].max():.1f}")
    col3.metric("📅 데이터 기준일", f"{start_time} 이후")

    # 메인 화면 레이아웃 (지도 / 데이터 테이블)
    st.markdown("---")
    st.subheader("🗺️ 세계 지진 발생 분포 지도")
    st.caption("💡 팁: 지도를 축소(Zoom Out)하여 전 세계적인 지진의 흐름을 관찰해 보세요. 점을 클릭하면 상세 정보가 나옵니다.")

    # Folium 지도 생성 (전체 세계가 보이도록 중심점 설정)
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB positron")

    # 지도에 지진 위치 마커(원형) 추가
    for _, row in df.iterrows():
        # 지진 규모에 따라 원의 크기와 색상 동적 설정 (시각적 효과)
        radius = row['mag'] * 1.8
        if row['mag'] >= 6.0:
            color = "#FF0000"  # 강한 지진: 빨간색
        elif row['mag'] >= 4.5:
            color = "#FFA500"  # 중간 지진: 주황색
        else:
            color = "#FFFF00"  # 약한 지진: 노란색

        # 팝업에 표시될 정보 텍스트 (한국어 구성)
        popup_text = f"""
        <b>위치:</b> {row['place']}<br>
        <b>규모:</b> M {row['mag']:.1f}<br>
        <b>깊이:</b> {row['depth']} km<br>
        <b>시간(UTC):</b> {row['time'].strftime('%Y-%m-%d %H:%M')}
        """
        
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=radius,
            popup=folium.Popup(popup_text, max_width=300),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            weight=1
        ).add_to(m)

    # Streamlit 화면에 지도 렌더링
    st_folium(m, width="100%", height=550, returned_objects=[])

    # 5. 학생 활동 및 탐구 가이드 안내
    st.markdown("---")
    with st.expander("📝 [수업 활용 활동지] 학생들과 함께 토론해 보세요!", expanded=True):
        st.markdown("""
        **1단계: 관찰하기**
        * 태평양 주변(주로 아시아 동부와 아메리카 서부 서안)을 따라 지진이 어떻게 배열되어 있나요?
        * 지진이 지구 전체에 고르게 퍼져 있나요, 아니면 띠 모양으로 뭉쳐 있나요?
        
        **2단계: 추론하기**
        * 과학자들은 이처럼 지진이 자주 발생하는 좁고 긴 띠 모양의 지역을 **'지진대'**라고 부릅니다.
        * 과학실 교과서 부록이나 세계 지도에 나오는 **'판의 경계'** 그림을 펼치고, 이 앱의 지진 분포와 비교해 보세요. 어떤 공통점을 찾을 수 있나요?
        
        **3단계: 결론 도출하기**
        * 지진은 왜 특정 지역에 몰려서 발생할까요? 아래 빈칸을 채워 결론을 내려봅시다.
          > *"지진은 주로 지구 겉부분을 이루는 (     )의 경계에서 서로 부딪히거나 멀어지면서 발생하기 때문에 특정 지역에 띠 모양으로 집중된다."*
        """)
        
    # 데이터 상세 보기 (하단 배치)
    with st.expander("📊 지진 데이터 원본 보기"):
        st.dataframe(
            df[['time', 'mag', 'place', 'latitude', 'longitude', 'depth']]
            .sort_values(by='mag', ascending=False),
            use_container_width=True
        )
else:
    st.warning("선택한 조건에 해당하는 지진 데이터가 없거나 API 연결에 실패했습니다. 사이드바에서 조건을 조절해 보세요.")
