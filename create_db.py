"""
create_db.py
────────────
bus_data.csv, cctv_data.csv, crime_data.csv 를 읽어
안전주거.db (SQLite) 로 저장하는 스크립트입니다.
app.py 를 실행하기 전에 먼저 이 파일을 실행해주세요.
"""
import sqlite3
import pandas as pd
import os

# AUTO-INJECTED: Korean font setup for matplotlib
import os as _os
import matplotlib.font_manager as _fm
import matplotlib.pyplot as _plt
if not any('NanumGothic' in f.name for f in _fm.fontManager.ttflist):
    for _font in ['/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
                  '/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf']:
        if _os.path.exists(_font):
            _fm.fontManager.addfont(_font)
_plt.rcParams.update({'font.family': 'NanumGothic', 'axes.unicode_minus': False})
del _os, _fm, _plt
# END AUTO-INJECTED Korean font setup


DB_PATH = "안전주거.db"
FILES   = {"bus": "bus_data.csv", "cctv": "cctv_data.csv", "crime": "crime_data.csv"}

for key, fname in FILES.items():
    if not os.path.exists(fname):
        print(f"❌  {fname} 파일이 없습니다. 같은 폴더에 넣어주세요.")
        exit(1)

conn = sqlite3.connect(DB_PATH)

bus   = pd.read_csv("bus_data.csv")
cctv  = pd.read_csv("cctv_data.csv")
crime = pd.read_csv("crime_data.csv")

# 컬럼명 정리 (공백 제거 및 SQLite 호환)
bus.columns   = ["자치구", "버스정류소개수"]
cctv.columns  = ["자치구", "CCTV개수"]
crime.columns = ["범죄대분류", "범죄중분류", "자치구", "건수"]

bus.to_sql("bus",   conn, if_exists="replace", index=False)
cctv.to_sql("cctv", conn, if_exists="replace", index=False)
crime.to_sql("crime", conn, if_exists="replace", index=False)

conn.close()
print(f"✅  {DB_PATH} 생성 완료!")
print("   → 이제 터미널에서  streamlit run app.py  를 실행하세요.")
