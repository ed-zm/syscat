#copyright ReportLab Inc. 2000-2012
#see license.txt for license details
#history www.reportlab.co.uk/rl-cgi/viewcvs.cgi/rlextra/__init__.py
Version='3.2.0'

#legacy support, to be removed.
__version__=Version
import sys

if sys.version_info[0:2]!=(2, 7) and sys.version_info<(3, 3):
    raise ImportError("""rlextra requires Python 2.7+ or 3.3+; 3.0-3.2 are not supported.""")

import reportlab
if reportlab.Version < '3.0.0':
	raise ImportError("""rlextra version %s requires at least reportlab 3.0.0, and you have reportlab %s; it is strongly recommended that you use the same versions""" % (Version, reportlab.Version))
