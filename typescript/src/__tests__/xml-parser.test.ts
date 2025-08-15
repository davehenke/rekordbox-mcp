import { RekordboxXMLParser } from '../xml-parser.js';
import { mockXmlData } from './test-data.js';

describe('RekordboxXMLParser', () => {
  let parser: RekordboxXMLParser;

  beforeEach(() => {
    parser = new RekordboxXMLParser();
  });

  describe('parseXML', () => {
    it('should parse XML data correctly', async () => {
      const collection = await parser.parseXML(mockXmlData);

      expect(collection.version).toBe('1.0.0');
      expect(collection.createdBy).toBe('Test Suite');
      expect(collection.productName).toBe('rekordbox');
      expect(collection.productCompany).toBe('AlphaTheta');
      expect(collection.totalEntries).toBe(3);
      expect(collection.tracks.size).toBe(3);
    });

    it('should parse track metadata correctly', async () => {
      const collection = await parser.parseXML(mockXmlData);
      const track = collection.tracks.get('1001');

      expect(track).toBeDefined();
      expect(track?.name).toBe('Test Track 1');
      expect(track?.artist).toBe('Test Artist 1');
      expect(track?.genre).toBe('House');
      expect(track?.averageBpm).toBe(128.00);
      expect(track?.playCount).toBe(5);
      expect(track?.rating).toBe(4);
      expect(track?.tonality).toBe('8A');
      expect(track?.totalTime).toBe(240);
    });

    it('should parse tempo data correctly', async () => {
      const collection = await parser.parseXML(mockXmlData);
      const track = collection.tracks.get('1001');

      expect(track?.tempoData).toHaveLength(1);
      expect(track?.tempoData[0].start).toBe(0.100);
      expect(track?.tempoData[0].bpm).toBe(128.00);
      expect(track?.tempoData[0].metro).toBe('4/4');
      expect(track?.tempoData[0].beat).toBe(1);
    });

    it('should parse cue points correctly', async () => {
      const collection = await parser.parseXML(mockXmlData);
      const track = collection.tracks.get('1001');

      expect(track?.cuePoints).toHaveLength(2); // Memory cues (Num=-1)
      expect(track?.hotCues).toHaveLength(2);   // Hot cues (Num=0,1)

      expect(track?.cuePoints[0].name).toBe('Cue 1');
      expect(track?.cuePoints[0].start).toBe(30.0);
      expect(track?.cuePoints[0].num).toBe(-1);

      expect(track?.hotCues[0].name).toBe('Cue 1');
      expect(track?.hotCues[0].start).toBe(30.0);
      expect(track?.hotCues[0].num).toBe(0);
    });

    it('should parse playlists correctly', async () => {
      const collection = await parser.parseXML(mockXmlData);
      
      expect(collection.playlists.name).toBe('ROOT');
      expect(collection.playlists.children).toHaveLength(2);

      const housePlaylist = collection.playlists.children[0];
      expect(housePlaylist.name).toBe('House Music');
      expect(housePlaylist.tracks).toEqual(['1001', '1003']);

      const technoPlaylist = collection.playlists.children[1];
      expect(technoPlaylist.name).toBe('Techno Tracks');
      expect(technoPlaylist.tracks).toEqual(['1002']);
    });

    it('should handle empty XML gracefully', async () => {
      const emptyXml = `<?xml version="1.0"?>
        <DJ_PLAYLISTS Version="1.0.0">
          <PRODUCT Name="rekordbox" Version="7.0.0" Company="AlphaTheta"/>
          <COLLECTION Entries="0"></COLLECTION>
          <PLAYLISTS><NODE Type="0" Name="ROOT" Count="0"></NODE></PLAYLISTS>
        </DJ_PLAYLISTS>`;

      const collection = await parser.parseXML(emptyXml);
      expect(collection.tracks.size).toBe(0);
      expect(collection.playlists.children).toHaveLength(0);
    });

    it('should handle tracks without optional fields', async () => {
      const minimalXml = `<?xml version="1.0"?>
        <DJ_PLAYLISTS Version="1.0.0">
          <PRODUCT Name="rekordbox" Version="7.0.0" Company="AlphaTheta"/>
          <COLLECTION Entries="1">
            <TRACK TrackID="999" Name="Minimal Track" Artist="Artist" Genre="" PlayCount="0" Rating="0" Location="file://localhost/test.mp3"/>
          </COLLECTION>
          <PLAYLISTS><NODE Type="0" Name="ROOT" Count="0"></NODE></PLAYLISTS>
        </DJ_PLAYLISTS>`;

      const collection = await parser.parseXML(minimalXml);
      const track = collection.tracks.get('999');
      
      expect(track).toBeDefined();
      expect(track?.name).toBe('Minimal Track');
      expect(track?.genre).toBe('');
      expect(track?.year).toBeUndefined();
      expect(track?.tonality).toBeUndefined();
    });
  });
});