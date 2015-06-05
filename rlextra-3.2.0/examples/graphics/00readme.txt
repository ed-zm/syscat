This directory contains examples of data-aware charts which you can run
from the command line and edit/run from the Drawing Editor.  There are 
three kinds of charts - some work with CSV or XML files and need no configuration, 
but some need you to set up a sample database.



Getting help
============
All charts support the new Python command line parser, so you can do '--help'
for available options e.g.

C:\rlextra\examples\graphics>legendedpie.py --help
usage: legendedpie.py [options]

options:
  -h, --help            show this help message and exit
  -d, --debug           show tracebacks if errors occur
  -v, --verbose         Show each chart as created
  -s, --save            save fetched data in file for later use
  -r, --replay          do not fetch data, instead replay last saved data set
  -m MAXCHARTS, --max=MAXCHARTS
                        create at most this number of charts


CSV charts
=========
There are five spreadsheet files containing data you can use to generate charts; 
these can be opened in Excel or other tools.

time_series.csv
legendedpie.csv
scatterplot.csv
slidebox.csv
stackedBar.csv     

There are also five corresponding Python scripts you can just execute from
a command prompt e.g.


C:\rlextra\examples\graphics>legendedpie.py
generating PDF file C:\Python24\rlextra\examples\graphics\output\piechart001.pdf
generating EPS file C:\Python24\rlextra\examples\graphics\output\piechart001.eps
generating PDF file C:\Python24\rlextra\examples\graphics\output\piechart002.pdf
generating EPS file C:\Python24\rlextra\examples\graphics\output\piechart002.eps





XML charts:
===========
sampleBar.xml, sampleBar.py

This works as above.  XML charts are rarely used by real customers but these days 
you have to support XML to be cool ;-)





Database charts:
================
retrieve data from an microsoft access or MySQL sample database.

MS Access:
----------
we provide an example Access database called 'sampledata.mdb' for the data aware charts. 
You need to unzip this from sampledata.zip and register it as an ODBC data source called
'samplechartdata'.

If not familiar with ODBC data sources, do the following:

Start => Settings => Control Panel => Administrative Tools => Data Sources (ODBC) 
on the User DSN(Data Source Name) tab, click 'Add'and then select Microsoft Access Driver (*.mdb) and click Finish.
You will be prompted with a Set Up window, give your Data Source Name the name "samplechartdata".
Then locate the sample database (sampledata.mdb) and then click OK twice.

if the ODBC connection is successful then you can run all data aware charts (you will notice the filenames end by underscore db "_db").
  
dotbox_db.py
gridlineplot_db.py
horizontalbarchart_db.py
slidebox_db.py
verticalbarchart_db.py

MySQL:
------
We also provide the sample database as an SQL script which is tested on MySQL. This should be trivial to adapt to any other server-side relational database.  

if do already have MySQL installed on you PC, connect to MySQL as you do normally and create the database by:

from command line: 
	once connected, type source path_where_sampledata.sql_lives
	
	e.g:	mysql>source C:\examples\graphics\sampledata.sql

from a client browser (MySQLFront or any other):
	open the browser, copy and paste the sampledata.sql contents and then run it as an SQL query

The above methods will create the database, all required tables as well as data to work with.

You will need to modify the connection parameters in each Database chart using the Drawing Editor to give it the MySQL connection parameters.
 





