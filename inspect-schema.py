#!/usr/bin/env python3
"""
Inspect the actual rekordbox database schema to understand the field names.
"""

import pyrekordbox

def main():
    print("🔍 Inspecting Rekordbox Database Schema")
    print("=" * 50)
    
    try:
        db = pyrekordbox.Rekordbox6Database()
        content = list(db.get_content())
        
        if not content:
            print("❌ No tracks found in database")
            return
        
        # Get the first track to inspect its attributes
        first_track = content[0]
        
        print(f"📊 Found {len(content)} tracks total")
        print(f"🔬 Inspecting first track structure...")
        print()
        
        # Get all attributes of the DjmdContent object
        attrs = [attr for attr in dir(first_track) if not attr.startswith('_')]
        
        print("📋 Available attributes:")
        for attr in sorted(attrs):
            try:
                value = getattr(first_track, attr)
                # Show type and sample value
                attr_type = type(value).__name__
                if hasattr(value, '__call__'):
                    print(f"  {attr}: {attr_type} (method)")
                else:
                    # Truncate long values
                    str_value = str(value)
                    if len(str_value) > 50:
                        str_value = str_value[:47] + "..."
                    print(f"  {attr}: {attr_type} = {str_value}")
            except Exception as e:
                print(f"  {attr}: Error accessing - {e}")
        
        print()
        print("🎵 Sample track data:")
        print("-" * 30)
        
        # Show key fields we're interested in
        key_fields = ['ID', 'Title', 'Artist', 'Album', 'Genre', 'Key', 'Length', 'Rating']
        for field in key_fields:
            try:
                value = getattr(first_track, field, "NOT_FOUND")
                print(f"  {field}: {value}")
            except Exception as e:
                print(f"  {field}: Error - {e}")
        
        print()
        print("🔍 Checking for deletion/status fields:")
        status_fields = [attr for attr in attrs if any(x in attr.lower() for x in ['delete', 'status', 'active', 'valid', 'sync', 'local'])]
        for field in status_fields:
            try:
                value = getattr(first_track, field)
                print(f"  {field}: {value}")
            except:
                pass
                
        print()
        print("📂 Checking multiple tracks for data quality:")
        # Check first 5 tracks to see variation in data
        for i, track in enumerate(content[:5]):
            print(f"\nTrack {i+1}:")
            print(f"  ID: {track.ID}")
            print(f"  Title: {track.Title}")
            print(f"  ArtistName: {getattr(track, 'ArtistName', 'NO_FIELD')}")
            if hasattr(track, 'Artist') and track.Artist:
                print(f"  Artist.Name: {getattr(track.Artist, 'Name', 'NO_NAME_FIELD')}")
            print(f"  AlbumName: {getattr(track, 'AlbumName', 'NO_FIELD')}")
            if hasattr(track, 'Album') and track.Album:
                print(f"  Album.Name: {getattr(track.Album, 'Name', 'NO_NAME_FIELD')}")
            print(f"  rb_local_deleted: {getattr(track, 'rb_local_deleted', 'NO_FIELD')}")
            print(f"  rb_data_status: {getattr(track, 'rb_data_status', 'NO_FIELD')}")
            print(f"  rb_local_data_status: {getattr(track, 'rb_local_data_status', 'NO_FIELD')}")
        
        # Look for BPM and PlayCount variants
        print()
        print("🔍 Searching for BPM and PlayCount fields:")
        bpm_fields = [attr for attr in attrs if 'bpm' in attr.lower() or 'tempo' in attr.lower()]
        play_fields = [attr for attr in attrs if 'play' in attr.lower() or 'count' in attr.lower()]
        
        if bpm_fields:
            print("  BPM-related fields:", bpm_fields)
            for field in bpm_fields:
                try:
                    value = getattr(first_track, field)
                    print(f"    {field}: {value}")
                except:
                    pass
        else:
            print("  No BPM-related fields found")
        
        if play_fields:
            print("  PlayCount-related fields:", play_fields)
            for field in play_fields:
                try:
                    value = getattr(first_track, field)
                    print(f"    {field}: {value}")
                except:
                    pass
        else:
            print("  No PlayCount-related fields found")
            
    except Exception as e:
        print(f"❌ Error inspecting database: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())