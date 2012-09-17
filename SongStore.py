from Song import Song

# http://code.google.com/p/leveldb/
# http://code.google.com/p/py-leveldb/
import leveldb

import appinfo
import utils

def dbRepr(o): return utils.betterRepr(o)


def dbUnRepr(s): return eval(s)


class DB:
    def __init__(self, dir):
        self.db = leveldb.LevelDB(appinfo.userdir + "/" + dir)

    def __getitem__(self, item):
        try:
            return dbUnRepr(self.db.Get(dbRepr(item)))
        except KeyError:
            return None

    def __setitem__(self, key, value):
        self.db.Put(dbRepr(key), dbRepr(value))

    def __delitem__(self, key):
        self.db.Delete(dbRepr(key))

    def setDefault(self, key, value):
        if self[key] is not None:
            return self[key]
        else:
            self[key] = value
            return self[key]

    #If not value set at key, it creates a set. Will append value to set
    def setAppend(self, key, valueToAppend):
        value = self.setDefault(key, set())
        value.add(valueToAppend)
        self[key] = value
        return value

    #if key not set does nothing. If it is set then remove the value from the key. If key is empty, removes key
    def setRemove(self, key, valueToRemove):
        if self[key] is not None:
            value = self[key]
            value.remove(valueToRemove)
            if len(value) == 0:
                del self[key]

    def match_prefix(self, searchString):

        keys = []

        for record in self.db.RangeIter():
            if record[0].startswith(searchString):
                keys.append(record[0])

        return keys



class SongStore:
    def __init__(self):
        self.artistIndex = DB(".artists")
        self.titleIndex = DB(".titles")
        self.genreIndex = DB(".genres")
        self.songStore = DB(".songs")

    def add(self, song):
        self.songStore.setAppend(song.fingerprint_AcoustID, song.url)
        self.artistIndex.setAppend(song.artist, song.fingerprint_AcoustID)
        self.titleIndex.setAppend(song.title, song.fingerprint_AcoustID)
        self.genreIndex.setAppend(song.genre, song.fingerprint_AcoustID)

    def addMany(self, songs):
        for song in songs:
            self.add(song)


    def remove(self, song):
        self.songStore.setRemove(song.fingerprint_AcoustID, song.url)
        self.artistIndex.setRemove(song.artist, song.fingerprint_AcoustID)
        self.titleIndex.setRemove(song.title, song.fingerprint_AcoustID)
        self.genreIndex.setRemove(song.genre, song.fingerprint_AcoustID)


    def removeMany(self, songs):
        for song in songs:
            self.remove(song)

    def get(self, AcoustId):
        return self.songStore[AcoustId]

    def searchByArtist(self, searchString):
        keys = self.artistIndex.match_prefix(searchString)
        songs = []

        for key in keys:
            songSet = self.songStore[key]
            for song in songSet:
                songs.append(Song(song))

        return songs


    def searchByTitle(self, searchString):
        keys = self.titleIndex.match_prefix(searchString)
        songs = []

        for key in keys:
            songSet = self.titleIndex[key]
            for song in songSet:
                songs.append(Song(song))

        return songs


    def searchByGenre(self, searchString):
        keys = self.genreIndex.match_prefix(searchString)
        songs = []

        for key in keys:
            songSet = self.genreIndex[key]
            for song in songSet:
                songs.append(Song(song))

        return songs


    def search(self, searchString):
        songs = []

        songs = songs + self.searchByArtist(searchString)
        songs = songs + self.searchByTitle(searchString)
        songs = songs + self.searchByGenre(searchString)

        return songs


    def getRandomSongs(self, oldSong=None, limit=1):
        from random import sample

        songs = []

        if oldSong is None:
            keys = sample(self.songStore.match_prefix(''), limit)

            for key in keys:
                songSet = self.songStore[key]
                for song in songSet:
                    songs.append(Song(song))

            return songs
        else:
            songs = songs + self.searchByArtist(oldSong.artist)
            songs = songs + self.searchByGenre(oldSong.genre)

            return sample(songs, limit)