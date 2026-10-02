"""Database connection layer with WAL and strict constraints."""
import sqlite3
from pathlib import Path

def get_connection(db_path: str = "aegis_zero.db") -> sqlite3.Connection:
    """
    Opens SQLite connection and enforces mandatory Phase 1 rules:
    1. WAL (Write-Ahead Logging) enabled
    2. Foreign Keys enabled
    """
    conn = sqlite3.connect(db_path)
    
    # Enable WAL mode for concurrent read/write safety
    conn.execute("PRAGMA journal_mode=WAL;")
    
    # Enforce foreign key constraints
    conn.execute("PRAGMA foreign_keys=ON;")
    
    conn.row_factory = sqlite3.Row
    return conn
