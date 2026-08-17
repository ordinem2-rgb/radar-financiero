# Contexto del proyecto: Radar Financiero

## 1. Objetivo general

Estamos construyendo una aplicación web pública, gratuita y educativa para analizar acciones, ETFs y otros activos del mercado estadounidense.

La aplicación debe permitir que una persona escriba un símbolo bursátil —por ejemplo `AAPL`, `MSFT`, `VOO`, `SPY` o `BND`— y reciba:

- Información de mercado.
- Análisis fundamental.
- Evaluación mediante el Método BASE.
- Análisis técnico.
- Valoración con supuestos transparentes.
- Simulación de portafolios.
- Interpretación generada por inteligencia artificial.

La aplicación es para uso personal, aunque puede ser pública y estar desplegada gratuitamente.

## 2. Usuario y requisitos confirmados

El usuario indicó:

1. Mercado principal: Estados Unidos.
2. Activos: combinación de acciones, ETFs y otros instrumentos compatibles.
3. Uso: principalmente personal.
4. Datos: gratuitos.
5. No desea introducir inicialmente su capital ni sus posiciones actuales.
6. Puede ser útil guardar información más adelante.
7. Quiere una aplicación web o página web gratuita y posiblemente pública.
8. Quiere dos capas claramente separadas:
   - Cálculos y reglas transparentes.
   - Interpretación generada por IA.

El usuario no tiene conocimientos previos de programación. Todas las instrucciones deben ser paso a paso, con lenguaje simple, indicando exactamente dónde hacer clic, qué escribir y qué esperar.

## 3. Tecnología elegida

La tecnología recomendada y aceptada es:

- Python.
- Streamlit para la interfaz web.
- yfinance para datos financieros gratuitos.
- Pandas para manipulación de datos.
- NumPy para cálculos numéricos.
- Plotly para gráficos interactivos.
- GitHub para guardar el código.
- Streamlit Community Cloud para publicar la app gratuitamente.
- Gemini, OpenAI u otro proveedor para la futura capa de IA.

La decisión de usar Streamlit se tomó porque es la opción más sencilla para construir una aplicación web de datos sin tener que desarrollar un frontend y backend separados.

## 4. Limitaciones que siempre deben explicarse

Los datos gratuitos pueden:

- Estar retrasados.
- Tener campos vacíos.
- Tener una cantidad histórica limitada.
- Cambiar de formato.
- Tener límites de consultas.
- Ser inadecuados para ejecutar operaciones en tiempo real.
- No incluir datos suficientes para ETFs o activos extranjeros.

La aplicación debe mostrar siempre, cuando sea posible:

- Fecha del último dato.
- Fecha de consulta.
- Fuente o proveedor.
- Campos no disponibles.
- Supuestos utilizados.
- Nivel de confianza.

Nunca se deben inventar métricas faltantes. Si un dato no existe debe aparecer como `N/D`, `No disponible` o `No concluyente`.

## 5. Nombre del proyecto

Nombre actual:

```text
Radar Financiero
```

En algunas versiones se utilizó el nombre:

```text
Radar Financiero Pro
```

La versión actual debe priorizar el nombre `Radar Financiero` y puede incluir el subtítulo `Método BASE`.

## 6. Marco analítico deseado

El usuario quiere un asesor educativo que combine:

- Filosofía cualitativa y cuantitativa asociada a Buffettología.
- Método BASE.
- Análisis técnico táctico.
- Gestión de portafolio.
- Disciplina psicológica.
- DCA.
- Diversificación.
- Control de concentración.

No se debe afirmar que la aplicación es oficial, está respaldada por Warren Buffett, Mary Buffett, David Clark, AMV, Mis Propias Finanzas u otra marca o institución.

El resultado debe ser educativo y analítico, nunca una recomendación formal personalizada de compra o venta.

## 7. Método BASE solicitado

### B — Base del negocio

La aplicación debe analizar, siempre que existan datos:

- Si el negocio es fácil de entender.
- Si existe un producto o servicio reconocible.
- Si existe recurrencia.
- Si la empresa tiene marca o ventaja competitiva.
- Si posee efectos de red, costes de cambio, escala u otra ventaja.
- Si tiene poder de fijación de precios.
- Si sus ingresos y beneficios son relativamente predecibles.
- Si está expuesta a obsolescencia rápida.
- Si es una empresa commodity.

