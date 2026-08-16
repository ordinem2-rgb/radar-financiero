import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Radar Financiero", page_icon="📈", layout="wide")

st.title("📈 Radar Financiero")
st.caption("Análisis educativo de acciones y ETFs del mercado estadounidense")

with st.sidebar:
    st.header("Configuración")
    symbol = st.text_input("Símbolo bursátil", "AAPL").strip().upper()
    period = st.selectbox("Periodo del gráfico", ["6mo", "1y", "3y", "5y", "10y"], index=2)
    interval = st.selectbox("Intervalo", ["1d", "1wk"], index=0)
    analyze = st.button("Analizar activo", type="primary", use_container_width=True)

if not analyze and "loaded_symbol" not in st.session_state:
    st.info("Escribe un símbolo, por ejemplo AAPL, MSFT, VOO o SPY, y pulsa «Analizar activo».")
    st.stop()

if analyze:
    st.session_state.loaded_symbol = symbol
    st.session_state.loaded_period = period
    st.session_state.loaded_interval = interval

symbol = st.session_state.loaded_symbol
period = st.session_state.loaded_period
interval = st.session_state.loaded_interval

@st.cache_data(ttl=900)
def load_data(symbol, period, interval):
    ticker = yf.Ticker(symbol)
    history = ticker.history(period=period, interval=interval, auto_adjust=False)
    try:
        info = ticker.info
    except Exception:
        info = {}
    return history, info

try:
    history, info = load_data(symbol, period, interval)
except Exception as error:
    st.error(f"No fue posible consultar {symbol}. Comprueba que el símbolo sea correcto.")
    st.caption(f"Detalle técnico: {error}")
    st.stop()

if history.empty:
    st.error("No se recibieron datos para este símbolo.")
    st.stop()

history = history.dropna(subset=["Close"]).copy()
close = history["Close"]
history["MA50"] = close.rolling(50).mean()
history["MA100"] = close.rolling(100).mean()
history["MA200"] = close.rolling(200).mean()
delta = close.diff()
gain = delta.clip(lower=0).rolling(14).mean()
loss = -delta.clip(upper=0).rolling(14).mean()
rs = gain / loss.replace(0, np.nan)
history["RSI14"] = 100 - (100 / (1 + rs))

last_price = float(close.iloc[-1])
previous_price = float(close.iloc[-2]) if len(close) > 1 else last_price
change = last_price - previous_price
change_pct = (change / previous_price * 100) if previous_price else 0
currency = info.get("currency", "USD")
name = info.get("longName") or info.get("shortName") or symbol
asset_type = info.get("quoteType", "No disponible")
sector = info.get("sector") or info.get("category") or "No disponible"
market_cap = info.get("marketCap")
pe = info.get("trailingPE")
eps = info.get("trailingEps")
roe = info.get("returnOnEquity")
profit_margin = info.get("profitMargins")
debt_to_equity = info.get("debtToEquity")
free_cash_flow = info.get("freeCashflow")

st.subheader(f"{name} ({symbol})")
metric_cols = st.columns(5)
metric_cols[0].metric("Precio", f"{currency} {last_price:,.2f}", f"{change_pct:+.2f}%")
metric_cols[1].metric("Tipo", str(asset_type).upper())
metric_cols[2].metric("Sector", sector)
metric_cols[3].metric("PER", f"{pe:.2f}" if isinstance(pe, (int, float)) and np.isfinite(pe) else "N/D")
metric_cols[4].metric("RSI 14", f"{history['RSI14'].iloc[-1]:.1f}" if pd.notna(history['RSI14'].iloc[-1]) else "N/D")

