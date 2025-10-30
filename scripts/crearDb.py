import pandas as pd
import mysql.connector
from mysql.connector import errorcode

def create_table(cursor, table_name, df):
    columns = []
    for col, dtype in zip(df.columns, df.dtypes):
        if "int" in str(dtype):
            max_val = df[col].max(skipna=True)
            if pd.notna(max_val) and abs(max_val) > 2000000000:
                sql_type = "BIGINT"
            else:
                sql_type = "INT"
        elif "float" in str(dtype):
            sql_type = "DOUBLE"
        else:
            sql_type = "VARCHAR(255)"
        col_name = col.replace(" ", "_").replace("-", "_")
        columns.append(f"`{col_name}` {sql_type}")
    sql = f"CREATE TABLE IF NOT EXISTS `{table_name}` ({', '.join(columns)});"
    cursor.execute(sql)
    print(f"Tabla {table_name} creada")

def insert_data(cursor, table_name, df):
    cols = [col.replace(" ", "_").replace("-", "_") for col in df.columns]
    placeholders = ", ".join(["%s"] * len(cols))

    insert_sql = f"INSERT INTO {table_name} ({", ".join('`'+c+'`' for c in cols)}) VALUES ({placeholders})"

    data = [tuple(row) for row in df.itertuples(index=False, name=None)]
    cursor.executemany(insert_sql, data)

def main():
    DB_HOST = "localhost"
    DB_DATABASE = "coffee"
    DB_USER = "analitica"
    DB_PASSWORD = "Operador1704"
    conn = mysql.connector.connect(
            host=DB_HOST,
            database=DB_DATABASE,
            user=DB_USER,
            password=DB_PASSWORD
        )
    print("✅ Conectado a DB")
    
    cursor = conn.cursor()

    xls = pd.ExcelFile("./data/clean/Dataset.xlsx")
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        df = df.fillna("")
        create_table(cursor, sheet_name, df)
        insert_data(cursor, sheet_name, df)
        conn.commit()
        print(f"✅ {len(df)} insertados en tabla '{sheet_name}'")

    cursor.close()
    conn.close()
    print("Fin")

if __name__ == "__main__":
    main()