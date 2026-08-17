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
.block-container {max-width: 1500px; padding-top: 1.5rem;}
[data-testid="stMetric"] {border: 1px solid #273449; border-radius: 12px; padding: 12px; background: #111827;}
</style>
""", unsafe_allow_html=True)

st.title("📊 Radar Financiero Pro")
st.caption("Análisis educativo de acciones y ETFs estadounidenses")

@st.cache_data(ttl=900, show_spinner=False)
def load_asset(symbol, period, interval):
    ticker = yf.Ticker(symbol)
    prices = ticker.history(period=period, interval=interval, auto_adjust=False)
    try: info = ticker.info
    except Exception: info = {}
    try: income = ticker.income_stmt
    except Exception: income = pd.DataFrame()
    try: balance = ticker.balance_sheet
    except Exception: balance = pd.DataFrame()
    try: cashflow = ticker.cashflow
    except Exception: cashflow = pd.DataFrame()
    return prices, info, income, balance, cashflow

def valid(v):
    return isinstance(v, (int, float, np.integer, np.floating)) and np.isfinite(v)

def fmt(v, decimals=2): return f"{v:,.{decimals}f}" if valid(v) else "N/D"
def pct(v): return f"{v * 100:.2f}%" if valid(v) else "N/D"
def money(v): return f"${v:,.0f}" if valid(v) else "N/D"

def indicators(df):
    df = df.dropna(subset=["Close"]).copy()
    c = df["Close"]
    for n in [20, 50, 100, 200]: df[f"MA{n}"] = c.rolling(n).mean()
    delta = c.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
    loss = -delta.clip(upper=0).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    df["RSI"] = 100 - 100 / (1 + rs)
    ema12, ema26 = c.ewm(span=12, adjust=False).mean(), c.ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_SIGNAL"] = df["MACD"].ewm(span=9, adjust=False).mean()
    mid, sd = c.rolling(20).mean(), c.rolling(20).std()
    df["BB_MID"], df["BB_UPPER"], df["BB_LOWER"] = mid, mid + 2*sd, mid - 2*sd
    return df

def base_score(info, prices):
    points, signals = 0, []
    pe, roe, margin, debt = info.get("trailingPE"), info.get("returnOnEquity"), info.get("profitMargins"), info.get("debtToEquity")
    tests = [(valid(pe) and 0 < pe < 25, "PER menor que 25"), (valid(roe) and roe > .15, "ROE mayor que 15%"), (valid(margin) and margin > .10, "Margen neto mayor que 10%"), (valid(debt) and debt < 100, "Deuda/patrimonio menor que 100")]
    for ok, text in tests:
        if ok: points += 1; signals.append(text)
    ma200 = prices["MA200"].iloc[-1]
    if pd.notna(ma200) and prices["Close"].iloc[-1] > ma200: points += 1; signals.append("Precio sobre MA200")
    return points, signals

def price_projection(info, current, growth, terminal_pe, years):
    eps = info.get("trailingEps")
    if not valid(eps) or eps <= 0: return None
    future_eps = eps * (1 + growth) ** years
    future_price = future_eps * terminal_pe
    annual_return = (future_price / current) ** (1 / years) - 1
    return eps, future_eps, future_price, annual_return

with st.sidebar:
    st.header("Configuración")
    symbol = st.text_input("Símbolo bursátil", "AAPL").strip().upper()
    period = st.selectbox("Periodo", ["6mo", "1y", "3y", "5y", "10y", "max"], index=2)
    interval = st.selectbox("Intervalo", ["1d", "1wk", "1mo"], index=0)
    chart = st.selectbox("Gráfico", ["Velas", "Línea"], index=0)
    st.divider()
    st.header("Supuestos de valoración")
    growth = st.slider("Crecimiento EPS anual", -20, 40, 10) / 100
    terminal_pe = st.slider("PER final", 5, 50, 20)
    years = st.slider("Horizonte", 3, 15, 10)
    target_return = st.slider("Rentabilidad objetivo", 5, 25, 15) / 100
    run = st.button("Analizar activo", type="primary", use_container_width=True)

if run or "asset" not in st.session_state:
    try:
        st.session_state.asset = load_asset(symbol, period, interval)
        st.session_state.symbol = symbol
    except Exception as e:
        st.error("No fue posible descargar el activo. Revisa el símbolo.")
        st.caption(str(e)); st.stop()
prices, info, income, balance, cashflow = st.session_state.asset
symbol = st.session_state.symbol
if prices.empty: st.error("No hay datos para este símbolo."); st.stop()
prices = indicators(prices)
close = prices["Close"]
current = float(close.iloc[-1])
previous = float(close.iloc[-2]) if len(close) > 1 else current
change = current / previous - 1 if previous else 0
name = info.get("longName") or info.get("shortName") or symbol
asset_type = str(info.get("quoteType", "Activo")).upper()
sector = info.get("sector") or info.get("category") or "N/D"
score, signals = base_score(info, prices)

st.subheader(f"{name} · {symbol}")
mc = st.columns(6)
mc[0].metric("Precio", f"${current:,.2f}", f"{change:+.2%}")
mc[1].metric("Tipo", asset_type)
mc[2].metric("PER", fmt(info.get("trailingPE")))
mc[3].metric("ROE", pct(info.get("returnOnEquity")))
mc[4].metric("RSI", fmt(prices["RSI"].iloc[-1], 1))
mc[5].metric("Puntaje", f"{score}/5")
st.caption(f"Sector: {sector} · Último dato: {prices.index[-1].strftime('%Y-%m-%d')} · Consulta: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

summary, fundamentals, technical, valuation, portfolio, ai = st.tabs(["Resumen", "Fundamental", "Técnico", "Valoración", "Portafolio", "IA"])

with summary:
    left, right = st.columns([2, 1])
    with left:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[.75, .25], vertical_spacing=.04)
        if chart == "Velas": fig.add_trace(go.Candlestick(x=prices.index, open=prices.Open, high=prices.High, low=prices.Low, close=prices.Close, name="Precio"), row=1, col=1)
        else: fig.add_trace(go.Scatter(x=prices.index, y=close, name="Cierre"), row=1, col=1)
        fig.add_trace(go.Bar(x=prices.index, y=prices.Volume, name="Volumen"), row=2, col=1)
        fig.update_layout(height=560, xaxis_rangeslider_visible=False, hovermode="x unified", margin=dict(l=10,r=10,t=20,b=10))
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.subheader("Lectura rápida")
        ma200, rsi = prices.MA200.iloc[-1], prices.RSI.iloc[-1]
        trend = "Alcista" if pd.notna(ma200) and current > ma200 else "Bajista o insuficiente"
        state = "Sobrecompra" if valid(rsi) and rsi > 70 else "Sobreventa" if valid(rsi) and rsi < 30 else "Zona intermedia"
        st.info(f"**Tendencia:** {trend}\n\n**RSI:** {fmt(rsi,1)} · {state}")
        st.write("**Señales calculadas:**")
        for signal in signals: st.write(f"✅ {signal}")
        if not signals: st.write("Sin señales positivas bajo estas reglas.")

with fundamentals:
    st.subheader("Métricas disponibles")
    data = {"Capitalización": money(info.get("marketCap")), "Ingresos": money(info.get("totalRevenue")), "Beneficio neto": money(info.get("netIncomeToCommon")), "EPS": fmt(info.get("trailingEps")), "PER": fmt(info.get("trailingPE")), "P/S": fmt(info.get("priceToSalesTrailing12Months")), "ROE": pct(info.get("returnOnEquity")), "ROA": pct(info.get("returnOnAssets")), "Margen neto": pct(info.get("profitMargins")), "Deuda/patrimonio": fmt(info.get("debtToEquity")), "Flujo de caja libre": money(info.get("freeCashflow")), "Dividendo": pct(info.get("dividendYield"))}
    st.dataframe(pd.DataFrame({"Métrica": data.keys(), "Valor": data.values()}), use_container_width=True, hide_index=True)
    st.subheader("Método BASE")
    st.write("**B — Base:** revisar producto, recurrencia, competencia, marca y poder de fijación de precios.")
    st.write("**A — Administración:** revisar crecimiento por acción, recompras, dividendos y asignación de capital.")
    st.write("**S — Salud:** interpretar ROE, márgenes, deuda, beneficios y flujo de caja conjuntamente.")
    st.write("**E — Evaluación:** combinar múltiplos, crecimiento, escenarios y margen de seguridad.")
    if not income.empty:
        st.subheader("Estado de resultados disponible")
        st.dataframe(income, use_container_width=True)

with technical:
    st.subheader("Tendencia, RSI y MACD")
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[.6,.2,.2], vertical_spacing=.04)
    fig.add_trace(go.Scatter(x=prices.index,y=close,name="Precio"),row=1,col=1)
    for col,color in [("MA50","orange"),("MA100","green"),("MA200","red")]: fig.add_trace(go.Scatter(x=prices.index,y=prices[col],name=col,line=dict(color=color)),row=1,col=1)
    fig.add_trace(go.Scatter(x=prices.index,y=prices.RSI,name="RSI"),row=2,col=1)
    fig.add_hline(y=70,line_dash="dash",line_color="red",row=2,col=1); fig.add_hline(y=30,line_dash="dash",line_color="green",row=2,col=1)
    fig.add_trace(go.Scatter(x=prices.index,y=prices.MACD,name="MACD"),row=3,col=1); fig.add_trace(go.Scatter(x=prices.index,y=prices.MACD_SIGNAL,name="Señal"),row=3,col=1)
    fig.update_layout(height=760,hovermode="x unified",margin=dict(l=10,r=10,t=20,b=10))
    st.plotly_chart(fig,use_container_width=True)
    st.caption("Los indicadores técnicos describen el comportamiento histórico; no garantizan resultados futuros.")

with valuation:
    st.subheader("Proyección transparente")
    result = price_projection(info, current, growth, terminal_pe, years)
    if result:
        eps, future_eps, future_price, annual_return = result
        c = st.columns(4)
        c[0].metric("EPS actual", f"${eps:.2f}")
        c[1].metric(f"EPS año {years}", f"${future_eps:.2f}")
        c[2].metric(f"Precio año {years}", f"${future_price:.2f}")
        c[3].metric("TIR simulada", f"{annual_return:.2%}")
        target_price = future_price / ((1 + target_return) ** years)
        st.info(f"Con estos supuestos, el precio teórico actual para alcanzar {target_return:.0%} anual sería aproximadamente **${target_price:.2f}**.")
        st.warning("Esta cifra depende completamente del crecimiento y PER final elegidos. No es un precio objetivo ni una recomendación.")
        scenario = pd.DataFrame({"Escenario": ["Pesimista", "Base", "Optimista"], "Crecimiento": [growth-.05, growth, growth+.05], "PER final": [max(8, terminal_pe-5), terminal_pe, terminal_pe+5]})
        scenario["Precio futuro"] = eps * (1 + scenario["Crecimiento"]) ** years * scenario["PER final"]
        scenario["TIR"] = (scenario["Precio futuro"] / current) ** (1 / years) - 1
        st.dataframe(scenario.style.format({"Crecimiento":"{:.2%}","PER final":"{:.1f}","Precio futuro":"${:.2f}","TIR":"{:.2%}"}), use_container_width=True, hide_index=True)
    else: st.warning("No hay EPS positivo disponible para realizar esta proyección.")

with portfolio:
    st.subheader("Simulador de portafolio")
    assets_text = st.text_input("Activos separados por comas", f"{symbol}, VOO, BND")
    weights_text = st.text_input("Pesos separados por comas", "50, 40, 10")
    if st.button("Calcular portafolio"):
        try:
            assets = [x.strip().upper() for x in assets_text.split(",") if x.strip()]
            weights = [float(x.strip())/100 for x in weights_text.split(",")]
            if len(assets) != len(weights) or abs(sum(weights)-1) > .001: st.error("Los pesos deben coincidir con los activos y sumar 100%.")
            else:
                hist = yf.download(assets, period="5y", auto_adjust=True, progress=False)["Close"]
                if isinstance(hist,pd.Series): hist=hist.to_frame(assets[0])
                ret=hist.pct_change().dropna(); p_ret=ret.mul(weights,axis=1).sum(axis=1)
                c=st.columns(3); c[0].metric("Rendimiento anualizado",f"{p_ret.mean()*252:.2%}"); c[1].metric("Volatilidad anualizada",f"{p_ret.std()*np.sqrt(252):.2%}"); c[2].metric("Máxima caída",f"{((1+p_ret).cumprod()/(1+p_ret).cumprod().cummax()-1).min():.2%}")
                st.subheader("Crecimiento histórico simulado")
                st.line_chart((1+p_ret).cumprod())
                st.subheader("Correlación")
                st.dataframe(ret.corr().round(2),use_container_width=True)
        except Exception as e: st.error(f"No se pudo calcular: {e}")

with ai:
    st.subheader("Analista IA")
    st.info("En el siguiente paso conectaremos un modelo de IA mediante una clave protegida. La IA recibirá los cálculos, supuestos y riesgos, pero no ejecutará operaciones.")
    st.json({"Activo":symbol,"Precio":current,"PER":info.get("trailingPE"),"ROE":info.get("returnOnEquity"),"RSI":prices.RSI.iloc[-1],"Puntaje":score,"Supuestos":{"crecimiento":growth,"PER_final":terminal_pe,"años":years}})

st.divider()
st.caption("Aviso educativo: no constituye recomendación formal de compra o venta. Los datos gratuitos pueden estar retrasados, incompletos o contener errores.")
