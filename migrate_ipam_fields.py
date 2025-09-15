"""
File: migrate_ipam_fields.py
Purpose: Add all missing fields to IPAM tables
Created: 2025-01-14
Author: DCMS Team

Revision History:
- v1.0.0: Complete migration to add all missing fields
          Based on SQLAlchemy error showing missing columns

Run this BEFORE starting the app with the new models:
    python migrate_ipam_fields.py

This will add:
- VLANs table: vrf, is_private, is_colo, is_vps, colo_client_id, colo_client_name
- IP Ranges table: netmask
- Networks table: is_public (if missing)
"""

import sqlite3
import sys
import os

# Get the database path
DB_PATH = 'instance/dcms.db'

def check_column_exists(conn, table_name, column_name):
    """Check if a column exists in a table"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    return column_name in column_names

def add_column_safe(conn, table_name, column_name, column_type, default_value=None):
    """Safely add a column if it doesn't exist"""
    if check_column_exists(conn, table_name, column_name):
        print(f"  ✓ Column '{column_name}' already exists in '{table_name}'")
        return False
    
    try:
        cursor = conn.cursor()
        if default_value is not None:
            if isinstance(default_value, bool):
                default = '1' if default_value else '0'
            elif isinstance(default_value, str):
                default = f"'{default_value}'"
            else:
                default = str(default_value)
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} DEFAULT {default}"
        else:
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        
        cursor.execute(sql)
        conn.commit()
        print(f"  ✅ Added column '{column_name}' to '{table_name}'")
        return True
    except Exception as e:
        print(f"  ❌ Error adding column '{column_name}' to '{table_name}': {str(e)}")
        return False

