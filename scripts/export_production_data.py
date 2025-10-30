#!/usr/bin/env python3
"""
Export production historic data from MySQL into CSV files consumable by Streamlit.

Outputs:
 - <out_dir>/production_long.csv  : long format with columns [country_id, country_name, year, production]
 - <out_dir>/countries.csv       : country id / name mapping

Usage:
    python scripts/export_production_data.py --out-dir data/clean/csv

Environment variables to override DB credentials (optional):
    MYSQL_HOST, MYSQL_DB, MYSQL_USER, MYSQL_PASSWORD

"""

import os
import argparse
from pathlib import Path
import pandas as pd
import mysql.connector

# Defaults (local DB only)
DEFAULT_DB = {
    'host': 'localhost',
    'database': 'coffee',
    'user': 'analitica',
    'password': 'Operador1704'
}


def get_connection():
    return mysql.connector.connect(**DEFAULT_DB)


def export(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Conectando a la base de datos...")
    conn = get_connection()

    try:
        print("Leyendo tablas 'production' y 'countries'...")
        df_production = pd.read_sql('SELECT * FROM production', con=conn)
        df_countries = pd.read_sql('SELECT id, name FROM countries', con=conn)

        print(f"Production shape: {df_production.shape}")
        print(f"Countries shape: {df_countries.shape}")

        # Identify year columns
        ignore_cols = {'id', 'country_id', 'coffee_type', 'total'}
        year_cols = [col for col in df_production.columns if col not in ignore_cols]

        if not year_cols:
            raise RuntimeError('No se encontraron columnas de años en la tabla production')

        print(f"Columnas de año detectadas: {len(year_cols)} ({year_cols[0]} - {year_cols[-1]})")

        # Transform to long format
        data_long = []
        for _, row in df_production.iterrows():
            country_id = row['country_id']
            for year_col in year_cols:
                try:
                    year = int(str(year_col).split('/')[0])
                except Exception:
                    # if column name is already a year number
                    try:
                        year = int(year_col)
                    except Exception:
                        # fallback: keep original column name
                        year = year_col

                production = row[year_col]
                if pd.notna(production):
                    data_long.append({'country_id': country_id, 'year': year, 'production': production})

        df_long = pd.DataFrame(data_long)

        # Merge country names
        df_long = df_long.merge(df_countries.rename(columns={'id': 'country_id', 'name': 'country_name'}), on='country_id', how='left')

        # Sort
        df_long = df_long.sort_values(['country_id', 'year']).reset_index(drop=True)

        # Save outputs
        prod_path = out_dir / 'production_long.csv'
        countries_path = out_dir / 'countries.csv'

        df_long.to_csv(prod_path, index=False)
        df_countries.to_csv(countries_path, index=False)

        print(f"Guardado: {prod_path} ({df_long.shape[0]} filas)")
        print(f"Guardado: {countries_path} ({df_countries.shape[0]} filas)")

    finally:
        conn.close()


if __name__ == '__main__':
    export(Path("./data/predictionData"))
