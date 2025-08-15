#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { RekordboxService } from './rekordbox-service.js';

const service = new RekordboxService();

const server = new Server(
  {
    name: 'rekordbox-mcp',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  },
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'search_tracks',
        description: 'Search tracks in the rekordbox library',
        inputSchema: {
          type: 'object',
          properties: {
            artist: {
              type: 'string',
              description: 'Filter by artist name (partial match)',
            },
            title: {
              type: 'string',
              description: 'Filter by track title (partial match)',
            },
            genre: {
              type: 'string',
              description: 'Filter by genre (partial match)',
            },
            key: {
              type: 'string',
              description: 'Filter by musical key (exact match, e.g., "2A", "11B")',
            },
            bpm_min: {
              type: 'number',
              description: 'Minimum BPM',
            },
            bpm_max: {
              type: 'number',
              description: 'Maximum BPM',
            },
            play_count_min: {
              type: 'number',
              description: 'Minimum play count',
            },
            play_count_max: {
              type: 'number',
              description: 'Maximum play count',
            },
            rating: {
              type: 'number',
              description: 'Filter by rating (0-5)',
            },
            year: {
              type: 'number',
              description: 'Filter by release year',
            },
            limit: {
              type: 'number',
              description: 'Maximum number of results to return (optional - omit for unlimited)',
            },
            sort_by: {
              type: 'string',
              description: 'Sort results by field: playCount, rating, bpm, dateAdded, dateModified, artist, title, genre, year, totalTime',
              enum: ['playCount', 'rating', 'bpm', 'dateAdded', 'dateModified', 'artist', 'title', 'genre', 'year', 'totalTime'],
            },
            sort_order: {
              type: 'string',
              description: 'Sort order: asc or desc (default: desc)',
              enum: ['asc', 'desc'],
            },
          },
        },
      },
      {
        name: 'get_track_details',
        description: 'Get detailed information about a specific track including cue points',
        inputSchema: {
          type: 'object',
          properties: {
            track_id: {
              type: 'string',
              description: 'The track ID',
            },
          },
          required: ['track_id'],
        },
      },
      {
        name: 'get_tracks_by_playlist',
        description: 'Get all tracks in a specific playlist',
        inputSchema: {
          type: 'object',
          properties: {
            playlist_name: {
              type: 'string',
              description: 'Name of the playlist',
            },
          },
          required: ['playlist_name'],
        },
      },
      {
        name: 'get_library_stats',
        description: 'Get statistics about the library (track count, genres, keys, etc.)',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
      {
        name: 'get_all_playlists',
        description: 'List all playlists in the library',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
      {
        name: 'update_track_play_count',
        description: 'Update the play count for a track',
        inputSchema: {
          type: 'object',
          properties: {
            track_id: {
              type: 'string',
              description: 'The track ID',
            },
            play_count: {
              type: 'number',
              description: 'New play count',
            },
          },
          required: ['track_id', 'play_count'],
        },
      },
      {
        name: 'update_track_rating',
        description: 'Update the rating for a track',
        inputSchema: {
          type: 'object',
          properties: {
            track_id: {
              type: 'string',
              description: 'The track ID',
            },
            rating: {
              type: 'number',
              description: 'New rating (0-5)',
              minimum: 0,
              maximum: 5,
            },
          },
          required: ['track_id', 'rating'],
        },
      },
      {
        name: 'get_tracks_by_key',
        description: 'Get all tracks in a specific musical key',
        inputSchema: {
          type: 'object',
          properties: {
            key: {
              type: 'string',
              description: 'Musical key (e.g., "2A", "11B")',
            },
          },
          required: ['key'],
        },
      },
      {
        name: 'get_tracks_by_bpm_range',
        description: 'Get tracks within a BPM range',
        inputSchema: {
          type: 'object',
          properties: {
            min_bpm: {
              type: 'number',
              description: 'Minimum BPM',
            },
            max_bpm: {
              type: 'number',
              description: 'Maximum BPM',
            },
          },
          required: ['min_bpm', 'max_bpm'],
        },
      },
      {
        name: 'analyze_library',
        description: 'Perform advanced analytics on the library with grouping and aggregation',
        inputSchema: {
          type: 'object',
          properties: {
            group_by: {
              type: 'string',
              description: 'Group results by: genre, key, year, artist, rating',
              enum: ['genre', 'key', 'year', 'artist', 'rating'],
            },
            aggregate_by: {
              type: 'string',
              description: 'Aggregate by: count, playCount, totalTime (default: count)',
              enum: ['count', 'playCount', 'totalTime'],
            },
            top_n: {
              type: 'number',
              description: 'Limit to top N results',
            },
            filters: {
              type: 'object',
              description: 'Apply filters (same as search_tracks)',
              properties: {
                artist: { type: 'string' },
                title: { type: 'string' },
                genre: { type: 'string' },
                key: { type: 'string' },
                bpm_min: { type: 'number' },
                bpm_max: { type: 'number' },
                play_count_min: { type: 'number' },
                play_count_max: { type: 'number' },
                rating: { type: 'number' },
                year: { type: 'number' },
              },
            },
          },
        },
      },
      {
        name: 'get_most_played_tracks',
        description: 'Get most played tracks, optionally filtered by genre',
        inputSchema: {
          type: 'object',
          properties: {
            genre: {
              type: 'string',
              description: 'Filter by genre (partial match)',
            },
            limit: {
              type: 'number',
              description: 'Maximum number of results (optional - omit for all)',
            },
          },
        },
      },
      {
        name: 'get_top_rated_tracks',
        description: 'Get highest rated tracks, optionally filtered by genre',
        inputSchema: {
          type: 'object',
          properties: {
            genre: {
              type: 'string',
              description: 'Filter by genre (partial match)',
            },
            limit: {
              type: 'number',
              description: 'Maximum number of results (optional - omit for all)',
            },
          },
        },
      },
      {
        name: 'get_unplayed_tracks',
        description: 'Get tracks with zero play count, optionally filtered and sorted',
        inputSchema: {
          type: 'object',
          properties: {
            genre: {
              type: 'string',
              description: 'Filter by genre (partial match)',
            },
            sort_by: {
              type: 'string',
              description: 'Sort by field: dateAdded, rating, bpm, artist, title, genre, year, totalTime',
              enum: ['dateAdded', 'rating', 'bpm', 'artist', 'title', 'genre', 'year', 'totalTime'],
            },
            limit: {
              type: 'number',
              description: 'Maximum number of results (optional - omit for all)',
            },
          },
        },
      },
      {
        name: 'get_track_file_path',
        description: 'Get the full file path for a specific track',
        inputSchema: {
          type: 'object',
          properties: {
            track_id: {
              type: 'string',
              description: 'The track ID',
            },
          },
          required: ['track_id'],
        },
      },
      {
        name: 'get_track_file_name',
        description: 'Get just the filename for a specific track',
        inputSchema: {
          type: 'object',
          properties: {
            track_id: {
              type: 'string',
              description: 'The track ID',
            },
          },
          required: ['track_id'],
        },
      },
      {
        name: 'search_tracks_by_filename',
        description: 'Search tracks by filename or file path',
        inputSchema: {
          type: 'object',
          properties: {
            filename: {
              type: 'string',
              description: 'Filename or path fragment to search for',
            },
          },
          required: ['filename'],
        },
      },
      {
        name: 'create_playlist_file',
        description: 'Create a playlist file from a list of track IDs',
        inputSchema: {
          type: 'object',
          properties: {
            track_ids: {
              type: 'array',
              items: { type: 'string' },
              description: 'Array of track IDs to include in the playlist',
            },
            file_path: {
              type: 'string',
              description: 'Path where the playlist file should be saved',
            },
            format: {
              type: 'string',
              enum: ['txt', 'm3u', 'm3u8', 'pls'],
              description: 'Playlist format (default: m3u8)',
            },
            playlist_name: {
              type: 'string',
              description: 'Name for the playlist (optional)',
            },
          },
          required: ['track_ids', 'file_path'],
        },
      },
      {
        name: 'create_playlist_from_search',
        description: 'Create a playlist file from search results',
        inputSchema: {
          type: 'object',
          properties: {
            file_path: {
              type: 'string',
              description: 'Path where the playlist file should be saved',
            },
            format: {
              type: 'string',
              enum: ['txt', 'm3u', 'm3u8', 'pls'],
              description: 'Playlist format (default: m3u8)',
            },
            playlist_name: {
              type: 'string',
              description: 'Name for the playlist (optional)',
            },
            search_filters: {
              type: 'object',
              description: 'Search filters (same as search_tracks)',
              properties: {
                artist: { type: 'string' },
                title: { type: 'string' },
                genre: { type: 'string' },
                key: { type: 'string' },
                bpm_min: { type: 'number' },
                bpm_max: { type: 'number' },
                play_count_min: { type: 'number' },
                play_count_max: { type: 'number' },
                rating: { type: 'number' },
                year: { type: 'number' },
                limit: { type: 'number' },
                sort_by: { 
                  type: 'string',
                  enum: ['playCount', 'rating', 'bpm', 'dateAdded', 'dateModified', 'artist', 'title', 'genre', 'year', 'totalTime']
                },
                sort_order: { 
                  type: 'string',
                  enum: ['asc', 'desc']
                },
              },
            },
          },
          required: ['file_path', 'search_filters'],
        },
      },
      {
        name: 'validate_track_ids',
        description: 'Validate a list of track IDs and show which are valid/invalid',
        inputSchema: {
          type: 'object',
          properties: {
            track_ids: {
              type: 'array',
              items: { type: 'string' },
              description: 'Array of track IDs to validate',
            },
          },
          required: ['track_ids'],
        },
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'search_tracks': {
        const searchOptions = {
          artist: args?.artist as string | undefined,
          title: args?.title as string | undefined,
          genre: args?.genre as string | undefined,
          key: args?.key as string | undefined,
          bpmMin: args?.bpm_min as number | undefined,
          bpmMax: args?.bpm_max as number | undefined,
          playCountMin: args?.play_count_min as number | undefined,
          playCountMax: args?.play_count_max as number | undefined,
          rating: args?.rating as number | undefined,
          year: args?.year as number | undefined,
          limit: args?.limit as number | undefined,
          sortBy: args?.sort_by as any,
          sortOrder: args?.sort_order as 'asc' | 'desc' | undefined,
        };

        const tracks = service.searchTracks(searchOptions);
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(
                tracks.map(track => ({
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
                })),
                null,
                2
              ),
            },
          ],
        };
      }

      case 'get_track_details': {
        const { track_id } = args as { track_id: string };
        const track = service.getTrackById(track_id);
        
        if (!track) {
          return {
            content: [
              {
                type: 'text',
                text: `Track with ID ${track_id} not found`,
              },
            ],
          };
        }

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(track, null, 2),
            },
          ],
        };
      }

      case 'get_tracks_by_playlist': {
        const { playlist_name } = args as { playlist_name: string };
        const tracks = service.getTracksByPlaylist(playlist_name);
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(
                tracks.map(track => ({
                  id: track.trackId,
                  title: track.name,
                  artist: track.artist,
                  bpm: track.averageBpm,
                  key: track.tonality,
                })),
                null,
                2
              ),
            },
          ],
        };
      }

      case 'get_library_stats': {
        const stats = service.getLibraryStats();
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(stats, null, 2),
            },
          ],
        };
      }

      case 'get_all_playlists': {
        const playlists = service.getAllPlaylists();
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(
                playlists.map(playlist => ({
                  name: playlist.name,
                  type: playlist.type,
                  trackCount: playlist.tracks.length,
                  entries: playlist.entries,
                })),
                null,
                2
              ),
            },
          ],
        };
      }

      case 'update_track_play_count': {
        const { track_id, play_count } = args as { track_id: string; play_count: number };
        const success = service.updateTrackPlayCount(track_id, play_count);
        
        return {
          content: [
            {
              type: 'text',
              text: success 
                ? `Successfully updated play count for track ${track_id} to ${play_count}`
                : `Failed to update play count: track ${track_id} not found`,
            },
          ],
        };
      }

      case 'update_track_rating': {
        const { track_id, rating } = args as { track_id: string; rating: number };
        const success = service.updateTrackRating(track_id, rating);
        
        return {
          content: [
            {
              type: 'text',
              text: success 
                ? `Successfully updated rating for track ${track_id} to ${rating}`
                : `Failed to update rating: track ${track_id} not found`,
            },
          ],
        };
      }

      case 'get_tracks_by_key': {
        const { key } = args as { key: string };
        const tracks = service.getTracksByKey(key);
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(
                tracks.map(track => ({
                  id: track.trackId,
                  title: track.name,
                  artist: track.artist,
                  bpm: track.averageBpm,
                  key: track.tonality,
                })),
                null,
                2
              ),
            },
          ],
        };
      }

      case 'get_tracks_by_bpm_range': {
        const { min_bpm, max_bpm } = args as { min_bpm: number; max_bpm: number };
        const tracks = service.getTracksByBPMRange(min_bpm, max_bpm);
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(
                tracks.map(track => ({
                  id: track.trackId,
                  title: track.name,
                  artist: track.artist,
                  bpm: track.averageBpm,
                  key: track.tonality,
                })),
                null,
                2
              ),
            },
          ],
        };
      }

      case 'analyze_library': {
        const query = {
          groupBy: args?.group_by as any,
          aggregateBy: args?.aggregate_by as any,
          topN: args?.top_n as number | undefined,
          filters: args?.filters ? {
            artist: (args.filters as any).artist as string | undefined,
            title: (args.filters as any).title as string | undefined,
            genre: (args.filters as any).genre as string | undefined,
            key: (args.filters as any).key as string | undefined,
            bpmMin: (args.filters as any).bpm_min as number | undefined,
            bpmMax: (args.filters as any).bpm_max as number | undefined,
            playCountMin: (args.filters as any).play_count_min as number | undefined,
            playCountMax: (args.filters as any).play_count_max as number | undefined,
            rating: (args.filters as any).rating as number | undefined,
            year: (args.filters as any).year as number | undefined,
          } : undefined,
        };

        const result = service.analyzeLibrary(query);
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case 'get_most_played_tracks': {
        const options = {
          genre: args?.genre as string | undefined,
          limit: args?.limit as number | undefined,
        };

        const tracks = service.getMostPlayedTracks(options);
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(tracks, null, 2),
            },
          ],
        };
      }

      case 'get_top_rated_tracks': {
        const options = {
          genre: args?.genre as string | undefined,
          limit: args?.limit as number | undefined,
        };

        const tracks = service.getTopRatedTracks(options);
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(tracks, null, 2),
            },
          ],
        };
      }

      case 'get_unplayed_tracks': {
        const options = {
          genre: args?.genre as string | undefined,
          sortBy: args?.sort_by as any,
          limit: args?.limit as number | undefined,
        };

        const tracks = service.getUnplayedTracks(options);
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(tracks, null, 2),
            },
          ],
        };
      }

      case 'get_track_file_path': {
        const { track_id } = args as { track_id: string };
        const filePath = service.getTrackFilePath(track_id);
        
        if (!filePath) {
          return {
            content: [
              {
                type: 'text',
                text: `Track with ID ${track_id} not found`,
              },
            ],
          };
        }

        return {
          content: [
            {
              type: 'text',
              text: filePath,
            },
          ],
        };
      }

      case 'get_track_file_name': {
        const { track_id } = args as { track_id: string };
        const fileName = service.getTrackFileName(track_id);
        
        if (!fileName) {
          return {
            content: [
              {
                type: 'text',
                text: `Track with ID ${track_id} not found`,
              },
            ],
          };
        }

        return {
          content: [
            {
              type: 'text',
              text: fileName,
            },
          ],
        };
      }

      case 'search_tracks_by_filename': {
        const { filename } = args as { filename: string };
        const tracks = service.searchTracksByFileName(filename);
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(
                tracks.map(track => ({
                  id: track.trackId,
                  title: track.name,
                  artist: track.artist,
                  fileName: service.getTrackFileName(track.trackId),
                  filePath: service.getTrackFilePath(track.trackId),
                })),
                null,
                2
              ),
            },
          ],
        };
      }

      case 'create_playlist_file': {
        const { track_ids, file_path, format, playlist_name } = args as {
          track_ids: string[];
          file_path: string;
          format?: 'txt' | 'm3u' | 'm3u8' | 'pls';
          playlist_name?: string;
        };

        const result = await service.createPlaylistFile(
          track_ids,
          file_path,
          format || 'm3u8',
          playlist_name
        );
        
        return {
          content: [
            {
              type: 'text',
              text: result,
            },
          ],
        };
      }

      case 'create_playlist_from_search': {
        const { file_path, format, playlist_name, search_filters } = args as {
          file_path: string;
          format?: 'txt' | 'm3u' | 'm3u8' | 'pls';
          playlist_name?: string;
          search_filters: any;
        };

        const searchOptions = {
          artist: search_filters?.artist as string | undefined,
          title: search_filters?.title as string | undefined,
          genre: search_filters?.genre as string | undefined,
          key: search_filters?.key as string | undefined,
          bpmMin: search_filters?.bpm_min as number | undefined,
          bpmMax: search_filters?.bpm_max as number | undefined,
          playCountMin: search_filters?.play_count_min as number | undefined,
          playCountMax: search_filters?.play_count_max as number | undefined,
          rating: search_filters?.rating as number | undefined,
          year: search_filters?.year as number | undefined,
          limit: search_filters?.limit as number | undefined,
          sortBy: search_filters?.sort_by as any,
          sortOrder: search_filters?.sort_order as 'asc' | 'desc' | undefined,
        };

        const result = await service.createPlaylistFromSearch(
          searchOptions,
          file_path,
          format || 'm3u8',
          playlist_name
        );
        
        return {
          content: [
            {
              type: 'text',
              text: result,
            },
          ],
        };
      }

      case 'validate_track_ids': {
        const { track_ids } = args as { track_ids: string[] };
        const validation = service.validateTrackIds(track_ids);
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                summary: `${validation.valid.length} valid, ${validation.invalid.length} invalid`,
                valid: validation.valid,
                invalid: validation.invalid,
              }, null, 2),
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `Error: ${error instanceof Error ? error.message : String(error)}`,
        },
      ],
      isError: true,
    };
  }
});

async function main() {
  // Require XML file path argument
  const xmlPath = process.argv[2];
  if (!xmlPath) {
    console.error('Error: XML file path is required as an argument');
    console.error('Usage: node dist/index.js <path-to-rekordbox.xml>');
    process.exit(1);
  }

  try {
    await service.loadLibrary(xmlPath);
    console.error(`Loaded rekordbox library from: ${xmlPath}`);
  } catch (error) {
    console.error(`Failed to load library: ${error}`);
    process.exit(1);
  }

  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((error) => {
  console.error('Server error:', error);
  process.exit(1);
});