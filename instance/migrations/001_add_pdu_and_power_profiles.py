"""
File: instance/migrations/001_add_pdu_and_power_profiles.py
Purpose: Migration script to add PDU model field and power profiles tables
Version: 1.0.0
Author: iambilky
Created: 2024-01-09

Revision History:
- v1.0.0 (2024-01-09): Initial migration for PDU enhancements and power profiles

Usage:
    python instance/migrations/001_add_pdu_and_power_profiles.py

Notes:
- Adds 'model' field to PDU table
- Creates power_profiles table
- Populates default TCH equipment power profiles
- Safe to run multiple times (checks if already applied)
"""

import sys
import os
import sqlite3
from datetime import datetime

# ========== CONFIGURATION ==========

DB_PATH = r'C:\Users\wgkish\Desktop\tchtits\instance\dcms.db'
MIGRATION_NAME = '001_add_pdu_and_power_profiles'

# ========== TCH EQUIPMENT PROFILES ==========

TCH_PROFILES = [
    # Dell Rx20 Generation
    ('Dell', 'R420', 'server', 'Rx20', 120, 165, 550, 2, '550W, 750W', 1, '1U, Dual Xeon E5-2400 series, 64GB typical'),
    ('Dell', 'R620', 'server', 'Rx20', 130, 175, 495, 2, '495W, 750W', 1, '1U, Dual Xeon E5-2600 series, 64GB typical'),
    ('Dell', 'R720', 'server', 'Rx20', 180, 265, 750, 2, '750W, 1100W', 2, '2U, Dual Xeon E5-2600 series, 64GB typical'),
    
    # Dell Rx30 Generation
    ('Dell', 'R430', 'server', 'Rx30', 125, 185, 550, 2, '450W, 550W', 1, '1U, Dual Xeon E5-2600 v3/v4, 64GB typical'),
    ('Dell', 'R630', 'server', 'Rx30', 135, 195, 495, 2, '495W, 750W', 1, '1U, Dual Xeon E5-2600 v3/v4, 64GB typical'),
    ('Dell', 'R730', 'server', 'Rx30', 190, 280, 750, 2, '750W, 1100W', 2, '2U, Dual Xeon E5-2600 v3/v4, 64GB typical'),
    
    # Dell Rx40 Generation
    ('Dell', 'R440', 'server', 'Rx40', 130, 200, 550, 2, '550W, 750W', 1, '1U, Dual Xeon Scalable, 64GB typical'),
    ('Dell', 'R640', 'server', 'Rx40', 140, 210, 495, 2, '495W, 750W', 1, '1U, Dual Xeon Scalable, 64GB typical'),
    ('Dell', 'R740', 'server', 'Rx40', 200, 300, 750, 2, '750W, 1100W, 1600W', 2, '2U, Dual Xeon Scalable, 64GB typical'),
    
    # Dell Rx10 Generation (Legacy)
    ('Dell', 'R410', 'server', 'Rx10', 110, 150, 480, 2, '480W, 580W', 1, '1U LEGACY - Being phased out'),
    ('Dell', 'R610', 'server', 'Rx10', 120, 160, 502, 2, '502W, 717W', 1, '1U LEGACY - Being phased out'),
    ('Dell', 'R710', 'server', 'Rx10', 170, 250, 870, 2, '570W, 870W', 2, '2U LEGACY - Being phased out'),
    
    # Custom Servers
    ('Custom', 'Custom 1U', 'server', 'Custom', 100, 150, 400, 1, 'Varies', 1, 'Generic profile for custom built 1U servers'),
    ('Custom', 'Custom 2U', 'server', 'Custom', 150, 250, 600, 1, 'Varies', 2, 'Generic profile for custom built 2U servers'),
    
    # MikroTik Switches (Private Network)
    ('MikroTik', 'CRS354-48G-4S+2Q+', 'switch', 'CRS3xx', 50, 70, 90, 1, 'Internal', 1, '48x1G + 4xSFP+ + 2xQSFP+ private network switch'),
    ('MikroTik', 'CRS326-24S+2Q+', 'switch', 'CRS3xx', 35, 45, 80, 1, 'Internal', 1, '24xSFP+ + 2xQSFP+ private network 10G switch'),
    ('MikroTik', 'CSS326-24G-2S+', 'switch', 'CSS3xx', 25, 35, 50, 1, 'Internal', 1, '24x1G + 2xSFP+ SwOS private network switch'),
    
    # Arista Switches (Public Network)
    ('Arista', 'DCS-7048T-A', 'switch', '7048', 130, 165, 200, 2, '460W', 1, '48x1G copper public network switch'),
    ('Arista', 'DCS-7050S-52', 'switch', '7050', 200, 275, 350, 2, '460W', 1, '52x10G SFP+ public network switch'),
]

