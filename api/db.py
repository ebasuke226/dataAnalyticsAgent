import pandas as pd
import sqlite3

def fetch_data(sql: str) -> pd.DataFrame:
    """Executes the SQL query on the SQLite DB and returns a DataFrame."""
    print(f"Executing SQL: {sql}")
    db_path = "data/odoo_test_data_v2.db"
    try:
        with sqlite3.connect(db_path) as con:
            df = pd.read_sql_query(sql, con)
            print(f"DataFrame loaded in fetch_data:\n{df.head()}") # 追加
            # 日付カラムをdatetime型に変換（例: 'date_order'カラムがある場合）
            if 'date_order' in df.columns:
                df['date_order'] = pd.to_datetime(df['date_order'])
            return df
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        # エラーが発生した場合は空のDataFrameを返すか、例外を再発生させる
        return pd.DataFrame()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return pd.DataFrame()