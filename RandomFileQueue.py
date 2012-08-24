
# loosely inspired from https://github.com/albertz/PictureSlider/blob/master/PictureSlider/FileQueue.cpp

import os, random

C_nonloaded_dirs_expectedFac = 0.5
C_nonloaded_dirs_expectedMin = 100

rndInt = random.randint

class RandomFileQueue:
	def __init__(self, rootdir, fileexts):
		self.rootdir = rootdir
		self.fileexts = fileexts
		
		def hasCorrectFileext(f):
			ext = os.path.splitext(f)[1]
			ext = ext.lower()
			for allowedExt in self.fileexts:
				if ext == "." + allowedExt.lower():
					return True
			return False
			
		class Dir:
			owner = self
			isLoaded = False
			base = None

			def __init__(self):
				self.files = []
				self.loadedDirs = []
				self.nonloadedDirs = []

			def load(self):
				self.isLoaded = True
				# Note: If we could use the C readdir() more directly, that would be much faster because it already provides the stat info (wether it is a file or dir), so we don't need to do a separate call for isfile/isdir.
				for f in os.listdir(self.base):
					if f.startswith("."): continue
					if os.path.isfile(self.base + "/" + f):
						if hasCorrectFileext(f):
							self.files += [f]
					elif os.path.isdir(self.base + "/" + f):
						subdir = Dir()
						subdir.base = self.base + "/" + f
						self.nonloadedDirs += [subdir]

			def expectedFilesCount(self):
				c = 0
				c += len(self.files)
				for d in self.loadedDirs:
					c += d.expectedFilesCount()
				c += len(self.nonloadedDirs) * \
					max(int(C_nonloaded_dirs_expectedFac * c), C_nonloaded_dirs_expectedMin)
				return c
				
			def randomGet(self):
				if not self.isLoaded: self.load()
				
				while True:
					rmax = self.expectedFilesCount()
					if rmax == 0: return None
					r = rndInt(0, rmax - 1)
					
					if r < len(self.files):
						return self.base + "/" + self.files[r]
					r -= len(self.files)
					
					for d in self.loadedDirs:
						c = d.expectedFilesCount()
						if r < c:
							f = d.randomGet()
							if f: return f
							r = None
							break
						r -= c
					if r is None: continue
					
					assert len(self.nonloadedDirs) > 0
					r = rndInt(0, len(self.nonloadedDirs) - 1)
					d = self.nonloadedDirs[r]
					self.nonloadedDirs = self.nonloadedDirs[:r] + self.nonloadedDirs[r+1:]
					d.load()
					self.loadedDirs += [d]
					
		self.root = Dir()
		self.root.base = rootdir
		
	def getNextFile(self):
		return self.root.randomGet()

def test():
	q = RandomFileQueue(rootdir = os.path.expanduser("~/Music"), fileexts=["mp3","ogg","flac"])
	i = 0
	while i < 100:
		i += 1
		print q.getNextFile()

if __name__ == '__main__':
	test()
