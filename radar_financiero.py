import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from base_engine_v2 import BuffettAnalyzer
from stock_screener import BuffettScreener

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
    st.caption("📋 Estos valores se usan para calcular si el precio actual permite lograr tu retorno objetivo")
    growth = st.slider("Crecimiento EPS anual", -20, 40, 10) / 100
    st.caption("Crecimiento esperado de ganancias por acción en los próximos 10 años")
    terminal_pe = st.slider("PER final", 5, 50, 20)
    st.caption("Múltiplo PER que esperas al final (ej: 20x significa 20 veces ganancias)")
    years = st.slider("Horizonte", 3, 15, 10)
    st.caption("Años que planeas mantener la acción")
    target_return = st.slider("Rentabilidad objetivo", 5, 25, 15) / 100
    st.caption("Retorno anual que deseas (15% es el estándar de Buffett)")
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

summary, base_analysis, fundamentals, technical, valuation, opportunities = st.tabs(["Resumen", "Análisis BASE", "Fundamental", "Técnico", "Valoración", "Oportunidades"])

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

with base_analysis:
    st.subheader("📊 Análisis Profesional - Método BASE + Buffettología")
    st.caption("Evaluación rigurosa siguiendo metodología de Warren Buffett y análisis fundamental profundo")
    
    # Ejecutar análisis profesional
    analyzer = BuffettAnalyzer(info, income, balance, cashflow, prices)
    summary = analyzer.get_executive_summary()
    full = summary['full_analysis']
    
    # ===== PUNTAJE GENERAL Y CLASIFICACIÓN =====
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    with col1:
        st.metric("🎯 Puntaje Total", f"{summary['overall_score']:.0f}/{summary['max_score']:.0f}")
        st.caption(f"{summary['percentage']:.0f}%")
    with col2:
        business_emoji = "💎" if full['B']['moat_strength'] == "Fuerte" else "⭐" if full['B']['moat_strength'] == "Moderado" else "🔹"
        st.metric(f"{business_emoji} Tipo de Negocio", full['B']['business_type'])
        st.caption(f"Foso: {full['B']['moat_strength']}")
    with col3:
        tir_emoji = "🚀" if summary['tir_projected'] and summary['tir_projected'] > 0.15 else "✅" if summary['tir_projected'] and summary['tir_projected'] > 0.10 else "⚠️"
        tir_display = f"{summary['tir_projected']:.1%}" if summary['tir_projected'] else "N/D"
        st.metric(f"{tir_emoji} TIR Proyectada (10 años)", tir_display)
    with col4:
        price_emoji = "🟢" if full['E']['valuation_level'] == 'Barata' else "🟡" if full['E']['valuation_level'] in ['Justa'] else "🔴"
        st.metric(f"{price_emoji} Valoración", full['E']['valuation_level'])
    
    # ===== RECOMENDACIÓN TÁCTICA =====
    st.markdown("---")
    st.subheader("⏰ Recomendación Táctica (Cuándo Comprar)")
    
    col_tactic_1, col_tactic_2 = st.columns([2, 1])
    with col_tactic_1:
        trend_emoji = "📈" if full['Technical']['trend'] == "Alcista" else "📉" if full['Technical']['trend'] == "Bajista" else "↔️"
        st.info(f"**Tendencia:** {trend_emoji} {full['Technical']['trend']}\n\n**Acción:** {full['Technical']['recommendation']}")
    with col_tactic_2:
        if summary.get('margin_of_safety') is not None:
            mos = summary.get('margin_of_safety', 0)
            mos_emoji = "✅" if mos > 0.15 else "⚠️" if mos > 0 else "❌"
            st.write(f"{mos_emoji} **Margen de Seguridad**")
            st.write(f"{mos:.0%}")
    
    if summary.get('target_price_15pct') and analyzer.current_price:
        st.write(f"**📍 Precio Objetivo para 15% TIR:** ${summary['target_price_15pct']:.2f} (actual: ${analyzer.current_price:.2f})")
    
    # ===== TABS ANÁLISIS PROFUNDO =====
    st.markdown("---")
    tabs_base = st.tabs(["B - Negocio", "A - Administración", "S - Salud", "E - Valoración", "Resumen"])
    
    # TAB B
    with tabs_base[0]:
        st.subheader("B — Base del Negocio (Foso Económico)")
        st.write("¿Posee un **monopolio de consumidor** o es un **commodity**? ¿Tiene ventaja competitiva sostenible?")
        
        col_b1, col_b2 = st.columns([1, 2])
        with col_b1:
            st.metric("Puntaje", f"{full['B']['score']}/{full['B']['max_score']}")
            st.write(f"**Clasificación:** {full['B']['business_type']}")
            st.write(f"**Foso:** {full['B']['moat_strength']}")
        with col_b2:
            if full['B']['signals']:
                st.write("**✅ Fortalezas Encontradas:**")
                for signal in full['B']['signals']:
                    st.write(f"  • {signal}")
            if full['B']['concerns']:
                st.write("**⚠️ Debilidades Detectadas:**")
                for concern in full['B']['concerns']:
                    st.write(f"  • {concern}")
        
        st.write("**❓ Preguntas para Investigación Cualitativa:**")
        for q in full['B']['questions']:
            st.write(f"  • {q}")
    
    # TAB A
    with tabs_base[1]:
        st.subheader("A — Administración (Asignación de Capital)")
        st.write("¿Genera valor la directiva? ¿Retorno sobre beneficios retenidos? ¿Deuda prudente?")
        
        col_a1, col_a2 = st.columns([1, 2])
        with col_a1:
            st.metric("Puntaje", f"{full['A']['score']}/{full['A']['max_score']}")
            st.write(f"**Recompras:** {full['A']['buyback_signal']}")
            st.write(f"**Deuda:** {full['A']['debt_assessment']}")
        with col_a2:
            if full['A']['signals']:
                st.write("**✅ Puntos Positivos:**")
                for signal in full['A']['signals']:
                    st.write(f"  • {signal}")
            if full['A']['concerns']:
                st.write("**⚠️ Preocupaciones:**")
                for concern in full['A']['concerns']:
                    st.write(f"  • {concern}")
        
        st.write("**❓ Investigación Adicional:**")
        for q in full['A']['questions']:
            st.write(f"  • {q}")
    
    # TAB S
    with tabs_base[2]:
        st.subheader("S — Salud Financiera")
        st.write("¿ROE consistente y alto? ¿Márgenes estables? ¿Flujo de caja real?")
        
        col_s1, col_s2 = st.columns([1, 2])
        with col_s1:
            st.metric("Puntaje", f"{full['S']['score']}/{full['S']['max_score']}")
            st.write(f"**Calidad ROE:** {full['S']['roe_quality']}")
            st.write(f"**Márgenes:** {full['S']['margin_trend']}")
        with col_s2:
            if full['S']['signals']:
                st.write("**✅ Señales Saludables:**")
                for signal in full['S']['signals']:
                    st.write(f"  • {signal}")
            if full['S']['concerns']:
                st.write("**⚠️ Banderas Rojas:**")
                for concern in full['S']['concerns']:
                    st.write(f"  • {concern}")
        
        st.write("**❓ Validar:**")
        for q in full['S']['questions']:
            st.write(f"  • {q}")
    
    # TAB E
    with tabs_base[3]:
        st.subheader("E — Evaluación del Precio")
        st.write("¿Es atractivo el precio actual? ¿Qué retorno esperado?")
        
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            st.metric("Puntaje", f"{full['E']['score']}/{full['E']['max_score']}")
            st.metric("Initial Yield", f"{full['E']['initial_yield']:.2%}" if full['E']['initial_yield'] else "N/D")
            st.metric("PER Actual", f"{info.get('trailingPE', 'N/D'):.1f}x" if info.get('trailingPE') else "N/D")
        with col_e2:
            st.metric("Valoración", full['E']['valuation_level'])
            st.metric("TIR Proyectada", f"{summary['tir_projected']:.1%}" if summary['tir_projected'] else "N/D")
            st.metric("Precio Objetivo (15%)", f"${summary['target_price_15pct']:.2f}" if summary['target_price_15pct'] else "N/D")
        
        if full['E']['signals']:
            st.write("**✅ Valoración Atractiva:**")
            for signal in full['E']['signals']:
                st.write(f"  • {signal}")
        if full['E']['concerns']:
            st.write("**⚠️ Valoración Cara:**")
            for concern in full['E']['concerns']:
                st.write(f"  • {concern}")
    
    # TAB RESUMEN
    with tabs_base[4]:
        st.subheader("📈 Análisis Integral")
        
        percentage = summary['percentage']
        if percentage >= 80:
            st.success(f"### ✅ Muy Favorable ({percentage:.0f}%)\nEl activo muestra características de **Monopolio de Consumidor** con valuación atractiva y administración solida.")
        elif percentage >= 60:
            st.info(f"### ⭐ Favorable ({percentage:.0f}%)\nBuen negocio con algunas señales positivas. Requiere revisión cualitativa adicional.")
        elif percentage >= 40:
            st.warning(f"### ⚠️ Mixto ({percentage:.0f}%)\nCaracterísticas positivas y negativas. Investigación adicional **obligatoria** antes de invertir.")
        else:
            st.error(f"### ❌ Desfavorable ({percentage:.0f}%)\nMás preocupaciones que fortalezas. Considerar alternativas.")
        
        st.markdown("---")
        st.write("**🎯 Conclusión de Análisis:**")
        
        conclusions = []
        if summary['business_type'] == 'MONOPOLIO CONSUMIDOR':
            conclusions.append(f"✅ Negocio de **calidad superior** con ventaja competitiva potencial")
        if summary['tir_projected'] and summary['tir_projected'] > 0.15:
            conclusions.append(f"✅ Retorno esperado **atractivo** (TIR {summary['tir_projected']:.1%})")
        if summary['valuation_level'] == 'Barata':
            conclusions.append(f"✅ Precio **actualmente atractivo** para comprar")
        if summary['trend'] == 'Alcista':
            conclusions.append(f"📈 Tendencia técnica **alcista**, favorable para entrada")
        
        if conclusions:
            for c in conclusions:
                st.write(f"  {c}")
        else:
            st.write("  • Revisar cuidadosamente antes de tomar decisión")
    
    # ADVERTENCIA LEGAL
    st.markdown("---")
    st.caption("⚠️ **Aviso Legal:** Este análisis es puramente educativo y analítico, basado en metodologías de Buffettología y Método BASE. No constituye una recomendación formal de compra o venta de valores. El análisis depende de datos incompletos y supuestos simplificados. Consulte con un asesor financiero calificado antes de invertir.")

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

