#!/usr/bin/env python3 

import os
import requests
import spotipy
import json
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
import spotipy.util as util

import re

GOOGLE_SHEET = f"https://sheets.googleapis.com/v4/spreadsheets/1fQFg52uaojpRCz29EzSHVpsX5SYVJ2VN8IuKs9XA5W8?ranges=2022+Prog-metal&fields=sheets(data(rowData(values(hyperlink))))&key={os.environ['GOOGLE_API_KEY']}"
PLAYLIST = "39gJ3OUrocQ3IdTehoAbMl" # 2022
USER_ID = "ttration"

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


def get_album_list_from_sheet(sheet):
    req = requests.get(sheet)
    if req.status_code > 300:
        return []
    data = req.text
    albums = re.findall(r"(https.*spotify.*album.*)\"", data)
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

if __name__ == '__main__':
    if token:
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=os.environ["SPOTIPY_CLIENT_ID"],
                                                       client_secret=os.environ["SPOTIPY_CLIENT_SECRET"],
                                                       redirect_uri=os.environ["SPOTIPY_REDIRECT_URI"],
                                                       scope="user-library-read playlist-modify-private"))
        spotify_list_albums = get_spotify_playlist_tracks(sp=sp, playlist=PLAYLIST, offset=0)
        google_sheet_albums = get_album_list_from_sheet(GOOGLE_SHEET)  # + get_album_list_from_sheet(GOOGLE_SHEET_PROGROG)
        # print(google_sheet_albums)
        missing = set(map(lambda x: re.findall(r"album/(.*?)(\?|$)", x)[0][0], google_sheet_albums)) - set(spotify_list_albums)
        if len(missing) > 0:
            print("Added %s" % str(missing))
            add_albums_to_spotify_playlist(sp=sp, username=USER_ID, playlist_id=PLAYLIST, albums=missing)
