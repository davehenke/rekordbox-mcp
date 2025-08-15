export const mockXmlData = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<DJ_PLAYLISTS Version="1.0.0" CreatedByApp="Test Suite" CreatedByVersion="1.0.0" CreationPlatform="Test" ModificationDate="2025-01-01 00:00:00-0000">
    <PRODUCT Name="rekordbox" Version="7.1.4" Company="AlphaTheta"></PRODUCT>
    <COLLECTION Entries="3">
        <TRACK TrackID="1001" Name="Test Track 1" Artist="Test Artist 1" Composer="" Album="Test Album 1" Grouping="" Genre="House" Kind="MP3 File" Size="10000000" TotalTime="240" DiscNumber="0" TrackNumber="1" Year="2023" AverageBpm="128.00" DateAdded="2024-01-01" BitRate="320" SampleRate="44100" Comments="8A - Energy 8" PlayCount="5" Rating="4" Location="file://localhost/Users/test/Music/Test%20Artist%201%20-%20Test%20Track%201.mp3" Remixer="" Tonality="8A" Label="Test Label" Mix="" DateModified="2024-01-01 00:00:00-0000">
            <TEMPO Inizio="0.100" Bpm="128.00" Metro="4/4" Battito="1"></TEMPO>
            <POSITION_MARK Name="Cue 1" Start="30.0" Type="0" Num="-1"></POSITION_MARK>
            <POSITION_MARK Name="Cue 2" Start="60.0" Type="0" Num="-1"></POSITION_MARK>
            <POSITION_MARK Name="Cue 1" Start="30.0" Type="0" Num="0"></POSITION_MARK>
            <POSITION_MARK Name="Cue 2" Start="60.0" Type="0" Num="1"></POSITION_MARK>
        </TRACK>
        <TRACK TrackID="1002" Name="Test Track 2" Artist="Test Artist 2" Composer="" Album="Test Album 2" Grouping="" Genre="Techno" Kind="MP3 File" Size="12000000" TotalTime="300" DiscNumber="0" TrackNumber="2" Year="2022" AverageBpm="132.00" DateAdded="2024-01-02" BitRate="320" SampleRate="44100" Comments="2B - Energy 9" PlayCount="0" Rating="5" Location="file://localhost/Users/test/Music/Test%20Artist%202%20-%20Test%20Track%202.mp3" Remixer="" Tonality="2B" Label="" Mix="" DateModified="2024-01-02 00:00:00-0000">
            <TEMPO Inizio="0.050" Bpm="132.00" Metro="4/4" Battito="1"></TEMPO>
            <POSITION_MARK Name="Cue 1" Start="45.0" Type="0" Num="0"></POSITION_MARK>
        </TRACK>
        <TRACK TrackID="1003" Name="Test Track 3" Artist="Test Artist 1" Composer="" Album="Test Album 3" Grouping="" Genre="House" Kind="MP3 File" Size="8000000" TotalTime="180" DiscNumber="0" TrackNumber="3" Year="2024" AverageBpm="124.00" DateAdded="2024-01-03" BitRate="320" SampleRate="44100" Comments="12A - Energy 6" PlayCount="10" Rating="3" Location="file://localhost/Users/test/Music/Test%20Artist%201%20-%20Test%20Track%203.mp3" Remixer="" Tonality="12A" Label="" Mix="" DateModified="2024-01-03 00:00:00-0000">
            <TEMPO Inizio="0.075" Bpm="124.00" Metro="4/4" Battito="1"></TEMPO>
        </TRACK>
    </COLLECTION>
    <PLAYLISTS>
        <NODE Type="0" Name="ROOT" Count="2">
            <NODE Name="House Music" Type="1" KeyType="0" Entries="2">
                <TRACK Key="1001"></TRACK>
                <TRACK Key="1003"></TRACK>
            </NODE>
            <NODE Name="Techno Tracks" Type="1" KeyType="0" Entries="1">
                <TRACK Key="1002"></TRACK>
            </NODE>
        </NODE>
    </PLAYLISTS>
</DJ_PLAYLISTS>`;

export const mockTrack1 = {
  trackId: '1001',
  name: 'Test Track 1',
  artist: 'Test Artist 1',
  album: 'Test Album 1',
  genre: 'House',
  year: 2023,
  averageBpm: 128.00,
  playCount: 5,
  rating: 4,
  tonality: '8A',
  totalTime: 240,
  location: 'file://localhost/Users/test/Music/Test%20Artist%201%20-%20Test%20Track%201.mp3'
};

export const mockTrack2 = {
  trackId: '1002',
  name: 'Test Track 2',
  artist: 'Test Artist 2',
  album: 'Test Album 2',
  genre: 'Techno',
  year: 2022,
  averageBpm: 132.00,
  playCount: 0,
  rating: 5,
  tonality: '2B',
  totalTime: 300,
  location: 'file://localhost/Users/test/Music/Test%20Artist%202%20-%20Test%20Track%202.mp3'
};

export const mockTrack3 = {
  trackId: '1003',
  name: 'Test Track 3',
  artist: 'Test Artist 1',
  album: 'Test Album 3',
  genre: 'House',
  year: 2024,
  averageBpm: 124.00,
  playCount: 10,
  rating: 3,
  tonality: '12A',
  totalTime: 180,
  location: 'file://localhost/Users/test/Music/Test%20Artist%201%20-%20Test%20Track%203.mp3'
};