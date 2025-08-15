import { readFile } from 'fs/promises';
import { parseStringPromise } from 'xml2js';
import { RekordboxCollection, RekordboxTrack, TempoData, CuePoint, PlaylistNode } from './types.js';

export class RekordboxXMLParser {
  private collection: RekordboxCollection | null = null;

  async loadFromFile(filePath: string): Promise<RekordboxCollection> {
    const xmlContent = await readFile(filePath, 'utf-8');
    return this.parseXML(xmlContent);
  }

  async parseXML(xmlContent: string): Promise<RekordboxCollection> {
    const result = await parseStringPromise(xmlContent);
    const djPlaylists = result.DJ_PLAYLISTS;

    const collection: RekordboxCollection = {
      version: djPlaylists.$.Version,
      createdBy: djPlaylists.$.CreatedByApp,
      createdByVersion: djPlaylists.$.CreatedByVersion,
      platform: djPlaylists.$.CreationPlatform,
      modificationDate: djPlaylists.$.ModificationDate,
      productName: djPlaylists.PRODUCT[0].$.Name,
      productVersion: djPlaylists.PRODUCT[0].$.Version,
      productCompany: djPlaylists.PRODUCT[0].$.Company,
      totalEntries: parseInt(djPlaylists.COLLECTION[0].$.Entries),
      tracks: new Map(),
      playlists: this.parsePlaylistNode(djPlaylists.PLAYLISTS[0].NODE[0])
    };

    // Parse tracks
    const trackElements = djPlaylists.COLLECTION[0].TRACK || [];
    for (const trackElement of trackElements) {
      const track = this.parseTrack(trackElement);
      collection.tracks.set(track.trackId, track);
    }

    this.collection = collection;
    return collection;
  }

  private parseTrack(trackElement: any): RekordboxTrack {
    const attrs = trackElement.$;
    
    // Parse tempo data
    const tempoData: TempoData[] = [];
    if (trackElement.TEMPO) {
      for (const tempo of trackElement.TEMPO) {
        tempoData.push({
          start: parseFloat(tempo.$.Inizio),
          bpm: parseFloat(tempo.$.Bpm),
          metro: tempo.$.Metro,
          beat: parseInt(tempo.$.Battito)
        });
      }
    }

    // Parse cue points
    const allCues: CuePoint[] = [];
    const hotCues: CuePoint[] = [];
    
    if (trackElement.POSITION_MARK) {
      for (const mark of trackElement.POSITION_MARK) {
        const cue: CuePoint = {
          name: mark.$.Name,
          start: parseFloat(mark.$.Start),
          type: parseInt(mark.$.Type),
          num: parseInt(mark.$.Num)
        };
        
        allCues.push(cue);
        
        // Hot cues have Num 0-7, memory cues have Num -1
        if (cue.num >= 0 && cue.num <= 7) {
          hotCues.push(cue);
        }
      }
    }

    return {
      trackId: attrs.TrackID,
      name: attrs.Name || '',
      artist: attrs.Artist || '',
      composer: attrs.Composer || undefined,
      album: attrs.Album || undefined,
      grouping: attrs.Grouping || undefined,
      genre: attrs.Genre || '',
      kind: attrs.Kind || '',
      size: parseInt(attrs.Size) || 0,
      totalTime: parseInt(attrs.TotalTime) || 0,
      discNumber: parseInt(attrs.DiscNumber) || 0,
      trackNumber: parseInt(attrs.TrackNumber) || 0,
      year: attrs.Year ? parseInt(attrs.Year) : undefined,
      averageBpm: parseFloat(attrs.AverageBpm) || 0,
      dateAdded: attrs.DateAdded || '',
      bitRate: parseInt(attrs.BitRate) || 0,
      sampleRate: parseInt(attrs.SampleRate) || 0,
      comments: attrs.Comments || undefined,
      playCount: parseInt(attrs.PlayCount) || 0,
      rating: parseInt(attrs.Rating) || 0,
      location: attrs.Location || '',
      remixer: attrs.Remixer || undefined,
      tonality: attrs.Tonality || undefined,
      label: attrs.Label || undefined,
      mix: attrs.Mix || undefined,
      dateModified: attrs.DateModified || '',
      tempoData,
      cuePoints: allCues.filter(c => c.num === -1),
      hotCues
    };
  }

  private parsePlaylistNode(nodeElement: any): PlaylistNode {
    const attrs = nodeElement.$;
    const node: PlaylistNode = {
      type: parseInt(attrs.Type),
      name: attrs.Name || 'ROOT',
      count: attrs.Count ? parseInt(attrs.Count) : undefined,
      entries: attrs.Entries ? parseInt(attrs.Entries) : undefined,
      keyType: attrs.KeyType ? parseInt(attrs.KeyType) : undefined,
      tracks: [],
      children: []
    };

    // Parse tracks in this playlist
    if (nodeElement.TRACK) {
      for (const track of nodeElement.TRACK) {
        node.tracks.push(track.$.Key);
      }
    }

    // Parse child playlists
    if (nodeElement.NODE) {
      for (const childNode of nodeElement.NODE) {
        node.children.push(this.parsePlaylistNode(childNode));
      }
    }

    return node;
  }

  getCollection(): RekordboxCollection | null {
    return this.collection;
  }
}