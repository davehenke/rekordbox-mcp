#!/usr/bin/env python3
"""
Test the updated playlist implementation.
"""

import asyncio
from rekordbox_mcp.database import RekordboxDatabase

async def test_playlists():
    print("🎼 Testing Updated Playlist Implementation")
    print("=" * 50)
    
    try:
        db = RekordboxDatabase()
        await db.connect()
        
        print("✅ Database connected successfully")
        
        # Test getting playlists
        print("\n📋 Testing get_playlists()...")
        playlists = await db.get_playlists()
        print(f"✅ Found {len(playlists)} playlists")
        
        if playlists:
            # Show first few playlists
            for i, playlist in enumerate(playlists[:5]):
                print(f"  {i+1}. {playlist.name} ({playlist.track_count} tracks) - ID: {playlist.id}")
        
        # Test getting tracks from a specific playlist
        if len(playlists) > 1:  # Skip "All Tracks"
            test_playlist = playlists[1]
            print(f"\n🎵 Testing get_playlist_tracks() for '{test_playlist.name}'...")
            
            tracks = await db.get_playlist_tracks(test_playlist.id)
            print(f"✅ Found {len(tracks)} tracks in playlist")
            
            if tracks:
                print("  First few tracks:")
                for i, track in enumerate(tracks[:3]):
                    print(f"    {i+1}. {track.artist} - {track.title}")
        
        print("\n✅ Playlist implementation test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(asyncio.run(test_playlists()))