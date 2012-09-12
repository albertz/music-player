import sqlite3
from Song import Song
import os
from kyotocabinet import *


class SongStore:
	def __init__(self, databasedir):
		self.databasedir = databasedir
		self.artistIndex = DB()
		self.titleIndex = DB()
		self.genreIndex = DB()
		self.songStore = DB()

	def open(self):
		self.artistIndex.open(self.databasedir + "/artistIndex.kct", DB.OWRITER | DB.OCREATE)
		self.titleIndex.open(self.databasedir + "/titleIndex.kct", DB.OWRITER | DB.OCREATE)
		self.genreIndex.open(self.databasedir + "/genreIndex.kct", DB.OWRITER | DB.OCREATE)
		self.songStore.open(self.databasedir + "/songStore.kct", DB.OWRITER | DB.OCREATE)

	def close(self):
		self.artistIndex.close()
		self.titleIndex.close()
		self.genreIndex.close()
		self.songStore.close()

	def add(self, song):
		if self.songStore[song.fingerprint_AcoustID] is None:
			self.songStore[song.fingerprint_AcoustID] = set(song.url)
		else:
			self.songStore[song.fingerprint_AcoustID].add(song.url)

		if self.artistIndex[song.artist] is None:
			self.artistIndex[song.artist] = set(song.fingerprint_AcoustID)
		else:
			self.artistIndex[song.artist].add(song.fingerprint_AcoustID)

		if self.titleIndex[song.title] is None:
			self.titleIndex[song.title] = set(song.fingerprint_AcoustID)
		else:
			self.titleIndex[song.title].add(song.fingerprint_AcoustID)

		if self.genreIndex[song.genre] is None:
			self.genreIndex[song.genre] = set(song.fingerprint_AcoustID)
		else:
			self.genreIndex[song.genre].add(song.fingerprint_AcoustID)


	def addMany(self, songs):
		for song in songs:
			self.add(song)


	def remove(self, song):
		if self.songStore[song.fingerprint_AcoustID]:
			self.songStore[song.fingerprint_AcoustID].remove(song.url)

		if len(self.songStore[song.fingerprint_AcoustID]) == 0:
			self.songStore.remove(song.fingerprint_AcoustID)

		if self.artistIndex[song.artist]:
			self.artistIndex[song.artist].remove(song.fingerprint_AcoustID)

		if len(self.artistIndex[song.artist]) == 0:
			self.artistIndex.remove(song.artist)

		if self.titleIndex[song.title]:
			self.titleIndex[song.title].remove(song.fingerprint_AcoustID)

		if len(self.titleIndex[song.title]) == 0:
			self.titleIndex.remove(song.title)

		if self.genreIndex[song.genre]:
			self.genreIndex[song.genre].remove(song.fingerprint_AcoustID)

		if len(self.genreIndex[song.genre]) == 0:
			self.genreIndex.remove(song.genre)


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