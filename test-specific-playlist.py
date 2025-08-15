#!/usr/bin/env python3
"""
Test specific playlist functionality.
"""

import asyncio
from rekordbox_mcp.database import RekordboxDatabase

async def test_specific_playlist():
    print("🎼 Testing Specific Playlist")
    print("=" * 40)
    
    try:
        db = RekordboxDatabase()
        await db.connect()
        
        # Get playlists and find one with tracks
        playlists = await db.get_playlists()
        print(f"Found {len(playlists)} playlists:")
        
        for playlist in playlists:
            print(f"  - {playlist.name}: {playlist.track_count} tracks (ID: {playlist.id})")
        
        # Test the "All" playlist which should have lots of tracks
        all_playlist = next((p for p in playlists if p.name == "All"), None)
        if all_playlist:
            print(f"\n🎵 Testing 'All' playlist ({all_playlist.track_count} tracks)...")
            tracks = await db.get_playlist_tracks(all_playlist.id)
            print(f"Actually retrieved {len(tracks)} tracks")
            
            if tracks:
                print("First few tracks:")
                for i, track in enumerate(tracks[:3]):
                    print(f"  {i+1}. {track.artist} - {track.title}")
        
        print("\n✅ Test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(asyncio.run(test_specific_playlist()))