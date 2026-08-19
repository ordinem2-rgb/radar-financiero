"""
Gemini AI Analyzer - Análisis profundo y cualitativo usando Google Gemini
Proporciona respuestas detalladas a preguntas de inversión según filosofía Buffett
"""

import google.generativeai as genai
from typing import Dict, Tuple
import os
import json

class GeminiAnalyzer:
    """
    Usa Google Gemini para análisis cualitativo profundo de acciones.
    Responde preguntas sobre moat, management, resilencia y valuación.
    """
    
    def __init__(self, api_key: str):
        """Inicializa con API key de Google Gemini"""
        genai.configure(api_key=api_key)
        self.model = None
        for candidate in [
            'gemini-2.0-flash',
            'gemini-1.5-flash',
            'gemini-1.5-flash-latest',
            'gemini-1.5-pro',
            'gemini-1.5-pro-latest'
        ]:
            try:
                self.model = genai.GenerativeModel(candidate)
                break
            except Exception:
                continue

    def _safe_generate(self, prompt: str) -> str:
        if self.model is None:
            return "Gemini no está disponible en este momento. Verifica la clave y la versión del modelo."
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error en análisis: {str(e)}"
    
    def analyze_business_moat(self, symbol: str, company_name: str, business_type: str, 
                             margins: float, roe: float) -> Tuple[str, str]:
        """
        Analiza el moat económico de la empresa.
        Responde: ¿Es un verdadero monopolio? ¿Qué tan sólida es la ventaja competitiva?
        """
        prompt = f"""
        Eres un analista de inversiones experto en filosofía Buffett.
        
        Empresa: {company_name} ({symbol})
        Tipo de negocio: {business_type}
        Margen bruto: {margins:.1%}
        ROE: {roe:.1%}
        
        Responde en 2-3 párrafos conciso en ESPAÑOL:
        1. ¿Tiene esta empresa un verdadero "moat económico" (ventaja competitiva durable)?
        2. ¿Qué factores protegen su posición (marca, red, switching costs, escala)?
        3. ¿Qué amenazas podrían debilitarla?
        
        Sé específico y basado en hechos conocidos sobre {company_name}. 
        Usa lenguaje directo, no académico.
        """

        moat_analysis = self._safe_generate(prompt)

        # Clasificación del foso
        moat_strength = "Fuerte"
        if "error" in moat_analysis.lower() or "no está disponible" in moat_analysis.lower():
            return moat_analysis, "N/A"
        if "débil" in moat_analysis.lower() or "riesgo" in moat_analysis.lower():
            moat_strength = "Moderado"
        if "commodity" in moat_analysis.lower() or "fácil" in moat_analysis.lower():
            moat_strength = "Débil"

        return moat_analysis, moat_strength
    
    def analyze_management_quality(self, symbol: str, company_name: str, roe_retained: float,
                                   debt_equity: float, eps_growth: float) -> str:
        """
        Analiza la calidad de la administración.
        Responde: ¿Cómo usa la empresa sus ganancias? ¿Deuda prudente? ¿Retorno sobre capital?
        """
        prompt = f"""
        Eres un analista de inversiones experto en filosofía Buffett.
        
        Empresa: {company_name} ({symbol})
        ROE sobre ganancias retenidas: {roe_retained:.1%}
        Deuda/Patrimonio: {debt_equity:.2f}x
        Crecimiento EPS: {eps_growth:.1%}
        
        Responde en 2-3 párrafos conciso en ESPAÑOL:
        1. ¿Cómo está administrando la empresa sus ganancias (reinversión, dividendos, buybacks)?
        2. ¿Está usando capital de forma inteligente (Buffett lo valoraría)?
        3. ¿Es la deuda prudente o arriesgada para este sector?
        
        Sé específico. Lenguaje directo, no académico.
        """
        
        return self._safe_generate(prompt)
    
    def analyze_business_resilience(self, symbol: str, company_name: str, sector: str,
                                   roe_consistency: float, margin_trend: str) -> str:
        """
        Analiza la resiliencia del negocio.
        Responde: ¿Qué tan consistente es? ¿Soportaría una recesión?
        """
        prompt = f"""
        Eres un analista de inversiones experto en filosofía Buffett.
        
        Empresa: {company_name} ({symbol})
        Sector: {sector}
        Consistencia ROE: {roe_consistency:.1%}
        Tendencia de márgenes: {margin_trend}
        
        Responde en 2-3 párrafos conciso en ESPAÑOL:
        1. ¿Qué tan resiliente es este negocio en recesiones o crisis?
        2. ¿Tiene demanda inelástica (la gente lo sigue comprando siempre)?
        3. ¿Cuáles son los riesgos específicos para {company_name}?
        
        Sé específico. Lenguaje directo.
        """
        
        return self._safe_generate(prompt)
    
    def analyze_valuation(self, symbol: str, company_name: str, current_price: float,
                         per: float, initial_yield: float, tir: float) -> str:
        """
        Analiza la valuación actual.
        Responde: ¿A qué precio es atractiva? ¿Hay margen de seguridad?
        """
        prompt = f"""
        Eres un analista de inversiones experto en filosofía Buffett.
        
        Empresa: {company_name} ({symbol})
        Precio actual: ${current_price:.2f}
        PER: {per:.1f}x
        Rendimiento inicial (EPS/Precio): {initial_yield:.2%}
        TIR proyectada 10 años: {tir:.1%}
        
        Responde en 2-3 párrafos conciso en ESPAÑOL:
        1. ¿Parece que el mercado está valuando correctamente esta empresa?
        2. ¿Hay margen de seguridad suficiente (Buffett exige >20%)?
        3. ¿A qué precio sería realmente atractiva la compra?
        
        Sé específico sobre números. Lenguaje directo.
        """
        
        return self._safe_generate(prompt)
    
    def get_company_description(self, company_name: str, sector: str) -> str:
        """
        Obtiene descripción breve de qué hace la empresa (1-2 párrafos)
        """
        prompt = f"""
        En 2-3 párrafos breves en ESPAÑOL, describe QUÉ ES y QUÉ HACE {company_name}.
        
        Sector: {sector}
        
        Incluye:
        1. Qué productos/servicios principales ofrece
        2. Dónde opera (geografía)
        3. Tamaño aprox (pequeña/mediana/grande/gigante)
        4. Posición en el mercado
        
        Sé conciso y claro. Para inversores, no para académicos.
        """
        
        return self._safe_generate(prompt)
    
    def classify_risk_profile(self, symbol: str, company_name: str, roe: float, 
                            debt_equity: float, per: float, sector: str) -> str:
        """
        Clasifica el riesgo de la inversión: Conservador / Moderado / Agresivo
        """
        prompt = f"""
        Clasifica el perfil de riesgo de {company_name} ({symbol}) en UNA de estas categorías:
        
        - CONSERVADOR: ROE alto, deuda baja, valuación barata, negocio estable
        - MODERADO: Buena empresa, pero con algunos riesgos o valuación media
        - AGRESIVO: Alto crecimiento, pero con riesgos (deuda, sector, competencia)
        
        Métricas:
        - ROE: {roe:.1%}
        - Deuda/Patrimonio: {debt_equity:.2f}x
        - PER: {per:.1f}x
        - Sector: {sector}
        
        Responde SOLO con la palabra (CONSERVADOR, MODERADO o AGRESIVO) seguida de 1 frase explicativa.
        """
        
        try:
            text = self._safe_generate(prompt)
            if "error" in text.lower() or "no está disponible" in text.lower():
                return "Moderado"
            classification = text.strip().split('\n')[0]
            if "CONSERVADOR" in classification.upper():
                return "Conservador"
            elif "AGRESIVO" in classification.upper():
                return "Agresivo"
            else:
                return "Moderado"
        except Exception:
            return "Moderado"
