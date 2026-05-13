import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import os

# 페이지 설정
st.set_page_config(page_title="예술의전당 데이터 분석 대시보드", layout="wide")

# DB 파일 경로 확인
DB_PATH = 'artcenter.db'

def get_connection():
    if not os.path.exists(DB_PATH):
        st.error(f"⚠️ '{DB_PATH}' 파일을 찾을 수 없습니다. 데이터베이스 파일이 같은 경로에 있는지 확인해주세요!")
        return None
    return sqlite3.connect(DB_PATH)

st.title("🎭 예술의전당 공공데이터 분석 대시보드")
st.markdown("시니어 개발자와 함께하는 데이터 기반 예술 경영 분석 리포트입니다.")

conn = get_connection()

if conn:
    # --- [분석 1] 공연장별 대관 승인율과 실제 공연 비중 ---
    st.header("1. 공연장별 대관 승인율과 실제 공연 비중")
    
    query1 = """
    SELECT 
        r.장소,
        ROUND(CAST(SUM(r.승인건수) AS FLOAT) / SUM(r.신청건수) * 100, 1) as 승인율,
        COUNT(p.제목) as 공연건수
    FROM rental r
    LEFT JOIN performance p ON p.공연장 LIKE '%' || r.장소 || '%'
    GROUP BY r.장소
    HAVING r.신청건수 > 0
    ORDER BY 공연건수 DESC
    """
    df1 = pd.read_sql(query1, conn)

    fig1 = go.Figure()
    fig1.add_trace(go.Bar(x=df1['장소'], y=df1['공연건수'], name='공연 건수(실제)', marker_color='indianred'))
    fig1.add_trace(go.Scatter(x=df1['장소'], y=df1['승인율'], name='승인율(%)', yaxis='y2', line=dict(color='royalblue', width=3)))

    fig1.update_layout(
        title="공연장별 운영 효율성 및 대관 경쟁력 분석",
        yaxis=dict(title="공연 건수"),
        yaxis2=dict(title="승인율 (%)", overlaying='y', side='right', range=[0, 100]),
        legend=dict(x=1.1, y=1),
        hovermode="x unified"
    )
    st.plotly_chart(fig1, use_container_width=True)
    
    with st.expander("🔍 SQL 쿼리 및 상세 인사이트 보기"):
        st.code(query1, language='sql')
        st.write("""
        - **리사이틀홀, IBK기입은행챔버홀, 콘서트홀**은 공연 건수가 압도적으로 높지만(붉은 막대), 승인율은 상대적으로 낮은 편(푸른 선)에 속합니다. 이 시설들은 예술의전당 내에서 가장 인기가 많은 '메인 공연장'임을 알 수 있습니다. 대관 경쟁이 매우 치열함에도 불구하고 실제 가동률이 가장 높다는 것은, 시설의 상업적 가치와 관객 선호도가 매우 높음을 시사합니다.
        - **기타공간, 신세계스퀘어 야외무대, 예술의전당(전체)** 항목은 승인율이 100%에 가깝게 치솟아 있지만, 실제 공연 건수는 다른 메인 홀에 비해 현저히 낮습니다. 이는 정기적인 실내 공연보다는 이벤트성 행사가 열리는 공간의 특성이 반영된 결과입니다. 대관 신청 시 승인될 확률은 매우 높지만, 실제 공연이 매일 열리지는 않는 '특수 목적 공간'으로 해석할 수 있습니다.
        - **인춘아트홀과 자유소극장, 한가람미술관**은 승인율이 40~50%대를 유지하면서 적정 수준의 공연 건수를 보여주고 있습니다. 메인 홀들보다 대관 문턱이 낮으면서도 꾸준히 공연이 개최되는 곳들입니다. 대형 공연보다는 중소규모 예술가들의 활동이 활발하게 일어나는 '문화예술의 완충지대' 역할을 충실히 수행하고 있다고 분석됩니다.
        """)

    st.divider()

    # --- [분석 2] 회원 등급별 핵심 관객층 분석 ---
    st.header("2. 회원 등급별 핵심 관객층 분석")
    
    query2 = """
    SELECT 
        CASE 
            WHEN 나이 < 30 THEN '20대 이하'
            WHEN 나이 BETWEEN 30 AND 49 THEN '30-40대'
            ELSE '50대 이상'
        END as 연령대,
        SUM(골드 + 블루) as 유료회원,
        SUM(무료) as 무료회원
    FROM members
    GROUP BY 연령대
    ORDER BY 연령대
    """
    df2 = pd.read_sql(query2, conn)
    df2_melted = df2.melt(id_vars='연령대', var_name='회원구분', value_name='인원수')

    fig2 = px.bar(df2_melted, x='연령대', y='인원수', color='회원구분', 
                 title="연령대별 유료/무료 회원 분포 현황", barmode='stack',
                 color_discrete_map={'유료회원': '#FFD700', '무료회원': '#C0C0C0'})
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("🔍 SQL 쿼리 및 상세 인사이트 보기"):
        st.code(query2, language='sql')
        st.write("""
        - **전체 막대의 높이**를 보면 30-40대 연령층이 다른 그룹에 비해 압도적으로 많으며, 약 60만 명에 육박하는 인원수를 보여줍니다. 예술의전당의 가장 두터운 관객층은 30-40대입니다. 이들은 경제 활동의 핵심 계층으로서 문화예술 소비의 가장 큰 파이를 차지하고 있음을 알 수 있습니다.
        - **50대 이상 연령층**은 막대의 전체 높이가 30-40대보다 낮지만, 노란색 부분(유료회원)이 차지하는 비율은 모든 연령대 중 가장 높습니다. 50대 이상 관객은 전체 인원수는 주력층보다 적을지 몰라도, 실제 유료 멤버십(골드, 블루 등)을 유지하는 비율이 가장 높습니다. 이는 이들이 예술의전당에 가장 높은 로열티를 가진 '핵심 실무 관객층'이자 VIP 마케팅의 주 타겟임을 시사합니다.
        - **20대 이하 그룹**은 인원수 자체는 적지 않으나, 유료회원의 비중(노란색)이 눈에 띄게 낮습니다. 학생 및 사회 초년생이 많은 20대 이하 그룹은 유료 멤버십 가입에 대한 경제적 부담이 있을 수 있습니다. 이들을 미래의 유료 고객으로 전환시키기 위한 청년 할인 혜택이나 특화된 입문자 프로그램이 필요하다는 전략적 해석이 가능합니다.
        """)

    st.divider()

    # --- [분석 3] 월별 공연 개최 성수기 분석 ---
    st.header("3. 월별 공연 개최 성수기 분석")
    
    query3 = """
    SELECT 
        strftime('%m', 공연시작일) as 월,
        COUNT(*) as 공연건수
    FROM performance
    WHERE 공연시작일 IS NOT NULL
    GROUP BY 월
    ORDER BY 월
    """
    df3 = pd.read_sql(query3, conn)
    df3['월'] = df3['월'].apply(lambda x: f"{int(x)}월")

    fig3 = px.line(df3, x='월', y='공연건수', title="월별 공연 개최 건수 추이", markers=True)
    fig3.update_yaxes(range=[0, df3['공연건수'].max() * 1.2]) 
    st.plotly_chart(fig3, use_container_width=True)

    with st.expander("🔍 SQL 쿼리 및 상세 인사이트 보기"):
        st.code(query3, language='sql')
        st.write("""
        - **그래프를 보면 5월(약 1,900건)과 11월(약 1,800건 이상)**을 정점으로 두 번의 큰 산이 형성되는 것을 볼 수 있습니다. 예술의전당 공연 시장은 연중 두 번의 확실한 대성수기를 가집니다. 5월은 '가정의 달'을 겨냥한 가족 단위 기획 공연이, 11~12월은 연말 결산 및 송년 음악회가 집중되면서 공연 개최 건수가 최고조에 달합니다.
        - **1월(약 700건대)**에 가장 낮은 수치를 보이며, 여름휴가 시즌인 **8월(약 1,300건대)**에도 상반기 성수기 대비 수치가 확연히 꺾이는 모습입니다. 1월은 연말 대형 공연들이 종료된 후 다음 시즌을 준비하는 교체기이며, 8월은 폭염과 휴가철의 영향으로 실내 공연 수요가 소폭 감소하거나 재정비에 들어가는 '계절적 휴식기'의 특징을 보입니다.
        - **1월 최저점을 찍은 후 5월까지** 매달 공연 건수가 가파르게 상승하는 우상향 곡선을 그립니다. 이는 예술계의 '시즌 오픈'이 3월부터 본격화되어 5월까지 열기가 이어짐을 나타냅니다. 예술의전당이 겨울철의 공백을 매우 빠르게 회복하며 문화예술 공급을 정상화하는 운영 능력을 갖추고 있음을 입증합니다.
        """)

    conn.close()