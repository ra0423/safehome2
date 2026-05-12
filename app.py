import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import numpy as np
import os

# ── 한글 폰트 설정 ──────────────────────────────────────────
import matplotlib
matplotlib.rcParams["font.family"] = "NanumGothic"
matplotlib.rcParams["axes.unicode_minus"] = False

st.set_page_config(page_title="서울 안전주거 분석 대시보드", page_icon="🏙️", layout="wide")

# ── DB 연결 ──────────────────────────────────────────────────
DB_PATH = "안전주거.db"

@st.cache_resource
def get_conn():
    if not os.path.exists(DB_PATH):
        return None
    return sqlite3.connect(DB_PATH, check_same_thread=False)

conn = get_conn()

if conn is None:
    st.error(
        "⚠️ **안전주거.db 파일을 찾을 수 없습니다.**\n\n"
        "아래 순서대로 파일을 준비해주세요:\n"
        "1. 이 앱과 같은 폴더에 `bus_data.csv`, `cctv_data.csv`, `crime_data.csv`를 넣어주세요.\n"
        "2. 터미널에서 `python create_db.py` 를 실행해 DB를 먼저 생성하세요.\n"
        "3. `안전주거.db` 파일이 생성된 것을 확인한 뒤 앱을 다시 실행하세요."
    )
    st.info("📌 `create_db.py` 파일도 함께 제공되어 있습니다. 먼저 실행해 주세요!")
    st.stop()

# ── SQL 쿼리 정의 ─────────────────────────────────────────────
SQL_TRAFFIC_CRIME = """
SELECT
    b.자치구,
    b.버스정류소개수,
    SUM(c.건수) AS 총범죄건수,
    ROUND(SUM(c.건수) * 1.0 / b.버스정류소개수, 2) AS 정류소당범죄율
FROM bus b
JOIN crime c ON b.자치구 = c.자치구
GROUP BY b.자치구
ORDER BY b.버스정류소개수 DESC
"""

SQL_CCTV_CRIME = """
SELECT
    cv.자치구,
    cv.CCTV개수,
    SUM(c.건수) AS 총범죄건수,
    ROUND(SUM(c.건수) * 1.0 / cv.CCTV개수, 4) AS CCTV당범죄율
FROM cctv cv
JOIN crime c ON cv.자치구 = c.자치구
GROUP BY cv.자치구
ORDER BY cv.CCTV개수 DESC
"""

SQL_TRIPLE = """
SELECT
    b.자치구,
    b.버스정류소개수,
    cv.CCTV개수,
    SUM(c.건수) AS 총범죄건수
FROM bus b
JOIN cctv cv ON b.자치구 = cv.자치구
JOIN crime c ON b.자치구 = c.자치구
GROUP BY b.자치구
ORDER BY SUM(c.건수) DESC
"""

@st.cache_data
def load(sql):
    return pd.read_sql_query(sql, conn)

df_tc  = load(SQL_TRAFFIC_CRIME)
df_cc  = load(SQL_CCTV_CRIME)
df_tri = load(SQL_TRIPLE)

# ── 색상 팔레트 ───────────────────────────────────────────────
COLOR_BUS   = "#4C72B0"
COLOR_CRIME = "#DD8452"
COLOR_CCTV  = "#55A868"

# ── 헤더 ─────────────────────────────────────────────────────
st.title("🏙️ 서울시 안전주거 분석 대시보드")
st.caption("버스 정류소 · CCTV · 범죄 데이터로 살펴보는 서울 25개 자치구 안전 지표")
st.divider()

# ════════════════════════════════════════════════════════════
# 1️⃣  교통 편의 vs 범죄율
# ════════════════════════════════════════════════════════════
st.subheader("1️⃣  교통 편의(버스 정류소) vs 범죄율")

with st.expander("🗄️ 사용된 SQLite 쿼리 보기"):
    st.code(SQL_TRAFFIC_CRIME, language="sql")

fig1, axes1 = plt.subplots(1, 2, figsize=(14, 5))

# 버스 정류소 많고 범죄 낮은 TOP5 / 버스 많고 범죄 높은 TOP5
df_sorted = df_tc.sort_values("버스정류소개수", ascending=False)
top_bus = df_sorted.head(10)

