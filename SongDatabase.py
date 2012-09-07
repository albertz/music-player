import sqlite3
from Song import Song

# Class for dealing with songs in the database
# Fills Database with songs and select next song to play
class SongDatabase:
	def __init__(self, databasepath):
		self.databasepath = databasepath

	def initDatabase(self):
		if not self.databaseExists():
			print "database not here"
			conn = sqlite3.connect(self.databasepath)
			conn.text_factory = str
			c = conn.cursor()
			c.execute('''CREATE TABLE directories(path text)''')
			c.execute('''CREATE TABLE songs
				(url text, album text, artist text, composer text, date text, duration text, title text, track int, genre text)''')

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

	def addSongs(self, filenames):
		conn = sqlite3.connect(self.databasepath)
		conn.text_factory = str
		c = conn.cursor()

		for file in filenames:
			c.execute('Select count(url) from songs where url = ?', (file,))

			count = c.fetchone()[0]

			if count is 0:
				song = Song(file)
				songData = (song.url,
							song.album, song.artist,
							song.composer, song.date,
							song.duration, song.title,
							song.track, song.genre)
				c.execute('INSERT INTO songs VALUES (?,?,?,?,?,?,?,?,?)', songData)
				conn.commit()

		c.close()

	def addSongsFromDirectory(self, dir):
		conn = sqlite3.connect(self.databasepath)
		conn.text_factory = str
		c = conn.cursor()

		c.execute('Select count(path) from directories where path = ?', (dir,))

		count = c.fetchone()[0]

		if count is 0:
			import utils

			files = utils.getMusicFromDirectory(dir)

			c.execute('insert into directories values (?)', (dir,))
			conn.commit()

			for file in files:
				song = Song(file)
				songData = (song.url,
							song.album, song.artist,
							song.composer, song.date,
							song.duration, song.title,
							song.track, song.genre)
				c.execute('INSERT INTO songs VALUES (?,?,?,?,?,?,?,?,?)', songData)
				conn.commit()

			c.close()
		else:
			print "directory already in database"




	#remove deleted files from database and add new ones
	def update(self):
		directories = self.getDirectories()
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

	def getDirectories(self):
		conn = sqlite3.connect(self.databasepath)
		c = conn.cursor()
		c.execute('Select path from directories')
		results = c.fetchall()
		c.close()

		directories = []

		for result in results:
			directories.append(result[0])

		return directories

	def getSongPathsInDirectory(self, dir):
		conn = sqlite3.connect(self.databasepath)
		conn.text_factory = str
		c = conn.cursor()
		c.execute('select url from songs where url like ?', (dir + '%',))

		results = c.fetchall()
		c.close()

		filenames = []

		for result in results:
			filenames.append(result[0])

		return filenames


	def getSongCount(self):
		conn = sqlite3.connect(self.databasepath)
		c = conn.cursor()
		c.execute('Select count(url) from songs')
		count = c.fetchone()[0]
		c.close()

		return count

	def search(self, searchString, limit=0):
		conn = sqlite3.connect(self.databasepath)
		conn.text_factory = str
		c = conn.cursor()
		param = '%' + searchString + '%'
		params = (param, param, param, param, param, param)
		c.execute('''SELECT url FROM songs where
		artist like ? or
		 album like ? or
		 composer like ? or
		 genre like ? or
		 date like ? or
		 title like ?
		 LIMIT ''' + str(limit), params)

		results = c.fetchall()
		c.close()

		songs = []

		for result in results:
			songs.append(Song(file))

		return songs

	# picks a new song to play based on an the song given or
	# randomly picks a song
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
					  oldSong.composer, '%' + oldSong.genre + '%')

			c.execute('SELECT url FROM songs where album = ? or artist = ? or composer = ? or genre like ? order by RANDOM() LIMIT ' + str(limit), params)
			nextSongs = c.fetchall()

		c.close()

		songs = []

		for song in nextSongs:
			songs.append(song[0])

		return songs

	def updateSong(self, song):
		conn = sqlite3.connect(self.databasepath)
		c = conn.cursor()
		c.execute('''Update songs
		 set album = ?, artist = ?,
		 composer = ?, date = ?,
		 duration = ?, title = ?,
		 track = ?, genre = ?
		 where url = ?''', (song.album, song.artist,
							song.composer, song.date,
							song.duration, song.title,
							song.track, song.genre,
							song.url))

		conn.commit()
		c.close()

	def removeSongs(self, filenames):
		conn = sqlite3.connect(self.databasepath)
		c = conn.cursor()

		for file in filenames:
			c.execute('Delete from songs where url = ?', (file,))

		conn.commit()
		c.close()


	def removeAllSongs(self):
		conn = sqlite3.connect(self.databasepath)
		c = conn.cursor()
		c.execute('Delete from songs')
		conn.commit()
		c.close()


	def removeDirectories(self, dirs):
		conn = sqlite3.connect(self.databasepath)
		c = conn.cursor()

		for dir in dirs:
			c.execute('Delete from directories where path = ?', (dir,))
			c.execute('Delete from songs where url like ?', (dir + '%',))


		conn.commit()
		c.close()


	def removeAllDirectories(self):
		conn = sqlite3.connect(self.databasepath)
		c = conn.cursor()
		c.execute('Delete from directories')
		c.execute('Delete from songs')
		conn.commit()
		c.close()
