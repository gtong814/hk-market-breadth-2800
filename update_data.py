import json
from datetime import datetime, timezone, timedelta
import pandas as pd
import yfinance as yf

# 對應 Pine Script 的 36 隻核心成分股（Yahoo Finance 需補滿 4 位數）
SECTORS = {
    "tech": ["0700.HK", "9988.HK", "3690.HK", "1810.HK", "9618.HK", "9999.HK", "9888.HK", "1024.HK", "0981.HK", "0992.HK"],
    "fin":  ["0005.HK", "1299.HK", "0939.HK", "0388.HK", "1398.HK", "3988.HK", "2318.HK", "3968.HK", "2628.HK", "2388.HK", "0016.HK", "1113.HK", "0823.HK", "0688.HK"],
    "cons": ["1211.HK", "0941.HK", "0883.HK", "0857.HK", "0001.HK", "0002.HK", "0669.HK", "2020.HK", "9633.HK", "0027.HK", "1093.HK", "0175.HK"],
}

ALL_TICKERS = SECTORS["tech"] + SECTORS["fin"] + SECTORS["cons"]

def main():
    # 下載 2 年日線復權數據（對應 TradingView ADJ）
    df = yf.download(ALL_TICKERS, period="2y", interval="1d", auto_adjust=False, progress=False)["Close"]
    df = df.ffill()

    # 計算 20 / 50 / 200 SMA 並判斷收盤價是否站上均線 (1 或 0)
    above_20  = (df > df.rolling(20).mean()).astype(int)
    above_50  = (df > df.rolling(50).mean()).astype(int)
    above_200 = (df > df.rolling(200).mean()).astype(int)

    def calc_pct(above_df, cols):
        return (above_df[cols].sum(axis=1) / len(cols) * 100.0).round(1)

    # 計算各板塊與整體百分比序列
    hsi_20,  hsi_50,  hsi_200  = calc_pct(above_20, ALL_TICKERS),     calc_pct(above_50, ALL_TICKERS),     calc_pct(above_200, ALL_TICKERS)
    tech_20, tech_50, tech_200 = calc_pct(above_20, SECTORS["tech"]), calc_pct(above_50, SECTORS["tech"]), calc_pct(above_200, SECTORS["tech"])
    fin_20,  fin_50,  fin_200  = calc_pct(above_20, SECTORS["fin"]),  calc_pct(above_50, SECTORS["fin"]),  calc_pct(above_200, SECTORS["fin"])
    cons_20, cons_50, cons_200 = calc_pct(above_20, SECTORS["cons"]), calc_pct(above_50, SECTORS["cons"]), calc_pct(above_200, SECTORS["cons"])

    # 取最新一日 (-1) 與 5 個交易日前 (-6，對應 Pine Script [5])
    hk_tz = timezone(timedelta(hours=8))
    updated_at = datetime.now(hk_tz).strftime("%Y-%m-%d %H:%M HKT")
    last_n = 20  # 圖表顯示最近 20 個交易日

    output = {
        "updated_at": updated_at,
        "trade_date": df.index[-1].strftime("%Y-%m-%d"),
        "dates": [d.strftime("%m-%d") for d in df.index[-last_n:]],
        "sectors": [
            {"key": "hsi",  "name": "● 1. 恒指整體", "color": "#a855f7", "v1": float(hsi_20.iloc[-1]),  "v2": float(hsi_50.iloc[-1]),  "v3": float(hsi_200.iloc[-1]),  "prev50": float(hsi_50.iloc[-6])},
            {"key": "tech", "name": "● 2. 科技核心", "color": "#00acc1", "v1": float(tech_20.iloc[-1]), "v2": float(tech_50.iloc[-1]), "v3": float(tech_200.iloc[-1]), "prev50": float(tech_50.iloc[-6])},
            {"key": "fin",  "name": "● 3. 金融地產", "color": "#3b82f6", "v1": float(fin_20.iloc[-1]),  "v2": float(fin_50.iloc[-1]),  "v3": float(fin_200.iloc[-1]),  "prev50": float(fin_50.iloc[-6])},
            {"key": "cons", "name": "● 4. 消費公用", "color": "#f57c00", "v1": float(cons_20.iloc[-1]), "v2": float(cons_50.iloc[-1]), "v3": float(cons_200.iloc[-1]), "prev50": float(cons_50.iloc[-6])},
        ],
        "history": {
            "hsi_20":  hsi_20.iloc[-last_n:].tolist(),
            "hsi_50":  hsi_50.iloc[-last_n:].tolist(),
            "hsi_200": hsi_200.iloc[-last_n:].tolist(),
            "tech_50": tech_50.iloc[-last_n:].tolist(),
            "fin_50":  fin_50.iloc[-last_n:].tolist(),
            "cons_50": cons_50.iloc[-last_n:].tolist(),
        }
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"Updated data.json for {output['trade_date']}")

if __name__ == "__main__":
    main()
