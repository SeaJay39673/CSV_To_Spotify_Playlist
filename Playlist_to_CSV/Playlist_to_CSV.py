import os
import sys
import io
from dotenv import load_dotenv
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

load_dotenv()
CID = os.getenv('CID')
SECRET = os.getenv('SECRET')
uri="http://localhost:8080"
scope="playlist-read-private, user-library-read, user-read-private"

def initialize():
    auth = SpotifyOAuth(client_id=CID, client_secret=SECRET, redirect_uri=uri, scope=scope, open_browser=True)
    sp = spotipy.Spotify(oauth_manager=auth)
    return sp

def getPlaylists(sp):
    playlists = dict({})
    results = sp.current_user_playlists()
    for item in results['items']:
        playlists[item['name']] = item['id']
    return playlists

def menu(title, list, exit):
    while True:
        print("==========")
        print(title)
        for i in range(len(list)):
            print(str(i+1) + ".) " + list[i])
            if (i == len(list) - 1 and exit):
                print(str(i+2) + ".) Exit")
        val = input("Please make a selection: " )
        if (not val.isdigit() or int(val) <= 0 or int(val) > len(list) + 1 if exit else len(list)):
            input("Incorrect selection, please enter a the number of the playlist you wish to copy to a csv. \nPress enter to try again: ")
        else:
            break
    val = int(val)
    if exit and val == len(list) + 1:
        return -1
    return val - 1

def getDir():
    path = os.path.dirname(sys.argv[0])
    dir = path + "/CSVs"
    return dir


def getFiles():
    dir = getDir()
    if not os.path.exists(dir):
        os.mkdir(dir)
    files = os.listdir(dir)
    files = [file for file in filter(lambda file: file.split(".")[-1] == "xlsx", files)]
    return files

def GetCSVMenu():
    files = getFiles()
    files.append("Create New Playlist CSV")
    while True:
        val = menu("Which File would you like to write to?", files, True)
        if val == -1:
            return val
        if val == len(files) - 1:
            while True:
                fileName = input("Please enter desired name of file (Exit to cancel): " )
                if fileName + ".xlsx" in files:
                    input("FileName already exists, please enter a new file\nPress enter to continue: ")
                elif fileName == "Exit":
                    break
                else:
                    return getDir() + "/" + fileName + ".xlsx"
        else:
            return getDir() + "/" +  files[val]

def GetPlaylistMenu(playlists):
    items = [key for key in playlists]
    return menu("Which playlist would you like to copy?", items, True)
    
def getSongsFromPlaylist(playlist, sp): # Gets a list of spotify songs from a specified playlist
    results = sp.playlist_tracks(playlist)
    items = results['items']
    while (len(items) < results['total']):
        results = sp.playlist_tracks(playlist, offset=len(items))
        items.extend(results['items'])
    songs = []
    for item in items:
        track = item['track']
        songDict = dict({})
        songDict['name'] = track['name']
        songDict['popularity'] = track['popularity']
        songDict['id'] = track['id']
        songDict['artists'] = []

        artists = track['artists']
        for artist in artists:
            di = dict({})
            di['artist'] = artist['name']
            di['id'] = artist['id']
            genres = []
            art = sp.artist(artist['id'])
            genres += art['genres']
            di['genres'] = genres
            songDict['artists'].append(di)
        songs.append(songDict)
    return songs

def putData(file, songs):
    newSongs = []
    for song in songs:
        songDict = dict({})
        songDict['Personal Rating'] = ""
        songDict['Mood'] = ""
        songDict['Song'] = song['name']
        artists = song['artists']
        for i in range(len(artists)):
            songDict[f'Artist {i+1}'] = artists[i]['artist']
            songDict[f'Artist {i+1} Genres'] = ", ".join(artists[i]['genres'])
        newSongs.append(songDict)
    df = pd.DataFrame(newSongs)
    df.to_excel(excel_writer=file, index=False)


def MENU(sp):
    while True:
        playlists = getPlaylists(sp)
        items = [key for key in playlists]
        play = GetPlaylistMenu(playlists)
        if play == -1:
            break
        songs = getSongsFromPlaylist(playlists[items[play]], sp)
        file = GetCSVMenu()
        if file == -1:
            break
        putData(file, songs)


sp = initialize()
MENU(sp)