def check_table_exists(conn, table_name):
    """Check if a table exists"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None

def migrate_database():
    """Run all migrations"""
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        print("   Please run the app once to create the database first.")
        return False
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    print(f"Connected to database: {DB_PATH}")
    
    try:
        # ========== MIGRATE VLANS TABLE ==========
        print("\n========== Migrating VLANs Table ==========")
        
        if not check_table_exists(conn, 'vlans'):
            print("  ❌ Table 'vlans' does not exist yet.")
            print("     It will be created when you run the app.")
        else:
            # Add all the new VLAN fields
            add_column_safe(conn, 'vlans', 'vrf', 'VARCHAR(50)')
            add_column_safe(conn, 'vlans', 'is_private', 'BOOLEAN', False)
            add_column_safe(conn, 'vlans', 'is_colo', 'BOOLEAN', False)
            add_column_safe(conn, 'vlans', 'is_vps', 'BOOLEAN', False)
            add_column_safe(conn, 'vlans', 'colo_client_id', 'INTEGER')
            add_column_safe(conn, 'vlans', 'colo_client_name', 'VARCHAR(100)')
            
            # Check for old columns and migrate data
            if check_column_exists(conn, 'vlans', 'vlan_type'):
                print("\n  Migrating old vlan_type data to new boolean fields...")
                cursor = conn.cursor()
                
                # Migrate based on vlan_type
                cursor.execute("""
                    UPDATE vlans 
                    SET is_private = CASE WHEN vlan_type = 'private' THEN 1 ELSE 0 END,
                        is_colo = CASE WHEN vlan_type = 'colo' THEN 1 ELSE 0 END,
                        is_vps = CASE WHEN vlan_type = 'vps' THEN 1 ELSE 0 END
                    WHERE vlan_type IS NOT NULL
                """)
                
                # Migrate customer_id if it exists
                if check_column_exists(conn, 'vlans', 'customer_id'):
                    cursor.execute("""
                        UPDATE vlans 
                        SET colo_client_id = customer_id 
                        WHERE customer_id IS NOT NULL
                    """)
                
                conn.commit()
                print("  ✅ Migrated old vlan_type to new boolean fields")
                
                # Inform about old columns
                print("\n  ℹ️  Old columns retained for safety:")
                print("     - vlan_type")
                print("     - customer_id")
                if check_column_exists(conn, 'vlans', 'svi_configured'):
                    print("     - svi_configured")
                if check_column_exists(conn, 'vlans', 'trunk_ports'):
                    print("     - trunk_ports")
                if check_column_exists(conn, 'vlans', 'access_ports'):
                    print("     - access_ports")
                print("     You can manually remove these later if desired.")
        
        # ========== MIGRATE IP_RANGES TABLE ==========
        print("\n========== Migrating IP Ranges Table ==========")
        
        if not check_table_exists(conn, 'ip_ranges'):
            print("  ❌ Table 'ip_ranges' does not exist yet.")
            print("     It will be created when you run the app.")
        else:
            # Add netmask field
            add_column_safe(conn, 'ip_ranges', 'netmask', 'VARCHAR(15)')
            
            # Try to set default netmasks for existing ranges
            if check_column_exists(conn, 'ip_ranges', 'netmask'):
                print("\n  Setting default netmasks for existing ranges...")
                cursor = conn.cursor()
                
                # Get ranges without netmask
                cursor.execute("SELECT id, start_ip, end_ip FROM ip_ranges WHERE netmask IS NULL")
                ranges = cursor.fetchall()
                
                for range_id, start_ip, end_ip in ranges:
                    # Simple heuristic: if range is in a /24, use that netmask
                    if start_ip and end_ip:
                        # Get the first three octets
                        start_parts = start_ip.split('.')
                        end_parts = end_ip.split('.')
                        
                        if len(start_parts) == 4 and len(end_parts) == 4:
                            if start_parts[:3] == end_parts[:3]:
                                # Same /24 network
                                cursor.execute(
                                    "UPDATE ip_ranges SET netmask = ? WHERE id = ?",
                                    ('255.255.255.0', range_id)
                                )
                                print(f"    Set netmask for range {start_ip}-{end_ip}")
                
                conn.commit()
        
        # ========== MIGRATE NETWORKS TABLE ==========
        print("\n========== Migrating Networks Table ==========")
        
        if not check_table_exists(conn, 'networks'):
            print("  ❌ Table 'networks' does not exist yet.")
            print("     It will be created when you run the app.")
        else:
            # Add is_public field if missing
            add_column_safe(conn, 'networks', 'is_public', 'BOOLEAN', True)
            
            # Auto-detect public/private for existing networks
            if check_column_exists(conn, 'networks', 'is_public'):
                print("\n  Auto-detecting public/private networks...")
                cursor = conn.cursor()
                
                # Update based on RFC1918 ranges
                cursor.execute("""
                    UPDATE networks 
                    SET is_public = 0 
                    WHERE network LIKE '10.%' 
                       OR network LIKE '172.16.%' 
                       OR network LIKE '172.17.%' 
                       OR network LIKE '172.18.%' 
                       OR network LIKE '172.19.%' 
                       OR network LIKE '172.20.%' 
                       OR network LIKE '172.21.%' 
                       OR network LIKE '172.22.%' 
                       OR network LIKE '172.23.%' 
                       OR network LIKE '172.24.%' 
                       OR network LIKE '172.25.%' 
                       OR network LIKE '172.26.%' 
                       OR network LIKE '172.27.%' 
                       OR network LIKE '172.28.%' 
                       OR network LIKE '172.29.%' 
                       OR network LIKE '172.30.%' 
                       OR network LIKE '172.31.%' 
                       OR network LIKE '192.168.%'
                """)
                
                affected = cursor.rowcount
                if affected > 0:
                    print(f"  ✅ Marked {affected} networks as private")
                
                conn.commit()
        
        # ========== VERIFICATION ==========
        print("\n========== Verification ==========")
        
        # Check VLANs table
        if check_table_exists(conn, 'vlans'):
            missing_vlan_cols = []
            required_vlan_cols = ['vrf', 'is_private', 'is_colo', 'is_vps', 'colo_client_id', 'colo_client_name']
            for col in required_vlan_cols:
                if not check_column_exists(conn, 'vlans', col):
                    missing_vlan_cols.append(col)
            
            if missing_vlan_cols:
                print(f"  ⚠️  VLANs table still missing: {', '.join(missing_vlan_cols)}")
            else:
                print("  ✅ VLANs table has all required columns")
        
        # Check IP ranges table
        if check_table_exists(conn, 'ip_ranges'):
            if not check_column_exists(conn, 'ip_ranges', 'netmask'):
                print("  ⚠️  IP Ranges table still missing: netmask")
            else:
                print("  ✅ IP Ranges table has netmask column")
        
        # Check Networks table
        if check_table_exists(conn, 'networks'):
            if not check_column_exists(conn, 'networks', 'is_public'):
                print("  ⚠️  Networks table still missing: is_public")
            else:
                print("  ✅ Networks table has is_public column")
        
        print("\n✅ Migration complete!")
        print("\nYou can now run the app with the updated models:")
        print("  python app.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("IPAM Database Migration")
    print("=" * 60)
    
    # Backup reminder
    print("\n⚠️  IMPORTANT: This will modify your database!")
    print("   It's recommended to backup your database first.")
    print(f"   Database location: {DB_PATH}")
    
    response = input("\nDo you want to continue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        success = migrate_database()
        sys.exit(0 if success else 1)
    else:
        print("\nMigration cancelled.")
        sys.exit(0)