ax = axes1[0]
x = np.arange(len(top_bus))
w = 0.4
bars1 = ax.bar(x - w/2, top_bus["버스정류소개수"], w, label="버스 정류소 수", color=COLOR_BUS)
ax2 = ax.twinx()
bars2 = ax2.bar(x + w/2, top_bus["총범죄건수"], w, label="총 범죄 건수", color=COLOR_CRIME, alpha=0.8)
ax.set_xticks(x)
ax.set_xticklabels(top_bus["자치구"], rotation=45, ha="right", fontsize=9)
ax.set_ylabel("버스 정류소 수", color=COLOR_BUS)
ax2.set_ylabel("총 범죄 건수", color=COLOR_CRIME)
ax.set_title("버스 정류소 상위 10구 – 범죄 건수 비교")
lines = [plt.Rectangle((0,0),1,1, color=COLOR_BUS), plt.Rectangle((0,0),1,1, color=COLOR_CRIME)]
ax.legend(lines, ["버스 정류소 수", "총 범죄 건수"], loc="upper right", fontsize=8)

# 산점도: 버스 수 vs 총 범죄
ax = axes1[1]
ax.scatter(df_tc["버스정류소개수"], df_tc["총범죄건수"], color=COLOR_BUS, s=80, alpha=0.8, edgecolors="white")
for _, row in df_tc.iterrows():
    ax.annotate(row["자치구"], (row["버스정류소개수"], row["총범죄건수"]), fontsize=7, ha="left", va="bottom")
m, b = np.polyfit(df_tc["버스정류소개수"], df_tc["총범죄건수"], 1)
xline = np.linspace(df_tc["버스정류소개수"].min(), df_tc["버스정류소개수"].max(), 100)
ax.plot(xline, m*xline + b, "r--", linewidth=1.5, label="추세선")
corr = df_tc["버스정류소개수"].corr(df_tc["총범죄건수"])
ax.set_xlabel("버스 정류소 수")
ax.set_ylabel("총 범죄 건수")
ax.set_title(f"버스 정류소 수 vs 총 범죄 건수  (상관계수 r = {corr:.2f})")
ax.legend(fontsize=8)

plt.tight_layout()
st.pyplot(fig1)
plt.close()

# 교통 좋고 치안 나쁜/좋은 구 하이라이트
bus_med   = df_tc["버스정류소개수"].median()
crime_med = df_tc["총범죄건수"].median()
good_both = df_tc[(df_tc["버스정류소개수"] >= bus_med) & (df_tc["총범죄건수"] <= crime_med)].sort_values("총범죄건수")
bad_safe  = df_tc[(df_tc["버스정류소개수"] <  bus_med) & (df_tc["총범죄건수"] >  crime_med)].sort_values("총범죄건수", ascending=False)

col1, col2 = st.columns(2)
with col1:
    st.success("🚌 교통 편리 & 범죄 적음 (추천 지역)")
    st.dataframe(good_both[["자치구","버스정류소개수","총범죄건수"]].reset_index(drop=True))
with col2:
    st.warning("🚨 교통 불편 & 범죄 많음 (주의 지역)")
    st.dataframe(bad_safe[["자치구","버스정류소개수","총범죄건수"]].reset_index(drop=True))

st.info(
    f"📌 **인사이트**  \n"
    f"버스 정류소 수와 총 범죄 건수의 상관계수는 **r = {corr:.2f}** 입니다. "
    f"정류소가 많아 유동인구가 많은 자치구일수록 범죄 노출 빈도가 높아지는 경향이 있습니다. "
    f"단, 교통 편의와 범죄율이 반드시 비례하지는 않으며, **{good_both['자치구'].iloc[0] if len(good_both) else ''}** 등 일부 구는 교통이 편리하면서도 범죄율이 낮아 안전한 생활환경을 유지하고 있습니다."
)

st.divider()

# ════════════════════════════════════════════════════════════
# 2️⃣  CCTV 개수 vs 범죄율
# ════════════════════════════════════════════════════════════
st.subheader("2️⃣  CCTV 개수 vs 범죄율")

with st.expander("🗄️ 사용된 SQLite 쿼리 보기"):
    st.code(SQL_CCTV_CRIME, language="sql")

fig2, axes2 = plt.subplots(1, 2, figsize=(14, 5))

