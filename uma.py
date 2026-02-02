import streamlit as st
import requests
from bs4 import BeautifulSoup
import math
import re
import time

st.set_page_config(page_title="競馬個別計算機", layout="wide")
st.title("🏇 個別払戻表示・全頭配分シミュレーター")

with st.sidebar:
    st.header("設定")
    url = st.text_input("レースURLを入力")
    bankroll = st.number_input("軍資金 (円)", value=100000, step=1000)
    target_profit = st.number_input("的中時の目標利益 (円)", value=5000, step=500)

if st.button("データ取得と計算を実行"):
    if not url:
        st.warning("URLを入力してください")
    else:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"}
            res = requests.get(url, headers=headers, timeout=10)
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, 'html.parser')

            horses = []
            rows = soup.find_all(["tr", "li", "div"])

            for row in rows:
                text_content = row.get_text(" ", strip=True)
                # オッズ候補（1.1〜150.0倍程度に限定して馬体重誤認を防ぐ）
                odds_matches = re.findall(r'\b\d{1,2}\.\d{1}\b|\b1[0-4]\d\.\d{1}\b', text_content)
                # 馬名候補（2文字以上のカタカナ）
                name_match = re.search(r'[ァ-ヴ]{2,9}', text_content)
                
                if name_match and odds_matches:
                    name = name_match.group().strip()
                    try:
                        # 見つかった数字のうち、もっともらしいものを採用
                        odds_val = float(odds_matches[0])
                        if not any(h['name'] == name for h in horses):
                            horses.append({"name": name, "odds": odds_val})
                    except: continue

            if not horses:
                st.error("データが見つかりませんでした。URLが正しいか、JavaScript専用ページでないか確認してください。")
            else:
                sorted_horses = sorted(horses, key=lambda x: x["odds"])
                
                curr_money = bankroll
                total_invested = 0
                display_data = []

                for h in sorted_horses:
                    # 追い上げ計算：(今までの合計投資 + 目標利益) / (オッズ - 1)
                    stake = math.ceil((total_invested + target_profit) / (h["odds"] - 1) / 100) * 100
                    
                    if stake <= curr_money:
                        # ★ここを修正：その馬単体での払戻を計算
                        individual_payout = int(stake * h["odds"])
                        
                        curr_money -= stake
                        total_invested += stake
                        
                        display_data.append({
                            "馬名": h["name"],
                            "オッズ": f"{h['odds']}倍",
                            "いくら賭けるか": f"{stake:,}円",
                            "的中時の払戻金": f"{individual_payout:,}円", # 個別の払戻金
                            "的中時の純利益": f"{(individual_payout - total_invested):,}円", # 合計投資を引いた利益
                            "残り軍資金": f"{curr_money:,}円"
                        })
                    else:
                        st.warning(f"資金終了: {h['name']} は購入できません")
                        break
                
                if display_data:
                    st.success(f"計算完了！ 合計投資額: {total_invested:,}円")
                    st.table(display_data)

        except Exception as e:
            st.error(f"エラー: {e}")

time.sleep(1)