"""
File: instance/migrations/002_fix_pdu_model_field.py
Purpose: Fix script to add missing PDU model field
Version: 1.0.0
Author: iambilky
Created: 2024-01-09

Revision History:
- v1.0.0 (2024-01-09): Fix to add missing PDU model field

Usage:
    python instance/migrations/002_fix_pdu_model_field.py

Notes:
- Specifically adds the model field to PDU table
- Safe to run multiple times
"""

import sys
import os
import sqlite3
from datetime import datetime

# ========== CONFIGURATION ==========

# Windows path - use raw string
DB_PATH = r'C:\Users\wgkish\Desktop\tchtits\instance\dcms.db'
MIGRATION_NAME = '002_fix_pdu_model_field'

# ========== MIGRATION FUNCTIONS ==========

def check_pdu_model_exists(conn):
    """
    Check if PDU model field exists
    """
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(pdus)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    return 'model' in column_names

def check_pdus_table_exists(conn):
    """
    Check if PDUs table exists
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='pdus'
    """)
    return cursor.fetchone() is not None

def add_pdu_model_field(conn):
    """
    Add model field to PDU table
    """
    cursor = conn.cursor()
    
    try:
        print("Adding 'model' field to PDU table...")
        cursor.execute("""
            ALTER TABLE pdus 
            ADD COLUMN model VARCHAR(50)
        """)
        conn.commit()
        print("✓ Successfully added 'model' field to PDU table")
        return True
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("✓ PDU 'model' field already exists")
            return False
        else:
            raise e

def verify_migration(conn):
    """
    Verify the migration was successful
    """
    cursor = conn.cursor()
    
    print("\n========== VERIFICATION ==========")
    
    # Check PDU table structure
    cursor.execute("PRAGMA table_info(pdus)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    print("\nPDU table columns:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    if 'model' in column_names:
        print("\n✓ SUCCESS: PDU table now has 'model' field")
    else:
        print("\n✗ ERROR: PDU table still missing 'model' field")
        return False
    
    return True

# ========== MAIN EXECUTION ==========

def main():
    """
    Run the migration fix
    """
    print(f"\n========== RUNNING MIGRATION FIX: {MIGRATION_NAME} ==========")
    print(f"Database: {DB_PATH}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"✗ ERROR: Database not found at {DB_PATH}")
        sys.exit(1)
    
    # Connect to database
    try:
        conn = sqlite3.connect(DB_PATH)
        print("✓ Connected to database")
    except Exception as e:
        print(f"✗ ERROR: Failed to connect to database: {e}")
        sys.exit(1)
    
    try:
        # Check if PDUs table exists
        if not check_pdus_table_exists(conn):
            print("✗ ERROR: PDUs table does not exist!")
            print("  Please run the application first to create all tables.")
            sys.exit(1)
        
        print("✓ PDUs table exists")
        
        # Check current state
        if check_pdu_model_exists(conn):
            print("✓ PDU 'model' field already exists - no action needed")
        else:
            print("✗ PDU 'model' field is missing - adding it now...")
            add_pdu_model_field(conn)
        
        # Verify
        if verify_migration(conn):
            print(f"\n✓ Migration fix {MIGRATION_NAME} completed successfully!")
        else:
            print(f"\n✗ Migration fix {MIGRATION_NAME} failed!")
            sys.exit(1)
        
    except Exception as e:
        print(f"\n✗ ERROR during migration: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()