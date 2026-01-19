"""Migrate study_guide_cache table to add version tracking"""
from db import get_conn, _get_db_type

def migrate_cache_table():
    db_type = _get_db_type()
    
    if db_type != "postgresql":
        print("SQLite - migration skipped")
        return
    
    print("=" * 60)
    print("MIGRATING study_guide_cache TABLE")
    print("=" * 60)
    
    with get_conn() as conn:
        cursor = conn.cursor()
        
        # Check if version column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'study_guide_cache' 
            AND column_name = 'version'
        """)
        
        if not cursor.fetchone():
            print("\n✓ Adding 'version' column...")
            cursor.execute("""
                ALTER TABLE study_guide_cache 
                ADD COLUMN version INTEGER DEFAULT 1
            """)
            conn.commit()
        else:
            print("✓ 'version' column already exists")
        
        # Check if updated_at column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'study_guide_cache' 
            AND column_name = 'updated_at'
        """)
        
        if not cursor.fetchone():
            print("✓ Adding 'updated_at' column...")
            cursor.execute("""
                ALTER TABLE study_guide_cache 
                ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """)
            conn.commit()
        else:
            print("✓ 'updated_at' column already exists")
        
        # Create index on version
        print("✓ Creating index on version...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_version_cache 
            ON study_guide_cache(version DESC)
        """)
        conn.commit()
        
        # Verify
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'study_guide_cache'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print(f"\n✓ Final table structure ({len(columns)} columns):")
        for col_name, col_type in columns:
            print(f"  - {col_name}: {col_type}")
        
        cursor.close()
    
    print("\n" + "=" * 60)
    print("MIGRATION COMPLETED ✓")
    print("=" * 60)

if __name__ == "__main__":
    migrate_cache_table()