with opportunities:
    st.subheader("🎯 Oportunidades de Inversión - Screening Buffett")
    st.caption("Análisis de acciones que cumplen criterios de calidad: Monopolio de Consumidor, ROE elevado, Deuda baja, Valuación atractiva")
    
    # Mensaje de inicio
    st.info("🔍 Analizando acciones de calidad según la filosofía de Buffett. Esto puede tomar 30-60 segundos...")
    
    progress_placeholder = st.empty()
    results_placeholder = st.empty()
    
    try:
        # Ejecutar screening
        screener = BuffettScreener()
        opportunities_list = screener.get_top_opportunities(num=15)
        
        if not opportunities_list:
            st.warning("No se encontraron acciones que cumplan los criterios de calidad en este momento.")
        else:
            # Mostrar resultados
            st.success(f"✅ Se encontraron {len(opportunities_list)} oportunidades de inversión")
            st.markdown("---")
            
            # Tabla de oportunidades
            st.subheader("Top Oportunidades")
            
            for idx, opp in enumerate(opportunities_list[:10], 1):
                col1, col2, col3, col4 = st.columns([1, 2, 2, 2])
                
                with col1:
                    st.metric(f"#{idx}", opp['symbol'], opp['score'])
                
                with col2:
                    st.write(f"**Sector:** {opp['sector']}")
                    st.write(f"**Precio:** {opp['price']}")
                
                with col3:
                    st.write(f"**Tipo:** {opp['business_type']}")
                    st.write(f"**Foso:** {opp['moat']}")
                
                with col4:
                    st.write("**Por qué es recomendable:**")
                    for reason in opp['reasons']:
                        st.write(f"  {reason}")
                
                st.markdown("---")
            
            # Tabla consolidada (opcional)
            st.subheader("Tabla Resumida")
            
            table_data = []
            for opp in opportunities_list[:10]:
                table_data.append({
                    'Símbolo': opp['symbol'],
                    'Puntaje': opp['score'],
                    'Precio': opp['price'],
                    'Sector': opp['sector'],
                    'Tipo de Negocio': opp['business_type'],
                    'Foso': opp['moat']
                })
            
            df_opportunities = pd.DataFrame(table_data)
            st.dataframe(df_opportunities, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.caption("💡 **Nota:** Estas son oportunidades identificadas por criterios cuantitativos. Realiza investigación cualitativa adicional, revisa informes anuales y noticias antes de invertir. Consulta con un asesor financiero calificado.")
    
    except Exception as e:
        st.error(f"Error al ejecutar screening: {str(e)}")
        st.caption("Intenta de nuevo en unos momentos o revisa la conexión a internet.")

st.divider()
st.caption("⚠️ **Aviso Legal:** Este análisis es puramente educativo y analítico. No constituye una recomendación formal de compra o venta de valores. Los datos gratuitos pueden estar retrasados, incompletos o contener errores. Consulte con un asesor financiero calificado antes de invertir.")