Regla importante: los datos de precios y estados financieros no prueban por sí solos la existencia de un foso económico. La app debe mostrar preguntas pendientes y pedir revisión cualitativa cuando no exista evidencia suficiente.

### A — Administración

La aplicación debe revisar:

- Evolución del EPS.
- Crecimiento por acción.
- Beneficios retenidos.
- Retorno generado sobre beneficios retenidos, cuando se pueda calcular.
- Recompras de acciones.
- Dilución por emisión de acciones.
- Dividendos y payout.
- Deuda utilizada para financiar el crecimiento.
- Asignación de capital.
- Calidad y consistencia de la administración, cuando existan fuentes cualitativas.

El usuario propuso exigir que el crecimiento del EPS represente al menos un 15 % de los beneficios retenidos acumulados. Esto debe tratarse como una regla configurable y explicarse con cuidado; no debe aplicarse sin comprobar unidades, periodo, moneda y disponibilidad histórica.

### S — Salud financiera

La aplicación debe combinar:

- Evolución histórica del EPS durante 7–10 años si los datos existen.
- Ingresos.
- Beneficio neto.
- Flujo de caja operativo.
- Flujo de caja libre.
- ROE.
- ROA.
- Márgenes bruto, operativo y neto.
- Deuda total.
- Deuda sobre patrimonio.
- Cobertura de intereses si está disponible.
- Dividendos.
- Consistencia de los beneficios.

El ROE no debe interpretarse aislado, ya que puede estar elevado por apalancamiento o patrimonio contable reducido.

### E — Evaluación del precio

Debe incluir, cuando existan datos:

- Precio actual.
- EPS actual.
- Rendimiento inicial: `EPS / Precio`.
- PER actual.
- Precio sobre flujo de caja libre.
- Precio sobre ventas.
- Comparación con promedio histórico de la empresa.
- Comparación con el sector.
- Comparación con competidores.
- Comparación con el mercado, por ejemplo S&P 500.
- Margen de seguridad.
- Proyecciones con escenarios.

No se debe afirmar que una acción está barata solo porque tiene un PER bajo.

## 8. Valoración a 10 años

La aplicación debe permitir editar los supuestos:

- Crecimiento anual del EPS.
- ROE.
- Porcentaje de retención.
- Tasa de dividendos.
- PER final.
- Horizonte.
- Rentabilidad objetivo.

Modelo simplificado actual:

```text
EPS futuro = EPS actual × (1 + crecimiento)^años
Precio futuro = EPS futuro × PER final
TIR = (Precio futuro / Precio actual)^(1/años) - 1
```

También debe calcularse un precio teórico actual que permita alcanzar una rentabilidad objetivo:

```text
Precio máximo teórico = Precio futuro / (1 + rentabilidad objetivo)^años
```

La aplicación debe mostrar escenarios:

- Pesimista.
- Base.
- Optimista.

Cada escenario debe indicar sus supuestos.

Los resultados son sensibles a los supuestos y no son precios objetivos ni recomendaciones.

## 9. Análisis técnico deseado

Debe incluir:

- Gráfico de velas.
- Gráfico de línea opcional.
- Volumen.
- Media móvil de 50 periodos.
- Media móvil de 100 periodos.
- Media móvil de 200 periodos.
- EMA de 20 periodos si resulta útil.
- RSI de 14 periodos.
- MACD.
- Bandas de Bollinger.
- Tendencia de largo plazo.
- Soportes aproximados.
- Resistencias aproximadas.

Reglas orientativas:

- Precio sobre MA200: tendencia de largo plazo potencialmente alcista.
- RSI mayor que 70: sobrecompra y cautela.
- RSI menor que 30: sobreventa, pero no necesariamente infravaloración.

El análisis técnico debe presentarse como complemento táctico, no como predictor seguro.

## 10. Portafolios

El usuario inicialmente no quiere introducir capital ni posiciones personales.

La app debe permitir una simulación opcional mediante:

- Lista de símbolos.
- Porcentajes asignados.
- Rendimiento histórico.
- Rendimiento anualizado aproximado.
- Volatilidad anualizada.
- Máxima caída histórica.
- Correlación entre activos.
- Gráfico del crecimiento simulado.
- Comparación con `SPY`, `VOO` o `BND`.
- Simulación DCA en una futura versión.

Ejemplo de entrada:

```text
AAPL, VOO, BND
```

