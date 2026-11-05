import yfinance as yf
import pandas as pd
import datetime
from typing import Tuple, Optional, Dict, Any

def format_ticker(ticker: str) -> str:
    """Garante que o ticker da B3 termine com .SA para o Yahoo Finance."""
    ticker = ticker.strip().upper()
    if not ticker.endswith(".SA") and not ticker.startswith("^"):
        return f"{ticker}.SA"
    return ticker

def get_asset_info(ticker: str) -> Dict[str, Any]:
    """Obtém informações cadastrais básicas do ativo."""
    formatted = format_ticker(ticker)
    try:
        t = yf.Ticker(formatted)
        info = t.info
        name = info.get("shortName") or info.get("longName") or formatted
        currency = info.get("currency", "BRL")
        current_price = info.get("currentPrice") or info.get("regularMarketPrice") or 0.0
        return {
            "symbol": formatted,
            "name": name,
            "currency": currency,
            "current_price": current_price,
            "sector": info.get("sector", "N/A"),
            "website": info.get("website", "")
        }
    except Exception as e:
        return {
            "symbol": formatted,
            "name": formatted,
            "currency": "BRL",
            "current_price": 0.0,
            "sector": "N/A",
            "website": ""
        }

def clean_yfinance_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Padroniza e limpa o DataFrame retornado pelo yfinance."""
    if df.empty:
        return df

    # Trata MultiIndex de colunas se existir
    if isinstance(df.columns, pd.MultiIndex):
        # Geralmente nível 0 é a métrica ('Close', 'Open', ...)
        df.columns = [col[0] for col in df.columns]

    # Garante colunas essenciais
    expected = ["Open", "High", "Low", "Close", "Volume"]
    for col in expected:
        if col not in df.columns:
            for c in df.columns:
                if c.lower() == col.lower():
                    df = df.rename(columns={c: col})
                    break

    # Converte tipos numéricos e remove NaNs
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["Close"])
    
    # Ordena pelo índice de data/hora
    df = df.sort_index()
    return df

def fetch_hybrid_data(ticker: str) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], str]:
    """
    Busca dados híbridos:
    - Diário (D1) para análise macro de tendência (último 1 ano)
    - 60 Minutos (1h) para timing refinado de entrada e saída (últimos 60 dias)
    
    Retorna: (df_daily, df_60m, error_message)
    """
    formatted = format_ticker(ticker)
    try:
        t = yf.Ticker(formatted)
        
        # 1. Dados Diários (1 ano de histórico para SMA 200)
        df_daily = t.history(period="1y", interval="1d", auto_adjust=True)
        df_daily = clean_yfinance_dataframe(df_daily)
        
        if df_daily.empty or len(df_daily) < 30:
            return None, None, f"Dados diários insuficientes para o ativo {formatted}."
            
        # 2. Dados de 60 Minutos (60 dias de histórico)
        df_60m = t.history(period="60d", interval="60m", auto_adjust=True)
        df_60m = clean_yfinance_dataframe(df_60m)
        
        if df_60m.empty or len(df_60m) < 20:
            # Fallback para tentar período menor caso haja restrição
            df_60m = t.history(period="30d", interval="60m", auto_adjust=True)
            df_60m = clean_yfinance_dataframe(df_60m)
            
        if df_60m.empty:
            return None, None, f"Não foi possível obter dados de 60 minutos para {formatted}."
            
        return df_daily, df_60m, ""
        
    except Exception as e:
        return None, None, f"Erro ao consultar {formatted}: {str(e)}"
