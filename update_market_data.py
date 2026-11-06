import sys
import json
import os
import datetime

# Garante import do módulo local analyzer
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from analyzer.data_fetcher import fetch_hybrid_data, get_asset_info
from analyzer.indicators import add_all_indicators
from analyzer.scoring import calculate_multifactor_score
from analyzer.risk_manager import calculate_technical_risk

def update_all_market_data():
    tickers = ["ITUB4", "BBDC4", "BBAS3", "PETR4", "VALE3", "WEGE3"]
    now_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    output = {
        "updated_at": now_str,
        "source": "B3 Oficial via Yahoo Finance (yfinance)",
        "assets": {}
    }

    for ticker in tickers:
        print(f"Atualizando cotações e indicadores de {ticker}...")
        df_d, df_h, err = fetch_hybrid_data(ticker)
        if err or df_d is None or df_h is None:
            print(f"Erro ao obter dados de {ticker}: {err}")
            continue

        df_d = add_all_indicators(df_d, is_intraday=False)
        df_h = add_all_indicators(df_h, is_intraday=True)

        score_res = calculate_multifactor_score(df_d, df_h)
        curr_p = float(df_h["Close"].iloc[-1])
        risk_res = calculate_technical_risk(curr_p, df_h, df_d)
        info = get_asset_info(ticker)

        # Histórico recente para gráficos (últimos 30 pregões)
        hist = []
        for idx, row in df_d.tail(30).iterrows():
            hist.append({
                "date": idx.strftime("%d/%m"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]),
                "ema9": round(float(row["EMA_9"]), 2) if "EMA_9" in row and not row.isna()["EMA_9"] else round(float(row["Close"]), 2),
                "ema21": round(float(row["EMA_21"]), 2) if "EMA_21" in row and not row.isna()["EMA_21"] else round(float(row["Close"]), 2)
            })

        prev_close = float(df_d["Close"].iloc[-2]) if len(df_d) > 1 else curr_p
        change_pct = round(((curr_p - prev_close) / prev_close) * 100, 2)

        output["assets"][ticker] = {
            "symbol": ticker,
            "name": info.get("name", ticker),
            "current_price": round(curr_p, 2),
            "previous_close": round(prev_close, 2),
            "change_pct": change_pct,
            "high_day": round(float(df_d["High"].iloc[-1]), 2),
            "low_day": round(float(df_d["Low"].iloc[-1]), 2),
            "volume_day": int(df_d["Volume"].iloc[-1]),
            "signal": score_res["signal"],
            "score": score_res["score"],
            "summary": score_res["summary"],
            "factors": score_res["factors"],
            "risk": risk_res,
            "history": hist
        }

    output_path = os.path.join(current_dir, "market_data.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Dados atualizados com sucesso em: {output_path}")

if __name__ == "__main__":
    update_all_market_data()