st.caption(f"Último dato disponible: {history.index[-1].strftime('%Y-%m-%d')} | Consulta: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

tab1, tab2, tab3, tab4 = st.tabs(["Resumen", "Método BASE", "Análisis técnico", "Valoración"])

with tab1:
    st.subheader("Gráfico de precios")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=history.index, y=close, name="Cierre", line=dict(width=2)))
    fig.update_layout(height=450, hovermode="x unified", yaxis_title=f"Precio ({currency})", xaxis_title="Fecha")
    st.plotly_chart(fig, use_container_width=True)
    st.info("Esta primera versión muestra datos de mercado y cálculos transparentes. La interpretación por IA se añadirá después de validar la base cuantitativa.")

with tab2:
    st.subheader("Evaluación BASE")
    base_rows = [
        ["B — Base del negocio", "Revisar marca, recurrencia, competencia y poder de precios.", "Requiere revisión"],
        ["A — Administración", "Revisar crecimiento por acción, recompras, dividendos y deuda.", "Requiere revisión"],
        ["S — Salud financiera", f"ROE: {roe * 100:.1f}%" if isinstance(roe, (int, float)) else "ROE: N/D", "Datos parciales"],
        ["E — Evaluación", f"PER actual: {pe:.2f}" if isinstance(pe, (int, float)) else "PER actual: N/D", "Ver valoración"],
    ]
    st.table(pd.DataFrame(base_rows, columns=["Área", "Resultado disponible", "Estado"]))
    st.warning("Las preguntas cualitativas no se convierten automáticamente en hechos. Deben comprobarse con informes de la empresa y fuentes confiables.")

with tab3:
    st.subheader("Indicadores técnicos")
    tech_cols = st.columns(3)
    ma200 = history["MA200"].iloc[-1]
    rsi = history["RSI14"].iloc[-1]
    trend = "Alcista" if pd.notna(ma200) and last_price > ma200 else "Bajista o datos insuficientes"
    rsi_label = "Sobrecompra" if pd.notna(rsi) and rsi > 70 else "Sobreventa" if pd.notna(rsi) and rsi < 30 else "Zona intermedia"
    tech_cols[0].metric("Tendencia vs. MA200", trend)
    tech_cols[1].metric("RSI 14", f"{rsi:.1f}" if pd.notna(rsi) else "N/D")
    tech_cols[2].metric("Lectura RSI", rsi_label)
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=history.index, y=close, name="Precio"))
    for column in ["MA50", "MA100", "MA200"]:
        fig2.add_trace(go.Scatter(x=history.index, y=history[column], name=column))
    fig2.update_layout(height=500, hovermode="x unified", yaxis_title=f"Precio ({currency})")
    st.plotly_chart(fig2, use_container_width=True)
    st.caption("Las medias móviles y el RSI describen el comportamiento reciente; no predicen por sí solos el precio futuro.")

with tab4:
    st.subheader("Valoración inicial")
    valuation = []
    valuation.append(["EPS actual", f"{eps:.2f}" if isinstance(eps, (int, float)) else "N/D"])
    valuation.append(["Rendimiento inicial (EPS / precio)", f"{eps / last_price * 100:.2f}%" if isinstance(eps, (int, float)) and last_price else "N/D"])
    valuation.append(["Margen neto", f"{profit_margin * 100:.2f}%" if isinstance(profit_margin, (int, float)) else "N/D"])
    valuation.append(["Deuda / patrimonio", f"{debt_to_equity:.2f}" if isinstance(debt_to_equity, (int, float)) else "N/D"])
    valuation.append(["Flujo de caja libre", f"{free_cash_flow:,.0f}" if isinstance(free_cash_flow, (int, float)) else "N/D"])
    st.table(pd.DataFrame(valuation, columns=["Métrica", "Valor"]))
    st.warning("Todavía no se proyecta una TIR a 10 años porque faltan supuestos históricos completos. Añadiremos escenarios explícitos en la siguiente versión.")

st.divider()
st.caption("Aviso: esta aplicación es educativa y no constituye una recomendación formal de compra o venta de valores. Los datos gratuitos pueden estar retrasados, incompletos o contener errores.")