```text
50, 40, 10
```

Los pesos deben sumar 100 %.

La aplicación debe advertir que la correlación y el rendimiento histórico pueden cambiar en el futuro.

## 11. Inteligencia artificial

La app debe diferenciar claramente:

### Cálculo transparente

- Datos descargados.
- Fórmulas.
- Indicadores.
- Puntajes.
- Supuestos.
- Resultados numéricos.

### Interpretación IA

La IA debe recibir los resultados calculados y explicar:

- Tesis de inversión.
- Fortalezas.
- Debilidades.
- Riesgos.
- Datos que contradicen la tesis.
- Preguntas cualitativas pendientes.
- Escenario favorable.
- Escenario desfavorable.
- Qué revisar en informes y fuentes.
- Nivel de confianza.

La IA no debe inventar datos faltantes ni ejecutar operaciones.

La IA debe responder con etiquetas como:

- Calidad alta / valoración atractiva.
- Calidad alta / valoración exigente.
- Calidad media / requiere investigación.
- Riesgo elevado / no concluyente.

La IA debe indicar que su análisis puede contener errores.

## 12. Seguridad de la IA

Nunca poner claves API en GitHub ni dentro del código.

Para Streamlit Community Cloud se debe usar el sistema de secretos de la aplicación, por ejemplo:

```toml
GEMINI_API_KEY = "clave_privada"
```

El código debería leerla mediante `st.secrets` o variables de entorno.

La documentación de Streamlit recomienda utilizar su sistema de secretos para API keys y credenciales, manteniéndolas fuera del repositorio. [web:35][web:41][web:46]

El archivo `requirements.txt` puede incluir:

```text
streamlit
yfinance
pandas
numpy
plotly
google-genai
```

Todavía no se ha conectado la IA funcionalmente.

## 13. Estado actual de los archivos

Archivos generados durante el proyecto:

- `radar_financiero.py`: primera versión básica.
- `requirements.txt`: dependencias iniciales.
- `app_pro.py`: versión Pro con gráficos, indicadores, valoración preliminar y portafolio.
- `requirements_pro.txt`: dependencias para la versión Pro.
- `radar_financiero_v3.py`: versión con proyecciones y simulación mejoradas.
- `requirements_v3.txt`: dependencias de la V3, incluyendo `google-genai`.
- `base_engine.py`: motor independiente para evaluar el Método BASE.
- `app_base_integrated.py`: aplicación integrada con el motor BASE.
- `requirements_base.txt`: dependencias de la aplicación BASE.

El estado deseado del repositorio es:

```text
radar-financiero/
├── app.py
├── base_engine.py
├── requirements.txt
├── README.md
└── .streamlit/
    └── secrets.toml.example
```

La app principal debería llamarse `app.py` y el motor BASE debería estar en la misma carpeta como `base_engine.py`.

## 14. Motor BASE actual

`base_engine.py` contiene funciones para:

- Validar valores numéricos.
- Extraer valores de estados financieros.
- Crear series históricas.
- Evaluar calidad de tendencia.
- Calcular una tabla BASE.
- Generar preguntas cualitativas pendientes.

El motor actual calcula señales aproximadas:

- B: historial de ingresos y beneficios.
- A: EPS, payout y recompras cuando están disponibles.
- S: ROE, margen neto y deuda.
- E: PER y rendimiento EPS/precio.

La app muestra:

- Puntaje total.
- Puntaje máximo.
- Porcentaje.
- Evidencia calculada.
- Preguntas cualitativas no resueltas.

Este motor todavía debe mejorarse. No debe considerarse una implementación definitiva del Método BASE.

## 15. Problemas pendientes

1. Integrar correctamente `base_engine.py` con `app.py`.
2. Verificar que Streamlit encuentre el módulo local.
3. Añadir datos históricos de 7–10 años.
4. Mejorar la extracción de estados financieros.
5. Calcular crecimiento histórico del EPS.
6. Calcular beneficios retenidos.
7. Detectar recompras y dilución correctamente.
8. Añadir deuda a largo plazo frente a beneficios netos.
9. Añadir comparación histórica de múltiplos.
10. Añadir comparación con sector y competidores.
11. Añadir análisis cualitativo de reportes empresariales.
12. Implementar IA funcional.
13. Implementar búsqueda o recuperación de fuentes.
14. Añadir exportación PDF y CSV.
15. Añadir guardado opcional de análisis.
16. Añadir página de configuración.
17. Añadir manejo robusto de errores y límites de API.
18. Añadir pruebas con acciones, ETFs y símbolos inválidos.
19. Evitar usar campos corporativos para ETFs cuando no sean aplicables.
20. Añadir nivel de confianza basado en cantidad y calidad de datos.

