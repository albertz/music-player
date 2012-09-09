import sqlite3
from Song import Song


# Class for dealing with songs in the database
# Fills Database with songs and select next song to play
class SongStore:
	def __init__(self, databasepath):
		self.databasepath = databasepath

	def initDatabase(self):
		if not self.databaseExists():
			print "database not here"
			conn = sqlite3.connect(self.databasepath)
			conn.text_factory = str
			c = conn.cursor()
			c.execute('''CREATE TABLE songs(key text, value text)''')

			conn.commit()
			c.close()
		else:
			print "already exist"


	def deleteDatabase(self):
		import os
		try:
			os.remove(self.databasepath)
		except:
			pass

	def databaseExists(self):
		try:
			with open(self.databasepath) as f: pass
			return True
		except IOError as e:
			return False

	def addSongs(self, filenames):
		conn = sqlite3.connect(self.databasepath)
		conn.text_factory = str
		c = conn.cursor()

		for file in filenames:
			c.execute('Select count(key) from songs where key = ?', (file,))

			count = c.fetchone()[0]

			if count is 0:
				song = Song(file)
				c.execute('INSERT INTO songs VALUES (?,?)', (song.url, str(song.metadata)))
				conn.commit()

		c.close()

	def addSongsFromDirectory(self, dir):
		import utils
		files = utils.getMusicFromDirectory(dir)
		self.addSongs(files)


	#remove deleted files from database and add new ones
	def update(self, directories):
		import utils
		for dir in directories:
			filesFromDisk = set(utils.getMusicFromDirectory(dir))
			filesFromDb = set(self.getSongPathsInDirectory(dir))

			#all songs that are in the database, but not on disk
			filesToDelete = list(filesFromDb - filesFromDisk)

			self.removeSongs(filesToDelete)

			#new songs added to disk, but not in db
			filesToAdd = list(filesFromDisk - filesFromDb)

			self.addSongs(filesToAdd)

	def getSongPathsInDirectory(self, dir):
		conn = sqlite3.connect(self.databasepath)
		conn.text_factory = str
		c = conn.cursor()
		c.execute('select key from songs where key like ?', (dir + '%',))

		results = c.fetchall()
		c.close()

		filenames = []

		for result in results:
			filenames.append(result[0])

		return filenames


	def getSongCount(self):
		conn = sqlite3.connect(self.databasepath)
		conn.text_factory = str
		c = conn.cursor()
		c.execute('Select count(key) from songs')
		count = c.fetchone()[0]
		c.close()

		return count

	def search(self, searchString, limit=0):
		conn = sqlite3.connect(self.databasepath)
		conn.text_factory = str
		c = conn.cursor()

		param = '%' + searchString + '%'
		if limit > 0:
			c.execute('''SELECT key FROM songs where value like ? LIMIT ''' + str(limit), (param,))
		else:
			c.execute('''SELECT key FROM songs where value like ? ''', (param,))

		results = c.fetchall()
		c.close()

		songs = []

		for result in results:
			songs.append(Song(result[0]))

		return songs

	# picks a new song to play based on an the song given or
	# randomly picks a song
	def getRandomSongs(self, oldSong=None, limit=1):
		conn = sqlite3.connect(self.databasepath)
		conn.text_factory = str
		c = conn.cursor()
		nextSong = ""
		if oldSong is None:
			c.execute('SELECT key FROM songs order by RANDOM() LIMIT ' + str(limit))
			nextSongs = c.fetchall()
		else:
			params = (oldSong.url, "%'album': '" + oldSong.album + "%", "%'artist': '" + oldSong.artist + "%",
					  "%'composer': '" + oldSong.composer + "%", "%'genre': '" + oldSong.genre + "%")

			c.execute('SELECT key FROM songs where key <> ? and (value like ? or value like ? or value like ? or value like ?) order by RANDOM() LIMIT ' + str(limit), params)
			nextSongs = c.fetchall()

		c.close()

		songs = []

		for song in nextSongs:
			songs.append(song[0])

		return songs

	def updateSong(self, song):
		conn = sqlite3.connect(self.databasepath)
		conn.text_factory = str
		c = conn.cursor()
		c.execute('''Update songs
		 set key = ?, value = ?
		 where key = ?''', (song.url, str(song.metadata), song.url))

		conn.commit()
		c.close()

	def removeSongs(self, filenames):
		conn = sqlite3.connect(self.databasepath)
		conn.text_factory = str
		c = conn.cursor()

		for file in filenames:
			c.execute('Delete from songs where key = ?', (file,))

		conn.commit()
		c.close()


	def removeAllSongs(self):
		conn = sqlite3.connect(self.databasepath)
		conn.text_factory = str
		c = conn.cursor()
		c.execute('Delete from songs')
		conn.commit()
		c.close()


	def removeDirectories(self, dirs):
		conn = sqlite3.connect(self.databasepath)
		conn.text_factory = str
		c = conn.cursor()

		for dir in dirs:
			c.execute('Delete from songs where key like ?', (dir + '%',))

		conn.commit()
		c.close()

