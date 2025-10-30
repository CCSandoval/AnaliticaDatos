"""
Modelo de Machine Learning para predecir la producción anual de café por país

Este script carga los datos históricos de producción de café (1990-2019) desde
la base de datos MySQL y entrena un modelo de regresión lineal simple para
estimar la producción futura de cada país.

Modelo implementado:
- Regresión Lineal

Métricas de evaluación:
- MAE (Mean Absolute Error)
- RMSE (Root Mean Squared Error)
- R² Score
"""

import pandas as pd
import numpy as np
import mysql.connector
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings('ignore')

# Configuración de conexión a la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'database': 'coffee',
    'user': 'analitica',
    'password': 'Operador1704'
}


def get_connection():
    """Crea y retorna una conexión a la base de datos"""
    return mysql.connector.connect(**DB_CONFIG)


def load_production_data():
    """
    Carga los datos de producción desde la base de datos y los transforma
    a formato largo para el modelado.
    
    Returns:
        pd.DataFrame: DataFrame con columnas [country_id, year, production]
    """
    print("📊 Cargando datos de producción...")
    conn = get_connection()
    
    # Cargar tabla de producción
    df_production = pd.read_sql('SELECT * FROM production', con=conn)
    df_countries = pd.read_sql('SELECT id, name FROM countries', con=conn)
    conn.close()
    
    print(f"✅ Datos cargados: {df_production.shape[0]} países")
    
    # Identificar columnas de años
    year_cols = [col for col in df_production.columns 
                 if col not in ['id', 'country_id', 'coffee_type', 'total']]
    
    print(f"📅 Años disponibles: {len(year_cols)} ({year_cols[0]} - {year_cols[-1]})")
    
    # Transformar a formato largo
    data_long = []
    for _, row in df_production.iterrows():
        country_id = row['country_id']
        for year_col in year_cols:
            # Extraer el año inicial del formato "1990/91" -> 1990
            year = int(year_col.split('/')[0])
            production = row[year_col]
            
            # Solo incluir valores no nulos
            if pd.notna(production):
                data_long.append({
                    'country_id': country_id,
                    'year': year,
                    'production': production
                })
    
    df_long = pd.DataFrame(data_long)
    
    # Unir con nombres de países
    df_long = df_long.merge(df_countries.rename(columns={'id': 'country_id', 'name': 'country_name'}),
                            on='country_id', how='left')
    
    print(f"✅ Dataset transformado: {len(df_long)} registros")
    print(f"   Países únicos: {df_long['country_id'].nunique()}")
    print(f"   Rango de años: {df_long['year'].min()} - {df_long['year'].max()}")
    
    return df_long


def create_features(df):
    """
    Crea features combinando año y producción histórica.
    
    Features creadas:
    - year: Año (captura tendencia temporal)
    - production_lag1: Producción del año anterior (captura inercia)
    
    Args:
        df: DataFrame con columnas [country_id, year, production]
    
    Returns:
        pd.DataFrame: DataFrame con features combinadas
    """
    print("\n🔧 Creando features combinadas...")
    
    df = df.copy()
    df = df.sort_values(['country_id', 'year'])
    
    # Feature: Producción del año anterior
    df['production_lag1'] = df.groupby('country_id')['production'].shift(1)
    
    # Eliminar primera fila de cada país (no tiene lag)
    df = df.dropna(subset=['production_lag1'])
    
    print("✅ Features creadas:")
    print("   - year (tendencia temporal)")
    print("   - production_lag1 (producción del año anterior)")
    
    return df


def prepare_train_test_data(df, test_years=3):
    """
    Prepara los datos de entrenamiento y prueba.
    
    Estrategia: Usar los últimos N años como conjunto de prueba.
    
    Args:
        df: DataFrame con todas las features
        test_years: Número de años a usar como conjunto de prueba
    
    Returns:
        X_train, X_test, y_train, y_test, test_df
    """
    print("\n📊 Preparando datos de entrenamiento y prueba...")
    print(f"   Usando últimos {test_years} años como conjunto de prueba")
    
    # Identificar el año de corte
    max_year = df['year'].max()
    cutoff_year = max_year - test_years + 1
    
    print(f"   Año de corte: {cutoff_year}")
    print(f"   Train: {df['year'].min()} - {cutoff_year - 1}")
    print(f"   Test: {cutoff_year} - {max_year}")
    
    # Dividir en train y test
    train_df = df[df['year'] < cutoff_year].copy()
    test_df = df[df['year'] >= cutoff_year].copy()
    
    # Seleccionar año y producción anterior como features
    feature_cols = ['year', 'production_lag1']
    
    X_train = train_df[feature_cols]
    y_train = train_df['production']
    
    X_test = test_df[feature_cols]
    y_test = test_df['production']
    
    print("\n✅ Datos preparados:")
    print(f"   Train: {len(X_train)} muestras")
    print(f"   Test: {len(X_test)} muestras")
    
    return X_train, X_test, y_train, y_test, test_df


