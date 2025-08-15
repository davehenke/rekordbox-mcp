#!/usr/bin/env python3
"""
Investigate smart playlist flags in rekordbox database.
"""

import pyrekordbox

def main():
    print("🧠 Investigating Smart Playlist Flags")
    print("=" * 50)
    
    try:
        db = pyrekordbox.Rekordbox6Database()
        
        # Get all playlists
        all_playlists = list(db.get_playlist())
        active_playlists = [p for p in all_playlists if getattr(p, 'rb_local_deleted', 0) == 0]
        
        print(f"Found {len(active_playlists)} active playlists")
        
        # Analyze empty vs non-empty playlists
        empty_playlists = []
        non_empty_playlists = []
        
        for playlist in active_playlists:
            try:
                playlist_songs = list(db.get_playlist_songs(PlaylistID=playlist.ID))
                active_songs = [s for s in playlist_songs if getattr(s, 'rb_local_deleted', 0) == 0]
                track_count = len(active_songs)
                
                if track_count == 0:
                    empty_playlists.append(playlist)
                else:
                    non_empty_playlists.append((playlist, track_count))
            except Exception as e:
                print(f"Error checking {playlist.Name}: {e}")
                empty_playlists.append(playlist)
        
        print(f"\n📋 Empty playlists ({len(empty_playlists)}):")
        for playlist in empty_playlists:
            attrs = [attr for attr in dir(playlist) if not attr.startswith('_')]
            
            print(f"\n  '{playlist.Name}' (ID: {playlist.ID})")
            
            # Check smart playlist indicators
            smart_indicators = {}
            for attr in ['SmartList', 'Attribute', 'is_smart_playlist', 'Type']:
                if hasattr(playlist, attr):
                    value = getattr(playlist, attr, None)
                    smart_indicators[attr] = value
                    print(f"    {attr}: {value}")
            
            # Check other potentially relevant fields
            other_fields = {}
            for attr in ['ParentID', 'Parent', 'Children', 'ImagePath', 'Seq']:
                if hasattr(playlist, attr):
                    value = getattr(playlist, attr, None)
                    other_fields[attr] = value
                    if value:  # Only show non-empty values
                        print(f"    {attr}: {value}")
        
        print(f"\n📋 Non-empty playlists (first 5 of {len(non_empty_playlists)}):")
        for playlist, count in non_empty_playlists[:5]:
            print(f"\n  '{playlist.Name}' (ID: {playlist.ID}) - {count} tracks")
            
            # Check same fields for comparison
            for attr in ['SmartList', 'Attribute', 'is_smart_playlist', 'Type']:
                if hasattr(playlist, attr):
                    value = getattr(playlist, attr, None)
                    print(f"    {attr}: {value}")
        
        # Look at the SmartList field more closely if it exists
        print(f"\n🔍 SmartList field analysis:")
        smartlist_values = {}
        for playlist in active_playlists:
            if hasattr(playlist, 'SmartList'):
                smartlist = playlist.SmartList
                if smartlist not in smartlist_values:
                    smartlist_values[smartlist] = []
                smartlist_values[smartlist].append((playlist.Name, playlist.ID))
        
        for smartlist_val, playlists in smartlist_values.items():
            print(f"  SmartList = {smartlist_val}: {len(playlists)} playlists")
            if len(playlists) <= 5:  # Show all if 5 or fewer
                for name, pid in playlists:
                    print(f"    - {name}")
        
        print("\n✅ Smart playlist investigation completed!")
        
    except Exception as e:
        print(f"❌ Error investigating smart playlists: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())