# ========== MIGRATION FUNCTIONS ==========

def check_migration_applied(conn):
    """
    Check if this migration has already been applied
    """
    cursor = conn.cursor()
    
    # Check if power_profiles table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='power_profiles'
    """)
    if cursor.fetchone():
        print(f"✓ Migration {MIGRATION_NAME} already applied - power_profiles table exists")
        return True
    
    # Check if PDU model column exists
    cursor.execute("PRAGMA table_info(pdus)")
    columns = cursor.fetchall()
    for col in columns:
        if col[1] == 'model':
            print(f"✓ Migration {MIGRATION_NAME} partially applied - PDU model field exists")
            # Continue to create power_profiles if needed
            return False
    
    return False

def add_pdu_model_field(conn):
    """
    Add model field to PDU table
    """
    cursor = conn.cursor()
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(pdus)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    if 'model' not in column_names:
        print("Adding 'model' field to PDU table...")
        cursor.execute("""
            ALTER TABLE pdus 
            ADD COLUMN model VARCHAR(50)
        """)
        conn.commit()
        print("✓ Added 'model' field to PDU table")
    else:
        print("✓ PDU 'model' field already exists")

def create_power_profiles_table(conn):
    """
    Create the power_profiles table
    """
    cursor = conn.cursor()
    
    print("Creating power_profiles table...")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS power_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            manufacturer VARCHAR(50) NOT NULL,
            model VARCHAR(100) NOT NULL UNIQUE,
            equipment_type VARCHAR(20) NOT NULL,
            generation VARCHAR(20),
            idle_watts FLOAT NOT NULL,
            typical_watts FLOAT NOT NULL,
            max_watts FLOAT NOT NULL,
            psu_count_typical INTEGER DEFAULT 2,
            psu_watts_common VARCHAR(50),
            rack_units INTEGER DEFAULT 1,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    print("✓ Created power_profiles table")

def populate_power_profiles(conn):
    """
    Populate default TCH equipment power profiles
    """
    cursor = conn.cursor()
    
    # Check if profiles already exist
    cursor.execute("SELECT COUNT(*) FROM power_profiles")
    count = cursor.fetchone()[0]
    
    if count > 0:
        print(f"✓ Power profiles already populated ({count} profiles exist)")
        return
    
    print("Populating TCH equipment power profiles...")
    
    for profile in TCH_PROFILES:
        cursor.execute("""
            INSERT INTO power_profiles (
                manufacturer, model, equipment_type, generation,
                idle_watts, typical_watts, max_watts,
                psu_count_typical, psu_watts_common, rack_units, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, profile)
    
    conn.commit()
    print(f"✓ Added {len(TCH_PROFILES)} TCH equipment power profiles")

def verify_migration(conn):
    """
    Verify the migration was successful
    """
    cursor = conn.cursor()
    
    print("\n========== VERIFICATION ==========")
    
    # Check PDU table
    cursor.execute("PRAGMA table_info(pdus)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    if 'model' in column_names:
        print("✓ PDU table has 'model' field")
    else:
        print("✗ PDU table missing 'model' field")
    
    # Check power_profiles table
    cursor.execute("SELECT COUNT(*) FROM power_profiles")
    profile_count = cursor.fetchone()[0]
    print(f"✓ Power profiles table has {profile_count} entries")
    
    # Show sample profiles
    cursor.execute("SELECT manufacturer, model, typical_watts FROM power_profiles LIMIT 5")
    samples = cursor.fetchall()
    print("\nSample power profiles:")
    for sample in samples:
        print(f"  - {sample[0]} {sample[1]}: {sample[2]}W typical")

# ========== MAIN EXECUTION ==========

def main():
    """
    Run the migration
    """
    print(f"\n========== RUNNING MIGRATION: {MIGRATION_NAME} ==========")
    print(f"Database: {DB_PATH}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"✗ ERROR: Database not found at {DB_PATH}")
        print("  Please ensure the application has been run at least once to create the database.")
        sys.exit(1)
    
    # Connect to database
    try:
        conn = sqlite3.connect(DB_PATH)
        print("✓ Connected to database")
    except Exception as e:
        print(f"✗ ERROR: Failed to connect to database: {e}")
        sys.exit(1)
    
    try:
        # Check if already applied
        if not check_migration_applied(conn):
            # Run migrations
            add_pdu_model_field(conn)
            create_power_profiles_table(conn)
            populate_power_profiles(conn)
        else:
            # Check if we need to create power_profiles table
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='power_profiles'
            """)
            if not cursor.fetchone():
                create_power_profiles_table(conn)
                populate_power_profiles(conn)
        
        # Verify
        verify_migration(conn)
        
        print(f"\n✓ Migration {MIGRATION_NAME} completed successfully!")
        
    except Exception as e:
        print(f"\n✗ ERROR during migration: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()