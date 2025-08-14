import { RekordboxCollection, RekordboxTrack, SearchOptions, PlaylistNode, SortField, AnalyticsQuery, TrackSummary } from './types.js';
import { RekordboxXMLParser } from './xml-parser.js';

export class RekordboxService {
  private parser: RekordboxXMLParser;
  private collection: RekordboxCollection | null = null;

  constructor() {
    this.parser = new RekordboxXMLParser();
  }

  async loadLibrary(xmlPath: string): Promise<void> {
    this.collection = await this.parser.loadFromFile(xmlPath);
  }

  searchTracks(options: SearchOptions): RekordboxTrack[] {
    if (!this.collection) {
      throw new Error('No library loaded. Call loadLibrary() first.');
    }

    const tracks = Array.from(this.collection.tracks.values());
    const filtered = tracks.filter(track => {
      if (options.artist && !track.artist.toLowerCase().includes(options.artist.toLowerCase())) {
        return false;
      }
      if (options.title && !track.name.toLowerCase().includes(options.title.toLowerCase())) {
        return false;
      }
      if (options.genre && !track.genre?.toLowerCase().includes(options.genre.toLowerCase())) {
        return false;
      }
      if (options.key && track.tonality !== options.key) {
        return false;
      }
      if (options.bpmMin && track.averageBpm < options.bpmMin) {
        return false;
      }
      if (options.bpmMax && track.averageBpm > options.bpmMax) {
        return false;
      }
      if (options.playCountMin && track.playCount < options.playCountMin) {
        return false;
      }
      if (options.playCountMax && track.playCount > options.playCountMax) {
        return false;
      }
      if (options.rating && track.rating !== options.rating) {
        return false;
      }
      if (options.year && track.year !== options.year) {
        return false;
      }
      return true;
    });

    // Apply sorting
    const sorted = this.sortTracks(filtered, options.sortBy, options.sortOrder);

    if (options.limit) {
      return sorted.slice(0, options.limit);
    }
    
    return sorted;
  }

  private sortTracks(tracks: RekordboxTrack[], sortBy?: SortField, sortOrder: 'asc' | 'desc' = 'desc'): RekordboxTrack[] {
    if (!sortBy) return tracks;

    return tracks.sort((a, b) => {
      let aVal: any, bVal: any;

      switch (sortBy) {
        case 'playCount':
          aVal = a.playCount;
          bVal = b.playCount;
          break;
        case 'rating':
          aVal = a.rating;
          bVal = b.rating;
          break;
        case 'bpm':
          aVal = a.averageBpm;
          bVal = b.averageBpm;
          break;
        case 'dateAdded':
          aVal = new Date(a.dateAdded);
          bVal = new Date(b.dateAdded);
          break;
        case 'dateModified':
          aVal = new Date(a.dateModified);
          bVal = new Date(b.dateModified);
          break;
        case 'artist':
          aVal = a.artist.toLowerCase();
          bVal = b.artist.toLowerCase();
          break;
        case 'title':
          aVal = a.name.toLowerCase();
          bVal = b.name.toLowerCase();
          break;
        case 'genre':
          aVal = (a.genre || '').toLowerCase();
          bVal = (b.genre || '').toLowerCase();
          break;
        case 'year':
          aVal = a.year || 0;
          bVal = b.year || 0;
          break;
        case 'totalTime':
          aVal = a.totalTime;
          bVal = b.totalTime;
          break;
        default:
          return 0;
      }

      if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });
  }

  getTrackById(trackId: string): RekordboxTrack | undefined {
    if (!this.collection) {
      throw new Error('No library loaded. Call loadLibrary() first.');
    }
    return this.collection.tracks.get(trackId);
  }

  getTracksByPlaylist(playlistName: string): RekordboxTrack[] {
    if (!this.collection) {
      throw new Error('No library loaded. Call loadLibrary() first.');
    }

    const playlist = this.findPlaylistByName(this.collection.playlists, playlistName);
    if (!playlist) {
      return [];
    }

    return playlist.tracks
      .map(trackId => this.collection!.tracks.get(trackId))
      .filter((track): track is RekordboxTrack => track !== undefined);
  }

  private findPlaylistByName(node: PlaylistNode, name: string): PlaylistNode | null {
    if (node.name.toLowerCase() === name.toLowerCase()) {
      return node;
    }

    for (const child of node.children) {
      const found = this.findPlaylistByName(child, name);
      if (found) {
        return found;
      }
    }

    return null;
  }

