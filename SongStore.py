from Song import Song
import sqlite3

# http://code.google.com/p/leveldb/
# http://code.google.com/p/py-leveldb/
import leveldb

import appinfo
import utils

def dbRepr(o): return utils.betterRepr(o)


def dbUnRepr(s): return eval(s)

class SqliteDB:
    def __init__(self, tableName):
        self.tableName = tableName
        self.dbPath = appinfo.userdir + "/db.sqlite"

        conn = sqlite3.connect(self.dbPath)
        c = conn.cursor()

        sql = 'create table if not exists ' + self.tableName + ' (key Text primary key, value Text)'
        c.execute(sql)

        conn.commit()
        c.close()

    def __getitem__(self, item):
        conn = sqlite3.connect(self.dbPath)
        conn.text_factory = str
        c = conn.cursor()

        c.execute('select value from ' + self.tableName + ' where key = ?', (dbRepr(item),))

        result = c.fetchall()

        if len(result) > 0:
            c.close()
            return dbUnRepr(result[0][0])

        c.close()
        return None


    def __setitem__(self, key, value):
        conn = sqlite3.connect(self.dbPath)
        conn.text_factory = str
        c = conn.cursor()

        repKey = dbRepr(key)
        repVal = dbRepr(value)

        c.execute('select key, value from ' + self.tableName + ' where key = ?', (repKey, ))

        result = c.fetchall()

        if len(result) > 0:
            c.execute('update ' + self.tableName + ' set value = ? where key = ?',(repVal, repKey,))
        else:
            c.execute('insert into ' + self.tableName + ' values(?,?)',(repKey, repVal,))

        conn.commit()
        c.close()

    def __delitem__(self, key):
        conn = sqlite3.connect(self.dbPath)
        conn.text_factory = str
        c = conn.cursor()

        c.execute('delete from ' + self.tableName + ' where key = ?',(dbRepr(key),))

        conn.commit()
        c.close()

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

        conn = sqlite3.connect(self.dbPath)
        c = conn.cursor()

        c.execute('select key from ' + self.tableName + ' where key like ?', (searchString + '%', ))

        keys = []

        for record in c.fetchall():
            keys.append(record[0])

        return keys


class DB:
    def __init__(self, dir):
        self.db = leveldb.LevelDB(appinfo.userdir + "/" + dir, max_open_files=200)

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
        self.artistIndex = DB("artists.db")
        self.titleIndex = DB("titles.db")
        self.genreIndex = DB("genres.db")
        self.songStore = DB("songs.db")

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

    def update(self, AcoustId, data):
        for d in data:
            self.songStore.setAppend(AcoustId, d)

    def searchByArtist(self, searchString):
        keys = self.artistIndex.match_prefix(searchString)
        songs = []

        for key in keys:
            songSet = self.songStore[key]
            if songSet is not None:
                for song in songSet:
                    songs.append(Song(song))

        return songs


    def searchByTitle(self, searchString):
        keys = self.titleIndex.match_prefix(searchString)
        songs = []

        for key in keys:
            songSet = self.titleIndex[key]
            if songSet is not None:
                for song in songSet:
                    songs.append(Song(song))

        return songs


    def searchByGenre(self, searchString):
        keys = self.genreIndex.match_prefix(searchString)
        songs = []

        for key in keys:
            songSet = self.genreIndex[key]
            if songSet is not None:
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
        if oldSong is None:
            return self._getRandomSongs(limit=limit)
        else:
            songs = self._getRandomSongsBasedOnSong(oldSong=oldSong, limit=limit)

            if songs is []:
                return self._getRandomSongs(limit=limit)

    def _getRandomSongs(self, limit=1):
        songs = []
        keys = self._getRandomItemsFromList(self.songStore.match_prefix(''), limit)

        for key in keys:
            songSet = self.songStore[key]
            for song in songSet:
                songs.append(Song(song))

        return songs

    def _getRandomSongsBasedOnSong(self, oldSong=None, limit=1):
        songs = []
        songs = songs + self.searchByArtist(oldSong.artist)
        songs = songs + self.searchByGenre(oldSong.genre)

        return self._getRandomItemsFromList(songs, limit)

    def _getRandomItemsFromList(self, list, numberToReturn=1):
        if list is None or list is [] or numberToReturn < 1 or numberToReturn > len(list):
            return []

        from random import shuffle
        shuffle(list)

        return list[0:numberToReturn]
