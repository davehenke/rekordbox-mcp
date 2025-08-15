#!/usr/bin/env python3
"""
Test getting songs from playlists.
"""

import pyrekordbox

def main():
    print("🎵 Testing Playlist Song Access")
    print("=" * 40)
    
    try:
        db = pyrekordbox.Rekordbox6Database()
        
        # Get a playlist first
        playlists = list(db.get_playlist())
        if not playlists:
            print("❌ No playlists found")
            return 1
        
        first_playlist = playlists[1]  # Skip "All Tracks" 
        playlist_id = first_playlist.ID
        playlist_name = first_playlist.Name
        print(f"🔍 Testing playlist: {playlist_name} (ID: {playlist_id})")
        
        # Try different approaches to get playlist songs
        print("\n📋 Trying different methods...")
        
        # Try with playlist ID
        try:
            songs = db.get_playlist_songs(PlaylistID=playlist_id)
            songs_list = list(songs)
            print(f"✅ get_playlist_songs(PlaylistID={playlist_id}) found {len(songs_list)} songs")
            
            if songs_list:
                first_song = songs_list[0]
                print(f"   First song type: {type(first_song)}")
                attrs = [attr for attr in dir(first_song) if not attr.startswith('_')]
                print(f"   Song attributes: {attrs}")
                
                # Check key fields
                print(f"   ContentID: {getattr(first_song, 'ContentID', 'NO_CONTENT_ID')}")
                print(f"   PlaylistID: {getattr(first_song, 'PlaylistID', 'NO_PLAYLIST_ID')}")
                print(f"   TrackNo: {getattr(first_song, 'TrackNo', 'NO_TRACK_NO')}")
                
        except Exception as e:
            print(f"❌ get_playlist_songs(PlaylistID=...) failed: {e}")
        
        # Try with ID parameter
        try:
            songs = db.get_playlist_songs(ID=playlist_id)
            songs_list = list(songs)
            print(f"✅ get_playlist_songs(ID={playlist_id}) found {len(songs_list)} songs")
        except Exception as e:
            print(f"❌ get_playlist_songs(ID=...) failed: {e}")
        
        # Try without parameters to see all song-playlist relationships
        try:
            all_song_playlist = list(db.get_playlist_songs())
            print(f"✅ get_playlist_songs() (all) found {len(all_song_playlist)} song-playlist relationships")
            
            # Filter by our playlist ID
            our_playlist_songs = [sp for sp in all_song_playlist if getattr(sp, 'PlaylistID', None) == str(playlist_id)]
            print(f"   Filtered to {len(our_playlist_songs)} songs for our playlist")
            
            if our_playlist_songs:
                first_song = our_playlist_songs[0]
                content_id = getattr(first_song, 'ContentID', None)
                print(f"   First song ContentID: {content_id}")
                
                # Try to get the actual track content
                if content_id:
                    try:
                        all_content = list(db.get_content())
                        track_content = next((c for c in all_content if str(c.ID) == str(content_id)), None)
                        if track_content:
                            print(f"   Track title: {track_content.Title}")
                            print(f"   Track artist: {getattr(track_content, 'ArtistName', 'NO_ARTIST')}")
                        else:
                            print(f"   Track not found for ContentID {content_id}")
                    except Exception as e:
                        print(f"   Error getting track content: {e}")
        except Exception as e:
            print(f"❌ get_playlist_songs() (all) failed: {e}")
        
        print("\n✅ Playlist song testing completed!")
        
    except Exception as e:
        print(f"❌ Error testing playlist songs: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())