  getAllPlaylists(): PlaylistNode[] {
    if (!this.collection) {
      throw new Error('No library loaded. Call loadLibrary() first.');
    }
    return this.flattenPlaylists(this.collection.playlists);
  }

  private flattenPlaylists(node: PlaylistNode): PlaylistNode[] {
    const playlists: PlaylistNode[] = [];
    
    if (node.name !== 'ROOT') {
      playlists.push(node);
    }

    for (const child of node.children) {
      playlists.push(...this.flattenPlaylists(child));
    }

    return playlists;
  }

  getLibraryStats() {
    if (!this.collection) {
      throw new Error('No library loaded. Call loadLibrary() first.');
    }

    const tracks = Array.from(this.collection.tracks.values());
    const genreCounts = new Map<string, number>();
    const keyCounts = new Map<string, number>();
    
    let totalPlayCount = 0;
    let totalDuration = 0;

    for (const track of tracks) {
      totalPlayCount += track.playCount;
      totalDuration += track.totalTime;

      const genre = track.genre || 'Unknown';
      genreCounts.set(genre, (genreCounts.get(genre) || 0) + 1);

      if (track.tonality) {
        keyCounts.set(track.tonality, (keyCounts.get(track.tonality) || 0) + 1);
      }
    }

    return {
      totalTracks: tracks.length,
      totalPlayCount,
      totalDurationSeconds: totalDuration,
      totalDurationHours: Math.round(totalDuration / 3600 * 100) / 100,
      topGenres: Array.from(genreCounts.entries())
        .sort(([,a], [,b]) => b - a)
        .slice(0, 10),
      topKeys: Array.from(keyCounts.entries())
        .sort(([,a], [,b]) => b - a)
        .slice(0, 12),
      playlistCount: this.getAllPlaylists().length
    };
  }

  updateTrackPlayCount(trackId: string, newPlayCount: number): boolean {
    if (!this.collection) {
      throw new Error('No library loaded. Call loadLibrary() first.');
    }

    const track = this.collection.tracks.get(trackId);
    if (!track) {
      return false;
    }

    track.playCount = newPlayCount;
    return true;
  }

  updateTrackRating(trackId: string, newRating: number): boolean {
    if (!this.collection) {
      throw new Error('No library loaded. Call loadLibrary() first.');
    }

    const track = this.collection.tracks.get(trackId);
    if (!track) {
      return false;
    }

    track.rating = Math.max(0, Math.min(5, newRating));
    return true;
  }

  getTracksByKey(key: string): RekordboxTrack[] {
    if (!this.collection) {
      throw new Error('No library loaded. Call loadLibrary() first.');
    }

    return Array.from(this.collection.tracks.values())
      .filter(track => track.tonality === key);
  }

  getTracksByBPMRange(minBpm: number, maxBpm: number): RekordboxTrack[] {
    if (!this.collection) {
      throw new Error('No library loaded. Call loadLibrary() first.');
    }

    return Array.from(this.collection.tracks.values())
      .filter(track => track.averageBpm >= minBpm && track.averageBpm <= maxBpm);
  }

