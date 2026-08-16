import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

st.set_page_config(page_title="Radar Financiero Pro", page_icon="📊", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1500px;}
[data-testid="stMetric"] {background: #111827; border: 1px solid #263244; padding: 14px; border-radius: 12px;}
.small-note {color: #94a3b8; font-size: 0.9rem;}
</style>
""", unsafe_allow_html=True)

st.title("📊 Radar Financiero Pro")
st.caption("Dashboard educativo para acciones y ETFs del mercado estadounidense")

@st.cache_data(ttl=900)
def get_market_data(symbol, period, interval):
    ticker = yf.Ticker(symbol)
    prices = ticker.history(period=period, interval=interval, auto_adjust=False)
    try:
        info = ticker.info
    except Exception:
        info = {}
    try:
        income = ticker.income_stmt
    except Exception:
        income = pd.DataFrame()
    try:
        balance = ticker.balance_sheet
    except Exception:
        balance = pd.DataFrame()
    try:
        cashflow = ticker.cashflow
    except Exception:
        cashflow = pd.DataFrame()
    return prices, info, income, balance, cashflow

def number(value, decimals=2):
    if value is None or not isinstance(value, (int, float, np.integer, np.floating)) or not np.isfinite(value):
        return "N/D"
    return f"{value:,.{decimals}f}"

def percent(value, decimals=2):
    if value is None or not isinstance(value, (int, float, np.integer, np.floating)) or not np.isfinite(value):
        return "N/D"
    return f"{value * 100:.{decimals}f}%"

def calculate_indicators(df):
    df = df.copy().dropna(subset=["Close"])
    close = df["Close"]
    df["MA50"] = close.rolling(50).mean()
    df["MA100"] = close.rolling(100).mean()
    df["MA200"] = close.rolling(200).mean()
    df["EMA20"] = close.ewm(span=20, adjust=False).mean()
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
    loss = -delta.clip(upper=0).ewm(alpha=1 / 14, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    df["RSI14"] = 100 - (100 / (1 + rs))
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["BB_mid"] = close.rolling(20).mean()
    std = close.rolling(20).std()
    df["BB_upper"] = df["BB_mid"] + 2 * std
    df["BB_lower"] = df["BB_mid"] - 2 * std
    return df

def valuation_score(info, df):
    score = 0
    reasons = []
    pe = info.get("trailingPE")
    roe = info.get("returnOnEquity")
    margin = info.get("profitMargins")
    debt = info.get("debtToEquity")
    if isinstance(pe, (int, float)) and 0 < pe < 25:
        score += 1
        reasons.append("PER inferior a 25")
    if isinstance(roe, (int, float)) and roe > 0.15:
        score += 1
        reasons.append("ROE superior al 15%")
    if isinstance(margin, (int, float)) and margin > 0.10:
        score += 1
        reasons.append("Margen neto superior al 10%")
    if isinstance(debt, (int, float)) and debt < 100:
        score += 1
        reasons.append("Deuda/patrimonio inferior a 100")
    price = df["Close"].iloc[-1]
    ma200 = df["MA200"].iloc[-1]
    if pd.notna(ma200) and price > ma200:
        score += 1
        reasons.append("Precio sobre MA200")
    return score, reasons

with st.sidebar:
    st.header("⚙️ Parámetros")
    symbol = st.text_input("Símbolo", "AAPL").strip().upper()
    period = st.selectbox("Histórico", ["6mo", "1y", "3y", "5y", "10y", "max"], index=2)
    interval = st.selectbox("Velas", ["1d", "1wk", "1mo"], index=0)
    chart_type = st.radio("Tipo de gráfico", ["Velas", "Línea"], index=0)
    st.divider()
    st.subheader("Simulación de valoración")
    growth = st.slider("Crecimiento anual supuesto", -20, 40, 10) / 100
    terminal_pe = st.slider("PER final supuesto", 5, 50, 20)
    years = st.slider("Horizonte", 3, 15, 10)
    analyze = st.button("🔍 Analizar", type="primary", use_container_width=True)

if analyze or "data" not in st.session_state:
    if not symbol:
        st.error("Escribe un símbolo bursátil.")
        st.stop()
    try:
        st.session_state.data = get_market_data(symbol, period, interval)
        st.session_state.symbol = symbol
    except Exception as error:
        st.error("No fue posible consultar los datos. Comprueba el símbolo e inténtalo de nuevo.")
        st.caption(str(error))
        st.stop()

prices, info, income, balance, cashflow = st.session_state.data
symbol = st.session_state.symbol
if prices.empty:
    st.error("No se encontraron datos para este símbolo.")
    st.stop()

prices = calculate_indicators(prices)
close = prices["Close"]
last = float(close.iloc[-1])
previous = float(close.iloc[-2]) if len(close) > 1 else last
daily_change = (last / previous - 1) if previous else 0
name = info.get("longName") or info.get("shortName") or symbol
currency = info.get("currency", "USD")
asset_type = str(info.get("quoteType", "Activo")).upper()
sector = info.get("sector") or info.get("category") or "N/D"
score, reasons = valuation_score(info, prices)

st.subheader(f"{name} · {symbol}")
cols = st.columns(6)
cols[0].metric("Precio", f"{currency} {last:,.2f}", f"{daily_change:+.2%}")
cols[1].metric("Tipo", asset_type)
cols[2].metric("PER", number(info.get("trailingPE")))
cols[3].metric("ROE", percent(info.get("returnOnEquity")))
cols[4].metric("Margen neto", percent(info.get("profitMargins")))
cols[5].metric("Puntaje inicial", f"{score}/5")
st.caption(f"Sector/categoría: {sector} · Último dato: {prices.index[-1].strftime('%Y-%m-%d')} · Datos gratuitos, posiblemente retrasados")

summary, fundamental, technical, portfolio, ai = st.tabs(["Resumen", "Fundamental", "Técnico", "Portafolio", "IA"])

with summary:
    left, right = st.columns([2, 1])
    with left:
        st.subheader("Precio y volumen")
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.72, 0.28])
        if chart_type == "Velas":
            fig.add_trace(go.Candlestick(x=prices.index, open=prices["Open"], high=prices["High"], low=prices["Low"], close=prices["Close"], name="Precio"), row=1, col=1)
        else:
            fig.add_trace(go.Scatter(x=prices.index, y=close, name="Cierre"), row=1, col=1)
        fig.add_trace(go.Bar(x=prices.index, y=prices["Volume"], name="Volumen", marker_color="#64748b"), row=2, col=1)
        fig.update_layout(height=560, margin=dict(l=10, r=10, t=20, b=10), xaxis_rangeslider_visible=False, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.subheader("Lectura rápida")
        ma200 = prices["MA200"].iloc[-1]
        rsi = prices["RSI14"].iloc[-1]
        trend = "Alcista" if pd.notna(ma200) and last > ma200 else "Bajista o insuficiente"
        rsi_state = "Sobrecompra" if pd.notna(rsi) and rsi > 70 else "Sobreventa" if pd.notna(rsi) and rsi < 30 else "Intermedia"
        st.info(f"**Tendencia:** {trend}\n\n**RSI:** {number(rsi, 1)} ({rsi_state})")
        st.markdown("**Señales positivas detectadas:**")
        if reasons:
            for reason in reasons:
                st.write(f"✅ {reason}")
        else:
            st.write("No hay suficientes señales positivas bajo estas reglas.")

with fundamental:
    st.subheader("Métricas fundamentales disponibles")
    fundamental_data = {
        "Capitalización": info.get("marketCap"),
        "Ingresos": info.get("totalRevenue"),
        "Beneficio neto": info.get("netIncomeToCommon"),
        "EPS": info.get("trailingEps"),
        "PER": info.get("trailingPE"),
        "Precio / ventas": info.get("priceToSalesTrailing12Months"),
        "ROE": percent(info.get("returnOnEquity")),
        "ROA": percent(info.get("returnOnAssets")),
        "Margen neto": percent(info.get("profitMargins")),
        "Deuda / patrimonio": info.get("debtToEquity"),
        "Flujo de caja libre": info.get("freeCashflow"),
        "Rendimiento dividendo": percent(info.get("dividendYield")),
    }
    table = pd.DataFrame({"Métrica": list(fundamental_data.keys()), "Valor": [number(v) if not isinstance(v, str) else v for v in fundamental_data.values()]})
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.subheader("Método BASE")
    st.write("**B — Base:** esta versión presenta datos de mercado, pero la ventaja competitiva requiere investigación cualitativa.")
    st.write("**A — Administración:** revisar crecimiento por acción, recompras, dividendos y asignación histórica del capital.")
    st.write("**S — Salud:** utilizar ROE, márgenes, deuda, beneficio y flujo de caja como señales iniciales, no como veredicto automático.")
    st.write("**E — Evaluación:** el puntaje inicial combina reglas visibles y no sustituye una valoración completa.")
    if not income.empty:
        st.subheader("Estados financieros disponibles")
        st.dataframe(income.head(8), use_container_width=True)

with technical:
    st.subheader("Indicadores técnicos")
    t1, t2, t3 = st.columns(3)
    t1.metric("MA50", number(prices["MA50"].iloc[-1]))
    t2.metric("MA100", number(prices["MA100"].iloc[-1]))
    t3.metric("MA200", number(prices["MA200"].iloc[-1]))
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.6, 0.2, 0.2])
    fig.add_trace(go.Scatter(x=prices.index, y=close, name="Precio"), row=1, col=1)
    for col, color in [("MA50", "#f59e0b"), ("MA100", "#22c55e"), ("MA200", "#ef4444")]:
        fig.add_trace(go.Scatter(x=prices.index, y=prices[col], name=col, line=dict(color=color)), row=1, col=1)
    fig.add_trace(go.Scatter(x=prices.index, y=prices["RSI14"], name="RSI14", line=dict(color="#a855f7")), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    fig.add_trace(go.Scatter(x=prices.index, y=prices["MACD"], name="MACD"), row=3, col=1)
    fig.add_trace(go.Scatter(x=prices.index, y=prices["MACD_signal"], name="Señal MACD"), row=3, col=1)
    fig.update_layout(height=750, margin=dict(l=10, r=10, t=20, b=10), hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Las señales técnicas describen comportamiento histórico y no garantizan resultados futuros.")

with portfolio:
    st.subheader("Simulador sencillo de portafolio")
    assets_text = st.text_input("Símbolos separados por comas", f"{symbol}, VOO, BND")
    weights_text = st.text_input("Pesos (%) separados por comas", "50, 40, 10")
    if st.button("Calcular portafolio"):
        assets = [x.strip().upper() for x in assets_text.split(",") if x.strip()]
        try:
            weights = [float(x.strip()) / 100 for x in weights_text.split(",")]
            if len(assets) != len(weights) or abs(sum(weights) - 1) > 0.001:
                st.error("Debe haber un peso por activo y la suma debe ser exactamente 100%.")
            else:
                data = yf.download(assets, period="5y", auto_adjust=True, progress=False)["Close"]
                if isinstance(data, pd.Series):
                    data = data.to_frame(assets[0])
                returns = data.pct_change().dropna()
                portfolio_returns = returns.mul(weights, axis=1).sum(axis=1)
                st.metric("Rendimiento anualizado aproximado", f"{portfolio_returns.mean() * 252:.2%}")
                st.metric("Volatilidad anualizada", f"{portfolio_returns.std() * np.sqrt(252):.2%}")
                st.dataframe(returns.corr().round(2), use_container_width=True)
        except Exception as error:
            st.error(f"No se pudo calcular el portafolio: {error}")

with ai:
    st.subheader("Interpretación por IA")
    st.info("La capa de IA se conectará en una siguiente etapa. Por ahora mostramos el contexto exacto que recibirá el modelo, separado de los cálculos.")
    context = {
        "Activo": symbol,
        "Tipo": asset_type,
        "Precio": last,
        "PER": info.get("trailingPE"),
        "ROE": info.get("returnOnEquity"),
        "Margen": info.get("profitMargins"),
        "RSI": prices["RSI14"].iloc[-1],
        "Puntaje": score,
        "Supuesto crecimiento": growth,
        "PER final": terminal_pe,
        "Horizonte": years,
    }
    st.json(context)
    st.warning("Una IA puede equivocarse. Su función será explicar datos y supuestos, no emitir órdenes automáticas.")

st.divider()
st.caption("Aviso educativo: este análisis no constituye una recomendación formal de compra o venta. Los datos gratuitos pueden estar retrasados, incompletos o contener errores.")


