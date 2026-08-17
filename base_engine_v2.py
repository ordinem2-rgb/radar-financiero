"""
Motor BASE Profesional - Análisis de Inversión Siguiendo Buffettología y Método BASE
Versión mejorada con análisis profundo, proyecciones de TIR y evaluación táctica.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime

def is_valid(v) -> bool:
    """Verifica si un valor es numérico válido."""
    return isinstance(v, (int, float, np.integer, np.floating)) and np.isfinite(v)

def safe_get(d: dict, key: str, default=None):
    """Obtiene un valor de un diccionario de forma segura."""
    try:
        return d.get(key, default)
    except:
        return default

class BuffettAnalyzer:
    """
    Analizador profesional de inversiones basado en Buffettología y Método BASE.
    Fusiona análisis fundamental profundo con proyecciones cuantitativas rigurosas.
    """
    
    def __init__(self, ticker_info: dict, income_stmt: pd.DataFrame, 
                 balance_sheet: pd.DataFrame, cashflow_stmt: pd.DataFrame, 
                 prices: pd.DataFrame):
        self.info = ticker_info or {}
        self.income = income_stmt if isinstance(income_stmt, pd.DataFrame) else pd.DataFrame()
        self.balance = balance_sheet if isinstance(balance_sheet, pd.DataFrame) else pd.DataFrame()
        self.cashflow = cashflow_stmt if isinstance(cashflow_stmt, pd.DataFrame) else pd.DataFrame()
        self.prices = prices if isinstance(prices, pd.DataFrame) else pd.DataFrame()
        
        # Datos clave extraídos
        self.symbol = safe_get(self.info, 'symbol', 'N/D')
        self.sector = safe_get(self.info, 'sector', 'N/D')
        self.industry = safe_get(self.info, 'industry', 'N/D')
        self.current_price = safe_get(self.info, 'currentPrice', safe_get(self.info, 'regularMarketPrice'))
        
        # Fundamentales
        self.eps = safe_get(self.info, 'trailingEps')
        self.eps_forward = safe_get(self.info, 'forwardEps')
        self.shares = safe_get(self.info, 'sharesOutstanding')
        self.market_cap = safe_get(self.info, 'marketCap')
        
        # Rentabilidad
        self.roe = safe_get(self.info, 'returnOnEquity')
        self.roa = safe_get(self.info, 'returnOnAssets')
        self.roic = safe_get(self.info, 'returnOnCapital')
        
        # Valuación
        self.trailing_pe = safe_get(self.info, 'trailingPE')
        self.forward_pe = safe_get(self.info, 'forwardPE')
        self.pb_ratio = safe_get(self.info, 'priceToBook')
        self.ps_ratio = safe_get(self.info, 'priceToSalesTrailing12Months')
        self.pcf_ratio = safe_get(self.info, 'priceToBook')  # Aproximación
        
        # Márgenes
        self.profit_margin = safe_get(self.info, 'profitMargins')
        self.operating_margin = safe_get(self.info, 'operatingMargins')
        self.gross_margin = safe_get(self.info, 'grossMargins')
        
        # Flujos y Financiamiento
        self.revenue = safe_get(self.info, 'totalRevenue')
        self.net_income = safe_get(self.info, 'netIncome')
        self.fcf = safe_get(self.info, 'freeCashflow')
        self.operating_cf = safe_get(self.info, 'operatingCashflow')
        self.dividend = safe_get(self.info, 'dividendRate', 0)
        self.dividend_yield = safe_get(self.info, 'dividendYield', 0)
        
        # Deuda
        self.total_debt = safe_get(self.info, 'totalDebt')
        self.short_debt = safe_get(self.info, 'shortTermDebt')
        self.long_debt = safe_get(self.info, 'longTermDebt')
        self.debt_to_equity = safe_get(self.info, 'debtToEquity')
        self.current_ratio = safe_get(self.info, 'currentRatio')
        
        # Patrimonio
        assets = safe_get(self.info, 'totalAssets')
        liabilities = safe_get(self.info, 'totalLiabilities')
        if is_valid(assets) and is_valid(liabilities):
            self.equity = assets - liabilities
        else:
            self.equity = None
            
        self.book_value = safe_get(self.info, 'bookValue')
    
    # ============================================================================
    # HISTÓRICOS Y TENDENCIAS
    # ============================================================================
    
    def get_historical_data(self) -> Dict:
        """Extrae datos históricos de 7-10 años."""
        history = {
            'eps': {},
            'revenue': {},
            'net_income': {},
            'fcf': {},
            'roe': {}
        }
        
        try:
            # EPS Histórico
            if 'Net Income' in self.income.index or 'Net Income Common Stockholders' in self.income.index:
                ni_key = 'Net Income' if 'Net Income' in self.income.index else 'Net Income Common Stockholders'
                ni_row = self.income.loc[ni_key]
                sh_key = 'Shares Outstanding' if 'Shares Outstanding' in self.income.index else None
                
                if sh_key and sh_key in self.income.index:
                    sh_row = self.income.loc[sh_key]
                    for date in ni_row.index[:10]:  # Últimos 10 años
                        ni = ni_row[date]
                        sh = sh_row[date]
                        if is_valid(ni) and is_valid(sh) and sh > 0:
                            year = date.year if hasattr(date, 'year') else int(str(date)[:4])
                            history['eps'][year] = ni / sh
            
            # Ingresos Históricos
            if 'Total Revenue' in self.income.index:
                rev_row = self.income.loc['Total Revenue']
                for date in rev_row.index[:10]:
                    rev = rev_row[date]
                    if is_valid(rev):
                        year = date.year if hasattr(date, 'year') else int(str(date)[:4])
                        history['revenue'][year] = rev
            
            # Beneficio Neto Histórico
            for ni_key in ['Net Income', 'Net Income Common Stockholders']:
                if ni_key in self.income.index:
                    ni_row = self.income.loc[ni_key]
                    for date in ni_row.index[:10]:
                        ni = ni_row[date]
                        if is_valid(ni):
                            year = date.year if hasattr(date, 'year') else int(str(date)[:4])
                            history['net_income'][year] = ni
                    break
        except Exception:
            pass
        
        return history
    
    def calculate_eps_growth_rate(self) -> Optional[Tuple[float, int]]:
        """Calcula la tasa de crecimiento de EPS histórico (CAGR)."""
        history = self.get_historical_data()
        eps_hist = history['eps']
        
        if len(eps_hist) < 2:
            return None
        
        years = sorted(eps_hist.keys())
        eps_first = eps_hist[years[0]]
        eps_last = eps_hist[years[-1]]
        
        if eps_first <= 0 or eps_last <= 0:
            return None
        
        n_years = years[-1] - years[0]
        if n_years <= 0:
            return None
        
        cagr = (eps_last / eps_first) ** (1 / n_years) - 1
        return (cagr, n_years) if is_valid(cagr) else None
    
    def evaluate_eps_consistency(self) -> Tuple[bool, str, float]:
        """
        Evalúa la consistencia y predictibilidad del EPS histórico (7-10 años).
        Retorna (es_predecible, descripción, porcentaje_años_positivos)
        """
        history = self.get_historical_data()
        eps_hist = history['eps']
        
        if len(eps_hist) < 3:
            return False, "Datos históricos insuficientes (< 3 años)", 0.0
        
        years = sorted(eps_hist.keys())
        eps_values = [eps_hist[y] for y in years]
        
        positive_years = sum(1 for e in eps_values if e > 0)
        pct_positive = positive_years / len(eps_values)
        
        # Evaluar volatilidad
        if pct_positive >= 0.8:
            description = "EPS consistentemente positivo (80%+ años positivos)"
            is_predictable = True
        elif pct_positive >= 0.6:
            description = "EPS moderadamente consistente (60-80% años positivos)"
            is_predictable = False
        else:
            description = "EPS impredecible o volátil (< 60% años positivos)"
            is_predictable = False
        
        return is_predictable, description, pct_positive
    
    # ============================================================================
    # BLOQUE B: BASE DEL NEGOCIO (MONOPOLIO DE CONSUMIDOR)
    # ============================================================================
    
    def analyze_b_business_deep(self) -> Dict:
        """
        Análisis profundo B: Determina si es Monopolio de Consumidor o Commodity.
        Sigue preguntas de Buffettología.
        """
        result = {
            'score': 0,
            'max_score': 10,
            'signals': [],
            'concerns': [],
            'questions': [],
            'business_type': 'DESCONOCIDO',
            'moat_strength': 'Débil'
        }
        
        # 1. ¿Marca fuerte con lealtad de consumo?
        # Indicadores proxy: P/S bajo, márgenes altos, ROE alto
        if is_valid(self.ps_ratio) and self.ps_ratio < 1.0:
            result['score'] += 2
            result['signals'].append(f"P/S bajo ({self.ps_ratio:.2f}x): posible marca fuerte")
        elif is_valid(self.ps_ratio) and self.ps_ratio < 2.0:
            result['score'] += 1
            result['signals'].append(f"P/S moderado ({self.ps_ratio:.2f}x)")
        else:
            if is_valid(self.ps_ratio):
                result['concerns'].append(f"P/S elevado ({self.ps_ratio:.2f}x): menor poder de marca")
        
        # 2. ¿Modelo de negocio fácil de entender?
        sector_simple = self.sector in ['Consumer Cyclical', 'Consumer Defensive', 'Utilities', 
                                        'Healthcare', 'Consumer Staples', 'Industrials']
        if sector_simple:
            result['score'] += 2
            result['signals'].append(f"Negocio simple de entender: {self.sector}")
        else:
            result['concerns'].append(f"Sector complejo o de alta tecnología: {self.sector}")
        
        # 3. ¿Inmune a obsolescencia tecnológica?
        tech_vulnerable = self.sector in ['Information Technology', 'Technology']
        if not tech_vulnerable:
            result['score'] += 2
            result['signals'].append("Negocio no vulnerable a obsolescencia tecnológica rápida")
        else:
            result['concerns'].append("Sector tecnológico: alto riesgo de obsolescencia")
        
        # 4. ¿Poder de fijación de precios? (Márgenes brutos/operativos altos y estables)
        if is_valid(self.gross_margin) and self.gross_margin > 0.40:
            result['score'] += 2
            result['signals'].append(f"Margen bruto alto ({self.gross_margin:.1%}): poder de precios")
        elif is_valid(self.gross_margin) and self.gross_margin > 0.25:
            result['score'] += 1
            result['signals'].append(f"Margen bruto moderado ({self.gross_margin:.1%})")
        else:
            if is_valid(self.gross_margin):
                result['concerns'].append(f"Margen bruto bajo ({self.gross_margin:.1%}): presión en precios")
        
        # 5. ¿Crecimiento de ingresos (indicador de demanda)
        growth_result = self.calculate_eps_growth_rate()
        if growth_result:
            eps_growth, years = growth_result
            if eps_growth > 0.12:
                result['score'] += 1
                result['signals'].append(f"Crecimiento sólido ({eps_growth:.1%} CAGR): demanda resiliente")
            elif eps_growth > 0:
                result['signals'].append(f"Crecimiento modesto ({eps_growth:.1%} CAGR)")
            else:
                result['concerns'].append(f"Crecimiento negativo: negocio maduro o declinante")
        
        # Clasificación de Moat (foso económico)
        if result['score'] >= 8:
            result['business_type'] = 'MONOPOLIO CONSUMIDOR'
            result['moat_strength'] = 'Fuerte'
        elif result['score'] >= 5:
            result['business_type'] = 'NEGOCIO DIFERENCIADO'
            result['moat_strength'] = 'Moderado'
        else:
            result['business_type'] = 'COMMODITY'
            result['moat_strength'] = 'Débil'
        
        result['questions'].extend([
            "¿La marca tiene fidelización real o es intercambiable?",
            "¿Qué tan resiliente es ante competencia de nuevos entrantes?",
            "¿Existen efectos de red o costos de cambio?",
            "¿Es la empresa dependiente de líderes (Amazon, Google) para distribución?"
        ])
        
        return result
    
    # ============================================================================
    # BLOQUE A: ADMINISTRACIÓN (ASIGNACIÓN DE CAPITAL)
    # ============================================================================
    
    def analyze_a_administration_deep(self) -> Dict:
        """
        Análisis profundo A: Eficiencia en asignación de capital.
        Enfoque: Retorno sobre beneficios retenidos, recompras, deuda.
        """
        result = {
            'score': 0,
            'max_score': 10,
            'signals': [],
            'concerns': [],
            'questions': [],
            'retorn_retained_earnings': None,
            'buyback_signal': 'Desconocido',
            'debt_assessment': 'Normal'
        }
        
        # 1. Retorno sobre beneficios retenidos (15% umbral de Buffett)
        growth_result = self.calculate_eps_growth_rate()
        if growth_result and self.eps and self.dividend:
            eps_growth, years = growth_result
            retention_rate = 1.0 - (self.dividend / self.eps) if self.eps > 0 else 0
            
            if retention_rate > 0:
                # RRE = EPS Growth / Retention Rate
                roe_on_retained = eps_growth / retention_rate
                result['retorn_retained_earnings'] = roe_on_retained
                
                if roe_on_retained > 0.15:
                    result['score'] += 3
                    result['signals'].append(f"Excelente ROE sobre beneficios retenidos: {roe_on_retained:.1%}")
                elif roe_on_retained > 0.10:
                    result['score'] += 2
                    result['signals'].append(f"Buen ROE sobre beneficios retenidos: {roe_on_retained:.1%}")
                elif roe_on_retained > 0.05:
                    result['score'] += 1
                    result['signals'].append(f"Moderado ROE sobre beneficios retenidos: {roe_on_retained:.1%}")
                else:
                    result['concerns'].append(f"Débil ROE sobre beneficios retenidos: {roe_on_retained:.1%}")
        
        # 2. Crecimiento de EPS limpio
        if growth_result:
            eps_growth, years = growth_result
            if eps_growth > 0.15:
                result['score'] += 2
                result['signals'].append(f"Crecimiento de EPS sólido ({eps_growth:.1%})")
            elif eps_growth > 0.08:
                result['score'] += 1
                result['signals'].append(f"Crecimiento de EPS moderado ({eps_growth:.1%})")
            else:
                result['concerns'].append(f"Crecimiento de EPS débil ({eps_growth:.1%})")
        
        # 3. Recompras de acciones (buyback)
        if is_valid(self.shares):
            # Si shares ha bajado en historia, hay recompras
            history = self.get_historical_data()
            eps_hist = history['eps']
            if len(eps_hist) >= 2:
                years_eps = sorted(eps_hist.keys())
                eps_first = eps_hist[years_eps[0]]
                eps_last = eps_hist[years_eps[-1]]
                
                # Si EPS creció más que Net Income creció, hubo recompras efectivas
                if eps_first > 0 and eps_last > 0:
                    eps_growth_rate = (eps_last / eps_first) ** (1 / (years_eps[-1] - years_eps[0])) - 1
                    
                    ni_hist = history['net_income']
                    if ni_hist:
                        ni_years = sorted(ni_hist.keys())
                        ni_first = ni_hist[ni_years[0]]
                        ni_last = ni_hist[ni_years[-1]]
                        if ni_first > 0 and ni_last > 0:
                            ni_growth_rate = (ni_last / ni_first) ** (1 / (ni_years[-1] - ni_years[0])) - 1
                            
                            if eps_growth_rate > ni_growth_rate + 0.02:
                                result['score'] += 1
                                result['signals'].append("Recompras de acciones estratégicas detectadas")
                                result['buyback_signal'] = 'Sí - Redujo acciones en circulación'
                            else:
                                result['buyback_signal'] = 'No evidente o dilución'
        
        # 4. Deuda prudente (máx 2-3x Net Income)
        if is_valid(self.total_debt) and is_valid(self.net_income) and self.net_income > 0:
            debt_to_income = self.total_debt / self.net_income
            if debt_to_income < 2.0:
                result['score'] += 2
                result['signals'].append(f"Deuda prudente ({debt_to_income:.1f}x ingresos netos)")
                result['debt_assessment'] = 'Conservadora'
            elif debt_to_income < 3.0:
                result['score'] += 1
                result['signals'].append(f"Deuda moderada ({debt_to_income:.1f}x ingresos netos)")
                result['debt_assessment'] = 'Normal'
            else:
                result['concerns'].append(f"Deuda elevada ({debt_to_income:.1f}x ingresos netos)")
                result['debt_assessment'] = 'Agresiva'
        elif is_valid(self.debt_to_equity):
            if self.debt_to_equity < 0.5:
                result['score'] += 2
                result['signals'].append(f"D/E bajo ({self.debt_to_equity:.2f})")
                result['debt_assessment'] = 'Conservadora'
            elif self.debt_to_equity < 1.0:
                result['score'] += 1
                result['signals'].append(f"D/E moderado ({self.debt_to_equity:.2f})")
            else:
                result['concerns'].append(f"D/E elevado ({self.debt_to_equity:.2f})")
                result['debt_assessment'] = 'Agresiva'
        
        # 5. Consistencia de ganancias
        is_predictable, description, pct_positive = self.evaluate_eps_consistency()
        if pct_positive > 0.8:
            result['score'] += 1
            result['signals'].append(description)
        elif pct_positive > 0.6:
            result['concerns'].append(description)
        else:
            result['concerns'].append(description)
        
        result['questions'].extend([
            "¿La directiva compra acciones solo cuando el precio es bajo (valor)",
            "¿Se reinvierten adecuadamente los beneficios retenidos?",
            "¿La deuda se usa para negocios productivos o para financiar operaciones?"
        ])
        
        return result
    
    # ============================================================================
    # BLOQUE S: SALUD FINANCIERA
    # ============================================================================
    
    def analyze_s_health_deep(self) -> Dict:
        """
        Análisis profundo S: Solidez financiera y estabilidad.
        Énfasis en consistencia histórica, ROE, márgenes.
        """
        result = {
            'score': 0,
            'max_score': 10,
            'signals': [],
            'concerns': [],
            'questions': [],
            'roe_quality': 'Desconocido',
            'margin_trend': 'Desconocido'
        }
        
        # 1. ROE consistentemente alto
        if is_valid(self.roe):
            if self.roe > 0.18:
                result['score'] += 3
                result['signals'].append(f"ROE excepcional ({self.roe:.1%}): valor superior")
                result['roe_quality'] = 'Excepcional'
            elif self.roe > 0.12:
                result['score'] += 2
                result['signals'].append(f"ROE sólido ({self.roe:.1%}): empresa de calidad")
                result['roe_quality'] = 'Bueno'
            elif self.roe > 0.08:
                result['score'] += 1
                result['signals'].append(f"ROE moderado ({self.roe:.1%})")
                result['roe_quality'] = 'Moderado'
            else:
                result['concerns'].append(f"ROE bajo ({self.roe:.1%}): retorno insuficiente")
                result['roe_quality'] = 'Débil'
        
        # 2. Márgenes estables/en expansión
        if is_valid(self.profit_margin):
            if self.profit_margin > 0.15:
                result['score'] += 2
                result['signals'].append(f"Margen neto alto ({self.profit_margin:.1%})")
                result['margin_trend'] = 'Bueno'
            elif self.profit_margin > 0.07:
                result['score'] += 1
                result['signals'].append(f"Margen neto moderado ({self.profit_margin:.1%})")
                result['margin_trend'] = 'Normal'
            else:
                result['concerns'].append(f"Margen neto bajo ({self.profit_margin:.1%})")
                result['margin_trend'] = 'Débil'
        
        if is_valid(self.operating_margin):
            if self.operating_margin > 0.15:
                result['score'] += 1
                result['signals'].append(f"Margen operativo fuerte ({self.operating_margin:.1%})")
            elif self.operating_margin < 0.05:
                result['concerns'].append(f"Margen operativo débil ({self.operating_margin:.1%})")
        
        # 3. EPS Consistencia (80%+ años positivos)
        is_predictable, description, pct_positive = self.evaluate_eps_consistency()
        if pct_positive > 0.8:
            result['score'] += 2
            result['signals'].append(description)
        elif pct_positive > 0.6:
            result['score'] += 1
            result['signals'].append(description)
        else:
            result['concerns'].append(description)
        
        # 4. Flujo de caja positivo
        if is_valid(self.operating_cf) and self.operating_cf > 0:
            result['score'] += 2
            result['signals'].append("Flujo de caja operativo positivo (caja real, no contable)")
        else:
            result['concerns'].append("Flujo de caja operativo débil o negativo")
        
        if is_valid(self.fcf) and self.fcf > 0:
            result['score'] += 1
            result['signals'].append(f"Flujo de caja libre positivo (FCF > 0)")
        else:
            result['concerns'].append("FCF negativo o insuficiente")
        
        # 5. Cobertura de deuda (EBIT / Intereses, aproximado via ROA)
        if is_valid(self.roa):
            if self.roa > 0.08:
                result['score'] += 1
                result['signals'].append(f"ROA sólido ({self.roa:.1%}): rentabilidad sobre activos")
            else:
                result['concerns'].append(f"ROA bajo ({self.roa:.1%})")
        
        result['questions'].extend([
            "¿Las ganancias son reales (flujo de caja) o solo contables?",
            "¿Hay consistencia en márgenes durante ciclos económicos?",
            "¿La deuda es pagable con los flujos actuales?"
        ])
        
        return result
    
    # ============================================================================
    # BLOQUE E: EVALUACIÓN CUANTITATIVA DEL PRECIO
    # ============================================================================
    
    def calculate_initial_yield(self) -> Optional[float]:
        """
        Test de la Obligación con Cupón en Expansión.
        Initial Yield = EPS / Price
        Se compara con rendimiento de bonos soberanos (~2-3%).
        """
        if is_valid(self.eps) and is_valid(self.current_price) and self.current_price > 0:
            return self.eps / self.current_price
        return None
    
    def analyze_e_valuation_deep(self) -> Dict:
        """
        Análisis profundo E: Evaluación cuantitativa del precio.
        - Initial Yield vs bonos soberanos
        - Múltiplos comparados (histórico, industria, mercado)
        - Proyección TIR a 10 años
        - Precio máximo de compra para 15% TIR
        """
        result = {
            'score': 0,
            'max_score': 10,
            'signals': [],
            'concerns': [],
            'questions': [],
            'initial_yield': None,
            'valuation_level': 'Desconocido',
            'tir_projected': None,
            'target_price_15pct': None,
            'margin_of_safety': 'Desconocido'
        }
        
        # 1. Initial Yield (EPS/Price)
        initial_yield = self.calculate_initial_yield()
        result['initial_yield'] = initial_yield
        
        if initial_yield:
            # Comparar con bono soberano (~2.5% actual)
            us_bond_yield = 0.025
            if initial_yield > us_bond_yield + 0.02:
                result['score'] += 3
                result['signals'].append(f"Initial Yield atractivo ({initial_yield:.2%} >> bono)")
            elif initial_yield > us_bond_yield:
                result['score'] += 1
                result['signals'].append(f"Initial Yield razonable ({initial_yield:.2%} vs bono)")
            else:
                result['concerns'].append(f"Initial Yield débil ({initial_yield:.2%} < bono soberano)")
        
        # 2. PER actual vs histórico, industria, mercado
        if is_valid(self.trailing_pe):
            # Comparativas
            # Industria promedio (referencia aproximada)
            industry_avg_pe = self._get_industry_avg_pe()
            market_pe = 22  # S&P 500 aproximado
            
            if self.trailing_pe < 0:
                result['concerns'].append("PER negativo: empresa en pérdidas")
            elif self.trailing_pe < 15:
                result['score'] += 2
                result['signals'].append(f"PER bajo ({self.trailing_pe:.1f}x) - Potencialmente atractivo")
                result['valuation_level'] = 'Barata'
            elif self.trailing_pe < 20:
                result['score'] += 1
                result['signals'].append(f"PER moderado ({self.trailing_pe:.1f}x) - Justo")
                result['valuation_level'] = 'Justa'
            elif self.trailing_pe < 30:
                result['signals'].append(f"PER elevado ({self.trailing_pe:.1f}x) - Caro")
                result['valuation_level'] = 'Cara'
            else:
                result['concerns'].append(f"PER muy elevado ({self.trailing_pe:.1f}x)")
                result['valuation_level'] = 'Muy Cara'
        
        # 3. P/FCF (Precio / FCF)
        if is_valid(self.fcf) and is_valid(self.market_cap) and self.fcf > 0:
            pcf = self.market_cap / self.fcf
            if pcf < 12:
                result['score'] += 1
                result['signals'].append(f"Precio/FCF atractivo ({pcf:.1f}x)")
            elif pcf > 20:
                result['concerns'].append(f"Precio/FCF elevado ({pcf:.1f}x)")
        
        # 4. P/S (Precio / Ventas)
        if is_valid(self.ps_ratio):
            if self.ps_ratio < 1.0:
                result['score'] += 1
                result['signals'].append(f"P/S muy bajo ({self.ps_ratio:.2f}x)")
            elif self.ps_ratio > 3.0:
                result['concerns'].append(f"P/S elevado ({self.ps_ratio:.2f}x)")
        
        # 5. Proyección TIR a 10 años
        tir_proj = self.project_10year_return()
        result['tir_projected'] = tir_proj
        
        if tir_proj:
            if tir_proj > 0.15:
                result['score'] += 2
                result['signals'].append(f"TIR proyectada atractiva ({tir_proj:.1%} > 15%)")
            elif tir_proj > 0.10:
                result['score'] += 1
                result['signals'].append(f"TIR proyectada moderada ({tir_proj:.1%})")
            else:
                result['concerns'].append(f"TIR proyectada débil ({tir_proj:.1%} < 15%)")
            
            # Calcular precio objetivo para 15% TIR
            target_price = self.calculate_target_price_for_tir(0.15)
            result['target_price_15pct'] = target_price
            
            if target_price and self.current_price and self.current_price > 0:
                margin_of_safety = (target_price / self.current_price) - 1.0
                result['margin_of_safety'] = margin_of_safety
                
                if margin_of_safety > 0.25:
                    result['signals'].append(f"Margen de seguridad excelente ({margin_of_safety:.0%})")
                elif margin_of_safety > 0.10:
                    result['signals'].append(f"Margen de seguridad bueno ({margin_of_safety:.0%})")
                elif margin_of_safety > 0:
                    result['signals'].append(f"Margen de seguridad pequeño ({margin_of_safety:.0%})")
                else:
                    result['concerns'].append(f"Precio sobre objetivo: margin negativo")
        
        result['questions'].extend([
            "¿El múltiplo actual es justo comparado con sector e histórico?",
            "¿La TIR proyectada justifica el riesgo?",
            "¿Existe margen de seguridad (precio actual << valor intrínseco)?"
        ])
        
        return result
    
    def project_10year_return(self) -> Optional[float]:
        """
        Proyecta la TIR esperada a 10 años usando:
        1. EPS proyectado = EPS actual * (1 + crecimiento)^10
        2. Precio proyectado = EPS * PER promedio
        3. TIR = (Precio_futuro / Precio_actual)^(1/10) - 1
        """
        if not (is_valid(self.eps) and is_valid(self.current_price) and self.current_price > 0):
            return None
        
        # Crecimiento esperado (histórico o forward)
        growth_result = self.calculate_eps_growth_rate()
        if growth_result:
            eps_growth, _ = growth_result
            # Conservador: reducir crecimiento futuro vs histórico
            expected_growth = eps_growth * 0.75
        else:
            expected_growth = 0.08  # Supuesto por defecto
        
        # PER futuro (promedio histórico o conservador)
        if is_valid(self.trailing_pe):
            pe_future = max(self.trailing_pe * 0.85, 12)  # No caer bajo 12
        else:
            pe_future = 16  # Supuesto
        
        # Proyección
        years = 10
        eps_future = self.eps * ((1 + expected_growth) ** years)
        price_future = eps_future * pe_future
        
        # TIR
        if price_future > 0:
            tir = (price_future / self.current_price) ** (1 / years) - 1
            return tir if is_valid(tir) else None
        
        return None
    
    def calculate_target_price_for_tir(self, target_tir: float = 0.15) -> Optional[float]:
        """
        Calcula el precio máximo que permite alcanzar una TIR objetivo (ej. 15%).
        Inversamente: Price_target = Price_future / (1 + target_tir)^10
        """
        if not (is_valid(self.eps) and is_valid(self.current_price) and self.current_price > 0):
            return None
        
        growth_result = self.calculate_eps_growth_rate()
        if growth_result:
            eps_growth, _ = growth_result
            expected_growth = eps_growth * 0.75
        else:
            expected_growth = 0.08
        
        if is_valid(self.trailing_pe):
            pe_future = max(self.trailing_pe * 0.85, 12)
        else:
            pe_future = 16
        
        years = 10
        eps_future = self.eps * ((1 + expected_growth) ** years)
        price_future = eps_future * pe_future
        
        target_price = price_future / ((1 + target_tir) ** years)
        return target_price if is_valid(target_price) else None
    
    def _get_industry_avg_pe(self) -> Optional[float]:
        """Retorna PER promedio aproximado por industria."""
        industry_pes = {
            'Technology': 30,
            'Healthcare': 22,
            'Financials': 15,
            'Consumer Cyclical': 18,
            'Consumer Defensive': 20,
            'Utilities': 16,
            'Industrials': 18,
            'Materials': 14,
            'Energy': 12,
            'Real Estate': 16
        }
        return industry_pes.get(self.sector, 22)
    
    # ============================================================================
    # ANÁLISIS TÉCNICO TÁCTICO INTEGRADO
    # ============================================================================
    
    def analyze_technical_tactical(self) -> Dict:
        """
        Análisis técnico para optimizar punto de entrada/salida.
        """
        result = {
            'score': 0,
            'max_score': 5,
            'signals': [],
            'concerns': [],
            'trend': 'Desconocido',
            'support': 'N/D',
            'resistance': 'N/D',
            'recommendation': 'Neutral'
        }
        
        if self.prices.empty:
            result['signals'].append("Datos de precio insuficientes")
            return result
        
        # Tendencia de largo plazo (MA 200)
        if 'MA200' in self.prices.columns:
            ma200 = self.prices['MA200'].iloc[-1]
            current = self.prices['Close'].iloc[-1]
            
            if pd.notna(ma200):
                if current > ma200 * 1.05:
                    result['score'] += 2
                    result['signals'].append(f"Tendencia alcista: Precio ({current:.2f}) >> MA200 ({ma200:.2f})")
                    result['trend'] = 'Alcista'
                elif current < ma200 * 0.95:
                    result['concerns'].append(f"Tendencia bajista: Precio ({current:.2f}) << MA200 ({ma200:.2f})")
                    result['trend'] = 'Bajista'
                else:
                    result['signals'].append("Tendencia lateral/consolidación")
                    result['trend'] = 'Lateral'
        
        # RSI (Nivel de entrada/salida)
        if 'RSI' in self.prices.columns:
            rsi = self.prices['RSI'].iloc[-1]
            if pd.notna(rsi):
                if rsi < 30:
                    result['score'] += 2
                    result['signals'].append(f"RSI sobreventa ({rsi:.0f}): potencial entrada")
                elif rsi > 70:
                    result['concerns'].append(f"RSI sobrecompra ({rsi:.0f}): esperar corrección")
                else:
                    result['signals'].append(f"RSI neutral ({rsi:.0f})")
        
        # MACD
        if 'MACD' in self.prices.columns and 'MACD_SIGNAL' in self.prices.columns:
            macd = self.prices['MACD'].iloc[-1]
            signal = self.prices['MACD_SIGNAL'].iloc[-1]
            if pd.notna(macd) and pd.notna(signal):
                if macd > signal:
                    result['signals'].append("MACD positivo: momento alcista")
                else:
                    result['concerns'].append("MACD negativo: momento bajista")
        
        # Recomendación táctica
        if result['trend'] == 'Alcista' and result['score'] >= 2:
            result['recommendation'] = 'Compra en correcciones leves (RSI 30-40)'
        elif result['trend'] == 'Bajista':
            result['recommendation'] = 'Esperar quiebre de MA200 o DCA lento'
        else:
            result['recommendation'] = 'Neutral - Esperar confirmación de tendencia'
        
        return result
    
    # ============================================================================
    # SÍNTESIS TOTAL
    # ============================================================================
    
    def generate_full_analysis(self) -> Dict:
        """Genera análisis profesional completo con todos los bloques."""
        return {
            'B': self.analyze_b_business_deep(),
            'A': self.analyze_a_administration_deep(),
            'S': self.analyze_s_health_deep(),
            'E': self.analyze_e_valuation_deep(),
            'Technical': self.analyze_technical_tactical(),
            'metadata': {
                'symbol': self.symbol,
                'sector': self.sector,
                'industry': self.industry,
                'price': self.current_price,
                'timestamp': datetime.now().isoformat()
            }
        }
    
    def get_executive_summary(self) -> Dict:
        """Genera un resumen ejecutivo profesional."""
        full = self.generate_full_analysis()
        
        total_score = sum(full[k]['score'] for k in ['B', 'A', 'S', 'E'])
        max_score = sum(full[k]['max_score'] for k in ['B', 'A', 'S', 'E'])
        percentage = (total_score / max_score * 100) if max_score > 0 else 0
        
        return {
            'overall_score': total_score,
            'max_score': max_score,
            'percentage': percentage,
            'business_type': full['B']['business_type'],
            'moat_strength': full['B']['moat_strength'],
            'tir_projected': full['E']['tir_projected'],
            'target_price_15pct': full['E']['target_price_15pct'],
            'valuation_level': full['E']['valuation_level'],
            'trend': full['Technical']['trend'],
            'recommendation': full['Technical']['recommendation'],
            'full_analysis': full
        }
