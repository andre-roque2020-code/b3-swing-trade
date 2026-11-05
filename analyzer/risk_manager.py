import pandas as pd
import numpy as np
from typing import Dict, Any

def calculate_technical_risk(
    current_price: float,
    df_60m: pd.DataFrame,
    df_daily: pd.DataFrame,
    risk_reward_target1: float = 1.5,
    risk_reward_target2: float = 2.5
) -> Dict[str, Any]:
    """
    Calcula os níveis de Risco Técnico para operação de Swing Trade:
    - Preço de Entrada Recomendado
    - Stop Loss Técnico (baseado no suporte do fundo recente de 60m ou ATR)
    - Alvo 1 (Take Profit Parcial - R:R 1:1.5 ou 1:2)
    - Alvo 2 (Take Profit Final - R:R 1:2.5 ou 1:3)
    - Distâncias em R$ e percentuais (%)
    """
    if current_price <= 0 or df_60m.empty:
        return {}

    entry_price = current_price

    # 1. Busca fundo recente nos 60m (últimos 15 candles de 60m = ~2 a 3 pregões)
    recent_low_60 = df_60m["Low"].iloc[-15:].min()

    # 2. ATR nos 60m e diário
    last_atr_60 = df_60m["ATR_14"].iloc[-1] if "ATR_14" in df_60m and not pd.isna(df_60m["ATR_14"].iloc[-1]) else (entry_price * 0.02)
    last_atr_d = df_daily["ATR_14"].iloc[-1] if not df_daily.empty and "ATR_14" in df_daily and not pd.isna(df_daily["ATR_14"].iloc[-1]) else (entry_price * 0.03)

    # Stop pelo fundo com pequena margem (0.5% ou meio centavo)
    stop_by_swing = recent_low_60 * 0.995

    # Stop por ATR (1.5x ATR diário ou 2x ATR 60m)
    stop_by_atr = entry_price - (1.5 * last_atr_d)

    # Escolhe o stop técnico coerente: não muito colado (mínimo 1.5%) e não absurdamente distante (máximo 6%)
    raw_stop = max(stop_by_swing, stop_by_atr)
    
    # Validações de segurança do Swing Trade
    min_stop_distance = entry_price * 0.015  # mínimo 1.5% de margem
    max_stop_distance = entry_price * 0.070  # máximo 7% de margem para não ficar desproporcional
    
    risk_amount = entry_price - raw_stop
    if risk_amount < min_stop_distance:
        stop_loss = entry_price - min_stop_distance
    elif risk_amount > max_stop_distance:
        stop_loss = entry_price - max_stop_distance
    else:
        stop_loss = raw_stop

    risk_per_share = entry_price - stop_loss
    risk_pct = (risk_per_share / entry_price) * 100

    # Alvos baseados na relação Risco : Retorno
    target_1_price = entry_price + (risk_per_share * risk_reward_target1)
    target_1_gain = target_1_price - entry_price
    target_1_pct = (target_1_gain / entry_price) * 100

    target_2_price = entry_price + (risk_per_share * risk_reward_target2)
    target_2_gain = target_2_price - entry_price
    target_2_pct = (target_2_gain / entry_price) * 100

    return {
        "entry_price": float(round(entry_price, 2)),
        "stop_loss": float(round(stop_loss, 2)),
        "risk_per_share": float(round(risk_per_share, 2)),
        "risk_pct": float(round(risk_pct, 2)),
        "target_1": float(round(target_1_price, 2)),
        "target_1_gain_pct": float(round(target_1_pct, 2)),
        "target_1_ratio": f"1:{risk_reward_target1:.1f}",
        "target_2": float(round(target_2_price, 2)),
        "target_2_gain_pct": float(round(target_2_pct, 2)),
        "target_2_ratio": f"1:{risk_reward_target2:.1f}",
        "atr_daily": float(round(last_atr_d, 2)),
        "recent_swing_low": float(round(recent_low_60, 2))
    }

def simulate_trade_position(
    entry_price: float,
    stop_loss: float,
    target_1: float,
    target_2: float,
    capital_to_invest: float
) -> Dict[str, Any]:
    """
    Simula uma operação com base no capital pretendido pelo investidor.
    """
    if entry_price <= 0 or capital_to_invest <= 0:
        return {}

    # Quantidade de ações que o capital compra
    num_shares = int(capital_to_invest // entry_price)
    if num_shares == 0:
        return {"error": "Capital insuficiente para comprar ao menos 1 ação."}

    total_invested = num_shares * entry_price
    max_loss = num_shares * (entry_price - stop_loss)
    gain_target_1 = num_shares * (target_1 - entry_price)
    gain_target_2 = num_shares * (target_2 - entry_price)

    return {
        "num_shares": num_shares,
        "total_invested": round(total_invested, 2),
        "max_loss_brl": round(max_loss, 2),
        "max_loss_pct": round(((stop_loss - entry_price) / entry_price) * 100, 2),
        "gain_target_1_brl": round(gain_target_1, 2),
        "gain_target_1_pct": round(((target_1 - entry_price) / entry_price) * 100, 2),
        "gain_target_2_brl": round(gain_target_2, 2),
        "gain_target_2_pct": round(((target_2 - entry_price) / entry_price) * 100, 2),
    }
