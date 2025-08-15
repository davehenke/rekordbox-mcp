import { SearchOptions, AnalyticsQuery, TrackSummary, SortField } from '../types.js';

describe('Types', () => {
  describe('SearchOptions', () => {
    it('should allow all optional properties', () => {
      const options1: SearchOptions = {};
      const options2: SearchOptions = {
        artist: 'Test Artist',
        genre: 'House',
        bpmMin: 120,
        bpmMax: 140,
        sortBy: 'playCount',
        sortOrder: 'desc'
      };

      expect(options1).toBeDefined();
      expect(options2.artist).toBe('Test Artist');
      expect(options2.sortBy).toBe('playCount');
    });

    it('should accept all valid sort fields', () => {
      const validFields: SortField[] = [
        'playCount', 'rating', 'bpm', 'dateAdded', 'dateModified',
        'artist', 'title', 'genre', 'year', 'totalTime'
      ];

      validFields.forEach(field => {
        const options: SearchOptions = { sortBy: field };
        expect(options.sortBy).toBe(field);
      });
    });

    it('should accept asc and desc sort orders', () => {
      const options1: SearchOptions = { sortOrder: 'asc' };
      const options2: SearchOptions = { sortOrder: 'desc' };
      
      expect(options1.sortOrder).toBe('asc');
      expect(options2.sortOrder).toBe('desc');
    });
  });

  describe('AnalyticsQuery', () => {
    it('should allow all optional properties', () => {
      const query1: AnalyticsQuery = {};
      const query2: AnalyticsQuery = {
        groupBy: 'genre',
        aggregateBy: 'playCount',
        topN: 10,
        filters: { artist: 'Test' }
      };

      expect(query1).toBeDefined();
      expect(query2.groupBy).toBe('genre');
      expect(query2.aggregateBy).toBe('playCount');
    });

    it('should accept valid groupBy values', () => {
      const validGroupBy = ['genre', 'key', 'year', 'artist', 'rating'];
      
      validGroupBy.forEach(groupBy => {
        const query: AnalyticsQuery = { groupBy: groupBy as any };
        expect(query.groupBy).toBe(groupBy);
      });
    });

    it('should accept valid aggregateBy values', () => {
      const validAggregateBy = ['count', 'playCount', 'totalTime'];
      
      validAggregateBy.forEach(aggregateBy => {
        const query: AnalyticsQuery = { aggregateBy: aggregateBy as any };
        expect(query.aggregateBy).toBe(aggregateBy);
      });
    });
  });

  describe('TrackSummary', () => {
    it('should enforce required properties', () => {
      const summary: TrackSummary = {
        id: '1001',
        title: 'Test Track',
        artist: 'Test Artist',
        bpm: 128,
        playCount: 5,
        rating: 4,
        duration: '4:00'
      };

      expect(summary.id).toBe('1001');
      expect(summary.title).toBe('Test Track');
      expect(summary.artist).toBe('Test Artist');
    });

    it('should allow optional properties', () => {
      const summary: TrackSummary = {
        id: '1001',
        title: 'Test Track',
        artist: 'Test Artist',
        album: 'Test Album',
        genre: 'House',
        bpm: 128,
        key: '8A',
        playCount: 5,
        rating: 4,
        duration: '4:00',
        year: 2023,
        comments: 'Great track',
        fileName: 'track.mp3',
        filePath: '/path/to/track.mp3'
      };

      expect(summary.album).toBe('Test Album');
      expect(summary.genre).toBe('House');
      expect(summary.key).toBe('8A');
      expect(summary.fileName).toBe('track.mp3');
      expect(summary.filePath).toBe('/path/to/track.mp3');
    });
  });
});