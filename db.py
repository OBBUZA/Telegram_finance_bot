import sqlite3
import pandas as pd
import os

DB_NAME = "finance.db"
DEFAULT_TABLE = "finance_data_finished"

def get_connection():
    return sqlite3.connect(DB_NAME)

def import_stock_csv(csv_path):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_dir, csv_path)          #Полный путь к файлу, ибо не работает

    if not os.path.exists(full_path):
        raise FileNotFoundError(f"CSV not found: {full_path}")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(f"""
        SELECT COUNT(*) FROM {DEFAULT_TABLE}
        WHERE user_id IS NULL""")
    
    if cur.fetchone()[0] > 0:
        conn.close()
        return

    df = pd.read_csv(full_path)

    for _, row in df.iterrows():
        cur.execute(f"""
            INSERT INTO {DEFAULT_TABLE}
            (user_id, date, category, amount, type, company)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (None, row["date"], row["category"], row["amount"], row["type"], row["company"]))

    conn.commit()
    conn.close()

def import_user_csv(csv_path: str, user_id: int):
    conn = get_connection()
    cur = conn.cursor()

    df = pd.read_csv(csv_path)
    df["type"] = df["type"].str.strip().str.lower()
    df["category"] = df["category"].str.strip()
    df["company"] = df["company"].str.strip()

    required_cols = {"date", "category", "amount", "type", "company"}
    if not required_cols.issubset(df.columns):
        conn.close()
        raise ValueError("Неверный формат CSV")

    for _, row in df.iterrows():
        cur.execute(f"""
            INSERT INTO {DEFAULT_TABLE}
            (user_id, date, category, amount, type, company)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, row["date"], row["category"], row["amount"], row["type"], row["company"]))

    conn.commit()
    conn.close()

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(f"""
    CREATE TABLE IF NOT EXISTS {DEFAULT_TABLE} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT,
        category TEXT,
        type TEXT,
        amount REAL,
        company TEXT)""")

    conn.commit()
    conn.close()

def get_user_data(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT date, type, category, company, amount
        FROM finance_data_finished
        WHERE user_id = ?""", (user_id,))
    rows = cur.fetchall()

    if not rows:
        cur.execute("""
            SELECT date, type, category, company, amount
            FROM finance_data_finished
            WHERE user_id IS NULL""")
        rows = cur.fetchall()

    conn.close()
    return rows