  analyzeLibrary(query: AnalyticsQuery): any {
    if (!this.collection) {
      throw new Error('No library loaded. Call loadLibrary() first.');
    }

    let tracks = Array.from(this.collection.tracks.values());

    // Apply filters first
    if (query.filters) {
      tracks = tracks.filter(track => {
        const options = query.filters!;
        if (options.artist && !track.artist.toLowerCase().includes(options.artist.toLowerCase())) return false;
        if (options.title && !track.name.toLowerCase().includes(options.title.toLowerCase())) return false;
        if (options.genre && !track.genre?.toLowerCase().includes(options.genre.toLowerCase())) return false;
        if (options.key && track.tonality !== options.key) return false;
        if (options.bpmMin && track.averageBpm < options.bpmMin) return false;
        if (options.bpmMax && track.averageBpm > options.bpmMax) return false;
        if (options.playCountMin && track.playCount < options.playCountMin) return false;
        if (options.playCountMax && track.playCount > options.playCountMax) return false;
        if (options.rating && track.rating !== options.rating) return false;
        if (options.year && track.year !== options.year) return false;
        return true;
      });
    }

    if (!query.groupBy) {
      // Return all tracks with aggregation
      const result = this.aggregateTracks(tracks, query.aggregateBy || 'count');
      return {
        totalMatches: tracks.length,
        result
      };
    }

    // Group by specified field
    const groups = new Map<string, RekordboxTrack[]>();
    
    tracks.forEach(track => {
      let groupKey: string;
      switch (query.groupBy) {
        case 'genre':
          groupKey = track.genre || 'Unknown';
          break;
        case 'key':
          groupKey = track.tonality || 'Unknown';
          break;
        case 'year':
          groupKey = track.year?.toString() || 'Unknown';
          break;
        case 'artist':
          groupKey = track.artist;
          break;
        case 'rating':
          groupKey = track.rating.toString();
          break;
        default:
          groupKey = 'Unknown';
      }

      if (!groups.has(groupKey)) {
        groups.set(groupKey, []);
      }
      groups.get(groupKey)!.push(track);
    });

    // Aggregate each group
    const results = Array.from(groups.entries()).map(([key, groupTracks]) => ({
      group: key,
      tracks: groupTracks.length,
      value: this.aggregateTracks(groupTracks, query.aggregateBy || 'count')
    }));

    // Sort by aggregation value and apply topN
    results.sort((a, b) => b.value - a.value);
    
    if (query.topN) {
      return results.slice(0, query.topN);
    }

    return results;
  }

  private aggregateTracks(tracks: RekordboxTrack[], aggregateBy: 'count' | 'playCount' | 'totalTime'): number {
    switch (aggregateBy) {
      case 'count':
        return tracks.length;
      case 'playCount':
        return tracks.reduce((sum, track) => sum + track.playCount, 0);
      case 'totalTime':
        return tracks.reduce((sum, track) => sum + track.totalTime, 0);
      default:
        return tracks.length;
    }
  }

  getMostPlayedTracks(options: { genre?: string; limit?: number } = {}): TrackSummary[] {
    if (!this.collection) {
      throw new Error('No library loaded. Call loadLibrary() first.');
    }

    let tracks = Array.from(this.collection.tracks.values());
    
    // Filter by genre if specified
    if (options.genre) {
      tracks = tracks.filter(track => 
        track.genre?.toLowerCase().includes(options.genre!.toLowerCase())
      );
    }

    // Sort by play count descending
    const sorted = tracks
      .filter(track => track.playCount > 0)
      .sort((a, b) => b.playCount - a.playCount);

    const limit = options.limit || sorted.length;
    
    return sorted.slice(0, limit).map(this.trackToSummary);
  }

  getTopRatedTracks(options: { genre?: string; limit?: number } = {}): TrackSummary[] {
    if (!this.collection) {
      throw new Error('No library loaded. Call loadLibrary() first.');
    }

    let tracks = Array.from(this.collection.tracks.values());
    
    // Filter by genre if specified
    if (options.genre) {
      tracks = tracks.filter(track => 
        track.genre?.toLowerCase().includes(options.genre!.toLowerCase())
      );
    }

    // Sort by rating descending, then by play count as tiebreaker
    const sorted = tracks
      .filter(track => track.rating > 0)
      .sort((a, b) => {
        if (b.rating !== a.rating) return b.rating - a.rating;
        return b.playCount - a.playCount;
      });

    const limit = options.limit || sorted.length;
    
    return sorted.slice(0, limit).map(this.trackToSummary);
  }

  getUnplayedTracks(options: { genre?: string; sortBy?: SortField; limit?: number } = {}): TrackSummary[] {
    if (!this.collection) {
      throw new Error('No library loaded. Call loadLibrary() first.');
    }

    let tracks = Array.from(this.collection.tracks.values())
      .filter(track => track.playCount === 0);
    
    // Filter by genre if specified
    if (options.genre) {
      tracks = tracks.filter(track => 
        track.genre?.toLowerCase().includes(options.genre!.toLowerCase())
      );
    }

    // Apply sorting
    if (options.sortBy) {
      tracks = this.sortTracks(tracks, options.sortBy, 'desc');
    }

    const limit = options.limit || tracks.length;
    
    return tracks.slice(0, limit).map(this.trackToSummary);
  }

