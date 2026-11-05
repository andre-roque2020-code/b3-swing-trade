import pandas as pd
import numpy as np

def calculate_sma(series: pd.Series, window: int) -> pd.Series:
    """Calcula a Média Móvel Simples (SMA)."""
    return series.rolling(window=window).mean()

def calculate_ema(series: pd.Series, span: int) -> pd.Series:
    """Calcula a Média Móvel Exponencial (EMA)."""
    return series.ewm(span=span, adjust=False).mean()

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Calcula o IFR (Índice de Força Relativa / RSI) com suavização clássica de Wilder.
    """
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Primeira média aritmética simples
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    # Wilder's smoothing
    for i in range(period, len(series)):
        avg_gain.iloc[i] = (avg_gain.iloc[i - 1] * (period - 1) + gain.iloc[i]) / period
        avg_loss.iloc[i] = (avg_loss.iloc[i - 1] * (period - 1) + loss.iloc[i]) / period

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)

def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """Calcula a Linha MACD, Linha de Sinal e Histograma."""
    ema_fast = calculate_ema(series, span=fast)
    ema_slow = calculate_ema(series, span=slow)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, span=signal)
    hist = macd_line - signal_line

    return pd.DataFrame({
        "MACD": macd_line,
        "MACD_Signal": signal_line,
        "MACD_Hist": hist
    }, index=series.index)

def calculate_bollinger_bands(series: pd.Series, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    """Calcula Bandas de Bollinger (Média, Superior, Inferior e Largura)."""
    middle = calculate_sma(series, window)
    std = series.rolling(window=window).std()
    upper = middle + (std * num_std)
    lower = middle - (std * num_std)
    width = (upper - lower) / middle.replace(0, np.nan)

    return pd.DataFrame({
        "BB_Upper": upper,
        "BB_Middle": middle,
        "BB_Lower": lower,
        "BB_Width": width
    }, index=series.index)

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calcula o Average True Range (ATR) para medição da volatilidade."""
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    prev_close = close.shift(1)

    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(span=period, adjust=False).mean()
    return atr

def calculate_obv(df: pd.DataFrame) -> pd.Series:
    """Calcula o On-Balance Volume (OBV)."""
    close = df["Close"]
    volume = df["Volume"].fillna(0)
    change = close.diff()

    direction = np.where(change > 0, 1, np.where(change < 0, -1, 0))
    obv = (direction * volume).cumsum()
    return pd.Series(obv, index=df.index, name="OBV")

def add_all_indicators(df: pd.DataFrame, is_intraday: bool = False) -> pd.DataFrame:
    """
    Enriquece o DataFrame com todos os indicadores técnicos necessários para o Swing Trade.
    """
    if df.empty:
        return df

    res = df.copy()

    # Médias Móveis
    res["EMA_9"] = calculate_ema(res["Close"], span=9)
    res["EMA_21"] = calculate_ema(res["Close"], span=21)
    res["SMA_50"] = calculate_sma(res["Close"], window=50)
    
    if not is_intraday:
        # No gráfico diário, SMA 200 é fundamental para o viés de longo prazo
        res["SMA_200"] = calculate_sma(res["Close"], window=200)

    # IFR (RSI 14)
    res["RSI_14"] = calculate_rsi(res["Close"], period=14)

    # MACD
    macd_df = calculate_macd(res["Close"])
    res["MACD"] = macd_df["MACD"]
    res["MACD_Signal"] = macd_df["MACD_Signal"]
    res["MACD_Hist"] = macd_df["MACD_Hist"]

    # Bandas de Bollinger
    bb_df = calculate_bollinger_bands(res["Close"])
    res["BB_Upper"] = bb_df["BB_Upper"]
    res["BB_Middle"] = bb_df["BB_Middle"]
    res["BB_Lower"] = bb_df["BB_Lower"]
    res["BB_Width"] = bb_df["BB_Width"]

    # ATR (Volatilidade para stops)
    res["ATR_14"] = calculate_atr(res, period=14)

    # Volume
    res["Vol_SMA20"] = calculate_sma(res["Volume"], window=20)
    res["Vol_Ratio"] = res["Volume"] / res["Vol_SMA20"].replace(0, np.nan)
    res["OBV"] = calculate_obv(res)

    return res
