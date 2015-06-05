This directory includes a basic CGI web app
to let us test chart functionality.  I
future, I hope we could evvolve a full
edit-through-web tool like the drawing editor.
For now it is limited to visual tests of the
quickchart functions.


This CGI script (modified for your
system) should be enough to kick it off.

#!C:\Python22\python.exe -u
import os
os.chdir('c:\\code\\rlextra\\graphics\\webcharts')
import sys
sys.path.insert(0, os.getcwd())
import chartcontroller
app = chartcontroller.WebChartApp()
app.cgiName = '/cgi-bin/webcharts.cgi'
app.handleCgi()
