from rlextra.utils.releaser import CVSLog
L = CVSLog(open('/tmp/ooo','r').read())
for l in L.entries:
	print l.wfn, l.tags
	for r in l.revs:
		print '\t'+str(r)
		#this is a dumb comment