# 막대+꺾은선
df_cc_s = df_cc.sort_values("CCTV개수", ascending=False).head(10)
ax = axes2[0]
x = np.arange(len(df_cc_s))
ax.bar(x, df_cc_s["CCTV개수"], color=COLOR_CCTV, label="CCTV 개수")
ax2 = ax.twinx()
ax2.plot(x, df_cc_s["총범죄건수"], "o-", color=COLOR_CRIME, linewidth=2, label="총 범죄 건수")
ax.set_xticks(x)
ax.set_xticklabels(df_cc_s["자치구"], rotation=45, ha="right", fontsize=9)
ax.set_ylabel("CCTV 개수", color=COLOR_CCTV)
ax2.set_ylabel("총 범죄 건수", color=COLOR_CRIME)
ax.set_title("CCTV 상위 10구 – 범죄 건수 추이")
lines = [plt.Rectangle((0,0),1,1, color=COLOR_CCTV), plt.Line2D([0],[0], color=COLOR_CRIME, marker="o")]
ax.legend(lines, ["CCTV 개수", "총 범죄 건수"], loc="upper right", fontsize=8)

# 산점도
ax = axes2[1]
ax.scatter(df_cc["CCTV개수"], df_cc["총범죄건수"], color=COLOR_CCTV, s=80, alpha=0.8, edgecolors="white")
for _, row in df_cc.iterrows():
    ax.annotate(row["자치구"], (row["CCTV개수"], row["총범죄건수"]), fontsize=7, ha="left", va="bottom")
m2, b2 = np.polyfit(df_cc["CCTV개수"], df_cc["총범죄건수"], 1)
xline2 = np.linspace(df_cc["CCTV개수"].min(), df_cc["CCTV개수"].max(), 100)
ax.plot(xline2, m2*xline2 + b2, "r--", linewidth=1.5, label="추세선")
corr2 = df_cc["CCTV개수"].corr(df_cc["총범죄건수"])
ax.set_xlabel("CCTV 개수")
ax.set_ylabel("총 범죄 건수")
ax.set_title(f"CCTV 개수 vs 총 범죄 건수  (상관계수 r = {corr2:.2f})")
ax.legend(fontsize=8)

plt.tight_layout()
st.pyplot(fig2)
plt.close()

cctv_med  = df_cc["CCTV개수"].median()
crime_med2 = df_cc["총범죄건수"].median()
safe_cctv = df_cc[(df_cc["CCTV개수"] >= cctv_med) & (df_cc["총범죄건수"] <= crime_med2)].sort_values("총범죄건수")

col3, col4 = st.columns(2)
with col3:
    st.success("📷 CCTV 많고 범죄 적음 (치안 효과 지역)")
    st.dataframe(safe_cctv[["자치구","CCTV개수","총범죄건수"]].reset_index(drop=True))
with col4:
    st.metric("CCTV–범죄 상관계수", f"{corr2:.2f}", help="1에 가까울수록 양의 상관, -1에 가까울수록 음의 상관")

st.info(
    f"📌 **인사이트**  \n"
    f"CCTV 수와 총 범죄 건수의 상관계수는 **r = {corr2:.2f}** 입니다. "
    f"CCTV가 많다고 해서 범죄가 반드시 줄어들지는 않으며, 이미 범죄 발생이 잦은 지역에 CCTV를 집중 배치하는 경향도 영향을 줍니다. "
    f"그러나 CCTV를 일찍부터 확대한 자치구에서는 상대적으로 낮은 범죄율을 유지하는 패턴도 확인됩니다."
)

st.divider()

# ════════════════════════════════════════════════════════════
# 3️⃣  버스 정류소 · CCTV · 범죄의 3자 상관관계
# ════════════════════════════════════════════════════════════
st.subheader("3️⃣  버스 정류소 · CCTV · 범죄 3자 상관관계 검증")

with st.expander("🗄️ 사용된 SQLite 쿼리 보기"):
    st.code(SQL_TRIPLE, language="sql")

fig3, axes3 = plt.subplots(1, 3, figsize=(17, 5))

# ① 버블 차트: 버스(x), CCTV(y), 크기=범죄
ax = axes3[0]
sizes = (df_tri["총범죄건수"] / df_tri["총범죄건수"].max()) * 800 + 50
sc = ax.scatter(df_tri["버스정류소개수"], df_tri["CCTV개수"],
                s=sizes, c=df_tri["총범죄건수"], cmap="YlOrRd",
                alpha=0.8, edgecolors="gray", linewidth=0.5)
plt.colorbar(sc, ax=ax, label="총 범죄 건수")
for _, row in df_tri.iterrows():
    ax.annotate(row["자치구"], (row["버스정류소개수"], row["CCTV개수"]),
                fontsize=6.5, ha="center", va="bottom")