  private trackToSummary = (track: RekordboxTrack): TrackSummary => ({
    id: track.trackId,
    title: track.name,
    artist: track.artist,
    album: track.album,
    genre: track.genre,
    bpm: track.averageBpm,
    key: track.tonality,
    playCount: track.playCount,
    rating: track.rating,
    duration: `${Math.floor(track.totalTime / 60)}:${(track.totalTime % 60).toString().padStart(2, '0')}`,
    year: track.year,
    comments: track.comments,
  });

  getTrackFilePath(trackId: string): string | null {
    if (!this.collection) {
      throw new Error('No library loaded. Call loadLibrary() first.');
    }

    const track = this.collection.tracks.get(trackId);
    if (!track) {
      return null;
    }

    // Convert file://localhost/path to /path and decode URL encoding
    return decodeURIComponent(track.location.replace('file://localhost', ''));
  }

  getTrackFileName(trackId: string): string | null {
    const filePath = this.getTrackFilePath(trackId);
    if (!filePath) {
      return null;
    }

    // Extract filename from path
    const parts = filePath.split('/');
    return parts[parts.length - 1];
  }

  searchTracksByFileName(filename: string): RekordboxTrack[] {
    if (!this.collection) {
      throw new Error('No library loaded. Call loadLibrary() first.');
    }

    const searchTerm = filename.toLowerCase();
    return Array.from(this.collection.tracks.values())
      .filter(track => {
        const path = decodeURIComponent(track.location.replace('file://localhost', ''));
        return path.toLowerCase().includes(searchTerm);
      });
  }

  async createPlaylistFile(
    trackIds: string[], 
    filePath: string, 
    format: 'txt' | 'm3u' | 'm3u8' | 'pls' = 'm3u8',
    playlistName?: string
  ): Promise<string> {
    if (!this.collection) {
      throw new Error('No library loaded. Call loadLibrary() first.');
    }

    const tracks = trackIds
      .map(id => this.collection!.tracks.get(id))
      .filter((track): track is RekordboxTrack => track !== undefined);

    if (tracks.length === 0) {
      throw new Error('No valid tracks found for the provided track IDs');
    }

    let content = '';
    const name = playlistName || `Playlist_${new Date().toISOString().split('T')[0]}`;

    switch (format) {
      case 'txt':
        content = tracks
          .map(track => this.getTrackFilePath(track.trackId))
          .join('\n');
        break;

      case 'm3u':
      case 'm3u8':
        content = '#EXTM3U\n';
        for (const track of tracks) {
          const filePath = this.getTrackFilePath(track.trackId);
          const duration = Math.round(track.totalTime);
          content += `#EXTINF:${duration},${track.artist} - ${track.name}\n`;
          content += `${filePath}\n`;
        }
        break;

      case 'pls':
        content = '[playlist]\n';
        content += `PlaylistName=${name}\n`;
        content += `NumberOfEntries=${tracks.length}\n\n`;
        
        tracks.forEach((track, index) => {
          const filePath = this.getTrackFilePath(track.trackId);
          const num = index + 1;
          content += `File${num}=${filePath}\n`;
          content += `Title${num}=${track.artist} - ${track.name}\n`;
          content += `Length${num}=${Math.round(track.totalTime)}\n\n`;
        });
        
        content += 'Version=2\n';
        break;
    }

    // Write file using Node.js fs
    const fs = await import('fs/promises');
    await fs.writeFile(filePath, content, 'utf-8');

    return `Created ${format.toUpperCase()} playlist "${name}" with ${tracks.length} tracks at: ${filePath}`;
  }

  validateTrackIds(trackIds: string[]): { valid: string[], invalid: string[] } {
    if (!this.collection) {
      throw new Error('No library loaded. Call loadLibrary() first.');
    }

    const valid: string[] = [];
    const invalid: string[] = [];

    for (const id of trackIds) {
      if (this.collection.tracks.has(id)) {
        valid.push(id);
      } else {
        invalid.push(id);
      }
    }

    return { valid, invalid };
  }

  createPlaylistFromSearch(
    searchOptions: SearchOptions,
    filePath: string,
    format: 'txt' | 'm3u' | 'm3u8' | 'pls' = 'm3u8',
    playlistName?: string
  ): Promise<string> {
    const tracks = this.searchTracks(searchOptions);
    const trackIds = tracks.map(track => track.trackId);
    return this.createPlaylistFile(trackIds, filePath, format, playlistName);
  }
}