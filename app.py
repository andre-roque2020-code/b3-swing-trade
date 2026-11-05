import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

from analyzer.data_fetcher import fetch_hybrid_data, get_asset_info, format_ticker
from analyzer.indicators import add_all_indicators
from analyzer.scoring import calculate_multifactor_score
from analyzer.risk_manager import calculate_technical_risk, simulate_trade_position

# -----------------------------------------------------------------------------
# Configuração da Página
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="B3 Swing Trade Pro | Sinais & Gestão de Risco",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização customizada em CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #1a1e24;
        border: 1px solid #2e3440;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .signal-badge-buy-strong {
        background-color: #0d5f3a;
        color: #e6fffa;
        padding: 8px 16px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 1.3rem;
        display: inline-block;
        border: 1px solid #10b981;
    }
    .signal-badge-buy {
        background-color: #064e3b;
        color: #a7f3d0;
        padding: 8px 16px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 1.3rem;
        display: inline-block;
        border: 1px solid #34d399;
    }
    .signal-badge-neutral {
        background-color: #374151;
        color: #f3f4f6;
        padding: 8px 16px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 1.3rem;
        display: inline-block;
        border: 1px solid #9ca3af;
    }
    .signal-badge-sell {
        background-color: #78350f;
        color: #fef3c7;
        padding: 8px 16px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 1.3rem;
        display: inline-block;
        border: 1px solid #f59e0b;
    }
    .signal-badge-sell-strong {
        background-color: #7f1d1d;
        color: #fee2e2;
        padding: 8px 16px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 1.3rem;
        display: inline-block;
        border: 1px solid #ef4444;
    }
    .tax-alert {
        background-color: #1e293b;
        border-left: 5px solid #38bdf8;
        padding: 12px 18px;
        border-radius: 6px;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Barra Lateral (Sidebar)
# -----------------------------------------------------------------------------
st.sidebar.title("📈 B3 Swing Trade Pro")
st.sidebar.markdown("Sinais técnicos automatizados para ações da B3 com foco em Swing Trade e isenção de IR.")

# Seleção de Ativos
default_assets = ["ITUB4", "BBDC4", "BBAS3", "PETR4", "VALE3", "WEGE3"]
selected_ticker = st.sidebar.selectbox(
    "Selecione o Ativo Principal:",
    options=default_assets,
    index=0
)

custom_ticker = st.sidebar.text_input("Ou digite outro ticker da B3 (ex: RENT3):", value="").strip().upper()
if custom_ticker:
    active_ticker = custom_ticker
else:
    active_ticker = selected_ticker

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Parâmetros de Risco Técnico")
rr_target1 = st.sidebar.slider("Relação Alvo 1 (R:R)", min_value=1.0, max_value=2.5, value=1.5, step=0.1)
rr_target2 = st.sidebar.slider("Relação Alvo 2 (R:R)", min_value=2.0, max_value=4.0, value=2.5, step=0.1)

if st.sidebar.button("🔄 Atualizar Análise Agora", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div class="tax-alert">
    <strong>🛡️ Regra de Ouro do IR:</strong><br>
    No Swing Trade em ações na B3, vendas totais de até <strong>R$ 20.000,00 por mês</strong> são 100% <strong>isentas de Imposto de Renda</strong> sobre o ganho de capital.
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Carregamento e Processamento dos Dados
# -----------------------------------------------------------------------------
@st.cache_data(ttl=300)
def load_and_process_ticker(ticker: str):
    df_daily, df_60m, err = fetch_hybrid_data(ticker)
    if err or df_daily is None or df_60m is None:
        return None, None, None, None, err

    df_d = add_all_indicators(df_daily, is_intraday=False)
    df_h = add_all_indicators(df_60m, is_intraday=True)

    score_result = calculate_multifactor_score(df_d, df_h)
    current_p = float(df_h["Close"].iloc[-1])
    risk_result = calculate_technical_risk(current_p, df_h, df_d, rr_target1, rr_target2)

    return df_d, df_h, score_result, risk_result, ""

with st.spinner(f"Coletando cotações e calculando indicadores de {active_ticker}..."):
    df_daily, df_60m, score_res, risk_res, error_msg = load_and_process_ticker(active_ticker)

if error_msg or df_daily is None or df_60m is None:
    st.error(f"Não foi possível processar o ativo {active_ticker}. Detalhe: {error_msg}")
    st.stop()

# Informações cadastrais
info = get_asset_info(active_ticker)
current_price = float(df_60m["Close"].iloc[-1])
prev_price = float(df_60m["Close"].iloc[-2]) if len(df_60m) > 1 else current_price
price_change = current_price - prev_price
price_change_pct = (price_change / prev_price) * 100 if prev_price > 0 else 0.0

# -----------------------------------------------------------------------------
# Cabeçalho Principal
# -----------------------------------------------------------------------------
col_header_1, col_header_2 = st.columns([3, 1])

with col_header_1:
    st.title(f"Análise Técnica: {active_ticker} - {info.get('name', '')}")
    st.caption("Estratégia Híbrida: Tendência Macro no Diário (D1) + Gatilho e Timing nos 60 Minutos (1h)")

with col_header_2:
    st.metric(
        label=f"Preço Atual ({active_ticker})",
        value=f"R$ {current_price:.2f}",
        delta=f"{price_change:+.2f} ({price_change_pct:+.2f}%) no 60m"
    )

# -----------------------------------------------------------------------------
# Painel do Sinal Principal (Hero Card)
# -----------------------------------------------------------------------------
signal = score_res["signal"]
score = score_res["score"]

badge_class = "signal-badge-neutral"
if signal == "COMPRA FORTE":
    badge_class = "signal-badge-buy-strong"
elif signal == "COMPRA":
    badge_class = "signal-badge-buy"
elif signal == "VENDA / REALIZAR":
    badge_class = "signal-badge-sell"
elif signal == "VENDA FORTE":
    badge_class = "signal-badge-sell-strong"

st.markdown(f"""
<div style="background-color: #111827; border: 1px solid #374151; border-radius: 12px; padding: 20px; margin-bottom: 25px;">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
        <div>
            <div style="font-size: 0.95rem; color: #9ca3af; text-transform: uppercase; letter-spacing: 1px;">Sinal Multifatorial Emitido</div>
            <div class="{badge_class}" style="margin-top: 6px;">{signal}</div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 0.95rem; color: #9ca3af;">Score Ponderado de Convicção</div>
            <div style="font-size: 2rem; font-weight: 800; color: {'#10b981' if score > 25 else ('#ef4444' if score < -25 else '#9ca3af')};">{score:+} / 100</div>
        </div>
    </div>
    <div style="margin-top: 14px; font-size: 1.05rem; color: #e5e7eb; border-top: 1px solid #1f2937; padding-top: 10px;">
        💡 <strong>Diagnóstico:</strong> {score_res['summary']}
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Métricas Técnicas de Execução (Risco / Retorno)
# -----------------------------------------------------------------------------
m1, m2, m3, m4, m5 = st.columns(5)

with m1:
    st.metric(
        label="🎯 Entrada Recomendada",
        value=f"R$ {risk_res['entry_price']:.2f}",
        help="Preço atual de referência para montagem da posição de Swing Trade."
    )

with m2:
    st.metric(
        label="🛑 Stop Loss Técnico",
        value=f"R$ {risk_res['stop_loss']:.2f}",
        delta=f"-{risk_res['risk_pct']:.2f}% (R$ -{risk_res['risk_per_share']:.2f})",
        delta_color="inverse",
        help="Nível de saída para proteção máxima de capital (baseado no suporte do fundo recente de 60m e volatilidade ATR)."
    )

with m3:
    st.metric(
        label=f"🥇 Alvo 1 ({risk_res['target_1_ratio']})",
        value=f"R$ {risk_res['target_1']:.2f}",
        delta=f"+{risk_res['target_1_gain_pct']:.2f}%",
        help="Primeiro objetivo de lucro: recomendado realizar parte da posição e mover o Stop Loss para o preço de entrada (Breakeven)."
    )

with m4:
    st.metric(
        label=f"🏆 Alvo 2 ({risk_res['target_2_ratio']})",
        value=f"R$ {risk_res['target_2']:.2f}",
        delta=f"+{risk_res['target_2_gain_pct']:.2f}%",
        help="Objetivo final da operação de Swing Trade."
    )

with m5:
    st.metric(
        label="📊 Volatilidade ATR (Diário)",
        value=f"R$ {risk_res['atr_daily']:.2f}",
        help="Oscilação média diária em reais nos últimos 14 pregões."
    )

st.markdown("---")

# -----------------------------------------------------------------------------
# Abas de Conteúdo
# -----------------------------------------------------------------------------
tab_charts, tab_scorecard, tab_simulator, tab_compare, tab_guide = st.tabs([
    "📊 Gráficos Interativos (60m & D1)",
    "📑 Detalhamento do Scorecard",
    "🎯 Simulador de Capital & Risco",
    "⚖️ Comparador ITUB4 vs BBDC4",
    "📘 Guia Operacional & Isenção IR"
])

# =============================================================================
# ABA 1: GRÁFICOS INTERATIVOS
# =============================================================================
with tab_charts:
    chart_view = st.radio("Selecione o Tempo Gráfico para Visualização:", ["60 Minutos (Gatilho Fino de Entrada/Saída)", "Diário (Macro Tendência)"], horizontal=True)

    if chart_view.startswith("60 Minutos"):
        st.subheader(f"Gráfico de 60 Minutos: {active_ticker} (Timing de Entrada e Stop Técnico)")
        
        # Cria figura com 3 linhas: Preço, Volume, IFR
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.04,
            row_heights=[0.60, 0.20, 0.20],
            subplot_titles=("Preço, Médias Móveis (EMA 9 e 21) & Bandas de Bollinger", "Volume Financeiro & Média 20", "IFR / RSI (14)")
        )

        # Candlestick
        fig.add_trace(go.Candlestick(
            x=df_60m.index,
            open=df_60m["Open"],
            high=df_60m["High"],
            low=df_60m["Low"],
            close=df_60m["Close"],
            name="Candles 60m"
        ), row=1, col=1)

        # Médias 9 e 21
        fig.add_trace(go.Scatter(x=df_60m.index, y=df_60m["EMA_9"], line=dict(color="#38bdf8", width=1.5), name="EMA 9 (Rápida)"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_60m.index, y=df_60m["EMA_21"], line=dict(color="#f97316", width=1.8), name="EMA 21 (Tendência 60m)"), row=1, col=1)

        # Bandas de Bollinger
        fig.add_trace(go.Scatter(x=df_60m.index, y=df_60m["BB_Upper"], line=dict(color="rgba(156, 163, 175, 0.4)", dash="dot"), name="Banda Superior"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_60m.index, y=df_60m["BB_Lower"], line=dict(color="rgba(156, 163, 175, 0.4)", dash="dot"), name="Banda Inferior"), row=1, col=1)

        # Níveis de Entrada, Stop e Alvos como linhas horizontais
        fig.add_hline(y=risk_res["entry_price"], line=dict(color="#06b6d4", dash="dash", width=1.2), annotation_text=f"Entrada R$ {risk_res['entry_price']:.2f}", row=1, col=1)
        fig.add_hline(y=risk_res["stop_loss"], line=dict(color="#ef4444", width=2), annotation_text=f"STOP LOSS R$ {risk_res['stop_loss']:.2f}", row=1, col=1)
        fig.add_hline(y=risk_res["target_1"], line=dict(color="#10b981", dash="dash", width=1.5), annotation_text=f"ALVO 1 R$ {risk_res['target_1']:.2f}", row=1, col=1)
        fig.add_hline(y=risk_res["target_2"], line=dict(color="#059669", width=2), annotation_text=f"ALVO 2 R$ {risk_res['target_2']:.2f}", row=1, col=1)

        # Volume
        vol_colors = ["#10b981" if c >= o else "#ef4444" for c, o in zip(df_60m["Close"], df_60m["Open"])]
        fig.add_trace(go.Bar(x=df_60m.index, y=df_60m["Volume"], marker_color=vol_colors, name="Volume 60m"), row=2, col=1)
        fig.add_trace(go.Scatter(x=df_60m.index, y=df_60m["Vol_SMA20"], line=dict(color="#eab308", width=1.5), name="Média Volume 20"), row=2, col=1)

        # IFR
        fig.add_trace(go.Scatter(x=df_60m.index, y=df_60m["RSI_14"], line=dict(color="#a855f7", width=1.5), name="IFR (14)"), row=3, col=1)
        fig.add_hline(y=70, line=dict(color="#ef4444", dash="dot"), row=3, col=1)
        fig.add_hline(y=30, line=dict(color="#10b981", dash="dot"), row=3, col=1)
        fig.add_hline(y=50, line=dict(color="rgba(156, 163, 175, 0.4)", dash="dash"), row=3, col=1)

        fig.update_layout(
            template="plotly_dark",
            height=800,
            xaxis_rangeslider_visible=False,
            margin=dict(l=40, r=40, t=40, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.subheader(f"Gráfico Diário (D1): {active_ticker} (Tendência Macro e Estrutura Ibovespa)")
        
        fig_d = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.04,
            row_heights=[0.60, 0.20, 0.20],
            subplot_titles=("Preço Diário, SMA 200 & EMA 21", "MACD (12, 26, 9)", "On-Balance Volume (OBV)")
        )

        # Candlestick Diário
        fig_d.add_trace(go.Candlestick(
            x=df_daily.index,
            open=df_daily["Open"],
            high=df_daily["High"],
            low=df_daily["Low"],
            close=df_daily["Close"],
            name="Candles D1"
        ), row=1, col=1)

        # SMA 200 e EMA 21
        if "SMA_200" in df_daily:
            fig_d.add_trace(go.Scatter(x=df_daily.index, y=df_daily["SMA_200"], line=dict(color="#ec4899", width=2), name="SMA 200 (Tendência Primária)"), row=1, col=1)
        fig_d.add_trace(go.Scatter(x=df_daily.index, y=df_daily["EMA_21"], line=dict(color="#f97316", width=1.8), name="EMA 21 Diária"), row=1, col=1)

        # MACD
        hist_colors = ["#10b981" if h >= 0 else "#ef4444" for h in df_daily["MACD_Hist"]]
        fig_d.add_trace(go.Bar(x=df_daily.index, y=df_daily["MACD_Hist"], marker_color=hist_colors, name="MACD Histograma"), row=2, col=1)
        fig_d.add_trace(go.Scatter(x=df_daily.index, y=df_daily["MACD"], line=dict(color="#38bdf8", width=1.5), name="MACD Linha"), row=2, col=1)
        fig_d.add_trace(go.Scatter(x=df_daily.index, y=df_daily["MACD_Signal"], line=dict(color="#eab308", width=1.5), name="Sinal MACD"), row=2, col=1)

        # OBV
        fig_d.add_trace(go.Scatter(x=df_daily.index, y=df_daily["OBV"], line=dict(color="#10b981", width=1.8), name="OBV"), row=3, col=1)

        fig_d.update_layout(
            template="plotly_dark",
            height=800,
            xaxis_rangeslider_visible=False,
            margin=dict(l=40, r=40, t=40, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_d, use_container_width=True)

# =============================================================================
# ABA 2: DETALHAMENTO DO SCORECARD
# =============================================================================
with tab_scorecard:
    st.subheader("📑 Decomposição do Sistema Multifatorial")
    st.markdown("Veja com transparência absoluta o peso e o status de cada critério técnico analisado:")

    factors_df = pd.DataFrame(score_res["factors"])
    
    # Formatação com emojis
    def format_status(st_val):
        if st_val == "Positivo":
            return "🟢 Positivo"
        elif st_val == "Negativo":
            return "🔴 Negativo"
        return "⚪ Neutro"

    factors_df["Status Visual"] = factors_df["status"].apply(format_status)
    factors_df["Pontos"] = factors_df["points"].apply(lambda p: f"{p:+d} pts")
    
    display_df = factors_df[["category", "factor", "Status Visual", "Pontos", "desc"]].rename(columns={
        "category": "Dimensão",
        "factor": "Indicador / Setup",
        "desc": "Leitura Técnica e Contexto"
    })

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown("""
    #### 📐 Metodologia de Ponderação:
    - **Macro Tendência Diária (D1) (~35%)**: Preço acima/abaixo da Média Móvel de 200 períodos e da Média Exponencial de 21 dias. Garante que nunca operamos contra a tendência do mercado institucional.
    - **Gatilho de Entrada nos 60 Minutos (~35%)**: Cruzamento EMA 9 sobre EMA 21, IFR com espaço para expansão e MACD acelerando. Define o momento exato da ordem para não entrar atrasado.
    - **Volume & Fluxo Institucional (~18%)**: Volume financeiro do candle atual superior a 1.25x da média dos últimos 20 períodos e OBV acumulando.
    - **Volatilidade & Bandas de Bollinger (~12%)**: Posição do preço em relação às bandas para evitar compras em topos esticados.
    """)

# =============================================================================
# ABA 3: SIMULADOR DE CAPITAL & RISCO
# =============================================================================
with tab_simulator:
    st.subheader("🎯 Dimensionamento de Posição & Simulador de Risco")
    st.markdown("Calcule exatamente quantas ações comprar, sua exposição máxima em reais e a distância do teto de isenção de IR.")

    sim_col1, sim_col2 = st.columns([1, 1])

    with sim_col1:
        capital = st.number_input(
            "Quanto capital você pretende alocar nesta operação? (R$)",
            min_value=500.0,
            max_value=100000.0,
            value=6000.0,
            step=500.0
        )

        sim = simulate_trade_position(
            current_price,
            risk_res["stop_loss"],
            risk_res["target_1"],
            risk_res["target_2"],
            capital
        )

        if "error" in sim:
            st.warning(sim["error"])
        else:
            st.markdown(f"""
            <div class="metric-card">
                <h4>📦 Quantidade Calculada</h4>
                <div style="font-size: 2rem; font-weight: 700; color: #38bdf8;">{sim['num_shares']} ações</div>
                <div style="color: #9ca3af;">Capital total investido: <strong>R$ {sim['total_invested']:,.2f}</strong></div>
            </div>
            """, unsafe_allow_html=True)

    with sim_col2:
        if "error" not in sim:
            st.markdown(f"""
            <div class="metric-card">
                <h4>⚖️ Balanço Financeiro da Operação</h4>
                <table style="width: 100%; border-collapse: collapse; font-size: 1.05rem;">
                    <tr style="border-bottom: 1px solid #374151; height: 38px;">
                        <td style="color: #ef4444;">🛑 <strong>Perda Máxima (Stop Loss):</strong></td>
                        <td style="text-align: right; color: #ef4444; font-weight: 700;">- R$ {sim['max_loss_brl']:,.2f} ({sim['max_loss_pct']:.2f}%)</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #374151; height: 38px;">
                        <td style="color: #34d399;">🥇 <strong>Lucro no Alvo 1:</strong></td>
                        <td style="text-align: right; color: #34d399; font-weight: 700;">+ R$ {sim['gain_target_1_brl']:,.2f} (+{sim['gain_target_1_pct']:.2f}%)</td>
                    </tr>
                    <tr style="height: 38px;">
                        <td style="color: #10b981;">🏆 <strong>Lucro no Alvo 2 (Final):</strong></td>
                        <td style="text-align: right; color: #10b981; font-weight: 700;">+ R$ {sim['gain_target_2_brl']:,.2f} (+{sim['gain_target_2_pct']:.2f}%)</td>
                    </tr>
                </table>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("🛡️ Termômetro de Isenção de IR (Limite de R$ 20.000,00 no Mês)")
    
    total_sale_sim = sim.get("num_shares", 0) * risk_res["target_2"]
    pct_of_limit = (total_sale_sim / 20000.0) * 100

    st.write(f"Valor bruto estimado da venda no Alvo 2: **R$ {total_sale_sim:,.2f}** ({pct_of_limit:.1f}% do teto mensal de R$ 20.000)")
    st.progress(min(1.0, total_sale_sim / 20000.0))

    if total_sale_sim < 20000.0:
        st.success(f"✅ Operação dentro do teto de isenção! Se você realizar essa venda e não ultrapassar R$ 20.000 em vendas de ações no mês, **o imposto sobre ganho de capital é R$ 0,00 (ZERO)**.")
    else:
        st.warning(f"⚠️ Atenção: A venda total desta operação atinge ou supera R$ 20.000,00. Caso encerre a operação no mesmo mês civil acima de R$ 20k, haverá incidência de 15% de IR sobre o lucro líquido via DARF.")

# =============================================================================
# ABA 4: COMPARADOR ITUB4 vs BBDC4
# =============================================================================
with tab_compare:
    st.subheader("⚖️ Batalha dos Bancões: ITUB4 vs BBDC4")
    st.markdown("Compare em tempo real qual dos dois ativos apresenta o setup técnico mais atrativo neste instante:")

    with st.spinner("Comparando métricas de ITUB4 e BBDC4..."):
        d_itub, h_itub, score_itub, risk_itub, err_itub = load_and_process_ticker("ITUB4")
        d_bbdc, h_bbdc, score_bbdc, risk_bbdc, err_bbdc = load_and_process_ticker("BBDC4")

    col_itub, col_bbdc = st.columns(2)

    with col_itub:
        st.markdown(f"""
        <div class="metric-card" style="border-top: 4px solid #f97316;">
            <h3>Itaú Unibanco (ITUB4)</h3>
            <p style="font-size: 1.5rem; font-weight: 700;">R$ {risk_itub['entry_price']:.2f}</p>
            <p><strong>Sinal:</strong> {score_itub['signal']} (Score: {score_itub['score']:+d})</p>
            <hr style="border-color: #374151;">
            <p>🛑 Stop Loss: <strong>R$ {risk_itub['stop_loss']:.2f}</strong> (-{risk_itub['risk_pct']:.2f}%)</p>
            <p>🥇 Alvo 1: <strong>R$ {risk_itub['target_1']:.2f}</strong> (+{risk_itub['target_1_gain_pct']:.2f}%)</p>
            <p>🏆 Alvo 2: <strong>R$ {risk_itub['target_2']:.2f}</strong> (+{risk_itub['target_2_gain_pct']:.2f}%)</p>
            <p>📊 IFR 60m: <strong>{h_itub['RSI_14'].iloc[-1]:.1f}</strong></p>
        </div>
        """, unsafe_allow_html=True)

    with col_bbdc:
        st.markdown(f"""
        <div class="metric-card" style="border-top: 4px solid #ef4444;">
            <h3>Banco Bradesco (BBDC4)</h3>
            <p style="font-size: 1.5rem; font-weight: 700;">R$ {risk_bbdc['entry_price']:.2f}</p>
            <p><strong>Sinal:</strong> {score_bbdc['signal']} (Score: {score_bbdc['score']:+d})</p>
            <hr style="border-color: #374151;">
            <p>🛑 Stop Loss: <strong>R$ {risk_bbdc['stop_loss']:.2f}</strong> (-{risk_bbdc['risk_pct']:.2f}%)</p>
            <p>🥇 Alvo 1: <strong>R$ {risk_bbdc['target_1']:.2f}</strong> (+{risk_bbdc['target_1_gain_pct']:.2f}%)</p>
            <p>🏆 Alvo 2: <strong>R$ {risk_bbdc['target_2']:.2f}</strong> (+{risk_bbdc['target_2_gain_pct']:.2f}%)</p>
            <p>📊 IFR 60m: <strong>{h_bbdc['RSI_14'].iloc[-1]:.1f}</strong></p>
        </div>
        """, unsafe_allow_html=True)

    # Gráfico comparativo de rentabilidade relativa (base 100)
    st.subheader("Desempenho Relativo nos Últimos 60 Dias (Base 100)")
    
    # Normaliza pelo primeiro preço comum
    itub_norm = (h_itub["Close"] / h_itub["Close"].iloc[0]) * 100
    bbdc_norm = (h_bbdc["Close"] / h_bbdc["Close"].iloc[0]) * 100

    fig_comp = go.Figure()
    fig_comp.add_trace(go.Scatter(x=itub_norm.index, y=itub_norm, name="ITUB4 (Itaú)", line=dict(color="#f97316", width=2)))
    fig_comp.add_trace(go.Scatter(x=bbdc_norm.index, y=bbdc_norm, name="BBDC4 (Bradesco)", line=dict(color="#ef4444", width=2)))
    fig_comp.update_layout(
        template="plotly_dark",
        height=400,
        yaxis_title="Desempenho Relativo (%)",
        margin=dict(l=40, r=40, t=20, b=20)
    )
    st.plotly_chart(fig_comp, use_container_width=True)

# =============================================================================
# ABA 5: GUIA OPERACIONAL & ISENÇÃO IR
# =============================================================================
with tab_guide:
    st.subheader("📘 Como Operar Swing Trade na Prática na B3")

    st.markdown("""
    ### 1. Como Lançar a Ordem no Home Broker da sua Corretora
    1. **Entrada na Operação**:
       - Quando o analisador indicar **COMPRA** ou **COMPRA FORTE**, abra o Home Broker da sua corretora (ex: XP, Clear, BTG, Inter, Rico, etc.).
       - Se for comprar lotes padrão (múltiplos de 100), digite o código `ITUB4` ou `BBDC4`.
       - Se o capital permitir um lote menor (ex: 45 ações), adicione a letra **F** no final: `ITUB4F` ou `BBDC4F` (Mercado Fracionário).
    2. **Ordem OCO (One Cancels the Other) ou Stop Simultâneo**:
       - Quase todos os Home Brokers possuem a boleta **Stop Simultâneo / OCO**.
       - Preencha o **Stop Loss** exatamente com o valor indicado na métrica (ex: R$ 38,24).
       - Preencha o **Stop Gain** com o valor do **Alvo 1** ou **Alvo 2**.
       - Com a ordem OCO cadastrada, se um preço for atingido, a corretora cancela o outro automaticamente, garantindo que você não precise ficar olhando o monitor o dia todo.

    ---

    ### 2. A Regra de Ouro do Imposto de Renda no Swing Trade (Art. 3º, Lei 11.033/2004)
    - **O que diz a lei?** Se o total de **vendas** de ações em operações comuns (Swing Trade) em um mesmo mês calendário for de até **R$ 20.000,00**, todo o lucro obtido nessas vendas é **ISENTO** de Imposto de Renda.
    - **Atenção:**
      1. A isenção é sobre o **valor bruto das vendas**, não sobre o lucro! Se você vendeu R$ 20.000,01 no mês, todo o lucro daquele mês passa a ser tributado à alíquota de 15%.
      2. **Day Trade NÃO tem isenção!** Se você comprar e vender a mesma ação no mesmo dia, paga 20% sobre qualquer lucro, mesmo que seja R$ 50. Para usufruir da isenção, segure a ação pelo menos até o dia seguinte (Swing Trade).
      3. **ETFs e FIIs não têm essa isenção de R$ 20k.** Ela se aplica estritamente a **ações ordinárias (ON) e preferenciais (PN)** da B3, exatamente o caso de `ITUB4` e `BBDC4`.

    ---

    ### 3. A Regra do Break-Even (Risco Zero)
    - Quando o ativo atingir o **Alvo 1**, realize metade da sua posição para colocar dinheiro no bolso.
    - Em seguida, **altere a ordem de Stop Loss da outra metade para o preço de entrada original**.
    - A partir desse momento, a operação passa a ter **risco financeiro ZERO**: você já lucrou no primeiro lote e o segundo lote não pode mais gerar prejuízo!
    """)

# -----------------------------------------------------------------------------
# Rodapé
# -----------------------------------------------------------------------------
st.markdown("---")
st.caption(f"B3 Swing Trade Pro • Análise gerada em tempo real com dados de mercado via Yahoo Finance • Última atualização: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
