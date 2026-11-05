# 📈 B3 Swing Trade Pro - Analisador Automático de Sinais

Analisador automático de sinais técnicos para **Swing Trade** na **B3 (Bolsa de Valores Brasileira)** com foco principal em **ITUB4** (Itaú Unibanco) e **BBDC4** (Banco Bradesco), além de suporte aberto para qualquer ativo da B3.

Projetado especialmente para investidores que desejam otimizar seus lucros aproveitando a **isenção total de Imposto de Renda** (vendas de ações até R$ 20.000,00 por mês).

---

## 🚀 Como Executar

### Opção 1: Via Arquivo Executável (Mais Fácil)
Dê um duplo clique no arquivo:
```
iniciar_analisador.bat
```
O painel abrirá automaticamente no seu navegador padrão (`http://localhost:8501`).

### Opção 2: Via Linha de Comando (PowerShell / Terminal)
```powershell
cd C:\Users\User\.gemini\antigravity\scratch\b3_swing_trade_analyzer
"C:\Users\User\AppData\Local\Programs\Python\Python311\python.exe" -m streamlit run app.py
```

---

## 🧠 Arquitetura do Sistema

### 1. Estratégia Híbrida de Tempo Gráfico
- **Gráfico Diário (D1 - Macro Tendência)**: Define a tendência institucional primária e secundária através de Médias Móveis (SMA 200, EMA 21), MACD e Acumulação por OBV.
- **Gráfico de 60 Minutos (1h - Timing e Gatilho)**: Refina o momento exato de entrada e saída por meio do alinhamento das médias rápidas (EMA 9 e EMA 21), sobrevenda/sobrecompra no IFR (RSI 14) e explosão de volatilidade nas Bandas de Bollinger.

### 2. Sistema Multifatorial Ponderado (Score de -100 a +100)
Cada indicador possui um peso proporcional testado no mercado brasileiro:
- **Macro Tendência Diária (~35%)**: Preço vs SMA 200, EMA 21 e MACD Diário.
- **Gatilho de 60 Minutos (~35%)**: Cruzamento EMA 9/21, IFR 14 e Histograma MACD 60m.
- **Volume & Fluxo (~18%)**: Volume > 1.25x da média dos 20 períodos e OBV acumulando.
- **Volatilidade Bollinger (~12%)**: Rejeição de fundos e prevenção de compras em topos esticados.

#### Classificação dos Sinais:
- 🟢 **COMPRA FORTE** (Score >= +55): Alta convicção com alinhamento total de prazos.
- 🟢 **COMPRA** (+25 a +54): Oportunidade favorável de swing trade.
- ⚪ **NEUTRO** (-24 a +24): Mercado em consolidação lateral ou sinais conflitantes.
- 🟠 **VENDA / REALIZAR** (-25 a -54): Perda de fôlego da alta, realizar lucros parciais.
- 🔴 **VENDA FORTE** (Score <= -55): Tendência de baixa consolidada, proteger capital.

### 3. Gestão de Risco Técnico
- **Stop Loss Técnico**: Calculado automaticamente com base na mínima do fundo recente nos 60m e na volatilidade diária ATR (Average True Range).
- **Alvo 1 (Take Profit Parcial)**: Relação Risco:Retorno de 1:1.5 (sugestão de realizar 50% da mão e mover o stop para o breakeven / 0 a 0).
- **Alvo 2 (Take Profit Final)**: Relação Risco:Retorno de 1:2.5 (alvo de extensão do movimento).

### 4. Isenção de Imposto de Renda (< R$ 20.000 / mês)
- O sistema inclui um termômetro que calcula o volume financeiro estimado da sua saída.
- No Swing Trade em ações (não válido para Day Trade ou FIIs), **vendas totais mensais de até R$ 20.000,00 são 100% isentas de imposto sobre ganho de capital** (Art. 3º, I, da Lei nº 11.033/2004).
