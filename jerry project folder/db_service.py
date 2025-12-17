import sqlite3
import pandas as pd
import shutil
import os

DB_NAME = "properties.db"
BACKUP_DB = "properties_backup.db"

# -----------------------
# Initialize Database
# -----------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address TEXT,
            price TEXT,
            size TEXT,
            systems TEXT
        )
    """)
    conn.commit()
    conn.close()

# -----------------------
# Add Property (simple insert)
# -----------------------
def add_property(address, price, size, systems):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO properties (address, price, size, systems) VALUES (?, ?, ?, ?)",
        (address, price, size, systems)
    )
    conn.commit()
    conn.close()

# -----------------------
# Add or Update Property (avoid duplicates)
# -----------------------
def add_or_update_property(address, price, size, systems):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # check if same address already exists
    cursor.execute("SELECT id FROM properties WHERE address = ?", (address,))
    row = cursor.fetchone()

    if row:
        # Update existing property
        cursor.execute(
            "UPDATE properties SET price=?, size=?, systems=? WHERE id=?",
            (price, size, systems, row[0])
        )
    else:
        # Insert new property
        cursor.execute(
            "INSERT INTO properties (address, price, size, systems) VALUES (?, ?, ?, ?)",
            (address, price, size, systems)
        )

    conn.commit()
    conn.close()

# -----------------------
# Get All Properties
# -----------------------
def get_all_properties():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM properties", conn)
    conn.close()
    return df

# -----------------------
# Delete Property by ID
# -----------------------
def delete_property_by_id(property_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM properties WHERE id=?", (property_id,))
    conn.commit()
    conn.close()

# -----------------------
# Clear All Properties (with backup)
# -----------------------
def clear_properties():
    if os.path.exists(DB_NAME):
        shutil.copy(DB_NAME, BACKUP_DB)  # backup before clearing
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM properties")
    conn.commit()
    conn.close()

# -----------------------
# Restore Properties from Backup
# -----------------------
def restore_properties():
    if os.path.exists(BACKUP_DB):
        shutil.copy(BACKUP_DB, DB_NAME)
