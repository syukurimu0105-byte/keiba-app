import streamlit as st
import re
import math

# --- ページ設定 ---
st.set_page_config(page_title="競馬・投資配分シミュレーター", layout="wide")
st.title("🏇 安定投シミュレーション")

# --- 設定エリア（サイドバー） ---
with st.sidebar:
    st.header("⚙️ 投資・予算設定")
    bankroll_input = st.number_input("軍資金 (円)", value=3000, step=100)
    target_base = st.number_input("目標金額 (円)", value=5000, step=500)
    
    st.divider()
    st.info("""
    【入力ヒント】
    「馬番 人気 馬名 オッズ」の順で貼り付けてください。
    例：
    1 3 サトノダイヤモンド 2.5
    7 1 キタサンブラック 1.8
    """)

# --- メイン：データ入力エリア ---
st.subheader("📝 出走馬データ入力")
raw_input = st.text_area(
    "入力エリア（馬番 人気 馬名 オッズ の順）", 
    value="", 
    height=250,
    placeholder="1 3 サトノダイヤモンド 2.5\n7 1 キタサンブラック 1.8"
)

if st.button("計算を実行"):
    if not raw_input.strip():
        st.warning("データが入力されていません。")
    else:
        horses = []
        lines = raw_input.strip().split('\n')
        for line in lines:
            # 正規表現で「馬番(数字) 人気(数字) 馬名(文字) オッズ(数字)」を抽出
            match = re.search(r'(\d+)\s+(\d+)\s+([^\d\s]+)\s+([\d.]+)', line)
            if match:
                num, fav, name, odds = match.group(1), match.group(2), match.group(3), float(match.group(4))
                if odds > 0:
                    horses.append({"num": num, "fav": fav, "name": name, "odds": odds})
            else:
                # 従来の「馬名 オッズ」形式にも一応対応
                match_simple = re.search(r'([^\d\s]+)\s+([\d.]+)', line)
                if match_simple:
                    name, odds = match_simple.group(1), float(match_simple.group(2))
                    horses.append({"num": "-", "fav": "-", "name": name, "odds": odds})

        if not horses:
            st.error("有効なデータを入力してください。「馬番 人気 馬名 オッズ」の順でスペース区切りが必要です。")
        else:
            # オッズの低い順（本命順）にソート
            sorted_horses = sorted(horses, key=lambda x: x["odds"])
            
            purchase_list = [] # 実際に買う馬
            all_results = []   # 全頭の結果
            current_bankroll = bankroll_input
            
            for h in sorted_horses:
                # 計算ロジックは変更なし
                raw_stake = target_base / h["odds"]
                planned_stake = math.ceil(raw_stake / 100) * 100
                
                if current_bankroll >= planned_stake:
                    status = "✅ 購入"
                    actual_stake = planned_stake
                    current_bankroll -= actual_stake
                    
                    actual_payout = int(actual_stake * h["odds"])
                    
                    # 購入リスト
                    purchase_list.append({
                        "馬番": h["num"],
                        "人気": h["fav"],
                        "馬名": h["name"],
                        "オッズ": f"{h['odds']}倍",
                        "投資額（買い）": f"{actual_stake:,}円",
                        "的中時払戻": f"{actual_payout:,}円"
                    })
                else:
                    status = "❌ 予算不足"
                    actual_stake = 0
                
                # 全頭リスト
                all_results.append({
                    "ステータス": status,
                    "馬番": h["num"],
                    "人気": h["fav"],
                    "馬名": h["name"],
                    "オッズ": f"{h['odds']}倍",
                    "投資額": f"{actual_stake:,}円",
                    "軍資金残金": f"{current_bankroll:,}円"
                })

            # --- 結果表示 ---
            st.subheader("💰 今回の買い目リスト")
            if purchase_list:
                st.table(purchase_list)
            else:
                st.error("購入可能な馬がいません。")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("初期軍資金", f"{bankroll_input:,}円")
            with col2:
                total_invest = bankroll_input - current_bankroll
                st.metric("最終軍資金残高", f"{current_bankroll:,}円", delta=f"-{total_invest:,}円", delta_color="inverse")

            with st.expander("📊 すべての計算詳細（スキップ含む）を表示"):
                st.table(all_results)
