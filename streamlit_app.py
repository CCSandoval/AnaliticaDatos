import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import joblib

years_ahead = 10
MODEL_PATH = Path('models/linear_regression_advanced.joblib')


@st.cache_data
def load_model(path: Path):
	if path.exists():
		try:
			return joblib.load(path)
		except Exception as e:
			st.error(f"Error cargando el modelo: {e}")
			return None
	return None


def build_mock_data():
	"""Construye datos ficticios por país y calcula las 6 features usadas por el modelo.

	Cada país tiene un pequeño historial de producción; calculamos rolling mean/std
	sobre los últimos 3 años, lag1, pct_change, interacción mean_x_pct y volatility_norm.
	"""
	mocked = [
		{"country_name": "Country A", "history": [950, 1000, 1100]},
		{"country_name": "Country B", "history": [2000, 1900, 1950]},
		{"country_name": "Country C", "history": [300, 400, 350]},
		{"country_name": "Country D", "history": [1200, 1250, 1300]},
	]

	rows = []
	for entry in mocked:
		name = entry['country_name']
		hist = entry['history']
		# asegurar al menos 3 valores
		recent = hist[-3:]
		rolling_mean = float(np.mean(recent))
		rolling_std = float(np.std(recent))
		prod_lag1 = float(recent[-1])
		pct_change = 0.0
		if len(recent) >= 2 and recent[-2] != 0:
			pct_change = float((recent[-1] - recent[-2]) / recent[-2])
		mean_x_pct = rolling_mean * pct_change
		volatility_norm = rolling_std / (rolling_mean + 1) if rolling_mean > 0 else 0.0

		rows.append({
			'country_name': name,
			'rolling_mean_3y': rolling_mean,
			'rolling_std_3y': rolling_std,
			'production_lag1': prod_lag1,
			'pct_change_1y': pct_change,
			'mean_x_pct': mean_x_pct,
			'volatility_norm': volatility_norm,
		})

	return pd.DataFrame(rows)


def main():
	st.title('Predicciones de Producción de Café')

	st.markdown(f'Carga el modelo entrenado y los datos históricos exportados localmente. Selecciona un país para ver la predicción de los próximos {years_ahead} años.')

	model = load_model(MODEL_PATH)
	if model is None:
		st.warning(f"No se encontró el modelo en '{MODEL_PATH}'. Ejecuta el notebook para entrenar y guardarlo en esa ruta.")
		st.stop()

	# Load exported data
	prod_path = Path('data/prediction_data/production_long.csv')
	countries_path = Path('data/prediction_data/countries.csv')

	if not prod_path.exists() or not countries_path.exists():
		st.warning('No se encontraron los CSV exportados en data/prediction_data/. Ejecuta scripts/export_production_data.py primero.')
		st.stop()

	df_long = pd.read_csv(prod_path)
	df_countries = pd.read_csv(countries_path)

	# Build country selector
	country_names = df_countries['name'].tolist() if 'name' in df_countries.columns else df_long['country_name'].unique().tolist()
	country = st.selectbox('Selecciona un país', options=country_names)

	# Extract historical series for selected country
	history = df_long[df_long['country_name'] == country].sort_values('year')
	if history.empty:
		st.info('No hay datos históricos para el país seleccionado.')
		st.stop()

	st.subheader(f'Histórico de producción - {country}')
	st.line_chart(history.set_index('year')['production'])
	# More readable headers for the historical table
	df_hist_display = history[['year', 'production']].reset_index(drop=True).rename(columns={
		'year': 'Año',
		'production': 'Producción (kg)'
	})
	st.dataframe(df_hist_display)

	# Prepare production history list
	production_history = history['production'].astype(float).tolist()
	last_year = int(history['year'].max())

	predictions = [{'year': last_year, 'predicted_production': float(production_history[-1])}]

	for i in range(1, years_ahead + 1):
		recent = production_history[-3:]
		rolling_mean = float(np.mean(recent))
		rolling_std = float(np.std(recent))
		prod_lag1 = float(production_history[-1])
		if len(recent) >= 2 and recent[-2] != 0:
			pct_change = float((recent[-1] - recent[-2]) / recent[-2])
		else:
			pct_change = 0.0
		mean_x_pct = rolling_mean * pct_change
		volatility_norm = rolling_std / (rolling_mean + 1) if rolling_mean > 0 else 0.0

		X_pred = np.array([[rolling_mean, rolling_std, prod_lag1, pct_change, mean_x_pct, volatility_norm]])
		pred = model.predict(X_pred)[0]
		if pred < 0:
			pred = rolling_mean

		pred_year = last_year + i
		predictions.append({'year': pred_year, 'predicted_production': float(pred)})

		# update history
		production_history.append(float(pred))

	df_preds = pd.DataFrame(predictions)

	st.subheader(f'Predicción (próximos {years_ahead} años)')
	# Show only the future years in the table (exclude the anchor last_year)
	df_preds_future = df_preds[df_preds['year'] > last_year].reset_index(drop=True).rename(columns={
		'year': 'Año',
		'predicted_production': 'Predicción (kg)'
	})
	st.table(df_preds_future)

	# Combined chart with separate series for historical vs prediction
	hist_df = history[['year', 'production']].rename(columns={'production': 'historical'}).set_index('year')
	pred_df = df_preds.rename(columns={'predicted_production': 'prediction'}).set_index('year')

	combined = pd.concat([hist_df, pred_df], axis=1)
	# Ensure years are sorted
	combined = combined.sort_index()

	st.subheader('Histórico vs Predicción')
	st.line_chart(combined)


if __name__ == '__main__':
	main()
