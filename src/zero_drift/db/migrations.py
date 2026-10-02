"""Database migration executor."""
import sqlite3
from pathlib import Path

def run_migrations(conn: sqlite3.Connection) -> None:
    """Loads and executes the schema.sql file."""
    schema_path = Path(__file__).parent / "schema.sql"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
        
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()
        
    conn.executescript(schema_sql)
    conn.commit()
