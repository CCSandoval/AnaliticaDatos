import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import joblib
import traceback
import sys

# Configure Streamlit page for better mobile compatibility
st.set_page_config(
    page_title="Predicción de Café",
    page_icon="☕️",
    initial_sidebar_state="collapsed"
)

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

def main():
	# Add a simple status indicator
	with st.spinner('Cargando aplicación...'):
		pass
	
	st.title('☕️ Predicciones de Producción de Café')

	st.markdown(f'Carga el modelo entrenado y los datos históricos exportados localmente. Selecciona un país para ver la predicción de los próximos {years_ahead} años.')

	# Initialize session state for better stability
	if 'initialized' not in st.session_state:
		st.session_state.initialized = True

	model = load_model(MODEL_PATH)
	if model is None:
		st.warning(f"No se encontró el modelo en '{MODEL_PATH}'. Ejecuta el notebook para entrenar y guardarlo en esa ruta.")
		return

	# Load exported data
	prod_path = Path('data/prediction_data/production_long.csv')
	countries_path = Path('data/prediction_data/countries.csv')

	if not prod_path.exists() or not countries_path.exists():
		st.warning('No se encontraron los CSV exportados en data/prediction_data/')
		return

	df_long = pd.read_csv(prod_path)
	df_countries = pd.read_csv(countries_path)

	# Build country selector
	country_names = df_countries['name'].tolist() if 'name' in df_countries.columns else df_long['country_name'].unique().tolist()
	country = st.selectbox('Selecciona un país', options=country_names)

	# Extract historical series for selected country
	history = df_long[df_long['country_name'] == country].sort_values('year')
	if history.empty:
		st.info('No hay datos históricos para el país seleccionado.')
		return

	st.subheader(f'Histórico de producción - {country}')
	st.line_chart(history.set_index('year')['production'])
	# More readable headers for the historical table
	df_hist_display = history[['year', 'production']].reset_index(drop=True).rename(columns={
		'year': 'Año',
		'production': 'Producción (kg)'
	})

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

	st.subheader(f'Histórico vs Predicción {country}')
	st.line_chart(combined)


if __name__ == '__main__':
	try:
		main()
	except Exception as e:
		tb = traceback.format_exc()
		try:
			st.error('La aplicación encontró un error al iniciarse. Revisa el detalle abajo.')
			st.code(tb)
		except Exception:
			# If Streamlit isn't available for UI rendering, print to stderr so platform logs capture it.
			print('FATAL ERROR - no se pudo renderizar el error en Streamlit UI', file=sys.stderr)
			print(tb, file=sys.stderr)
