import os, sqlite3, fnmatch
from Song import Song

# Class for dealing with songs in the database
# Fills Database with songs and select next song to play
class SongDatabase:
	def __init__(self, rootdir, fileexts, databasepath):
		self.rootdir = rootdir
		self.fileexts = fileexts
		self.databasepath = databasepath


	def fillDatabase(self):

		if self.databaseExists() is False:
			print "database not here"
			conn = sqlite3.connect(self.databasepath)
			conn.text_factory = str
			c = conn.cursor()
			c.execute('''CREATE TABLE songs
				(url text, album text, artist text, composer text, date text, duration text, title text, track int, genre text)''')

			files = self.getFiles()
			songs = []

			for file in files:
				song = Song(file)
				songData = (song.url,
							song.album, song.artist,
							song.composer, song.date,
							song.duration, song.title,
							song.track, song.genre)

				songs.append(songData)


			c.executemany('INSERT INTO songs VALUES (?,?,?,?,?,?,?,?,?)', songs)
			conn.commit()
			c.close()
		else:
			print "already exist"


	def databaseExists(self):
		try:
			with open(self.databasepath) as f: pass
			return True
		except IOError as e:
			return False


	def getFiles(self):
		matches = []
		for root, dirnames, filenames in os.walk(self.rootdir):
			for filename in filenames:
				if filename.endswith(self.fileexts):
					matches.append(os.path.join(root, filename))

		return matches


	# picks a new song to play based on an the song given or
	# randomly picks a song
	def getRandomSong(self, oldSong=None):
		conn = sqlite3.connect(self.databasepath)
		conn.text_factory = str
		c = conn.cursor()
		nextSong = ""
		if oldSong is None:
			c.execute('SELECT url FROM songs order by RANDOM() LIMIT 1')
			nextSong = c.fetchone()
		else:
			params = (oldSong.album, oldSong.artist, 
				oldSong.composer, oldSong.genre)

			c.execute('SELECT url FROM songs where album = ? or artist = ? or composer = ? or genre = ? order by RANDOM() LIMIT 1', params)
			nextSong = c.fetchone()

		c.close()

		return Song(nextSong[0])


	def getRandomSongs(self, oldSong=None, limit=1):
		conn = sqlite3.connect(self.databasepath)
		conn.text_factory = str
		c = conn.cursor()
		nextSong = ""
		if oldSong is None:
			c.execute('SELECT url FROM songs order by RANDOM() LIMIT ' + str(limit))
			nextSongs = c.fetchall()
		else:
			params = (oldSong.album, oldSong.artist,
					  oldSong.composer, oldSong.genre)

			c.execute('SELECT url FROM songs where album = ? or artist = ? or composer = ? or genre = ? order by RANDOM() LIMIT ' + str(limit), params)
			nextSongs = c.fetchall()

		c.close()

		songs = []

		for song in nextSongs:
			songs.append(Song(song[0]))

		return songs

	def removeSongs(self, filenames):
		conn = sqlite3.connect(self.databasepath)
		c = conn.cursor()

		for file in filenames:
			params = (file)
			c.execute('Delete from songs where url = ?', params)


		conn.commit()
		c.close()


	def removeAllSongs(self):
		conn = sqlite3.connect(self.databasepath)
		c = conn.cursor()
		c.execute('Delete from songs')
		conn.commit()
		c.close()


	def getSongCount(self):
		conn = sqlite3.connect(self.databasepath)
		c = conn.cursor()
		c.execute('Select count(url) from songs')
		count = c.fetchone()
		c.close()

		return count
