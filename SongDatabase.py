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
			c = conn.cursor()
			c.execute('''CREATE TABLE songs
				(url text, album text, artist text, composer text, date text, duration text, title text, track int)''')

			songs = []
			files = self.getFiles()

			for file in files:
				song = Song(file)
				songs.append((song.url.decode('utf-16'), 
					song.album.decode('utf-16'), song.artist.decode('utf-16'), 
					song.composer.decode('utf-16'), song.date.decode('utf-16'), song.duration, 
					song.title.decode('utf-16'), song.track))

			c.executemany('INSERT INTO songs VALUES (?,?,?,?,?,?,?,?)', songs)

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
			for filename in fnmatch.filter(filenames, "*.mp3"):
				matches.append(os.path.join(root, filename))

		return matches


	# picks a new song to play based on an the song given or
	# randomly picks a song
	def getRandomSong(self, oldSong=None):
		conn = sqlite3.connect(self.databasepath)
		c = conn.cursor()
		nextSong = ""
		if(oldSong is None):
			c.execute('SELECT url FROM songs order by RANDOM() LIMIT 1')
			nextSong = c.fetchone()
		else:
			params = (oldSong.album, oldSong.artist, 
				oldSong.composer)

			c.execute('SELECT url FROM songs where album = ? or artist = ? or composer = ? order by RANDOM() LIMIT 1', params)			
			nextSong = c.fetchone()

		c.close()

		return Song(nextSong)	
