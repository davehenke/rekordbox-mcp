#!/usr/bin/env python3
"""
Test the database field mappings to ensure they work correctly.
"""

import asyncio
from rekordbox_mcp.database import RekordboxDatabase
from rekordbox_mcp.models import SearchOptions

async def test_mappings():
    print("🧪 Testing Database Field Mappings")
    print("=" * 40)
    
    try:
        db = RekordboxDatabase()
        await db.connect()
        
        print("✅ Database connected successfully")
        
        # Test basic track search
        print("\n🔍 Testing track search...")
        search_options = SearchOptions(limit=3)
        tracks = await db.search_tracks(search_options)
        
        print(f"✅ Found {len(tracks)} tracks")
        
        if tracks:
            track = tracks[0]
            print(f"\n📀 Sample track:")
            print(f"  ID: {track.id}")
            print(f"  Title: {track.title}")
            print(f"  Artist: {track.artist}")
            print(f"  Album: {track.album}")
            print(f"  Genre: {track.genre}")
            print(f"  BPM: {track.bpm}")
            print(f"  Key: {track.key}")
            print(f"  Rating: {track.rating}")
            print(f"  Play Count: {track.play_count}")
            print(f"  Length: {track.length}s")
            print(f"  File Path: {track.file_path}")
        
        # Test most played tracks
        print("\n🎵 Testing most played tracks...")
        try:
            most_played = await db.get_most_played_tracks(5)
            print(f"✅ Found {len(most_played)} most played tracks")
            
            for i, track in enumerate(most_played[:3]):
                print(f"  {i+1}. {track.artist} - {track.title} (played {track.play_count} times)")
        
        except Exception as e:
            print(f"❌ Most played tracks failed: {e}")
        
        # Test library stats
        print("\n📊 Testing library statistics...")
        try:
            stats = await db.get_library_stats()
            print(f"✅ Library stats:")
            print(f"  Total tracks: {stats['total_tracks']}")
            print(f"  Total playtime: {stats['total_playtime_seconds']}s")
            print(f"  Average BPM: {stats['average_bpm']}")
            print(f"  Top genres: {list(stats['genre_distribution'].keys())[:3]}")
        
        except Exception as e:
            print(f"❌ Library stats failed: {e}")
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(asyncio.run(test_mappings()))