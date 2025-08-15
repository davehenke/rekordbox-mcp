#!/usr/bin/env python3
"""
Test rekordbox playlist functionality.
"""

import pyrekordbox

def main():
    print("🎼 Testing Rekordbox Playlist Access")
    print("=" * 50)
    
    try:
        db = pyrekordbox.Rekordbox6Database()
        
        # Try get_playlist without arguments to see what happens
        print("🔍 Testing get_playlist() method...")
        try:
            all_playlists = db.get_playlist()
            print(f"✅ get_playlist() returned: {type(all_playlists)}")
            playlists_list = list(all_playlists)
            print(f"   Found {len(playlists_list)} playlists")
            
            if playlists_list:
                for i, playlist in enumerate(playlists_list[:5]):  # First 5 playlists
                    print(f"\n📋 Playlist {i+1}:")
                    print(f"   Type: {type(playlist)}")
                    attrs = [attr for attr in dir(playlist) if not attr.startswith('_')]
                    print(f"   Attributes: {attrs}")
                    
                    # Try to get key attributes
                    try:
                        print(f"   ID: {getattr(playlist, 'ID', 'NO_ID')}")
                        print(f"   Name: {getattr(playlist, 'Name', 'NO_NAME')}")
                        print(f"   Title: {getattr(playlist, 'Title', 'NO_TITLE')}")
                        print(f"   Parent: {getattr(playlist, 'Parent', 'NO_PARENT')}")
                        print(f"   Type: {getattr(playlist, 'Type', 'NO_TYPE')}")
                    except Exception as e:
                        print(f"   Error getting attributes: {e}")
                        
                # Test getting songs for first playlist
                if len(playlists_list) > 0:
                    first_playlist = playlists_list[0]
                    playlist_id = getattr(first_playlist, 'ID', None)
                    if playlist_id:
                        print(f"\n🎵 Testing playlist contents for playlist {playlist_id}...")
                        try:
                            songs = db.get_playlist_songs(playlist_id)
                            songs_list = list(songs)
                            print(f"   Found {len(songs_list)} songs in playlist")
                            
                            if songs_list:
                                first_song = songs_list[0]
                                print(f"   First song type: {type(first_song)}")
                                song_attrs = [attr for attr in dir(first_song) if not attr.startswith('_')]
                                print(f"   Song attributes: {song_attrs}")
                        except Exception as e:
                            print(f"   Error getting playlist songs: {e}")
        except Exception as e:
            print(f"❌ get_playlist() failed: {e}")
        
        print("\n✅ Playlist testing completed!")
        
    except Exception as e:
        print(f"❌ Error testing playlists: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())