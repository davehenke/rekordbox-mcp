#!/usr/bin/env python
"""
Export tracks by genre to a zip file
"""

import asyncio
import zipfile
import os
from pathlib import Path
from datetime import datetime
from rekordbox_mcp.database import RekordboxDatabase


async def export_genre_to_zip(genre_name: str, output_dir: str = "."):
    """
    Export all tracks matching a genre to a zip file.

    Args:
        genre_name: Genre to search for (case-insensitive substring match)
        output_dir: Directory to save the zip file (default: current directory)
    """
    db = RekordboxDatabase()

    try:
        print(f"Connecting to rekordbox database...")
        await db.connect()

        print(f"Searching for tracks with genre: '{genre_name}'")
        filepaths = await db.get_tracks_by_genre(genre_name)

        if not filepaths:
            print(f"No tracks found with genre '{genre_name}'")
            return

        print(f"Found {len(filepaths)} tracks matching '{genre_name}'")

        # Create zip filename with timestamp
        safe_genre = genre_name.replace("/", "-").replace("&", "and").replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"{safe_genre}_{timestamp}.zip"
        zip_path = Path(output_dir) / zip_filename

        # Quick check for missing files
        existing_files = []
        missing_count = 0
        for filepath in filepaths:
            if os.path.exists(filepath):
                existing_files.append(filepath)
            else:
                missing_count += 1

        if missing_count > 0:
            print(f"Warning: {missing_count} files not found on disk")

        if not existing_files:
            print("No files found on disk to export")
            return

        # Calculate total size for existing files only
        total_size = sum(os.path.getsize(f) for f in existing_files)
        total_size_mb = total_size / (1024 * 1024)
        print(f"Total size: {total_size_mb:.1f} MB ({len(existing_files)} files)")

        # Confirm before creating large zip
        if total_size_mb > 1000:  # If over 1GB
            response = input(f"This will create a {total_size_mb:.1f} MB zip file. Continue? (y/n): ")
            if response.lower() != 'y':
                print("Export cancelled")
                return

        # Create zip file
        print(f"Creating zip file: {zip_path}")

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            used_names = set()

            for i, filepath in enumerate(existing_files, 1):
                # Use just the filename in the zip to avoid deep paths
                filename = Path(filepath).name
                arcname = filename

                # Handle duplicates
                if arcname in used_names:
                    stem = Path(filepath).stem
                    suffix = Path(filepath).suffix
                    counter = 1
                    while f"{stem}_{counter}{suffix}" in used_names:
                        counter += 1
                    arcname = f"{stem}_{counter}{suffix}"

                used_names.add(arcname)
                zipf.write(filepath, arcname)

                # Progress indicator
                if i % 10 == 0 or i == len(existing_files):
                    progress = (i / len(existing_files)) * 100
                    print(f"Progress: {i}/{len(existing_files)} ({progress:.1f}%)", end='\r')

        print()  # New line after progress
        final_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
        print(f"\n✅ Successfully exported {len(existing_files)} tracks to {zip_path}")
        print(f"   Compressed size: {final_size_mb:.1f} MB")
        print(f"   Compression ratio: {(final_size_mb / total_size_mb * 100):.1f}%")

    except KeyboardInterrupt:
        print("\n\nExport cancelled by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await db.disconnect()


async def main():
    import sys

    # Check for command line arguments
    if len(sys.argv) > 1:
        genre = " ".join(sys.argv[1:])
    else:
        genre = "Melodic House & Techno"

    print(f"Exporting genre: {genre}")
    await export_genre_to_zip(genre)


if __name__ == "__main__":
    asyncio.run(main())