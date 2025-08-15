import { RekordboxService } from '../rekordbox-service.js';
import { RekordboxXMLParser } from '../xml-parser.js';
import { mockXmlData, mockTrack1, mockTrack2, mockTrack3 } from './test-data.js';

// Mock fs module
jest.mock('fs/promises', () => ({
  writeFile: jest.fn().mockResolvedValue(undefined),
  readFile: jest.fn().mockResolvedValue('')  // Will be overridden in beforeEach
}));

describe('RekordboxService', () => {
  let service: RekordboxService;

  beforeEach(async () => {
    service = new RekordboxService();
    // Mock the parser to avoid file system dependencies
    const mockParser = new RekordboxXMLParser();
    jest.spyOn(mockParser, 'loadFromFile').mockResolvedValue(await mockParser.parseXML(mockXmlData));
    (service as any).parser = mockParser;
    
    await service.loadLibrary('/mock/path.xml');
  });

  describe('searchTracks', () => {
    it('should return all tracks when no filters applied', () => {
      const results = service.searchTracks({});
      expect(results).toHaveLength(3);
    });

    it('should filter by artist', () => {
      const results = service.searchTracks({ artist: 'Test Artist 1' });
      expect(results).toHaveLength(2);
      expect(results[0].artist).toBe('Test Artist 1');
      expect(results[1].artist).toBe('Test Artist 1');
    });

    it('should filter by genre', () => {
      const results = service.searchTracks({ genre: 'House' });
      expect(results).toHaveLength(2);
      expect(results.every(track => track.genre === 'House')).toBe(true);
    });

    it('should filter by key', () => {
      const results = service.searchTracks({ key: '8A' });
      expect(results).toHaveLength(1);
      expect(results[0].tonality).toBe('8A');
    });

    it('should filter by BPM range', () => {
      const results = service.searchTracks({ bpmMin: 125, bpmMax: 130 });
      expect(results).toHaveLength(1);
      expect(results[0].averageBpm).toBe(128.00);
    });

    it('should filter by play count range', () => {
      const results = service.searchTracks({ playCountMin: 5 });
      expect(results).toHaveLength(2);
      expect(results.every(track => track.playCount >= 5)).toBe(true);
    });

    it('should filter by rating', () => {
      const results = service.searchTracks({ rating: 5 });
      expect(results).toHaveLength(1);
      expect(results[0].rating).toBe(5);
    });

    it('should filter by year', () => {
      const results = service.searchTracks({ year: 2023 });
      expect(results).toHaveLength(1);
      expect(results[0].year).toBe(2023);
    });

    it('should sort by play count descending', () => {
      const results = service.searchTracks({ sortBy: 'playCount', sortOrder: 'desc' });
      expect(results[0].playCount).toBe(10);
      expect(results[1].playCount).toBe(5);
      expect(results[2].playCount).toBe(0);
    });

    it('should sort by BPM ascending', () => {
      const results = service.searchTracks({ sortBy: 'bpm', sortOrder: 'asc' });
      expect(results[0].averageBpm).toBe(124.00);
      expect(results[1].averageBpm).toBe(128.00);
      expect(results[2].averageBpm).toBe(132.00);
    });

    it('should limit results', () => {
      const results = service.searchTracks({ limit: 2 });
      expect(results).toHaveLength(2);
    });

    it('should combine multiple filters', () => {
      const results = service.searchTracks({ 
        genre: 'House', 
        artist: 'Test Artist 1',
        playCountMin: 3
      });
      expect(results).toHaveLength(2);
      expect(results.every(track => 
        track.genre === 'House' && 
        track.artist === 'Test Artist 1' && 
        track.playCount >= 3
      )).toBe(true);
    });
  });

  describe('getTrackById', () => {
    it('should return track by ID', () => {
      const track = service.getTrackById('1001');
      expect(track).toBeDefined();
      expect(track?.name).toBe('Test Track 1');
    });

    it('should return undefined for non-existent track', () => {
      const track = service.getTrackById('9999');
      expect(track).toBeUndefined();
    });
  });

  describe('getTracksByPlaylist', () => {
    it('should return tracks from existing playlist', () => {
      const tracks = service.getTracksByPlaylist('House Music');
      expect(tracks).toHaveLength(2);
      expect(tracks[0].trackId).toBe('1001');
      expect(tracks[1].trackId).toBe('1003');
    });

    it('should return empty array for non-existent playlist', () => {
      const tracks = service.getTracksByPlaylist('Non-existent');
      expect(tracks).toHaveLength(0);
    });

    it('should be case insensitive', () => {
      const tracks = service.getTracksByPlaylist('house music');
      expect(tracks).toHaveLength(2);
    });
  });

  describe('getAllPlaylists', () => {
    it('should return all playlists except ROOT', () => {
      const playlists = service.getAllPlaylists();
      expect(playlists).toHaveLength(2);
      expect(playlists[0].name).toBe('House Music');
      expect(playlists[1].name).toBe('Techno Tracks');
    });
  });

  describe('getLibraryStats', () => {
    it('should return correct library statistics', () => {
      const stats = service.getLibraryStats();
      
      expect(stats.totalTracks).toBe(3);
      expect(stats.totalPlayCount).toBe(15); // 5 + 0 + 10
      expect(stats.totalDurationSeconds).toBe(720); // 240 + 300 + 180
      expect(stats.totalDurationHours).toBe(0.2); // 720/3600 rounded
      expect(stats.playlistCount).toBe(2);
      
      expect(stats.topGenres).toEqual([
        ['House', 2],
        ['Techno', 1]
      ]);
      
      expect(stats.topKeys).toContainEqual(['8A', 1]);
      expect(stats.topKeys).toContainEqual(['2B', 1]);
      expect(stats.topKeys).toContainEqual(['12A', 1]);
    });
  });

  describe('updateTrackPlayCount', () => {
    it('should update play count for existing track', () => {
      const success = service.updateTrackPlayCount('1001', 20);
      expect(success).toBe(true);
      
      const track = service.getTrackById('1001');
      expect(track?.playCount).toBe(20);
    });

    it('should return false for non-existent track', () => {
      const success = service.updateTrackPlayCount('9999', 20);
      expect(success).toBe(false);
    });
  });

  describe('updateTrackRating', () => {
    it('should update rating for existing track', () => {
      const success = service.updateTrackRating('1001', 5);
      expect(success).toBe(true);
      
      const track = service.getTrackById('1001');
      expect(track?.rating).toBe(5);
    });

    it('should clamp rating to valid range', () => {
      service.updateTrackRating('1001', 10);
      let track = service.getTrackById('1001');
      expect(track?.rating).toBe(5);

      service.updateTrackRating('1001', -5);
      track = service.getTrackById('1001');
      expect(track?.rating).toBe(0);
    });

    it('should return false for non-existent track', () => {
      const success = service.updateTrackRating('9999', 5);
      expect(success).toBe(false);
    });
  });

  describe('getTracksByKey', () => {
    it('should return tracks with specific key', () => {
      const tracks = service.getTracksByKey('8A');
      expect(tracks).toHaveLength(1);
      expect(tracks[0].tonality).toBe('8A');
    });

    it('should return empty array for non-existent key', () => {
      const tracks = service.getTracksByKey('1B');
      expect(tracks).toHaveLength(0);
    });
  });

  describe('getTracksByBPMRange', () => {
    it('should return tracks within BPM range', () => {
      const tracks = service.getTracksByBPMRange(125, 130);
      expect(tracks).toHaveLength(1);
      expect(tracks[0].averageBpm).toBe(128.00);
    });

    it('should include boundary values', () => {
      const tracks = service.getTracksByBPMRange(124, 132);
      expect(tracks).toHaveLength(3);
    });

    it('should return empty array for invalid range', () => {
      const tracks = service.getTracksByBPMRange(200, 250);
      expect(tracks).toHaveLength(0);
    });
  });

  describe('getMostPlayedTracks', () => {
    it('should return tracks sorted by play count', () => {
      const tracks = service.getMostPlayedTracks();
      expect(tracks[0].playCount).toBe(10);
      expect(tracks[1].playCount).toBe(5);
      expect(tracks).toHaveLength(2); // Only tracks with play count > 0
    });

    it('should filter by genre', () => {
      const tracks = service.getMostPlayedTracks({ genre: 'House' });
      expect(tracks).toHaveLength(2);
      expect(tracks.every(track => track.genre === 'House')).toBe(true);
    });

    it('should respect limit', () => {
      const tracks = service.getMostPlayedTracks({ limit: 1 });
      expect(tracks).toHaveLength(1);
      expect(tracks[0].playCount).toBe(10);
    });
  });

  describe('getTopRatedTracks', () => {
    it('should return tracks sorted by rating', () => {
      const tracks = service.getTopRatedTracks();
      expect(tracks[0].rating).toBe(5);
      expect(tracks[1].rating).toBe(4);
      expect(tracks[2].rating).toBe(3);
    });

    it('should use play count as tiebreaker', () => {
      // Set two tracks to same rating
      service.updateTrackRating('1001', 5);
      service.updateTrackRating('1002', 5);
      
      const tracks = service.getTopRatedTracks();
      // Track with higher play count should come first
      expect(tracks[0].playCount).toBeGreaterThanOrEqual(tracks[1].playCount);
    });
  });

  describe('getUnplayedTracks', () => {
    it('should return tracks with zero play count', () => {
      const tracks = service.getUnplayedTracks();
      expect(tracks).toHaveLength(1);
      expect(tracks[0].playCount).toBe(0);
    });

    it('should filter by genre', () => {
      const tracks = service.getUnplayedTracks({ genre: 'Techno' });
      expect(tracks).toHaveLength(1);
      expect(tracks[0].genre).toBe('Techno');
    });
  });

  describe('File path methods', () => {
    describe('getTrackFilePath', () => {
      it('should return clean file path', () => {
        const path = service.getTrackFilePath('1001');
        expect(path).toBe('/Users/test/Music/Test Artist 1 - Test Track 1.mp3');
      });

      it('should return null for non-existent track', () => {
        const path = service.getTrackFilePath('9999');
        expect(path).toBeNull();
      });
    });

    describe('getTrackFileName', () => {
      it('should return filename only', () => {
        const filename = service.getTrackFileName('1001');
        expect(filename).toBe('Test Artist 1 - Test Track 1.mp3');
      });

      it('should return null for non-existent track', () => {
        const filename = service.getTrackFileName('9999');
        expect(filename).toBeNull();
      });
    });

    describe('searchTracksByFileName', () => {
      it('should find tracks by filename fragment', () => {
        const tracks = service.searchTracksByFileName('Test Artist 1');
        expect(tracks).toHaveLength(2);
      });

      it('should be case insensitive', () => {
        const tracks = service.searchTracksByFileName('test artist 1');
        expect(tracks).toHaveLength(2);
      });

      it('should return empty array for non-matching search', () => {
        const tracks = service.searchTracksByFileName('Non-existent');
        expect(tracks).toHaveLength(0);
      });
    });
  });

  describe('Analytics', () => {
    describe('analyzeLibrary', () => {
      it('should group by genre', () => {
        const result = service.analyzeLibrary({ groupBy: 'genre' });
        expect(result).toHaveLength(2);
        expect(result[0].group).toBe('House');
        expect(result[0].tracks).toBe(2);
        expect(result[1].group).toBe('Techno');
        expect(result[1].tracks).toBe(1);
      });

      it('should aggregate by play count', () => {
        const result = service.analyzeLibrary({ 
          groupBy: 'genre', 
          aggregateBy: 'playCount' 
        });
        
        const houseEntry = result.find((r: any) => r.group === 'House');
        expect(houseEntry?.value).toBe(15); // 5 + 10
        
        const technoEntry = result.find((r: any) => r.group === 'Techno');
        expect(technoEntry?.value).toBe(0);
      });

      it('should limit results with topN', () => {
        const result = service.analyzeLibrary({ 
          groupBy: 'genre',
          topN: 1
        });
        expect(result).toHaveLength(1);
        expect(result[0].group).toBe('House');
      });

      it('should apply filters', () => {
        const result = service.analyzeLibrary({
          groupBy: 'artist',
          filters: { genre: 'House' }
        });
        expect(result).toHaveLength(1);
        expect(result[0].group).toBe('Test Artist 1');
        expect(result[0].tracks).toBe(2);
      });
    });

    describe('validateTrackIds', () => {
      it('should separate valid and invalid IDs', () => {
        const result = service.validateTrackIds(['1001', '1002', '9999', '8888']);
        expect(result.valid).toEqual(['1001', '1002']);
        expect(result.invalid).toEqual(['9999', '8888']);
      });

      it('should handle empty array', () => {
        const result = service.validateTrackIds([]);
        expect(result.valid).toEqual([]);
        expect(result.invalid).toEqual([]);
      });

      it('should handle all valid IDs', () => {
        const result = service.validateTrackIds(['1001', '1002', '1003']);
        expect(result.valid).toEqual(['1001', '1002', '1003']);
        expect(result.invalid).toEqual([]);
      });
    });
  });

  describe('Playlist creation', () => {
    describe('createPlaylistFile', () => {
      it('should create M3U8 playlist file', async () => {
        const fs = await import('fs/promises');
        const writeFileMock = fs.writeFile as jest.Mock;
        writeFileMock.mockClear();
        
        const result = await service.createPlaylistFile(
          ['1001', '1002'],
          '/test/playlist.m3u8',
          'm3u8',
          'Test Playlist'
        );

        expect(writeFileMock).toHaveBeenCalled();
        const [filePath, content] = writeFileMock.mock.calls[0];
        expect(filePath).toBe('/test/playlist.m3u8');
        expect(content).toContain('#EXTM3U');
        expect(content).toContain('#EXTINF:240,Test Artist 1 - Test Track 1');
        expect(content).toContain('/Users/test/Music/Test Artist 1 - Test Track 1.mp3');
        expect(result).toContain('Created M3U8 playlist');
      });

      it('should create PLS playlist file', async () => {
        const fs = await import('fs/promises');
        const writeFileMock = fs.writeFile as jest.Mock;
        writeFileMock.mockClear();
        
        await service.createPlaylistFile(
          ['1001'],
          '/test/playlist.pls',
          'pls',
          'Test Playlist'
        );

        const [, content] = writeFileMock.mock.calls[0];
        expect(content).toContain('[playlist]');
        expect(content).toContain('PlaylistName=Test Playlist');
        expect(content).toContain('NumberOfEntries=1');
        expect(content).toContain('File1=/Users/test/Music/Test Artist 1 - Test Track 1.mp3');
      });

      it('should create TXT playlist file', async () => {
        const fs = await import('fs/promises');
        const writeFileMock = fs.writeFile as jest.Mock;
        writeFileMock.mockClear();
        
        await service.createPlaylistFile(
          ['1001', '1002'],
          '/test/playlist.txt',
          'txt'
        );

        const [, content] = writeFileMock.mock.calls[0];
        expect(content).toBe('/Users/test/Music/Test Artist 1 - Test Track 1.mp3\n/Users/test/Music/Test Artist 2 - Test Track 2.mp3');
      });

      it('should handle invalid track IDs', async () => {
        await expect(
          service.createPlaylistFile(['9999'], '/test/playlist.m3u8')
        ).rejects.toThrow('No valid tracks found');
      });
    });

    describe('createPlaylistFromSearch', () => {
      it('should create playlist from search results', async () => {
        const fs = await import('fs/promises');
        const writeFileMock = fs.writeFile as jest.Mock;
        
        const result = await service.createPlaylistFromSearch(
          { genre: 'House' },
          '/test/house.m3u8',
          'm3u8',
          'House Tracks'
        );

        expect(writeFileMock).toHaveBeenCalled();
        expect(result).toContain('Created M3U8 playlist "House Tracks" with 2 tracks');
      });
    });
  });
});