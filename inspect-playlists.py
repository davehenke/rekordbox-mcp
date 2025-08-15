#!/usr/bin/env python3
"""
Inspect rekordbox playlist data and schema.
"""

import pyrekordbox

def main():
    print("🎵 Inspecting Rekordbox Playlist Data")
    print("=" * 50)
    
    try:
        db = pyrekordbox.Rekordbox6Database()
        
        # Check what playlist methods are available
        print("🔍 Available database methods:")
        methods = [method for method in dir(db) if not method.startswith('_') and callable(getattr(db, method))]
        playlist_methods = [m for m in methods if 'playlist' in m.lower()]
        
        if playlist_methods:
            print("  Playlist-related methods:")
            for method in playlist_methods:
                print(f"    - {method}")
        else:
            print("  No obvious playlist methods found")
        
        print(f"\n  All methods: {methods}")
        
        # Try to get playlists using different approaches
        print("\n🎼 Attempting to access playlists...")
        
        # Try get_playlists if it exists
        if hasattr(db, 'get_playlists'):
            try:
                playlists = db.get_playlists()
                print(f"✅ get_playlists() returned: {type(playlists)}")
                playlists_list = list(playlists)
                print(f"   Found {len(playlists_list)} playlists")
                if playlists_list:
                    first_playlist = playlists_list[0]
                    print(f"   First playlist type: {type(first_playlist)}")
                    print(f"   First playlist attributes: {[attr for attr in dir(first_playlist) if not attr.startswith('_')]}")
            except Exception as e:
                print(f"❌ get_playlists() failed: {e}")
        
        # Check if there are other table names we can inspect
        print("\n🗃️ Inspecting database structure...")
        try:
            # Try to access the SQLAlchemy engine to see table names
            engine = db.engine
            if engine:
                from sqlalchemy import inspect
                inspector = inspect(engine)
                tables = inspector.get_table_names()
                print(f"📋 Database tables: {tables}")
                
                playlist_tables = [t for t in tables if 'playlist' in t.lower() or 'djmd' in t.lower()]
                print(f"🎼 Playlist-related tables: {playlist_tables}")
        except Exception as e:
            print(f"❌ Could not inspect database structure: {e}")
        
        # Try direct SQL query approach
        print("\n🔧 Trying direct database access...")
        try:
            # Check if we can access the session
            if hasattr(db, 'session'):
                session = db.session
                print(f"✅ Database session available: {session}")
                
                # Try to find playlist-related models
                from sqlalchemy.ext.declarative import declarative_base
                Base = declarative_base()
                
                # Look for DjmdPlaylist or similar
                try:
                    result = session.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%playlist%' OR name LIKE '%Djmd%';")
                    playlist_tables = result.fetchall()
                    print(f"📋 Playlist tables from SQL: {playlist_tables}")
                except Exception as e:
                    print(f"❌ SQL query failed: {e}")
                    
        except Exception as e:
            print(f"❌ Direct database access failed: {e}")
        
        print("\n✅ Playlist inspection completed!")
        
    except Exception as e:
        print(f"❌ Error inspecting playlists: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())