ax.set_xlabel("버스 정류소 수")
ax.set_ylabel("CCTV 개수")
ax.set_title("버스·CCTV·범죄 버블 차트\n(버블 크기·색상 = 범죄 건수)")

# ② 상관관계 히트맵
ax = axes3[1]
corr_mat = df_tri[["버스정류소개수","CCTV개수","총범죄건수"]].corr()
sns.heatmap(corr_mat, annot=True, fmt=".2f", cmap="coolwarm",
            ax=ax, linewidths=0.5, square=True,
            xticklabels=["버스 정류소","CCTV","범죄"],
            yticklabels=["버스 정류소","CCTV","범죄"])
ax.set_title("변수 간 상관계수 히트맵")

# ③ 4분면 산점도: 버스(x), 범죄(y), CCTV 색상
ax = axes3[2]
sc2 = ax.scatter(df_tri["버스정류소개수"], df_tri["총범죄건수"],
                 c=df_tri["CCTV개수"], cmap="Blues", s=100,
                 edgecolors="gray", linewidth=0.5)
plt.colorbar(sc2, ax=ax, label="CCTV 개수")
xm, ym = df_tri["버스정류소개수"].mean(), df_tri["총범죄건수"].mean()
ax.axvline(xm, color="gray", linestyle="--", linewidth=1)
ax.axhline(ym, color="gray", linestyle="--", linewidth=1)
for _, row in df_tri.iterrows():
    ax.annotate(row["자치구"], (row["버스정류소개수"], row["총범죄건수"]),
                fontsize=6.5, ha="left", va="bottom")
ax.set_xlabel("버스 정류소 수")
ax.set_ylabel("총 범죄 건수")
ax.set_title("4분면 분석: 버스·범죄·CCTV\n(색 진할수록 CCTV 많음)")
ax.text(xm*0.6, ym*1.05, "교통↓ 범죄↑", fontsize=8, color="red")
ax.text(xm*1.02, ym*1.05, "교통↑ 범죄↑", fontsize=8, color="darkorange")
ax.text(xm*0.6, ym*0.6, "교통↓ 범죄↓", fontsize=8, color="green")
ax.text(xm*1.02, ym*0.6, "교통↑ 범죄↓", fontsize=8, color="steelblue")

plt.tight_layout()
st.pyplot(fig3)
plt.close()

r_bus_crime  = df_tri["버스정류소개수"].corr(df_tri["총범죄건수"])
r_cctv_crime = df_tri["CCTV개수"].corr(df_tri["총범죄건수"])
r_bus_cctv   = df_tri["버스정류소개수"].corr(df_tri["CCTV개수"])

col5, col6, col7 = st.columns(3)
col5.metric("버스↔범죄 상관계수", f"{r_bus_crime:.2f}")
col6.metric("CCTV↔범죄 상관계수", f"{r_cctv_crime:.2f}")
col7.metric("버스↔CCTV 상관계수", f"{r_bus_cctv:.2f}")

st.info(
    f"📌 **종합 인사이트**  \n"
    f"**① 버스 정류소가 많은 곳(교통 편의 지역)에서 범죄율도 높은가?**  \n"
    f"버스 정류소 수와 범죄 건수의 상관계수는 **r = {r_bus_crime:.2f}** 로, 유동인구가 많은 교통 중심지일수록 범죄 노출 빈도가 다소 높게 나타납니다.  \n"
    f"**② CCTV가 많은 동네에서 실제 범죄율이 낮은가?**  \n"
    f"CCTV↔범죄 상관계수 **r = {r_cctv_crime:.2f}** — CCTV가 많다고 범죄가 일방적으로 줄지는 않지만, 버스 정류소 수에 비해 CCTV가 충분히 많은 자치구에서 범죄 억제 효과가 관찰됩니다.  \n"
    f"**③ 교통·CCTV·범죄 3자 관계는?**  \n"
    f"버스↔CCTV 상관 **r = {r_bus_cctv:.2f}** 는 교통이 발달한 구에 CCTV도 함께 집중되는 경향을 보여줍니다. "
    f"결국 '교통 편의 → 유동인구 증가 → CCTV 확충 → 범죄 억제'라는 선순환 구조가 일부 자치구에서 작동하고 있음을 확인할 수 있습니다."
)

st.divider()

# ── 푸터 ──────────────────────────────────────────────────────
st.caption(
    "📊 데이터 출처: 서울 열린데이터 광장 | "
    "분석: 버스 정류소 · CCTV · 범죄 통계 (서울 25개 자치구)"
)
