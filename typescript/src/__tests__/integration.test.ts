import { RekordboxService } from '../rekordbox-service.js';
import { RekordboxXMLParser } from '../xml-parser.js';
import { mockXmlData } from './test-data.js';

// Mock fs module for file operations
jest.mock('fs/promises', () => ({
  writeFile: jest.fn().mockResolvedValue(undefined),
  readFile: jest.fn().mockResolvedValue('')  // Will be overridden in beforeEach
}));

describe('Integration Tests', () => {
  let service: RekordboxService;

  beforeEach(async () => {
    service = new RekordboxService();
    // Mock the parser to avoid file system dependencies
    const mockParser = new RekordboxXMLParser();
    jest.spyOn(mockParser, 'loadFromFile').mockResolvedValue(await mockParser.parseXML(mockXmlData));
    (service as any).parser = mockParser;
    
    await service.loadLibrary('/mock/path.xml');
  });

  describe('End-to-end workflows', () => {
    it('should support complete DJ set preparation workflow', async () => {
      // 1. Find high-energy house tracks
      const houseTracksHighEnergy = service.searchTracks({
        genre: 'House',
        rating: 4,
        sortBy: 'playCount',
        sortOrder: 'desc'
      });
      
      expect(houseTracksHighEnergy).toHaveLength(1);
      expect(houseTracksHighEnergy[0].genre).toBe('House');
      expect(houseTracksHighEnergy[0].rating).toBeGreaterThanOrEqual(4);

      // 2. Find harmonic matches (compatible keys)
      const keyMatches = service.getTracksByKey('8A');
      expect(keyMatches).toHaveLength(1);

      // 3. Create a playlist from the results
      const trackIds = [...houseTracksHighEnergy, ...keyMatches].map(t => t.trackId);
      const uniqueTrackIds = [...new Set(trackIds)]; // Remove duplicates
      
      const playlistResult = await service.createPlaylistFile(
        uniqueTrackIds,
        '/tmp/dj-set.m3u8',
        'm3u8',
        'DJ Set Prep'
      );
      
      expect(playlistResult).toContain('Created M3U8 playlist');
      expect(playlistResult).toContain('DJ Set Prep');
    });

    it('should support library analysis workflow', () => {
      // 1. Get overall library statistics
      const stats = service.getLibraryStats();
      expect(stats.totalTracks).toBe(3);
      expect(stats.totalPlayCount).toBe(15);

      // 2. Analyze genre distribution
      const genreAnalysis = service.analyzeLibrary({
        groupBy: 'genre',
        aggregateBy: 'count'
      });
      
      expect(genreAnalysis).toHaveLength(2);
      expect(genreAnalysis[0].group).toBe('House');
      expect(genreAnalysis[0].tracks).toBe(2);

      // 3. Find most played tracks in top genre
      const mostPlayedHouse = service.getMostPlayedTracks({ genre: 'House' });
      expect(mostPlayedHouse).toHaveLength(2);
      expect(mostPlayedHouse[0].playCount).toBe(10);

      // 4. Discover unplayed tracks
      const unplayed = service.getUnplayedTracks();
      expect(unplayed).toHaveLength(1);
      expect(unplayed[0].playCount).toBe(0);
    });

    it('should support harmonic mixing workflow', () => {
      // 1. Start with a track in 8A
      const currentTrack = service.getTrackById('1001');
      expect(currentTrack?.tonality).toBe('8A');

      // 2. Find compatible keys for harmonic mixing
      const compatibleKeys = ['8B', '7A', '9A']; // Theoretical compatible keys
      const allCompatibleTracks = compatibleKeys.flatMap(key => 
        service.getTracksByKey(key)
      );

      // In our test data, we don't have these keys, so expect empty
      expect(allCompatibleTracks).toHaveLength(0);

      // 3. Find tracks in same key for energy building
      const sameKeyTracks = service.getTracksByKey('8A');
      expect(sameKeyTracks).toHaveLength(1);

      // 4. Find similar BPM tracks for smooth transitions
      const similarBpmTracks = service.getTracksByBPMRange(125, 130);
      expect(similarBpmTracks).toHaveLength(1);
    });

    it('should support playlist management workflow', async () => {
      // 1. Browse existing playlists
      const allPlaylists = service.getAllPlaylists();
      expect(allPlaylists).toHaveLength(2);

      // 2. Get tracks from a specific playlist
      const housePlaylistTracks = service.getTracksByPlaylist('House Music');
      expect(housePlaylistTracks).toHaveLength(2);

      // 3. Create a new playlist based on playlist content + additional filters
      const playlistTrackIds = housePlaylistTracks.map(t => t.trackId);
      
      // Validate the track IDs before creating playlist
      const validation = service.validateTrackIds(playlistTrackIds);
      expect(validation.valid).toHaveLength(2);
      expect(validation.invalid).toHaveLength(0);

      // 4. Create the new playlist file
      const result = await service.createPlaylistFile(
        validation.valid,
        '/tmp/enhanced-house.pls',
        'pls',
        'Enhanced House Mix'
      );
      
      expect(result).toContain('Enhanced House Mix');
    });

    it('should support file management workflow', () => {
      // 1. Search by filename
      const tracksByFilename = service.searchTracksByFileName('Test Artist 1');
      expect(tracksByFilename).toHaveLength(2);

      // 2. Get file paths for external processing
      const track = tracksByFilename[0];
      const filePath = service.getTrackFilePath(track.trackId);
      const fileName = service.getTrackFileName(track.trackId);

      expect(filePath).toBe('/Users/test/Music/Test Artist 1 - Test Track 1.mp3');
      expect(fileName).toBe('Test Artist 1 - Test Track 1.mp3');

      // 3. Validate file paths exist in search results
      const fileSearchResults = service.searchTracksByFileName('Test Artist 1 - Test Track 1.mp3');
      expect(fileSearchResults).toHaveLength(1);
      expect(fileSearchResults[0].trackId).toBe(track.trackId);
    });

    it('should support complex analytics workflow', () => {
      // 1. Analyze play patterns by year
      const yearAnalysis = service.analyzeLibrary({
        groupBy: 'year',
        aggregateBy: 'playCount',
        topN: 3
      });
      
      expect(yearAnalysis.length).toBeLessThanOrEqual(3);
      
      // 2. Find artists with most total play time
      const artistPlayTime = service.analyzeLibrary({
        groupBy: 'artist',
        aggregateBy: 'totalTime'
      });
      
      expect(artistPlayTime).toHaveLength(2); // Test Artist 1 and Test Artist 2
      
      const testArtist1 = artistPlayTime.find((a: any) => a.group === 'Test Artist 1');
      expect(testArtist1?.value).toBe(420); // 240 + 180 seconds

      // 3. Analyze high-rated tracks only
      const highRatedAnalysis = service.analyzeLibrary({
        groupBy: 'genre',
        filters: { rating: 4 }
      });
      
      // Only tracks with rating >= 4
      expect(highRatedAnalysis.length).toBeGreaterThan(0);
      
      // 4. Get top genres by track count in high-energy range
      const energyAnalysis = service.analyzeLibrary({
        groupBy: 'genre',
        aggregateBy: 'count',
        filters: { playCountMin: 1 },
        topN: 2
      });
      
      expect(energyAnalysis.length).toBeLessThanOrEqual(2);
    });
  });

  describe('Error handling and edge cases', () => {
    it('should handle empty search results gracefully', () => {
      const results = service.searchTracks({ 
        genre: 'NonExistentGenre',
        bpmMin: 200,
        bpmMax: 300
      });
      
      expect(results).toHaveLength(0);
    });

    it('should handle invalid analytics queries gracefully', () => {
      const result = service.analyzeLibrary({
        groupBy: 'genre',
        filters: { artist: 'NonExistentArtist' }
      });
      
      expect(result).toHaveLength(0);
    });

    it('should handle mixed valid/invalid track IDs', () => {
      const validation = service.validateTrackIds(['1001', '9999', '1002', '8888']);
      
      expect(validation.valid).toEqual(['1001', '1002']);
      expect(validation.invalid).toEqual(['9999', '8888']);
    });

    it('should handle playlist creation with some invalid IDs', async () => {
      const validation = service.validateTrackIds(['1001', '9999', '1002']);
      
      // Should succeed with valid IDs only
      const result = await service.createPlaylistFile(
        validation.valid,
        '/tmp/partial.m3u8'
      );
      
      expect(result).toContain('2 tracks');
    });

    it('should handle empty playlist creation gracefully', async () => {
      await expect(
        service.createPlaylistFile([], '/tmp/empty.m3u8')
      ).rejects.toThrow('No valid tracks found');
    });
  });
});