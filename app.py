import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import os

# 페이지 설정
st.set_page_config(page_title="예술의전당 데이터 분석", layout="wide")

# DB 파일 경로 확인
DB_PATH = 'artcenter.db'

def get_connection():
    if not os.path.exists(DB_PATH):
        st.error(f"⚠️ '{DB_PATH}' 파일을 찾을 수 없습니다. 데이터베이스 파일이 같은 경로에 있는지 확인해주세요!")
        return None
    return sqlite3.connect(DB_PATH)

st.title("🎭 예술의전당 운영 현황 분석 대시보드")
st.markdown("공공데이터를 활용하여 대관 승인율, 회원 분포, 공연 성수기를 분석합니다.")

conn = get_connection()

if conn:
    # --- [분석 1] 공연장별 대관 승인율과 실제 공연 비중 ---
    st.header("1. 공연장별 대관 승인율 vs 실제 공연 비중")
    
    query1 = """
    SELECT 
        r.장소,
        ROUND(CAST(SUM(r.승인건수) AS FLOAT) / SUM(r.신청건수) * 100, 1) as 승인율,
        COUNT(p.제목) as 공연건수
    FROM rental r
    LEFT JOIN performance p ON p.공연장 LIKE '%' || r.장소 || '%'
    GROUP BY r.장소
    HAVING r.신청건수 > 0
    """
    df1 = pd.read_sql(query1, conn)

    fig1 = go.Figure()
    fig1.add_trace(go.Bar(x=df1['장소'], y=df1['공연건수'], name='공연 건수', marker_color='indianred'))
    fig1.add_trace(go.Scatter(x=df1['장소'], y=df1['승인율'], name='승인율(%)', yaxis='y2', line=dict(color='royalblue', width=3)))

    fig1.update_layout(
        title="장소별 운영 효율성 (JOIN 분석)",
        yaxis=dict(title="공연 건수"),
        yaxis2=dict(title="승인율 (%)", overlaying='y', side='right', range=[0, 100]),
        legend=dict(x=1.1, y=1)
    )
    st.plotly_chart(fig1, use_container_width=True)
    
    with st.expander("🔍 SQL 쿼리 및 인사이트 보기"):
        st.code(query1, language='sql')
        st.write("- **인사이트**: 특정 공연장은 승인율이 높음에도 공연 건수가 적을 수 있습니다. 이는 대관 외 자체 기획 공연 비중이 높거나 시설 유지보수 기간이 길었음을 시사합니다.")

    st.divider()

    # --- [분석 2] 회원 등급별 핵심 관객층 분석 ---
    st.header("2. 연령대별 유료/무료 회원 비중 분석")
    
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
                 title="연령별 회원 등급 분포 (CASE WHEN 활용)", barmode='stack',
                 color_discrete_map={'유료회원': '#FFD700', '무료회원': '#C0C0C0'})
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("🔍 SQL 쿼리 및 인사이트 보기"):
        st.code(query2, language='sql')
        st.write("- **인사이트**: 30-40대 층에서 유료 회원 전환율이 가장 높게 나타난다면, 해당 연령대를 타겟으로 한 프리미엄 멤버십 마케팅이 효과적일 것입니다.")

    st.divider()

    # --- [분석 3] 월별 공연 개최 성수기 분석 ---
    st.header("3. 월별 공연 성수기 트렌드")
    
    # SQLite는 strftime을 사용하여 날짜에서 월을 추출합니다.
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

    fig3 = px.line(df3, x='월', y='공연건수', title="연간 공연 개최 패턴", markers=True)
    fig3.update_yaxes(range=[0, df3['공연건수'].max() * 1.2]) # Y축 여유 공간 확보
    st.plotly_chart(fig3, use_container_width=True)

    with st.expander("🔍 SQL 쿼리 및 인사이트 보기"):
        st.code(query3, language='sql')
        st.write("- **인사이트**: 연말(11-12월) 혹은 특정 시즌에 공연이 집중되는 경향이 보입니다. 이를 통해 관객 혼잡도 관리 및 비수기 타겟 할인 프로모션 전략을 수립할 수 있습니다.")

    conn.close()