def train_model(X_train, y_train):
    """
    Entrena un modelo de regresión lineal simple.
    
    Args:
        X_train: Features de entrenamiento
        y_train: Target de entrenamiento
    
    Returns:
        LinearRegression: Modelo entrenado
    """
    print("\n🤖 Entrenando modelo de Regresión Lineal...")
    print("-" * 60)
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # Mostrar coeficientes
    print("\n✅ Modelo entrenado")
    print(f"   Coeficiente año: {model.coef_[0]:.4f}")
    print(f"   Coeficiente producción(t-1): {model.coef_[1]:.4f}")
    print(f"   Intercepto: {model.intercept_:.2f}")
    print(f"\n   Ecuación: producción = {model.coef_[0]:.4f}*año + {model.coef_[1]:.4f}*producción(t-1) + {model.intercept_:.2f}")
    
    print("-" * 60)
    return model


def evaluate_model(model, X_test, y_test):
    """
    Evalúa el modelo en el conjunto de prueba.
    
    Args:
        model: Modelo entrenado
        X_test: Features de prueba
        y_test: Target de prueba
    
    Returns:
        dict: Métricas de evaluación
    """
    print("\n📊 Evaluando modelo en conjunto de prueba...")
    print("-" * 60)
    
    # Predicciones
    y_pred = model.predict(X_test)
    
    # Métricas
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    results = {
        'MAE': mae,
        'RMSE': rmse,
        'R²': r2
    }
    
    print("\nRegresión Lineal:")
    print(f"   MAE:  {mae:,.2f}")
    print(f"   RMSE: {rmse:,.2f}")
    print(f"   R²:   {r2:.4f}")
    print("-" * 60)
    
    return results


