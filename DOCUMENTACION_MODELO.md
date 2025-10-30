# Documentación del Modelo Predictivo de Producción de Café

## Tabla de Contenidos
1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Arquitectura del Modelo](#arquitectura-del-modelo)
3. [Proceso de Desarrollo](#proceso-de-desarrollo)
4. [Features (Características) del Modelo](#features-características-del-modelo)
5. [Métricas de Evaluación](#métricas-de-evaluación)
6. [Resultados y Conclusiones](#resultados-y-conclusiones)

---

## Resumen Ejecutivo

Este documento describe el desarrollo de un **modelo híbrido avanzado de regresión lineal** diseñado para predecir la producción anual de café por país. El modelo utiliza un enfoque innovador que combina características estadísticas tradicionales con interacciones complejas para capturar patrones temporales y específicos de cada país.

### Objetivo
Predecir la producción de café (en kilogramos) para los próximos 5 años (2020-2024) basándose en datos históricos de producción por país.

### Tipo de Modelo
Regresión Lineal Múltiple con 6 features híbridas (tendencia, volatilidad, inercia, momentum e interacciones).

### Unidades de Medida
Todas las predicciones y métricas se expresan en **kilogramos (kg)** de café producido.

---

## Arquitectura del Modelo

### 1. Fuente de Datos
- **Base de datos**: MySQL (database: `coffee`)
- **Tablas principales**: 
  - `production`: Datos de producción por país y año (en kg)
  - `countries`: Información de países
- **Formato original**: Wide format (columnas por año)
- **Transformación**: Conversión a long format (registros por país-año)

### 2. Pipeline del Modelo

```
Datos Crudos → Transformación → Feature Engineering → División Train/Test → 
Entrenamiento → Evaluación → Predicción Futura
```

#### Flujo Detallado:

1. **Carga de Datos**: Extracción desde MySQL y transformación a formato largo
2. **Feature Engineering**: Creación de 6 características derivadas
3. **División Temporal**: Últimos 3 años para testing, el resto para entrenamiento
4. **Entrenamiento**: Ajuste del modelo de regresión lineal
5. **Evaluación**: Cálculo de métricas MAE, RMSE, R²
6. **Predicción**: Generación de pronósticos 5 años adelante

---

## Proceso de Desarrollo

### Fase 1: Carga y Preparación de Datos

#### Transformación de Datos
Los datos originales están en formato **wide** (una columna por año):

```
country_id | 1990/91 | 1991/92 | ... | 2018/19
-----------+---------+---------+-----+---------
     1     | 1500000 | 1600000 | ... | 1800000
```

Se transforman a formato **long** (una fila por país-año):

```
country_id | year | production | country_name
-----------+------+------------+-------------
     1     | 1990 | 1500000    | Brazil
     1     | 1991 | 1600000    | Brazil
```

**Ventajas del formato largo**:
- Facilita operaciones temporales (lags, rolling windows)
- Compatible con sklearn y análisis de series temporales
- Permite agrupar por país de forma eficiente

#### Estadísticas Clave
- **Registros totales**: ~1,000+ observaciones país-año
- **Países únicos**: 50+ países productores
- **Rango temporal**: 1990-2019 (30 años de historia)
- **Unidad de medida**: Kilogramos (kg)

---

## Features (Características) del Modelo

El modelo utiliza **6 features híbridas** que capturan diferentes aspectos del comportamiento de producción:

### 1. **rolling_mean_3y** (Promedio Móvil de 3 Años)

**Definición**: Promedio de producción de los últimos 3 años.

**Fórmula**:
$$\text{rolling\_mean}_t = \frac{1}{3}\sum_{i=0}^{2} \text{production}_{t-i}$$

**Propósito**: 
- Captura la **tendencia local** reciente
- Suaviza fluctuaciones aleatorias año a año
- Diferencia entre tendencia de corto plazo vs. histórico completo

**Ejemplo práctico**:
```
País X:
2016: 1,000,000 kg
2017: 1,100,000 kg
2018: 1,050,000 kg
→ rolling_mean_3y(2018) = (1,000,000 + 1,100,000 + 1,050,000) / 3 = 1,050,000 kg
```

**Interpretación**: Si un país tiene tendencia creciente en los últimos 3 años, es probable que continúe creciendo.

**Importancia**: Esta feature tiene típicamente el coeficiente más alto (~0.5), indicando que el promedio reciente es el predictor más fuerte de producción futura.

---

### 2. **rolling_std_3y** (Desviación Estándar Móvil de 3 Años)

**Definición**: Desviación estándar de producción de los últimos 3 años.

**Fórmula**:
$$\text{rolling\_std}_t = \sqrt{\frac{1}{3}\sum_{i=0}^{2}(\text{production}_{t-i} - \text{rolling\_mean}_t)^2}$$

**Propósito**:
- Mide la **volatilidad** de la producción
- Identifica países con producción estable vs. errática
- Ayuda al modelo a ajustar confianza en predicciones

**Ejemplo práctico**:
```
País A (estable):           País B (volátil):
2016: 1,000,000 kg          2016: 1,000,000 kg
2017: 1,020,000 kg          2017: 1,500,000 kg
2018: 1,010,000 kg          2018:   800,000 kg
→ std_A = 10,000 kg         → std_B = 360,000 kg
```

**Interpretación**: Países con alta volatilidad requieren predicciones más conservadoras. Un coeficiente negativo típico (~-0.01) indica que mayor volatilidad reduce ligeramente la producción esperada.

**Factores que aumentan volatilidad**:
- Dependencia de clima errático
- Plagas recurrentes
- Inestabilidad política o económica
- Monocultivo sin diversificación

---

### 3. **production_lag1** (Producción Año Anterior)

**Definición**: Valor de producción del año inmediatamente anterior.

**Fórmula**:
$$\text{production\_lag1}_t = \text{production}_{t-1}$$

**Propósito**:
- Captura la **inercia** del sistema productivo
- Refleja capacidad instalada, infraestructura, clima del año anterior
- Base de referencia más cercana para predicción

**Ejemplo práctico**:
```
Si en 2018 un país produjo 5,000,000 kg, es más probable que en 2019 
produzca ~5,000,000 kg que saltar a 10,000,000 kg.
```

**Interpretación**: La producción tiende a ser similar año tras año debido a factores estructurales como:
- Número de plantas de café (toma años cambiar)
- Infraestructura de procesamiento
- Mano de obra disponible
- Prácticas agrícolas establecidas

**Coeficiente típico**: ~0.45, indicando que el 45% de la producción del año anterior se "transfiere" al año siguiente.

---

### 4. **pct_change_1y** (Cambio Porcentual Anual)

**Definición**: Porcentaje de cambio de producción respecto al año anterior.

**Fórmula**:
$$\text{pct\_change}_t = \frac{\text{production}_t - \text{production}_{t-1}}{\text{production}_{t-1}}$$

**Propósito**:
- Captura el **momentum** de cambio
- Identifica aceleraciones o desaceleraciones
- Normaliza cambios (10% es significativo independiente de la escala)

**Ejemplo práctico**:
```
2017: 1,000,000 kg
2018: 1,100,000 kg
→ pct_change = (1,100,000 - 1,000,000) / 1,000,000 = 0.10 = +10%

Si el país venía creciendo 2% anual y ahora crece 10%, 
esto señala una aceleración que el modelo debe considerar.
```

**Interpretación**: Países en fase de crecimiento acelerado seguirán esa tendencia en el corto plazo. Un coeficiente positivo alto (~150) significa que por cada 1% de crecimiento, la producción aumenta ~150,000 kg adicionales.

**Casos de uso**:
- **pct_change > +10%**: Expansión agrícola, tecnología nueva, condiciones óptimas
- **pct_change ≈ 0%**: Producción estable, madurez del sector
- **pct_change < -10%**: Sequía, plagas, inestabilidad política

---

### 5. **mean_x_pct** (Interacción: Tendencia × Momentum) ⭐ NUEVA

**Definición**: Producto de la tendencia reciente por el momentum de cambio.

**Fórmula**:
$$\text{mean\_x\_pct}_t = \text{rolling\_mean\_3y}_t \times \text{pct\_change\_1y}_t$$

**Propósito**:
- Captura **aceleraciones no lineales**
- Diferencia entre crecimiento de países grandes vs. pequeños
- Amplifica señales de cambio en países con alta producción

**Ejemplo práctico**:
```
País A (grande):            País B (pequeño):
rolling_mean = 10,000,000   rolling_mean = 1,000,000
pct_change = +5%            pct_change = +5%
→ mean_x_pct = 500,000      → mean_x_pct = 50,000

Mismo momentum, pero País A tiene 10x más impacto absoluto.
```

**Interpretación**: Esta feature permite al modelo ajustar predicciones según la escala de producción del país.

**Casos extremos**:
- **Brasil** (50M kg) con +5% momentum → mean_x_pct = 2,500,000
- **Costa Rica** (500K kg) con +5% momentum → mean_x_pct = 25,000

El modelo aprende que el mismo momentum porcentual tiene diferentes impactos según el tamaño del país.

---

### 6. **volatility_norm** (Volatilidad Normalizada) ⭐ NUEVA

**Definición**: Volatilidad relativa a la escala de producción.

**Fórmula**:
$$\text{volatility\_norm}_t = \frac{\text{rolling\_std\_3y}_t}{\text{rolling\_mean\_3y}_t + 1}$$

**Propósito**:
- Normaliza volatilidad por escala de producción
- Identifica inestabilidad relativa (no absoluta)
- Ajusta confianza en predicciones según estabilidad del país

**Ejemplo práctico**:
```
País A (grande estable):    País B (pequeño errático):
rolling_std = 100,000       rolling_std = 100,000
rolling_mean = 10,000,000   rolling_mean = 500,000
→ vol_norm = 0.01 (1%)      → vol_norm = 0.20 (20%)

Misma volatilidad absoluta, pero País B es 20x más errático relativamente.
```

**Interpretación**: Países con alta volatilidad normalizada tienen predicciones menos confiables. Un coeficiente negativo (~-45) penaliza la producción esperada en países inestables.

**Aplicación práctica**:
- **vol_norm < 0.05 (5%)**: Producción muy estable → predicciones confiables
- **vol_norm 0.05-0.15**: Volatilidad moderada → ajuste ligero
- **vol_norm > 0.15 (15%)**: Alta inestabilidad → reducción significativa en predicción

---

## Métricas de Evaluación

El modelo se evalúa usando tres métricas estándar de regresión:

### 1. **MAE (Mean Absolute Error)**

**Definición**: Promedio de los errores absolutos.

**Fórmula**:
$$\text{MAE} = \frac{1}{n}\sum_{i=1}^{n}|y_i - \hat{y}_i|$$

**Interpretación**:
- **Unidades**: Kilogramos (misma unidad que producción)
- **Significado**: En promedio, las predicciones se desvían ±X kilogramos del valor real
- **Ventaja**: Fácil de interpretar, penaliza todos los errores por igual

**Ejemplo**:
```
MAE = 150,000 kg → Las predicciones se desvían ±150 toneladas en promedio
```

**¿Qué es un buen MAE?**
- Depende de la escala: Para Brasil (~50M kg), MAE de 150,000 kg es excelente (<0.3%)
- Para países pequeños (~500K kg), MAE de 150,000 kg sería malo (30%)

**Ventajas del MAE**:
- Interpretación directa en kg
- No se ve afectado por outliers extremos
- Útil para comunicar precisión a stakeholders no técnicos

**Limitaciones**:
- Trata igual error de 100K kg que de 1M kg
- No captura la gravedad de errores grandes

---

### 2. **RMSE (Root Mean Squared Error)**

**Definición**: Raíz cuadrada del promedio de errores al cuadrado.

**Fórmula**:
$$\text{RMSE} = \sqrt{\frac{1}{n}\sum_{i=1}^{n}(y_i - \hat{y}_i)^2}$$

**Interpretación**:
- **Unidades**: Kilogramos (misma unidad que producción)
- **Significado**: Penaliza más los errores grandes (outliers)
- **Relación con MAE**: RMSE ≥ MAE siempre

**Ejemplo**:
```
RMSE = 200,000 kg → Errores típicos alrededor de 200 toneladas, 
                     con algunos outliers más grandes
```

**¿Cuándo RMSE >> MAE?**
- Indica presencia de errores muy grandes esporádicos
- Sugiere que el modelo falla significativamente en algunos casos específicos

**Ratio RMSE/MAE**:
```
RMSE/MAE ≈ 1.0 → Errores uniformes, sin outliers
RMSE/MAE ≈ 1.2-1.3 → Distribución normal de errores
RMSE/MAE > 1.5 → Presencia de outliers significativos
```

**Ejemplo comparativo**:
```
Modelo A: MAE = 150K, RMSE = 160K → Ratio = 1.07 (muy consistente)
Modelo B: MAE = 150K, RMSE = 250K → Ratio = 1.67 (errores grandes ocasionales)
```

---

### 3. **R² (Coeficiente de Determinación)**

**Definición**: Proporción de varianza explicada por el modelo.

**Fórmula**:
$$R^2 = 1 - \frac{\sum_{i=1}^{n}(y_i - \hat{y}_i)^2}{\sum_{i=1}^{n}(y_i - \bar{y})^2}$$

**Interpretación**:
- **Rango**: -∞ a 1 (típicamente 0 a 1)
- **R² = 1**: Predicción perfecta (nunca en la práctica)
- **R² = 0**: Modelo tan bueno como predecir la media
- **R² < 0**: Modelo peor que predecir la media (muy malo)

**Ejemplo**:
```
R² = 0.85 → El modelo explica 85% de la variabilidad en la producción
            15% restante son factores no capturados (clima, políticas, etc.)
```

**¿Qué es un buen R²?**
- **> 0.90**: Excelente - Captura casi toda la variabilidad
- **0.70-0.90**: Bueno - Captura mayoría de patrones importantes
- **0.50-0.70**: Moderado - Captura tendencias generales
- **< 0.50**: Pobre - Modelo poco útil

**Interpretación por industria**:
- Ciencias físicas: R² > 0.95 esperado
- Economía/finanzas: R² > 0.60 es bueno
- **Agricultura**: R² > 0.75 es excelente (muchos factores no controlados)

**Factores del 15% no explicado** (si R² = 0.85):
- Clima año específico (sequías, heladas)
- Plagas y enfermedades impredecibles
- Políticas gubernamentales nuevas
- Fluctuaciones de precios internacionales
- Conflictos sociales o políticos

---

## Comparación de Métricas

### Sensibilidad a Outliers

```
Escenario: Predicciones en kg
Predicción: [1,000,000, 1,050,000,  980,000, 1,020,000]
Real:       [1,000,000, 1,000,000, 1,000,000, 1,500,000]  ← outlier

Error absoluto: [0, 50K, 20K, 480K]
Error al cuadrado: [0, 2.5B, 0.4B, 230.4B]

MAE  = (0 + 50K + 20K + 480K) / 4 = 137,500 kg
RMSE = √[(0 + 2.5B + 0.4B + 230.4B) / 4] = √[58.3B] = 241,600 kg

→ RMSE es 1.76x mayor que MAE debido al outlier de 480K kg
```

**Análisis**:
- MAE ignora que un error fue 10x más grande que los otros
- RMSE castiga severamente el error de 480K
- En agricultura, outliers son comunes → RMSE más informativo

### Interpretación Conjunta

- **MAE bajo + RMSE bajo**: Predicciones consistentemente buenas ✅
  - Ejemplo: MAE=100K, RMSE=120K → Modelo confiable

- **MAE bajo + RMSE alto**: Buenas en promedio, pero con errores grandes ocasionales ⚠️
  - Ejemplo: MAE=100K, RMSE=300K → Revisar países/años con errores grandes

- **MAE alto + RMSE alto**: Predicciones generalmente pobres ❌
  - Ejemplo: MAE=500K, RMSE=800K → Modelo no captura patrones

- **R² alto + MAE/RMSE bajos**: Modelo captura bien los patrones ⭐
  - Ejemplo: R²=0.88, MAE=120K, RMSE=150K → Modelo listo para producción

### Tabla de Referencia de Métricas

| Métrica | Excelente | Bueno | Moderado | Pobre |
|---------|-----------|-------|----------|-------|
| **R²** | > 0.90 | 0.75-0.90 | 0.50-0.75 | < 0.50 |
| **MAE** (% de media) | < 5% | 5-10% | 10-20% | > 20% |
| **RMSE/MAE Ratio** | 1.0-1.2 | 1.2-1.4 | 1.4-1.6 | > 1.6 |

---

## Resultados y Conclusiones

### Ventajas del Modelo Híbrido

1. **Captura Múltiples Patrones**:
   - **Tendencias locales** (rolling_mean): Se adapta a cambios recientes, no histórico completo
   - **Volatilidad específica** (rolling_std): Reconoce países estables vs. erráticos
   - **Inercia productiva** (lag1): Respeta límites físicos de cambio año a año
   - **Momentum de cambio** (pct_change): Identifica aceleraciones/desaceleraciones
   - **Efectos de escala** (mean_x_pct): Mismo % tiene diferente impacto en Brasil vs. Costa Rica
   - **Estabilidad relativa** (volatility_norm): Normaliza riesgo por tamaño del país

2. **Sin Supuestos de Linealidad Temporal**:
   - No asume que todos los países crecen al mismo ritmo
   - No impone tendencia global (2% anual para todos)
   - Adapta predicciones según comportamiento reciente
   - Reconoce que países estables vs. volátiles requieren diferentes aproximaciones

3. **Robustez**:
   - Maneja datos faltantes (dropna controlado)
   - Evita divisiones por cero (rolling_mean + 1)
   - Limpia valores infinitos de pct_change
   - Predicciones nunca negativas (usa rolling_mean como fallback)

4. **Interpretabilidad**:
   - Coeficientes claros y explicables
   - Features basadas en conceptos agronómicos conocidos
   - Métricas en kg, fáciles de comunicar

### Limitaciones Conocidas

1. **Factores Externos No Capturados**:
   - **Clima extremo**: Sequías, heladas, huracanes
   - **Políticas gubernamentales**: Subsidios, aranceles, reformas agrarias
   - **Precios internacionales**: Boom/crash de precios del café
   - **Plagas y enfermedades**: Roya del café, broca
   - **Tecnología**: Nuevas variedades resistentes, automatización

2. **Supuestos del Modelo**:
   - Asume que patrones de últimos 3 años continuarán
   - No captura cambios estructurales abruptos (ej: nueva ley)
   - Requiere al menos 3 años de historia por país
   - Linealidad entre features (no captura interacciones de orden superior)

3. **División Train/Test Temporal**:
   - Test solo en últimos 3 años
   - No valida en diferentes períodos históricos
   - Sensible a si período de test fue atípico (sequía generalizada)

4. **Granularidad**:
   - Predicción a nivel país (no región/finca)
   - No distingue entre tipos de café (arábica vs. robusta)
   - Anual (no puede predecir por temporada)

### Casos de Uso Recomendados

✅ **Apropiado para**:
- **Planificación de cadena de suministro** a mediano plazo (2-3 años)
  - Estimar necesidades de importación/exportación
  - Planificar capacidad de procesamiento
  
- **Identificación de países con tendencias** de crecimiento/declive
  - Decisiones de inversión en infraestructura
  - Estrategias de sourcing de café
  
- **Análisis de impacto relativo** de volatilidad
  - Identificar países de riesgo alto
  - Diversificación de proveedores

- **Benchmarking de países**
  - Comparar producción esperada vs. real
  - Identificar países sobre/sub-performers

❌ **No apropiado para**:
- **Predicciones de muy largo plazo** (>5 años)
  - Cambio climático altera patrones fundamentales
  - Tecnología puede cambiar radicalmente producción
  
- **Países sin historia de producción**
  - Requiere 3+ años de datos
  - No puede predecir para países nuevos
  
- **Escenarios con cambios estructurales esperados**
  - Nueva tecnología disruptiva
  - Cambio climático abrupto
  - Crisis económica/política mayor
  
- **Decisiones de producción a nivel finca**
  - Demasiado agregado (nivel país)
  - No considera condiciones locales

### Mejoras Futuras Sugeridas

#### 1. **Incorporar Variables Exógenas**:
   
   **Variables climáticas**:
   - Temperatura promedio anual (°C)
   - Precipitación total anual (mm)
   - Índices de sequía (SPEI, SPI)
   - Frecuencia de eventos extremos
   
   **Variables económicas**:
   - Precio internacional del café (USD/kg)
   - PIB per cápita del país
   - Tipo de cambio vs. USD
   - Índice de fertilizantes
   
   **Variables socio-políticas**:
   - Estabilidad política (índice)
   - Subsidios agrícolas
   - Políticas de exportación

#### 2. **Modelos Alternativos**:
   
   **Random Forest**:
   - ✅ Captura no linealidades
   - ✅ Robusto a outliers
   - ❌ Menos interpretable
   
   **XGBoost**:
   - ✅ Mejor con interacciones complejas
   - ✅ Maneja datos faltantes
   - ❌ Requiere más datos de entrenamiento
   
   **LSTM (Redes Neuronales)**:
   - ✅ Excelente para series temporales largas
   - ✅ Captura patrones complejos
   - ❌ Caja negra, difícil interpretación
   - ❌ Requiere muchos datos
   
   **Prophet (Facebook)**:
   - ✅ Maneja estacionalidad automáticamente
   - ✅ Robusto a datos faltantes
   - ✅ Fácil incorporar holidays/eventos
   - ❌ Orientado a series univariadas

#### 3. **Feature Engineering Adicional**:
   
   **Lags múltiples**:
   - production_lag2, production_lag3
   - Captura ciclos de producción del café (bienales)
   
   **Promedios móviles variables**:
   - rolling_mean_5y, rolling_mean_7y
   - Para países con ciclos más largos
   
   **Features estacionales**:
   - Tipo de clima del país (tropical, subtropical)
   - Temporada de cosecha (primer/segundo semestre)
   
   **Clustering de países**:
   - Agrupar países similares (ej: "grandes productores", "países andinos")
   - Modelos específicos por cluster

#### 4. **Validación Cruzada Temporal**:
   
   **Walk-forward validation**:
   ```
   Train: 1990-2010 → Test: 2011-2012
   Train: 1990-2012 → Test: 2013-2014
   Train: 1990-2014 → Test: 2015-2016
   ...
   ```
   
   **Ventajas**:
   - Valida en múltiples períodos históricos
   - Detecta si modelo es robusto a diferentes épocas
   - Más confianza en capacidad predictiva

#### 5. **Análisis de Incertidumbre**:
   
   **Intervalos de confianza**:
   - No solo predicción puntual (ej: 5,000,000 kg)
   - Rango probable (ej: 4,500,000 - 5,500,000 kg con 95% confianza)
   
   **Predicciones probabilísticas**:
   - Distribución de posibles resultados
   - Útil para gestión de riesgo

---

## Apéndice: Interpretación de Coeficientes

Los coeficientes del modelo de regresión lineal indican la **contribución de cada feature** a la predicción:

### Ejemplo de Coeficientes Típicos

```python
Coef. rolling_mean_3y:   +0.5234  
→ Por cada 1,000 kg de aumento en promedio 3Y, 
  predicción aumenta 523 kg
  
Interpretación: El promedio reciente explica ~52% de la producción futura.
Si rolling_mean = 2,000,000 kg → contribuye 1,046,800 kg a la predicción
```

```python
Coef. rolling_std_3y:    -0.0123  
→ Por cada 1,000 kg de aumento en volatilidad,
  predicción disminuye 12.3 kg (ajuste de riesgo)
  
Interpretación: Mayor volatilidad → menor producción esperada (conservador).
Si rolling_std = 100,000 kg → reduce predicción en 1,230 kg
```

```python
Coef. production_lag1:   +0.4512  
→ Por cada 1,000 kg del año pasado,
  predicción aumenta 451 kg (inercia)
  
Interpretación: 45% de la producción del año anterior persiste.
Si producción 2018 = 3,000,000 kg → contribuye 1,353,600 kg en 2019
```

```python
Coef. pct_change_1y:     +150,230  
→ Por cada 1% de crecimiento año pasado,
  predicción aumenta 150,230 kg (momentum)
  
Interpretación: Crecimiento porcentual tiene impacto absoluto fijo.
Si pct_change = +5% → contribuye +751,150 kg a la predicción
```

```python
Coef. mean_x_pct:        +0.0089  
→ Amplificador de escala: países grandes con
  momentum alto reciben boost adicional
  
Interpretación: Efecto no lineal de escala + momentum.
País grande: mean_x_pct = 500,000 → +4,450 kg adicionales
País pequeño: mean_x_pct = 50,000 → +445 kg adicionales
```

```python
Coef. volatility_norm:   -45,670   
→ Por cada 1% de volatilidad relativa,
  predicción baja 45,670 kg (descuento por riesgo)
  
Interpretación: Países inestables penalizados fuertemente.
Si volatility_norm = 0.15 (15%) → reduce predicción en 6,850 kg
```

### Ecuación Completa del Modelo

$$\hat{y}_t = \beta_0 + \beta_1 \cdot \text{rolling\_mean} + \beta_2 \cdot \text{rolling\_std} + \beta_3 \cdot \text{lag1} + \beta_4 \cdot \text{pct\_change} + \beta_5 \cdot \text{mean\_x\_pct} + \beta_6 \cdot \text{volatility\_norm}$$

Donde:
- $\hat{y}_t$ = Predicción de producción en año $t$ **(en kilogramos)**
- $\beta_0$ = Intercepto (producción base, típicamente pequeño ~1,000 kg)
- $\beta_1, ..., \beta_6$ = Coeficientes aprendidos por el modelo

### Ejemplo Numérico Completo

**País X en 2019** (valores hipotéticos):
```
rolling_mean_3y  = 2,500,000 kg
rolling_std_3y   =   120,000 kg
production_lag1  = 2,600,000 kg
pct_change_1y    = +4% = 0.04
mean_x_pct       = 2,500,000 × 0.04 = 100,000
volatility_norm  = 120,000 / 2,500,000 = 0.048 (4.8%)

Predicción 2020:
  = 1,000                            (intercepto)
  + 0.5234 × 2,500,000               = +1,308,500
  - 0.0123 × 120,000                 = -1,476
  + 0.4512 × 2,600,000               = +1,173,120
  + 150,230 × 0.04                   = +6,009
  + 0.0089 × 100,000                 = +890
  - 45,670 × 0.048                   = -2,192
  ─────────────────────────────────
  = 2,485,851 kg ≈ 2.49 millones kg

Análisis:
- Tendencia (+1.31M): Factor más importante
- Inercia (+1.17M): Segundo más importante  
- Momentum (+6K): Pequeño ajuste positivo
- Volatilidad (-3.7K): Penalización por inestabilidad
- TOTAL: ~2.49M kg para 2020
```

---

## Referencias Técnicas

### Documentación
- **Sklearn Documentation**: [LinearRegression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LinearRegression.html)
- **Sklearn Metrics**: [Model Evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html)
- **Pandas Time Series**: [Time Series / Date Functionality](https://pandas.pydata.org/docs/user_guide/timeseries.html)

### Literatura Académica
- **Feature Engineering**: Applied Predictive Modeling (Kuhn & Johnson, 2013)
- **Time Series Forecasting**: Forecasting: Principles and Practice (Hyndman & Athanasopoulos, 3rd ed.)
- **Agricultural Forecasting**: FAO Statistical Development Series (Food and Agriculture Organization)

### Datasets y Fuentes
- **International Coffee Organization (ICO)**: Datos históricos de producción mundial
- **USDA Foreign Agricultural Service**: Reportes de producción por país
- **FAO STAT**: Base de datos de producción agrícola

---

## Glosario de Términos

**Feature**: Característica o variable independiente usada para hacer predicciones.

**Lag**: Valor retrasado en el tiempo (ej: lag1 = valor del año anterior).

**Rolling window**: Ventana móvil que calcula estadísticas sobre N períodos consecutivos.

**Momentum**: Tendencia de cambio (aceleración o desaceleración) en una serie temporal.

**Inercia**: Tendencia de un sistema a mantener su estado actual (resistencia al cambio).

**Volatilidad**: Grado de variación o inestabilidad en una serie temporal.

**Outlier**: Valor atípico que se desvía significativamente del patrón general.

**Train/Test split**: División de datos para entrenamiento y evaluación del modelo.

**Overfitting**: Modelo que aprende el ruido de entrenamiento, no los patrones reales.

**Underfitting**: Modelo demasiado simple que no captura patrones importantes.

---

**Documento generado**: Octubre 2025  
**Versión del Modelo**: Híbrido Avanzado v2 (6 features)  
**Autor**: Cristián Sandoval - Universidad  
**Proyecto**: Actividad DB Café - Momento 2  
**Unidades**: Kilogramos (kg)
