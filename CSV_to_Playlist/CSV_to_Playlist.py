import os
from dotenv import load_dotenv
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

load_dotenv()
CID = os.getenv('CID')
SECRET = os.getenv('SECRET')
uri="http://localhost:8080"
scope="playlist-read-private, user-library-read, user-read-private, playlist-modify-private"

def initialize():
    auth = SpotifyOAuth(client_id=CID, client_secret=SECRET, redirect_uri=uri, scope=scope, open_browser=True)
    sp = spotipy.Spotify(oauth_manager=auth)
    return sp

#====| CSV Related |====#
def getData(csv):
    df = pd.read_excel(csv)
    return df

def getSongsFromData(df): # Returns name, artist, and rating for each song.
    songs = []
    for i in range(len(df['Artist'])):
        songs.append([df['Name'][i], df['Artist'][i], df['Rating out of 10'][i]])
    return songs

def getBestInOrder(file):
    df = getData(file)
    songs = getSongsFromData(df)
    filtered = filter(lambda x: x[2] >= 7, songs)
    sorted = [x for x in filtered]
    sorted.sort(reverse=True, key=(lambda x: float(x[2])))
    return sorted


#====| Spotify Related |====#
def FindOrCreatePlaylist(name, sp): # Find Playlist, else create it and recurse
    playlists = sp.current_user_playlists()
    for item in playlists['items']:
        # print(item['name'])
        if name == item['name']:
            return item['id']
    userID = sp.current_user()["id"]
    sp.user_playlist_create(user=userID, name=name, public=False, collaborative=True)
    return FindOrCreatePlaylist(name)

def getSPSongsFromSongList(songs, sp): # Looks for all of the spotify songs in the list and returns a list of their IDs
    songIDs = []
    for song in songs:
        try:
            songID = sp.search(q=f"{song[0]} {song[1]}", limit=1, type='track')['tracks']['items']
            songIDs.append(songID[0]['id'])
        except:
            print(f'{song[0]} by {song[1]} Not able to be searched')
    return songIDs

def AddSongsToPlaylist(playlist, songs, sp): # Receives list of spotify songs and adds them to the playlist
    spotSongs = getSongsFromPLaylist(playlist, sp)
    songs = filter(lambda x: x not in spotSongs, songs) # Avoid adding the same song twice
    songs = [song for song in songs]
    chunks = [songs[i:i+25] for i in range(0, len(songs), 25)] # Send songs off in chunks to prevent errors
    for chunk in chunks:
        sp.playlist_add_items(playlist_id=playlist, items=chunk)

def getSongsFromPLaylist(playlist, sp): # Gets a list of spotify songs from a specified playlist
    results = sp.playlist_tracks(playlist)
    items = results['items']
    while (len(items) < results['total']):
        results = sp.playlist_tracks(playlist, offset=len(items))
        items.extend(results['items'])
    return [item['track']['id'] for item in items]





playlist = "Atlas CSV Filtered"

dataSongs = getBestInOrder("CSV_to_Playlist\Songs for Chris.xlsx")
sp = initialize()
PID = FindOrCreatePlaylist(playlist, sp)

songs = getSPSongsFromSongList(dataSongs, sp)
AddSongsToPlaylist(PID, songs, sp)