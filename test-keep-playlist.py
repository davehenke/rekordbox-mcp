#!/usr/bin/env python3
"""
Test the Keep playlist specifically.
"""

import asyncio
from rekordbox_mcp.database import RekordboxDatabase

async def test_keep_playlist():
    print("📋 Testing 'Keep' Playlist")
    print("=" * 30)
    
    try:
        db = RekordboxDatabase()
        await db.connect()
        
        # Get the Keep playlist
        playlists = await db.get_playlists()
        keep_playlist = next((p for p in playlists if p.name == "Keep"), None)
        
        if not keep_playlist:
            print("❌ Keep playlist not found")
            return 1
        
        print(f"✅ Found 'Keep' playlist: {keep_playlist.track_count} tracks")
        
        # Get tracks from the playlist
        tracks = await db.get_playlist_tracks(keep_playlist.id)
        print(f"✅ Retrieved {len(tracks)} tracks from playlist")
        
        if tracks:
            print("\nFirst 10 tracks in 'Keep' playlist:")
            for i, track in enumerate(tracks[:10]):
                print(f"  {i+1:2}. {track.artist} - {track.title}")
                if track.bpm > 0:
                    print(f"      BPM: {track.bpm}, Key: {track.key or 'Unknown'}")
        
        print(f"\n✅ Playlist test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(asyncio.run(test_keep_playlist()))