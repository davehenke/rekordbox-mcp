export interface RekordboxTrack {
  trackId: string;
  name: string;
  artist: string;
  composer?: string;
  album?: string;
  grouping?: string;
  genre?: string;
  kind: string;
  size: number;
  totalTime: number;
  discNumber: number;
  trackNumber: number;
  year?: number;
  averageBpm: number;
  dateAdded: string;
  bitRate: number;
  sampleRate: number;
  comments?: string;
  playCount: number;
  rating: number;
  location: string;
  remixer?: string;
  tonality?: string;
  label?: string;
  mix?: string;
  dateModified: string;
  tempoData: TempoData[];
  cuePoints: CuePoint[];
  hotCues: CuePoint[];
}

export interface TempoData {
  start: number;
  bpm: number;
  metro: string;
  beat: number;
}

export interface CuePoint {
  name: string;
  start: number;
  type: number;
  num: number;
}

export interface PlaylistNode {
  type: number;
  name: string;
  count?: number;
  entries?: number;
  keyType?: number;
  tracks: string[];
  children: PlaylistNode[];
}

export interface RekordboxCollection {
  version: string;
  createdBy: string;
  createdByVersion: string;
  platform: string;
  modificationDate: string;
  productName: string;
  productVersion: string;
  productCompany: string;
  totalEntries: number;
  tracks: Map<string, RekordboxTrack>;
  playlists: PlaylistNode;
}

export interface SearchOptions {
  artist?: string;
  title?: string;
  genre?: string;
  key?: string;
  bpmMin?: number;
  bpmMax?: number;
  playCountMin?: number;
  playCountMax?: number;
  rating?: number;
  year?: number;
  limit?: number;
  sortBy?: SortField;
  sortOrder?: 'asc' | 'desc';
}

export type SortField = 
  | 'playCount' 
  | 'rating' 
  | 'bpm' 
  | 'dateAdded' 
  | 'dateModified' 
  | 'artist' 
  | 'title' 
  | 'genre' 
  | 'year' 
  | 'totalTime';

export interface AnalyticsQuery {
  groupBy?: 'genre' | 'key' | 'year' | 'artist' | 'rating';
  aggregateBy?: 'count' | 'playCount' | 'totalTime';
  filters?: SearchOptions;
  topN?: number;
}

export interface TrackSummary {
  id: string;
  title: string;
  artist: string;
  album?: string;
  genre?: string;
  bpm: number;
  key?: string;
  playCount: number;
  rating: number;
  duration: string;
  year?: number;
  comments?: string;
  fileName?: string;
  filePath?: string;
}