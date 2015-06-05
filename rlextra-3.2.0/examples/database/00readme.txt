This sample shows you how to get content out of a database
and create some dynamic documents with it using RML, mySQL and ReportLab's
templating engine, 'preppy'.

To run it:

1. Create a mysql database using the file 'create_rldb.sql'.  Log into mySQL
   and execute 'create database rldb'.  Then from a command line, run:
   mysql -u <username> -p <password> rldb <create_rldb.sql
2. Edit the database connection parameters inside rldb.py
3. Run it from the command line:
    python rldb.py
    
You should see four new pdf files being created in the same directory.

The basic architecture is:

1. Connect to the database and retrieve the data.  We have used the 'Table'
class to create a set of python lists containing our 'friends' data. For more
extensive database mapping with read/write etc., use a library like SQLObject
or SQLAlchemy.
2. Loop over the results.  We've used ReportLab's 'preppy' module to merge
the data from the table row into a Report Markup Language 'template', to create
a unique RML file for each person.  This can be done with any templating engine
such as genshi or mako.
3. The RML is compiled into a PDF file using RML2PDF.


The code is extensively commented.  For further information, consult the
documentation included with the distribution, or see the documentation page
on our website at http://www.reportlab.com