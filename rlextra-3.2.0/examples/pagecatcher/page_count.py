#!/usr/home/rptlab2/bin/python -u
import fnmatch
import sys, os
from rlextra.utils.buildutils import kill

_debug = 0
_prune = ['(*)']

def find(pattern, dir = os.curdir, noDirs=0, noFiles=0):
	L = []
	names = os.listdir(dir)
	names.sort()
	for name in names:
		if name in (os.curdir, os.pardir): continue
		fullname = os.path.join(dir, name)
		isDir = os.path.isdir(fullname)
		if fnmatch.fnmatch(name, pattern):
			if (isDir and not noDirs) or (not isDir and not noFiles): L.append(fullname)
		if isDir and not os.path.islink(fullname):
			for p in _prune:
				if fnmatch.fnmatch(name, p):
					if _debug: print("skip", repr(fullname))
					break
			else:
				if _debug: print("descend into", repr(fullname))
				L += find(pattern, fullname, noDirs=noDirs, noFiles=noFiles)
	return L

def count_pages(infn):
	from rlextra.pageCatcher import pageCatcher
	from reportlab.pdfgen.canvas import Canvas
	from reportlab.lib import units
	import sys
	D = pageCatcher.storeFormsInDict(open(infn,'rb').read(),all=1)
	names = D[None]
	del D
	return len(names)

def main(indir):
	indir = os.path.normpath(os.path.abspath(indir))
	while indir[-1]==os.sep: indir = indir[:-1]
	if not os.path.isdir(indir): raise ValueError('%s isn\'t a directory' % indir)
	n = len(indir)
	m = n+len(os.sep)

	total = 0
	num = 0
	for fn in find('*.pdf', dir=indir, noDirs=1, noFiles=0):
		pc = count_pages(fn)
		total += pc
		num += 1
		print("%6d: '%s' %d pages, total=%d" % (num, fn[m:],pc,total))

if __name__=='__main__':
	if len(sys.argv)<2: raise ValueError('Need indir argument')
	for indir in sys.argv[1:]:
		main(indir)