## 16. Mejoras recomendadas al motor BASE

### B

- Extraer `longBusinessSummary`.
- Crear un formulario cualitativo editable para que el usuario responda preguntas.
- Permitir que la IA analice la descripción del negocio, el informe anual y los riesgos.
- Diferenciar empresa de producto, empresa commodity y empresa financiera.

### A

- Calcular crecimiento de EPS y acciones en circulación.
- Detectar reducción o aumento de acciones.
- Medir retorno sobre beneficios retenidos.
- Separar dividendos de recompras.
- Comparar deuda total con beneficio neto y flujo de caja.

### S

- Usar varios años, no solo el valor actual.
- Graficar ingresos, EPS, margen neto, ROE y flujo de caja.
- Penalizar pérdidas recurrentes.
- Identificar años anómalos.
- Separar deuda de empresas financieras de deuda de empresas no financieras.

### E

- Guardar una serie histórica de precios y múltiplos.
- Crear un promedio histórico de PER y P/FCF.
- Comparar con el ETF sectorial adecuado.
- Usar rangos y no cifras puntuales.
- Crear sensibilidad de crecimiento y múltiplo final.

## 17. Reglas de interfaz

La interfaz debe ser sencilla para alguien que no sabe programar.

Debe tener pestañas o páginas:

- Resumen.
- Análisis BASE.
- Fundamental.
- Técnico.
- Valoración.
- Portafolio.
- IA.
- Fuentes y supuestos.

Debe mostrar señales visuales:

- Verde: favorable bajo las reglas.
- Amarillo: mixto o necesita revisión.
- Rojo: desfavorable o riesgo elevado.
- Gris: no disponible.

No saturar al usuario. Mostrar primero un resumen ejecutivo y permitir desplegar el detalle.

## 18. Publicación actual

El usuario creó un repositorio público de GitHub llamado:

```text
radar-financiero
```

La aplicación está desplegada o en proceso de despliegue en Streamlit Community Cloud.

El usuario aprendió a:

1. Crear una cuenta de GitHub.
2. Crear un repositorio.
3. Subir archivos.
4. Editar archivos directamente en GitHub.
5. Hacer commits.
6. Desplegar la app en Streamlit.
7. Reiniciar la aplicación desde Streamlit.

Siempre dar instrucciones paso a paso y explicar qué debe esperar ver.

## 19. Estilo de acompañamiento

Responder siempre en español.

Usar lenguaje sencillo y definir términos técnicos brevemente.

No asumir conocimientos previos.

Cuando se entregue código:

- Entregar el archivo completo.
- Usar nombres exactos.
- Explicar dónde reemplazarlo.
- Explicar cómo guardar el cambio.
- Explicar cómo reiniciar la app.

Cuando haya un error:

1. Diagnosticar la causa más probable.
2. Pedir el mensaje exacto si falta información.
3. Dar máximo dos alternativas.
4. No pedir que cambie muchas cosas al mismo tiempo.

No decir solamente “consulta la documentación”. Intentar resolver el caso concreto.

## 20. Advertencia obligatoria

Al final de cada análisis financiero generado por la app debe aparecer una nota similar a:

> Este análisis es puramente educativo y analítico, basado en datos disponibles, supuestos explícitos y metodologías de análisis fundamental, técnico y Método BASE. No constituye una recomendación formal de compra o venta de valores.

También debe advertir que los datos gratuitos pueden estar retrasados, incompletos o contener errores.

## 21. Próximo paso recomendado

El próximo trabajo más importante es integrar y mejorar `base_engine.py` para que:

1. Calcule tendencias históricas de EPS, ingresos y flujo de caja.
2. Identifique beneficios retenidos.
3. Evalúe recompra o dilución de acciones.
4. Compare deuda con beneficios y flujo de caja.
5. Genere un análisis BASE más completo.
6. Prepare un objeto estructurado para enviarlo a la IA.

Después de validar esos cálculos, conectar la IA utilizando secretos de Streamlit y una API como Gemini.