def plot_predictions_vs_actual(model, X_test, y_test, test_df):
    """
    Visualiza predicciones vs valores reales para países seleccionados.
    
    Args:
        model: Modelo entrenado
        X_test: Features de prueba
        y_test: Target de prueba
        test_df: DataFrame con información adicional
    """
    # Hacer predicciones
    y_pred = model.predict(X_test)
    
    # Crear DataFrame con resultados
    results = test_df.copy()
    results['prediction'] = y_pred
    results['actual'] = y_test.values
    
    # Seleccionar top 5 países por producción promedio
    top_countries = results.groupby('country_name')['actual'].mean().nlargest(5).index
    
    _, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.flatten()
    
    for idx, country in enumerate(top_countries):
        if idx >= 6:
            break
        
        country_data = results[results['country_name'] == country].sort_values('year')
        
        ax = axes[idx]
        ax.plot(country_data['year'], country_data['actual'], 
               marker='o', linewidth=2.5, markersize=8, label='Real', color='#2E8B57')
        ax.plot(country_data['year'], country_data['prediction'], 
               marker='s', linewidth=2.5, markersize=8, label='Predicción', 
               color='#DC143C', linestyle='--')
        
        ax.set_xlabel('Año', fontsize=11, fontweight='bold')
        ax.set_ylabel('Producción', fontsize=11, fontweight='bold')
        ax.set_title(f'{country}', fontsize=12, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
    
    # Ocultar ejes sobrantes
    for idx in range(len(top_countries), 6):
        axes[idx].axis('off')
    
    plt.suptitle('Predicciones vs Valores Reales - Regresión Lineal', 
                 fontsize=15, fontweight='bold', y=1.00)
    plt.tight_layout()
    print("\n📊 Gráfico de predicciones generado")
    plt.show()


def predict_future_production(model, df, future_years=5):
    """
    Predice la producción futura usando año y producción histórica.
    
    Args:
        model: Modelo entrenado
        df: DataFrame con datos históricos completos
        future_years: Número de años a predecir
    
    Returns:
        pd.DataFrame: Predicciones futuras por país
    """
    print(f"\n🔮 Prediciendo producción futura ({future_years} años)...")
    
    max_year = df['year'].max()
    future_predictions = []
    
    # Por cada país
    for country_id in df['country_id'].unique():
        country_data = df[df['country_id'] == country_id].sort_values('year')
        country_name = country_data['country_name'].iloc[0]
        
        # Obtener última producción conocida
        last_production = country_data['production'].iloc[-1]
        
        # Predecir cada año futuro
        for year_offset in range(1, future_years + 1):
            future_year = max_year + year_offset
            
            # Usar año y producción del año anterior como features
            x_future = np.array([[future_year, last_production]])
            
            # Predecir
            prediction = model.predict(x_future)[0]
            prediction = max(0, prediction)  # No permitir valores negativos
            
            future_predictions.append({
                'country_id': country_id,
                'country_name': country_name,
                'year': future_year,
                'predicted_production': prediction
            })
            
            # Actualizar last_production para siguiente iteración
            last_production = prediction
    
    future_df = pd.DataFrame(future_predictions)
    
    print(f"✅ Predicciones generadas para {future_df['country_id'].nunique()} países")
    print(f"   Años predichos: {future_df['year'].min()} - {future_df['year'].max()}")
    
    return future_df


def plot_future_predictions(df, future_df, top_n=5):
    """
    Visualiza las predicciones futuras para los principales países productores.
    
    Args:
        df: DataFrame con datos históricos
        future_df: DataFrame con predicciones futuras
        top_n: Número de países a visualizar
    """
    # Seleccionar top países por producción histórica
    top_countries = df.groupby('country_name')['production'].mean().nlargest(top_n).index
    
    _, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.flatten()
    
    for idx, country in enumerate(top_countries):
        if idx >= 6:
            break
        
        ax = axes[idx]
        
        # Datos históricos
        historical = df[df['country_name'] == country].sort_values('year')
        ax.plot(historical['year'], historical['production'], 
               marker='o', linewidth=2.5, markersize=7, label='Histórico', 
               color='#2E8B57')
        
        # Predicciones futuras
        future = future_df[future_df['country_name'] == country].sort_values('year')
        ax.plot(future['year'], future['predicted_production'], 
               marker='s', linewidth=2.5, markersize=7, label='Predicción', 
               color='#DC143C', linestyle='--')
        
        # Línea vertical separando histórico de predicción
        if len(future) > 0:
            ax.axvline(x=historical['year'].max(), color='gray', 
                      linestyle=':', linewidth=2, alpha=0.5)
        
        ax.set_xlabel('Año', fontsize=11, fontweight='bold')
        ax.set_ylabel('Producción', fontsize=11, fontweight='bold')
        ax.set_title(f'{country}', fontsize=12, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
    
    # Ocultar ejes sobrantes
    for idx in range(len(top_countries), 6):
        axes[idx].axis('off')
    
    plt.suptitle('Predicción de Producción Futura de Café (2020-2024)', 
                 fontsize=15, fontweight='bold', y=1.00)
    plt.tight_layout()
    print("\n📊 Gráfico de predicciones futuras generado")
    plt.show()



def main():
    """
    Función principal que ejecuta todo el pipeline de modelado.
    """
    print("=" * 60)
    print("🚀 MODELO PREDICTIVO DE PRODUCCIÓN DE CAFÉ")
    print("=" * 60)
    
    # 1. Cargar datos
    df = load_production_data()
    
    # 2. Crear features
    df = create_features(df)
    
    # 3. Preparar datos de entrenamiento y prueba
    X_train, X_test, y_train, y_test, test_df = prepare_train_test_data(df, test_years=3)
    
    # 4. Entrenar modelo de regresión lineal
    model = train_model(X_train, y_train)
    
    # 5. Evaluar modelo
    results = evaluate_model(model, X_test, y_test)
    
    print("\n🏆 Modelo de Regresión Lineal")
    print(f"   MAE: {results['MAE']:,.2f}")
    print(f"   RMSE: {results['RMSE']:,.2f}")
    print(f"   R²: {results['R²']:.4f}")
    
    # 6. Visualizar predicciones vs valores reales
    plot_predictions_vs_actual(model, X_test, y_test, test_df)
    
    # 7. Predecir producción futura
    future_predictions = predict_future_production(model, df, future_years=5)
    
    # 8. Visualizar predicciones futuras
    plot_future_predictions(df, future_predictions, top_n=5)
    
    # 9. Mostrar muestra de predicciones
    print("\n📋 Muestra de predicciones futuras:")
    print(future_predictions.head(10).to_string(index=False))
    
    # 10. Resumen final
    print("\n" + "=" * 60)
    print("✅ PIPELINE COMPLETADO")
    print("=" * 60)
    print("\nVisualizaciones generadas (no guardadas)")
    print("\n" + "=" * 60)
    
    return df, model, results, future_predictions


if __name__ == '__main__':
    df, model, results, future_predictions = main()
