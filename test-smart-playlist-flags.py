#!/usr/bin/env python3
"""
Test the updated smart playlist flag implementation.
"""

import asyncio
from rekordbox_mcp.database import RekordboxDatabase

async def test_smart_playlist_flags():
    print("🧠 Testing Smart Playlist Flag Implementation")
    print("=" * 60)
    
    try:
        db = RekordboxDatabase()
        await db.connect()
        
        # Get all playlists
        playlists = await db.get_playlists()
        print(f"✅ Found {len(playlists)} playlists")
        
        # Categorize playlists
        smart_playlists = [p for p in playlists if p.is_smart_playlist]
        regular_playlists = [p for p in playlists if not p.is_smart_playlist and not p.is_folder]
        folders = [p for p in playlists if p.is_folder]
        
        print(f"\n📊 Playlist breakdown:")
        print(f"  🧠 Smart playlists: {len(smart_playlists)}")
        print(f"  📋 Regular playlists: {len(regular_playlists)}")
        print(f"  📁 Folders: {len(folders)}")
        
        print(f"\n🧠 Smart playlists (showing track counts and criteria):")
        for playlist in smart_playlists:
            print(f"  '{playlist.name}': {playlist.track_count} tracks (ID: {playlist.id})")
            if playlist.smart_criteria:
                # Extract key criteria from the XML
                criteria_str = playlist.smart_criteria
                if 'artist' in criteria_str:
                    # Try to extract artist name
                    import re
                    artist_match = re.search(r'ValueLeft="([^"]+)"', criteria_str)
                    if artist_match:
                        print(f"    → Criteria: Artist contains '{artist_match.group(1)}'")
                elif 'stockDate' in criteria_str:
                    # Time-based criteria
                    value_match = re.search(r'ValueLeft="(\d+)"', criteria_str)
                    unit_match = re.search(r'ValueUnit="([^"]*)"', criteria_str)
                    if value_match and unit_match:
                        print(f"    → Criteria: Added in last {value_match.group(1)} {unit_match.group(1)}(s)")
                elif 'counter' in criteria_str:
                    # Play count criteria
                    value_match = re.search(r'ValueLeft="(\d+)"', criteria_str)
                    if value_match:
                        print(f"    → Criteria: Play count ≤ {value_match.group(1)}")
                else:
                    print(f"    → Criteria: {criteria_str[:100]}...")
        
        print(f"\n📁 Folder structure:")
        for folder in folders:
            print(f"  '{folder.name}' (ID: {folder.id})")
            # Find child playlists
            children = [p for p in playlists if p.parent_id == folder.id]
            for child in children:
                playlist_type = "🧠 Smart" if child.is_smart_playlist else "📋 Regular"
                print(f"    ├── {playlist_type}: '{child.name}' ({child.track_count} tracks)")
        
        print(f"\n📋 Regular playlists:")
        for playlist in regular_playlists:
            print(f"  '{playlist.name}': {playlist.track_count} tracks")
        
        print(f"\n✅ Smart playlist flag test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(asyncio.run(test_smart_playlist_flags()))