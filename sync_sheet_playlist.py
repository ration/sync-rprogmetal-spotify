#!/usr/bin/env python3 

import os
import requests
import spotipy
import json
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util

import re

GOOGLE_SHEET="https://spreadsheets.google.com/feeds/cells/1fQFg52uaojpRCz29EzSHVpsX5SYVJ2VN8IuKs9XA5W8/1/public/full?alt=json"
PLAYLIST="1JhoE1TBSTYsP3i2l5F5Yd" # https://open.spotify.com/playlist/1JhoE1TBSTYsP3i2l5F5Yd?si=BF_eFvalTx6wfFByf7PfIA
USER_ID="ttration"

def get_spotify_playlist_tracks(sp, playlist, offset=0):
    playlist_data = sp.playlist_tracks(PLAYLIST, limit=100, offset=offset)
    spotify_list_albums = []
    if len(playlist_data['items']) > 0:
        for tracks in playlist_data['items']:
            track = tracks['track']
            if track['album']['id'] not in spotify_list_albums:
                spotify_list_albums.append(track['album']['id'])
        spotify_list_albums = spotify_list_albums + get_spotify_playlist_tracks(sp, playlist, offset+100)
    return spotify_list_albums
    
def get_album_list_from_sheet():
    google_sheet_data = json.loads(requests.get(GOOGLE_SHEET).text)
    albums = []
    album_re = re.compile("spotify\.com\/album\/(.*?)[\"|\?]")
    for entry in google_sheet_data['feed']['entry']:
        cell = entry['gs$cell']
        spotify_match = album_re.search(cell['inputValue'])
        if cell['col'] == "9" and spotify_match:
            albums.append(spotify_match[1])
    return albums


def add_albums_to_spotify_playlist(sp, username, playlist_id, albums):
    for album in albums:
        ids = []
        sp_album = sp.album_tracks(album)
        if 'items' in sp_album:
            for track in sp_album['items']:            
                ids.append(track['id'])
        elif 'tracks' in sp_album:
            for track in sp_album['tracks']['items']:
                ids.append(track['id'])
        sp.user_playlist_add_tracks(username, playlist_id, ids)

        

scope = 'playlist-modify-public'
token = util.prompt_for_user_token(USER_ID, scope)

if token:
    sp = spotipy.Spotify(auth=token)
    spotify_list_albums = get_spotify_playlist_tracks(sp=sp, playlist=PLAYLIST, offset=0)
    #print(spotify_list_albums)
    google_sheet_albums = get_album_list_from_sheet()
    #print(google_sheet_albums)
    missing = set(google_sheet_albums) - set(spotify_list_albums)
    print("Added %s" % str(missing))
    add_albums_to_spotify_playlist(sp=sp, username=USER_ID, playlist_id=PLAYLIST,albums=missing)


