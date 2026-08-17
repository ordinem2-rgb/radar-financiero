"""
Motor BASE para análisis fundamental de acciones y ETFs.
Método BASE: Business, Administration, Salud, Evaluation.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional

def is_valid(v) -> bool:
    """Verifica si un valor es numérico válido."""
    return isinstance(v, (int, float, np.integer, np.floating)) and np.isfinite(v)

def safe_get(d: dict, key: str, default=None):
    """Obtiene un valor de un diccionario de forma segura."""
    try:
        return d.get(key, default)
    except:
        return default

class BASEAnalyzer:
    """Analiza un activo usando el Método BASE."""
    
    def __init__(self, ticker_info: dict, income_stmt: pd.DataFrame, 
                 balance_sheet: pd.DataFrame, cashflow_stmt: pd.DataFrame, 
                 prices: pd.DataFrame):
        self.info = ticker_info or {}
        self.income = income_stmt if isinstance(income_stmt, pd.DataFrame) else pd.DataFrame()
        self.balance = balance_sheet if isinstance(balance_sheet, pd.DataFrame) else pd.DataFrame()
        self.cashflow = cashflow_stmt if isinstance(cashflow_stmt, pd.DataFrame) else pd.DataFrame()
        self.prices = prices if isinstance(prices, pd.DataFrame) else pd.DataFrame()
        
        # Extraer datos clave
        self.current_price = safe_get(self.info, 'currentPrice', safe_get(self.info, 'regularMarketPrice'))
        self.eps = safe_get(self.info, 'trailingEps')
        self.shares = safe_get(self.info, 'sharesOutstanding')
        self.market_cap = safe_get(self.info, 'marketCap')
        self.roe = safe_get(self.info, 'returnOnEquity')
        self.roe_annual = safe_get(self.info, 'returnOnCapital')
        self.trailing_pe = safe_get(self.info, 'trailingPE')
        self.forward_pe = safe_get(self.info, 'forwardPE')
        self.dividend = safe_get(self.info, 'dividendRate', 0)
        self.debt_to_equity = safe_get(self.info, 'debtToEquity')
        self.short_debt = safe_get(self.info, 'shortTermDebt')
        self.long_debt = safe_get(self.info, 'longTermDebt')
        self.total_debt = safe_get(self.info, 'totalDebt')
        self.pb_ratio = safe_get(self.info, 'priceToBook')
        self.ps_ratio = safe_get(self.info, 'priceToSalesTrailing12Months')
        self.profit_margin = safe_get(self.info, 'profitMargins')
        self.operating_margin = safe_get(self.info, 'operatingMargins')
        self.gross_margin = safe_get(self.info, 'grossMargins')
        self.fcf = safe_get(self.info, 'freeCashflow')
        self.operating_cf = safe_get(self.info, 'operatingCashflow')
        self.revenue = safe_get(self.info, 'totalRevenue')
        self.net_income = safe_get(self.info, 'netIncome')
        self.equity = safe_get(self.info, 'totalAssets') - safe_get(self.info, 'totalLiabilities', 0)
        
    def get_historical_eps(self) -> Dict[int, float]:
        """Extrae EPS histórico del estado de resultados."""
        eps_history = {}
        if self.income.empty:
            return eps_history
        
        try:
            if 'Net Income' in self.income.index:
                net_income_row = self.income.loc['Net Income']
            elif 'Net Income Common Stockholders' in self.income.index:
                net_income_row = self.income.loc['Net Income Common Stockholders']
            else:
                return eps_history
            
            if 'Shares Outstanding' in self.income.index:
                shares_row = self.income.loc['Shares Outstanding']
            else:
                return eps_history
            
            for date in net_income_row.index:
                ni = net_income_row[date]
                sh = shares_row[date]
                if is_valid(ni) and is_valid(sh) and sh > 0:
                    year = date.year if hasattr(date, 'year') else int(str(date)[:4])
                    eps_history[year] = ni / sh
        except Exception:
            pass
        
        return eps_history
    
    def get_historical_revenue(self) -> Dict[int, float]:
        """Extrae ingresos históricos."""
        revenue_history = {}
        if self.income.empty:
            return revenue_history
        
        try:
            if 'Total Revenue' in self.income.index:
                revenue_row = self.income.loc['Total Revenue']
                for date in revenue_row.index:
                    rev = revenue_row[date]
                    if is_valid(rev):
                        year = date.year if hasattr(date, 'year') else int(str(date)[:4])
                        revenue_history[year] = rev
        except Exception:
            pass
        
        return revenue_history
    
    def get_historical_net_income(self) -> Dict[int, float]:
        """Extrae beneficio neto histórico."""
        ni_history = {}
        if self.income.empty:
            return ni_history
        
        try:
            for row_name in ['Net Income', 'Net Income Common Stockholders']:
                if row_name in self.income.index:
                    ni_row = self.income.loc[row_name]
                    for date in ni_row.index:
                        ni = ni_row[date]
                        if is_valid(ni):
                            year = date.year if hasattr(date, 'year') else int(str(date)[:4])
                            ni_history[year] = ni
                    break
        except Exception:
            pass
        
        return ni_history
    
    def calculate_eps_growth(self) -> Optional[float]:
        """Calcula crecimiento anual promedio del EPS."""
        eps_hist = self.get_historical_eps()
        if len(eps_hist) < 2:
            return None
        
        years = sorted(eps_hist.keys())
        if len(years) < 2:
            return None
        
        eps_first = eps_hist[years[0]]
        eps_last = eps_hist[years[-1]]
        
        if eps_first <= 0 or eps_last <= 0:
            return None
        
        n_years = years[-1] - years[0]
        if n_years <= 0:
            return None
        
        cagr = (eps_last / eps_first) ** (1 / n_years) - 1
        return cagr if is_valid(cagr) else None
    
    def calculate_revenue_growth(self) -> Optional[float]:
        """Calcula crecimiento anual promedio de ingresos."""
        rev_hist = self.get_historical_revenue()
        if len(rev_hist) < 2:
            return None
        
        years = sorted(rev_hist.keys())
        if len(years) < 2:
            return None
        
        rev_first = rev_hist[years[0]]
        rev_last = rev_hist[years[-1]]
        
        if rev_first <= 0 or rev_last <= 0:
            return None
        
        n_years = years[-1] - years[0]
        if n_years <= 0:
            return None
        
        cagr = (rev_last / rev_first) ** (1 / n_years) - 1
        return cagr if is_valid(cagr) else None
    
    def analyze_b_business(self) -> Dict:
        """
        Análisis B: Base del negocio.
        Evalúa la calidad y sostenibilidad del modelo de negocio.
        """
        result = {
            'score': 0,
            'max_score': 5,
            'signals': [],
            'concerns': [],
            'questions': []
        }
        
        # Facilidad de entender el negocio: usar descripción y sector
        sector = safe_get(self.info, 'sector', 'N/D')
        industry = safe_get(self.info, 'industry', 'N/D')
        result['signals'].append(f"Sector: {sector}")
        result['signals'].append(f"Industria: {industry}")
        
        # Márgenes neto como indicador de poder de fijación de precios
        if is_valid(self.profit_margin):
            if self.profit_margin > 0.15:
                result['score'] += 1
                result['signals'].append(f"Margen neto elevado: {self.profit_margin:.1%}")
            elif self.profit_margin > 0.05:
                result['signals'].append(f"Margen neto moderado: {self.profit_margin:.1%}")
            else:
                result['concerns'].append(f"Margen neto bajo: {self.profit_margin:.1%}")
        
        # Estabilidad de ingresos: evaluar crecimiento
        rev_growth = self.calculate_revenue_growth()
        if rev_growth is not None:
            if 0.05 <= rev_growth <= 0.30:
                result['score'] += 1
                result['signals'].append(f"Crecimiento de ingresos estable: {rev_growth:.1%}")
            elif rev_growth < 0:
                result['concerns'].append(f"Ingresos decrecientes: {rev_growth:.1%}")
        
        # Márgenes operativos como indicador de eficiencia
        if is_valid(self.operating_margin):
            if self.operating_margin > 0.15:
                result['score'] += 1
                result['signals'].append(f"Margen operativo sólido: {self.operating_margin:.1%}")
        
        # Posición de efectivo relativa a deuda
        if is_valid(self.debt_to_equity):
            if self.debt_to_equity < 0.5:
                result['score'] += 1
                result['signals'].append(f"Deuda/Patrimonio bajo: {self.debt_to_equity:.2f}")
            elif self.debt_to_equity < 1.0:
                result['signals'].append(f"Deuda/Patrimonio moderado: {self.debt_to_equity:.2f}")
            else:
                result['concerns'].append(f"Deuda/Patrimonio elevado: {self.debt_to_equity:.2f}")
        
        result['questions'].extend([
            "¿Es el negocio fácil de entender?",
            "¿Existe un producto o servicio reconocible?",
            "¿Tiene la empresa una marca o ventaja competitiva clara?",
            "¿Cuál es el poder de fijación de precios?"
        ])
        
        return result
    
    def analyze_a_administration(self) -> Dict:
        """
        Análisis A: Administración.
        Evalúa la gestión del capital y crecimiento de ganancias.
        """
        result = {
            'score': 0,
            'max_score': 5,
            'signals': [],
            'concerns': [],
            'questions': []
        }
        
        # Crecimiento del EPS
        eps_growth = self.calculate_eps_growth()
        if eps_growth is not None:
            if eps_growth > 0.15:
                result['score'] += 2
                result['signals'].append(f"EPS crecimiento fuerte: {eps_growth:.1%}")
            elif eps_growth > 0.08:
                result['score'] += 1
                result['signals'].append(f"EPS crecimiento moderado: {eps_growth:.1%}")
            elif eps_growth > 0:
                result['signals'].append(f"EPS crecimiento débil: {eps_growth:.1%}")
            else:
                result['concerns'].append(f"EPS decreciente: {eps_growth:.1%}")
        
        # Dividendos como señal de confianza en ganancias
        if is_valid(self.dividend) and self.dividend > 0:
            payout_ratio = self.dividend / (self.eps if self.eps and self.eps > 0 else float('inf'))
            if 0 < payout_ratio < 0.5:
                result['score'] += 1
                result['signals'].append(f"Dividendo sostenible: {payout_ratio:.1%} payout")
            elif payout_ratio >= 0.5:
                result['concerns'].append(f"Payout ratio elevado: {payout_ratio:.1%}")
        
        # ROE como retorno sobre beneficios retenidos
        if is_valid(self.roe):
            if self.roe > 0.15:
                result['score'] += 1
                result['signals'].append(f"ROE elevado: {self.roe:.1%}")
            elif self.roe > 0.10:
                result['signals'].append(f"ROE moderado: {self.roe:.1%}")
            else:
                result['concerns'].append(f"ROE bajo: {self.roe:.1%}")
        
        # Consistencia de ganancias (años positivos)
        ni_hist = self.get_historical_net_income()
        if len(ni_hist) >= 3:
            positive_years = sum(1 for ni in ni_hist.values() if ni > 0)
            if positive_years >= len(ni_hist) * 0.8:
                result['score'] += 1
                result['signals'].append(f"Ganancias consistentes: {positive_years}/{len(ni_hist)} años")
            else:
                result['concerns'].append(f"Ganancias inconsistentes: {positive_years}/{len(ni_hist)} años")
        
        result['questions'].extend([
            "¿Cuál es el crecimiento histórico del EPS?",
            "¿Ha habido recompras o dilución de acciones?",
            "¿Cuál es el retorno sobre beneficios retenidos?",
            "¿La gestión asigna capital de forma eficiente?"
        ])
        
        return result
    
    def analyze_s_health(self) -> Dict:
        """
        Análisis S: Salud financiera.
        Evalúa la solidez y estabilidad financiera.
        """
        result = {
            'score': 0,
            'max_score': 5,
            'signals': [],
            'concerns': [],
            'questions': []
        }
        
        # Años positivos de EPS histórico
        eps_hist = self.get_historical_eps()
        if len(eps_hist) >= 3:
            positive_eps = sum(1 for eps in eps_hist.values() if eps > 0)
            if positive_eps >= len(eps_hist) * 0.9:
                result['score'] += 1
                result['signals'].append(f"EPS positivo histórico: {positive_eps}/{len(eps_hist)} años")
        
        # ROE consistente
        if is_valid(self.roe):
            if self.roe > 0.12:
                result['score'] += 1
                result['signals'].append(f"ROE saludable: {self.roe:.1%}")
        
        # Deuda manejable
        if is_valid(self.debt_to_equity):
            if self.debt_to_equity < 1.0:
                result['score'] += 1
                result['signals'].append(f"Deuda/Patrimonio controlada: {self.debt_to_equity:.2f}")
            else:
                result['concerns'].append(f"Deuda/Patrimonio elevada: {self.debt_to_equity:.2f}")
        
        # Márgenes estables
        if is_valid(self.profit_margin):
            if self.profit_margin > 0.08:
                result['score'] += 1
                result['signals'].append(f"Márgenes sanos: {self.profit_margin:.1%}")
        
        # Flujo de caja operativo positivo
        if is_valid(self.operating_cf) and self.operating_cf > 0:
            result['score'] += 1
            result['signals'].append(f"Flujo de caja operativo positivo")
        
        result['questions'].extend([
            "¿Cuál es la cobertura de deuda?",
            "¿Es sostenible el nivel actual de deuda?",
            "¿El flujo de caja cubre los dividendos?",
            "¿Hay consistencia en los márgenes?"
        ])
        
        return result
    
    def analyze_e_valuation(self) -> Dict:
        """
        Análisis E: Evaluación de precio.
        Evalúa si el precio es atractivo.
        """
        result = {
            'score': 0,
            'max_score': 5,
            'signals': [],
            'concerns': [],
            'questions': []
        }
        
        # PER actual
        if is_valid(self.trailing_pe):
            if self.trailing_pe < 0:
                result['concerns'].append(f"Ganancias negativas: PER negativo")
            elif self.trailing_pe < 15:
                result['score'] += 2
                result['signals'].append(f"PER atractivo: {self.trailing_pe:.1f}x")
            elif self.trailing_pe < 25:
                result['score'] += 1
                result['signals'].append(f"PER moderado: {self.trailing_pe:.1f}x")
            else:
                result['concerns'].append(f"PER elevado: {self.trailing_pe:.1f}x")
        
        # Rendimiento de ganancias (EPS/Precio)
        if is_valid(self.eps) and is_valid(self.current_price) and self.current_price > 0:
            earnings_yield = self.eps / self.current_price
            if earnings_yield > 0.10:
                result['score'] += 1
                result['signals'].append(f"Rendimiento de ganancias atractivo: {earnings_yield:.1%}")
            elif earnings_yield > 0.06:
                result['signals'].append(f"Rendimiento de ganancias moderado: {earnings_yield:.1%}")
            else:
                result['concerns'].append(f"Rendimiento de ganancias bajo: {earnings_yield:.1%}")
        
        # Precio sobre libro (si está disponible)
        if is_valid(self.pb_ratio):
            if self.pb_ratio < 2.0:
                result['score'] += 1
                result['signals'].append(f"Precio/Libro atractivo: {self.pb_ratio:.2f}x")
            elif self.pb_ratio < 3.0:
                result['signals'].append(f"Precio/Libro moderado: {self.pb_ratio:.2f}x")
            else:
                result['concerns'].append(f"Precio/Libro elevado: {self.pb_ratio:.2f}x")
        
        # Precio sobre ventas
        if is_valid(self.ps_ratio):
            if self.ps_ratio < 1.0:
                result['score'] += 1
                result['signals'].append(f"Precio/Ventas atractivo: {self.ps_ratio:.2f}x")
            elif self.ps_ratio < 2.0:
                result['signals'].append(f"Precio/Ventas moderado: {self.ps_ratio:.2f}x")
        
        result['questions'].extend([
            "¿Es atractivo el PER comparado con el sector?",
            "¿Cuál es el margen de seguridad?",
            "¿Qué precio justificaría las ganancias futuras?",
            "¿Es mejor esperar a un precio más bajo?"
        ])
        
        return result
    
    def calculate_base_score(self) -> Dict:
        """Calcula el puntaje BASE completo."""
        b = self.analyze_b_business()
        a = self.analyze_a_administration()
        s = self.analyze_s_health()
        e = self.analyze_e_valuation()
        
        total_score = b['score'] + a['score'] + s['score'] + e['score']
        max_score = b['max_score'] + a['max_score'] + s['max_score'] + e['max_score']
        percentage = (total_score / max_score * 100) if max_score > 0 else 0
        
        return {
            'B': b,
            'A': a,
            'S': s,
            'E': e,
            'total_score': total_score,
            'max_score': max_score,
            'percentage': percentage,
            'all_signals': [s for sec in [b, a, s, e] for s in sec['signals']],
            'all_concerns': [c for sec in [b, a, s, e] for c in sec['concerns']],
            'all_questions': [q for sec in [b, a, s, e] for q in sec['questions']]
        }
    
    def get_summary(self) -> Dict:
        """Retorna un resumen con datos clave."""
        return {
            'current_price': self.current_price,
            'eps': self.eps,
            'trailing_pe': self.trailing_pe,
            'forward_pe': self.forward_pe,
            'roe': self.roe,
            'profit_margin': self.profit_margin,
            'debt_to_equity': self.debt_to_equity,
            'dividend': self.dividend,
            'market_cap': self.market_cap,
            'sector': safe_get(self.info, 'sector'),
            'industry': safe_get(self.info, 'industry')
        }
