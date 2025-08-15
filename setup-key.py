#!/usr/bin/env python3
"""
Setup script for rekordbox database encryption key.

This script helps extract or download the encryption key needed to access
the rekordbox database in versions 6.6.5+.
"""

import sys
import os
from pathlib import Path

def main():
    print("🔑 Rekordbox Database Key Setup")
    print("=" * 40)
    
    try:
        import pyrekordbox
        print("✅ pyrekordbox imported successfully")
    except ImportError:
        print("❌ pyrekordbox not found. Please install it first.")
        return 1
    
    print("\n🔍 Checking for existing key...")
    
    try:
        # Try to create a database connection
        db = pyrekordbox.Rekordbox6Database()
        print("✅ Database key found and working!")
        
        # Test basic connection
        try:
            content_count = len(list(db.get_content()))
            print(f"✅ Successfully connected! Found {content_count} tracks.")
            return 0
        except Exception as e:
            print(f"⚠️  Key found but database access failed: {e}")
            
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Database connection failed: {error_msg}")
        
        if "No key found" in error_msg:
            print("\n🔧 Attempting to resolve key issue...")
            
            # Check rekordbox version guidance
            if "6.6.5" in error_msg:
                print("\n📝 Rekordbox 6.6.5+ Key Issue Detected")
                print("   Pioneer obfuscated the key extraction in newer versions.")
                print("   Here are your options:")
                print()
                print("1. 🔄 Try automatic key download:")
                print("   This may work for some systems.")
                
                try:
                    # Attempt key download
                    print("\n   Attempting automatic key download...")
                    # Note: This is a placeholder - actual implementation depends on pyrekordbox API
                    print("   ⚠️  Automatic download not implemented in this version")
                    
                except Exception as download_error:
                    print(f"   ❌ Download failed: {download_error}")
                
                print("\n2. 📁 Manual key extraction:")
                print("   - Downgrade to rekordbox 6.6.4 temporarily")
                print("   - Run this script to cache the key")
                print("   - Upgrade back to your preferred version")
                print()
                print("3. 🔍 Check existing cache:")
                
                # Check for cached keys
                cache_locations = [
                    Path.home() / ".pyrekordbox",
                    Path.home() / "Library" / "Application Support" / "pyrekordbox",
                ]
                
                found_cache = False
                for cache_path in cache_locations:
                    if cache_path.exists():
                        print(f"   Found cache directory: {cache_path}")
                        found_cache = True
                        
                        # List cache contents
                        for item in cache_path.iterdir():
                            print(f"     - {item.name}")
                
                if not found_cache:
                    print("   No cache directories found")
                    
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())