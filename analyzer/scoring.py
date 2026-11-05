import pandas as pd
import numpy as np
from typing import Dict, Any, List

def calculate_multifactor_score(df_daily: pd.DataFrame, df_60m: pd.DataFrame) -> Dict[str, Any]:
    """
    Executa o Sistema Multifatorial Ponderado integrando:
    1. Macro Tendência (Gráfico Diário - D1)
    2. Gatilho e Momento (Gráfico de 60 Minutos)
    3. Volume Institucional e Confirmação
    4. Volatilidade e Suportes/Resistências
    
    Retorna:
    - score: Pontuação total normalizada (-100 a +100)
    - signal: 'COMPRA FORTE', 'COMPRA', 'NEUTRO', 'VENDA / REALIZAR', 'VENDA FORTE'
    - factors: Lista de dicionários com cada critério, peso, pontos e explicação
    - summary: Resumo textual executivo
    """
    if df_daily.empty or df_60m.empty:
        return {
            "score": 0,
            "signal": "DADOS INSUFICIENTES",
            "confidence": 0,
            "factors": [],
            "summary": "Não há dados suficientes para realizar a análise."
        }

    last_d = df_daily.iloc[-1]
    prev_d = df_daily.iloc[-2] if len(df_daily) > 1 else last_d
    prev3_d = df_daily.iloc[-4] if len(df_daily) > 4 else prev_d

    last_60 = df_60m.iloc[-1]
    prev_60 = df_60m.iloc[-2] if len(df_60m) > 1 else last_60
    prev3_60 = df_60m.iloc[-4] if len(df_60m) > 4 else prev_60

    factors: List[Dict[str, Any]] = []
    total_score = 0

    # -------------------------------------------------------------
    # 1. MACRO TENDÊNCIA (DIÁRIO - D1) - PESO MÁXIMO ~35 pts
    # -------------------------------------------------------------
    # Critério 1.1: Preço vs SMA 200 (Tendência Primária de Longo Prazo)
    if "SMA_200" in last_d and not pd.isna(last_d["SMA_200"]):
        if last_d["Close"] > last_d["SMA_200"]:
            pts = 12
            desc = f"Preço (R$ {last_d['Close']:.2f}) acima da SMA 200 (R$ {last_d['SMA_200']:.2f}) - Viés de Alta no Diário"
            status = "Positivo"
        else:
            pts = -12
            desc = f"Preço (R$ {last_d['Close']:.2f}) abaixo da SMA 200 (R$ {last_d['SMA_200']:.2f}) - Abaixo da média de 200 dias"
            status = "Negativo"
        factors.append({"category": "Macro (D1)", "factor": "SMA 200 Diária", "status": status, "points": pts, "desc": desc})
        total_score += pts

    # Critério 1.2: Preço vs EMA 21 (Tendência de Médio Prazo do Swing Trade)
    if "EMA_21" in last_d and not pd.isna(last_d["EMA_21"]):
        ema_slope_up = last_d["EMA_21"] > prev3_d.get("EMA_21", last_d["EMA_21"])
        if last_d["Close"] > last_d["EMA_21"]:
            pts = 12 if ema_slope_up else 6
            desc = f"Preço acima da EMA 21 Diária ({'EMA 21 ascendente' if ema_slope_up else 'EMA 21 sem inclinação forte'})"
            status = "Positivo"
        else:
            pts = -12 if not ema_slope_up else -6
            desc = f"Preço abaixo da EMA 21 Diária (pressão vendedora no swing trade)"
            status = "Negativo"
        factors.append({"category": "Macro (D1)", "factor": "EMA 21 Diária", "status": status, "points": pts, "desc": desc})
        total_score += pts

    # Critério 1.3: MACD Diário
    if "MACD_Hist" in last_d and not pd.isna(last_d["MACD_Hist"]):
        if last_d["MACD_Hist"] > 0:
            pts = 8
            desc = "Histograma MACD diário positivo (compradores no controle macro)"
            status = "Positivo"
        else:
            pts = -8
            desc = "Histograma MACD diário negativo (momentum macro desfavorável)"
            status = "Negativo"
        factors.append({"category": "Macro (D1)", "factor": "MACD Diário", "status": status, "points": pts, "desc": desc})
        total_score += pts

    # -------------------------------------------------------------
    # 2. GATILHO & TIMING (60 MINUTOS) - PESO MÁXIMO ~35 pts
    # -------------------------------------------------------------
    # Critério 2.1: Alinhamento de Médias Rápidas no 60m (EMA 9 vs EMA 21)
    if "EMA_9" in last_60 and "EMA_21" in last_60:
        if last_60["EMA_9"] > last_60["EMA_21"]:
            pts = 14
            desc = f"EMA 9 (R$ {last_60['EMA_9']:.2f}) acima da EMA 21 (R$ {last_60['EMA_21']:.2f}) no 60m - Alinhamento altista"
            status = "Positivo"
        else:
            pts = -14
            desc = f"EMA 9 abaixo da EMA 21 no 60m - Alinhamento baixista no timing de entrada"
            status = "Negativo"
        factors.append({"category": "Timing (60m)", "factor": "Cruzamento EMA 9/21", "status": status, "points": pts, "desc": desc})
        total_score += pts

    # Critério 2.2: IFR / RSI (14) nos 60 Minutos
    rsi_60 = last_60.get("RSI_14", 50)
    if rsi_60 < 30:
        pts = 12
        desc = f"IFR 60m em {rsi_60:.1f} (Sobrevenda extrema - alta probabilidade de repique técnico)"
        status = "Positivo"
    elif 30 <= rsi_60 <= 45 and rsi_60 > prev_60.get("RSI_14", rsi_60):
        pts = 12
        desc = f"IFR 60m em {rsi_60:.1f} saindo de sobrevenda com inclinação altista (gatilho favorável)"
        status = "Positivo"
    elif 45 < rsi_60 <= 65:
        pts = 8
        desc = f"IFR 60m em {rsi_60:.1f} em zona saudável de tendência compradora, com espaço para alta"
        status = "Positivo"
    elif rsi_60 > 72:
        pts = -12
        desc = f"IFR 60m em {rsi_60:.1f} (Sobrecomprado - risco elevado para novas compras no topo)"
        status = "Negativo"
    else:
        pts = 0
        desc = f"IFR 60m em {rsi_60:.1f} em zona neutra"
        status = "Neutro"
    factors.append({"category": "Timing (60m)", "factor": "IFR 14 (60m)", "status": status, "points": pts, "desc": desc})
    total_score += pts

    # Critério 2.3: MACD no 60m (Aceleração do gatilho)
    macd_hist_60 = last_60.get("MACD_Hist", 0)
    prev_macd_hist_60 = prev_60.get("MACD_Hist", 0)
    if macd_hist_60 > 0 and macd_hist_60 > prev_macd_hist_60:
        pts = 9
        desc = "MACD 60m com histograma positivo e expandindo (força compradora acelerando)"
        status = "Positivo"
    elif macd_hist_60 < 0 and macd_hist_60 < prev_macd_hist_60:
        pts = -9
        desc = "MACD 60m com histograma negativo e acelerando para baixo"
        status = "Negativo"
    else:
        pts = 0
        desc = "MACD 60m sem aceleração definida no momento"
        status = "Neutro"
    factors.append({"category": "Timing (60m)", "factor": "MACD Histograma 60m", "status": status, "points": pts, "desc": desc})
    total_score += pts

    # -------------------------------------------------------------
    # 3. VOLUME & FLUXO INSTITUCIONAL - PESO MÁXIMO ~18 pts
    # -------------------------------------------------------------
    vol_ratio_60 = last_60.get("Vol_Ratio", 1.0)
    is_green_candle = last_60["Close"] >= last_60["Open"]

    if vol_ratio_60 >= 1.25:
        if is_green_candle:
            pts = 10
            desc = f"Volume no 60m {vol_ratio_60:.2f}x acima da média de 20 períodos em candle de alta (Fluxo comprador forte)"
            status = "Positivo"
        else:
            pts = -10
            desc = f"Volume no 60m {vol_ratio_60:.2f}x acima da média em candle de baixa (Pressão vendedora forte)"
            status = "Negativo"
    else:
        pts = 2 if is_green_candle else -2
        desc = f"Volume no 60m ({vol_ratio_60:.2f}x da média) dentro da normalidade"
        status = "Neutro"
    factors.append({"category": "Volume", "factor": "Volume 60m vs Média 20", "status": status, "points": pts, "desc": desc})
    total_score += pts

    # OBV Diário
    if "OBV" in last_d and len(df_daily) > 5:
        obv_up = last_d["OBV"] > df_daily["OBV"].iloc[-5]
        if obv_up:
            pts = 6
            desc = "OBV no Diário em tendência ascendente nos últimos dias (Acumulação)"
            status = "Positivo"
        else:
            pts = -6
            desc = "OBV no Diário em tendência descendente nos últimos dias (Distribuição)"
            status = "Negativo"
        factors.append({"category": "Volume", "factor": "OBV Diário (Acumulação)", "status": status, "points": pts, "desc": desc})
        total_score += pts

    # -------------------------------------------------------------
    # 4. VOLATILIDADE & BANDAS DE BOLLINGER - PESO MÁXIMO ~12 pts
    # -------------------------------------------------------------
    close_60 = last_60["Close"]
    bb_upper = last_60.get("BB_Upper", close_60)
    bb_lower = last_60.get("BB_Lower", close_60)
    bb_mid = last_60.get("BB_Middle", close_60)

    if close_60 > bb_upper:
        pts = -6
        desc = "Preço esticado acima da Banda de Bollinger Superior (risco de retorno à média)"
        status = "Negativo"
    elif close_60 < bb_lower:
        pts = 6
        desc = "Preço abaixo da Banda Inferior de Bollinger (região extrema de suporte/repique)"
        status = "Positivo"
    elif close_60 > bb_mid:
        pts = 5
        desc = "Preço acima da média central de Bollinger no 60m (região compradora)"
        status = "Positivo"
    else:
        pts = -5
        desc = "Preço abaixo da média central de Bollinger no 60m"
        status = "Negativo"
    factors.append({"category": "Volatilidade", "factor": "Bandas de Bollinger (60m)", "status": status, "points": pts, "desc": desc})
    total_score += pts

    # Normalização final (-100 a +100)
    normalized_score = max(-100, min(100, total_score))

    # Classificação do Sinal
    if normalized_score >= 55:
        signal = "COMPRA FORTE"
        confidence_desc = "Alta convicção: Alinhamento macro diário com confirmação de gatilho de entrada nos 60 minutos."
    elif 25 <= normalized_score < 55:
        signal = "COMPRA"
        confidence_desc = "Oportunidade compradora identificada: Indicadores predominantemente favoráveis para swing trade."
    elif -24 <= normalized_score < 25:
        signal = "NEUTRO"
        confidence_desc = "Mercado sem tendência clara ou sinais divergentes. Recomendável aguardar definição."
    elif -55 < normalized_score <= -25:
        signal = "VENDA / REALIZAR"
        confidence_desc = "Sinal de fraqueza técnica: Momento propício para realizar lucros ou apertar stops protetivos."
    else:
        signal = "VENDA FORTE"
        confidence_desc = "Tendência de baixa confirmada em ambos os prazos: Evitar compras e proteger capital."

    return {
        "score": normalized_score,
        "signal": signal,
        "confidence": abs(normalized_score),
        "factors": factors,
        "summary": confidence_desc
    }
