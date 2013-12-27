
import os, sys

def sysExec(cmd):
	print " ".join(cmd)
	r = os.system(" ".join(cmd))
	if r != 0: sys.exit(r)


def is_uptodate(outfile, depfiles=None):
	try: outmtime = os.path.getmtime(outfile)
	except OSError: return False
	if depfiles is None:
		try: depfiles = get_depfiles(outfile)
		except IOError: return False
	for depfn in depfiles:
		try:
			if os.path.getmtime(depfn) > outmtime:
				return False
		except OSError:
			return False
	return True

def get_cc_outfilename(infile):
	return os.path.splitext(os.path.basename(infile))[0] + ".o"

def get_depfilename(outfile):
	return outfile + ".deps"

def get_depfiles(outfile):
	depfile = get_depfilename(outfile)
	firstLine = True
	lastLine = False
	fileList = []
	for line in open(depfile):
		line = line.strip()
		if not line: continue
		assert not lastLine
		if firstLine:
			assert line.startswith(outfile + ": ")
			line = line[len(outfile) + 2:]
			firstLine = False
		if line[-2:] == " \\":
			line = line[:-2]
		else:
			lastLine = True
		fileList += line.split()
	assert lastLine
	return fileList

def get_mtime(filename):
	return os.path.getmtime(filename)


LDFLAGS = os.environ.get("LDFLAGS", "").split()

def link(outfile, infiles, options):
	if "--weak-linking" in options:
		idx = options.index("--weak-linking")
		options[idx:idx+1] = ["-undefined", "dynamic_lookup"]

	if is_uptodate(outfile, depfiles=infiles):
		print "up-to-date:", outfile
		return

	if sys.platform == "darwin":
		sysExec(
			["libtool", "-dynamic", "-o", outfile] +
			infiles +
			options +
			LDFLAGS +
			["-lc"]
		)
	else:
		sysExec(
			["ld"] +
			["-L/usr/local/lib"] +
			infiles +
			options +
			LDFLAGS +
			["-lc"] +
			["-shared", "-o", outfile]
		)

def link_exec(outfile, infiles, options):
	if is_uptodate(outfile, depfiles=infiles):
		print "up-to-date:", outfile
		return

	sysExec(
		["cc"] +
		infiles +
		options +
		LDFLAGS +
		["-o", outfile]
	)


CFLAGS = os.environ.get("CFLAGS", "").split()
CFLAGS += ["-fpic"]

def cc_single(infile, options):
	if os.path.splitext(infile)[1] == ".cpp":
		options += ["-std=c++11"]

	outfilename = get_cc_outfilename(infile)
	depfilename = get_depfilename(outfilename)

	if is_uptodate(outfilename):
		print "up-to-date:", outfilename
		return

	sysExec(
		["cc"] + options + CFLAGS +
		["-c", infile, "-o", outfilename, "-MMD", "-MF", depfilename]
	)

def cc(files, options):
	for f in files:
		cc_single(f, options)



LinkPython = False
UsePyPy = False

def get_python_linkopts():
	if LinkPython:
		if sys.platform == "darwin":
			return ["-framework", "Python"]
		else:
			return ["-lpython2.7"]
	else:
		return ["--weak-linking"]

def get_python_ccopts():
	if UsePyPy:
		return ["-I", "/usr/local/Cellar/pypy/1.9/include"]
	else:
		return [
			"-I", "/System/Library/Frameworks/Python.framework/Headers/", # mac
			"-I", "/usr/include/python2.7", # common linux/unix
		]
