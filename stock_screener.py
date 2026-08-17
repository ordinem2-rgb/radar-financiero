"""
Stock Screener - Busca y rankea acciones según filosofía Buffett/Método BASE
Identifica oportunidades de inversión en el mercado estadounidense
"""
import pandas as pd
import numpy as np
import yfinance as yf
from typing import List, Dict, Tuple
from base_engine_v2 import BuffettAnalyzer, is_valid

class ScreenedStock:
    """Representa una acción que ha pasado el screening"""
    def __init__(self, symbol: str, score: float, max_score: float, reasons: List[str], 
                 price: float, sector: str, business_type: str, moat: str, 
                 risk_profile: str = "Moderado", company_description: str = ""):
        self.symbol = symbol
        self.score = score
        self.max_score = max_score
        self.percentage = (score / max_score * 100) if max_score > 0 else 0
        self.reasons = reasons
        self.price = price
        self.sector = sector
        self.business_type = business_type
        self.moat = moat
        self.risk_profile = risk_profile  # Conservador, Moderado, Agresivo
        self.company_description = company_description  # Descripción de qué hace
    
    def __lt__(self, other):
        """Permite ordenar por score descendente"""
        return self.percentage > other.percentage

class BuffettScreener:
    """
    Screener de acciones siguiendo filosofía Buffett.
    Busca monopolios de consumidor con valoración atractiva.
    """
    
    # Lista curada de acciones estadounidenses de calidad (sector diverso)
    QUALITY_CANDIDATES = [
        # Consumo Masivo - Monopolios clásicos Buffett
        'KO', 'PEP', 'MDLZ', 'CL', 'PG', 'GIS', 'MO', 'KMB', 'EL',
        
        # Financiero & Pagos
        'V', 'MA', 'AXP', 'JPM', 'BAC', 'USB', 'WFC', 'BLK', 'SCHW',
        
        # Healthcare/Pharma
        'JNJ', 'UNH', 'PFE', 'ABBV', 'MRK', 'LLY', 'BPOB', 'TMO', 'ILMN',
        
        # Tech (con moat duradero)
        'AAPL', 'MSFT', 'GOOG', 'CRM', 'ADBE', 'INTU', 'PAYC',
        
        # Utilities & Defensivos
        'NEE', 'SO', 'DUK', 'EXC', 'XEL', 'ED', 'AEP',
        
        # Industrial/Fabricación
        'BA', 'GE', 'CAT', 'DE', 'ABB', 'EMR', 'ITW',
        
        # Retail/Distribución
        'AMZN', 'HD', 'LOW', 'KR', 'TJX', 'WMT', 'MCD', 'SBUX',
        
        # Diversificadas
        'BRK.B', 'COST', 'NFLX', 'NKE', 'YUM', 'KKR', 'PLD'
    ]
    
    def __init__(self):
        self.results = []
    
    def screen_symbol(self, symbol: str, verbose: bool = False) -> Tuple[bool, ScreenedStock, str]:
        """
        Analiza una acción individual según criterios Buffett.
        Retorna: (passed, ScreenedStock, reason_if_failed)
        """
        try:
            # Descargar datos
            ticker = yf.Ticker(symbol)
            prices = ticker.history(period="3y", interval="1d", auto_adjust=False)
            
            try:
                info = ticker.info
            except:
                info = {}
            
            try:
                income = ticker.income_stmt
            except:
                income = pd.DataFrame()
            
            try:
                balance = ticker.balance_sheet
            except:
                balance = pd.DataFrame()
            
            try:
                cashflow = ticker.cashflow
            except:
                cashflow = pd.DataFrame()
            
            if prices.empty:
                return False, None, f"{symbol}: No hay datos de precio"
            
            # Analizar
            analyzer = BuffettAnalyzer(info, income, balance, cashflow, prices)
            summary = analyzer.get_executive_summary()
            full = summary['full_analysis']
            
            # Criterios de screening (bastante selectivos, style Buffett)
            passed = True
            reasons = []
            failures = []
            
            # 1. Debe ser Monopolio o Negocio Diferenciado (no commodity)
            if full['B']['business_type'] not in ['MONOPOLIO CONSUMIDOR', 'NEGOCIO DIFERENCIADO']:
                failures.append(f"Negocio commodity (clasificado como {full['B']['business_type']})")
                passed = False
            else:
                reasons.append(f"✅ {full['B']['business_type']}")
            
            # 2. ROE debe ser > 10% (consistente y alto)
            if is_valid(analyzer.roe):
                if analyzer.roe > 0.12:
                    reasons.append(f"✅ ROE fuerte: {analyzer.roe:.1%}")
                elif analyzer.roe > 0.10:
                    reasons.append(f"✅ ROE adecuado: {analyzer.roe:.1%}")
                else:
                    failures.append(f"ROE bajo: {analyzer.roe:.1%}")
                    passed = False
            else:
                failures.append("ROE no disponible")
            
            # 3. Deuda prudente (D/E < 1.5)
            if is_valid(analyzer.debt_to_equity):
                if analyzer.debt_to_equity < 1.0:
                    reasons.append(f"✅ Deuda conservadora: D/E {analyzer.debt_to_equity:.2f}")
                elif analyzer.debt_to_equity < 1.5:
                    reasons.append(f"✅ Deuda moderada: D/E {analyzer.debt_to_equity:.2f}")
                else:
                    failures.append(f"Deuda elevada: D/E {analyzer.debt_to_equity:.2f}")
                    passed = False
            
            # 4. Márgenes netos > 5%
            if is_valid(analyzer.profit_margin):
                if analyzer.profit_margin > 0.10:
                    reasons.append(f"✅ Márgenes saludables: {analyzer.profit_margin:.1%}")
                elif analyzer.profit_margin > 0.05:
                    reasons.append(f"✅ Márgenes aceptables: {analyzer.profit_margin:.1%}")
                else:
                    failures.append(f"Márgenes bajos: {analyzer.profit_margin:.1%}")
                    passed = False
            else:
                failures.append("Márgenes no disponibles")
            
            # 5. Valuación: PER < 25 o Initial Yield atractivo
            valuation_ok = False
            if is_valid(analyzer.trailing_pe):
                if analyzer.trailing_pe < 20:
                    reasons.append(f"✅ Valuación atractiva: PER {analyzer.trailing_pe:.1f}x")
                    valuation_ok = True
                elif analyzer.trailing_pe < 25:
                    reasons.append(f"✅ Valuación justa: PER {analyzer.trailing_pe:.1f}x")
                    valuation_ok = True
                else:
                    failures.append(f"PER elevado: {analyzer.trailing_pe:.1f}x")
                    passed = False
            
            if full['E']['initial_yield']:
                if full['E']['initial_yield'] > 0.06:
                    reasons.append(f"✅ Initial Yield atractivo: {full['E']['initial_yield']:.2%}")
                    valuation_ok = True
            
            if not valuation_ok and passed:
                # Tolerar un poco si resto es bueno
                pass
            
            # 6. TIR proyectada decente (> 10%)
            if summary.get('tir_projected'):
                tir = summary['tir_projected']
                if tir > 0.12:
                    reasons.append(f"✅ Retorno proyectado sólido: {tir:.1%}")
                elif tir > 0.08:
                    reasons.append(f"✅ Retorno proyectado moderado: {tir:.1%}")
                else:
                    # TIR muy baja, pero si todo lo demás es bueno, no descalificar
                    pass
            
            # 7. Puntaje BASE > 50% (calidad general)
            overall_pct = summary['percentage']
            if overall_pct < 40:
                failures.append(f"Puntaje BASE bajo: {overall_pct:.0f}%")
                passed = False
            
            # Si falló, retornar
            if not passed:
                reason = " | ".join(failures)
                return False, None, reason
            
            # Si pasó, crear objeto ScreenedStock
            score = summary['overall_score']
            max_score = summary['max_score']
            
            screened = ScreenedStock(
                symbol=symbol,
                score=score,
                max_score=max_score,
                reasons=reasons,
                price=analyzer.current_price or 0,
                sector=analyzer.sector or "N/D",
                business_type=full['B']['business_type'],
                moat=full['B']['moat_strength'],
                risk_profile="Moderado",  # Se asignará en radar_financiero con Gemini
                company_description=""  # Se asignará en radar_financiero con Gemini
            )
            
            return True, screened, None
        
        except Exception as e:
            return False, None, f"{symbol}: Error en análisis ({str(e)[:40]})"
    
    def screen_portfolio(self, symbols: List[str] = None, progress_callback=None) -> List[ScreenedStock]:
        """
        Screening de múltiples acciones.
        Retorna lista ordenada de acciones que pasaron el filter.
        """
        if symbols is None:
            symbols = self.QUALITY_CANDIDATES
        
        results = []
        total = len(symbols)
        
        for idx, symbol in enumerate(symbols):
            if progress_callback:
                progress_callback(f"Analizando {symbol}... ({idx+1}/{total})")
            
            passed, stock, reason = self.screen_symbol(symbol)
            
            if passed:
                results.append(stock)
        
        # Ordenar por puntaje descendente
        results.sort()
        
        return results
    
    def get_top_opportunities(self, num: int = 10, symbols: List[str] = None) -> List[Dict]:
        """
        Retorna las mejores oportunidades formateadas para mostrar.
        """
        screened = self.screen_portfolio(symbols)
        
        opportunities = []
        for stock in screened[:num]:
            opportunity = {
                'symbol': stock.symbol,
                'score': f"{stock.percentage:.0f}%",
                'price': f"${stock.price:.2f}" if stock.price > 0 else "N/D",
                'sector': stock.sector,
                'business_type': stock.business_type,
                'moat': stock.moat,
                'reasons': stock.reasons
            }
            opportunities.append(opportunity)
        
        return opportunities

def get_quick_recommendations() -> List[Dict]:
    """
    Función rápida que retorna oportunidades de inversión.
    Usado en la UI de Streamlit.
    """
    screener = BuffettScreener()
    
    # Usar subset más pequeño para velocidad (las más conocidas)
    quick_symbols = [
        'KO', 'PEP', 'V', 'MA', 'JNJ', 'AAPL', 'MSFT', 
        'WMT', 'HD', 'AMZN', 'BRK.B', 'PG', 'COST'
    ]
    
    return screener.get_top_opportunities(num=10, symbols=quick_symbols)
