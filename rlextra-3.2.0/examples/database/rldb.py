"""
This ReportLab sample demonstrates how to create dynamic documents
using RML and a mySQL database with the 'preppy' templating engine.
It creates a few simple one-page PDFs.

Other databases (odbc, Postgres etc) all follow a highly similar API - typically
the connect method is all that differs at this level.

Create the required database with the script 'create_rldb.sql', and look
inside 'rldb.prep' to see how the basic PDF document is described in Report
Markup Language.

If you're an old Python hand, probably the only portions relevant here
are the 'main()' function at the bottom and the 'rmltemplate.prep' file.
If new to the language, we'll digress for a little and discuss how the
language handles databases.

If you're sitting down to write a database report using Python, preppy and RML,
you may be pleasantly surprised how readable it can be.  Python has a standard
database API, so the connection code for MySQL, Postgresql, Oracle, ODBC and so
on tends to be almost identical.

When writing a report or generating a web page, we generally just want no-fuss
access to variables.  People from Java or old Microsoft days remember a lot of lines
of code with names like OpenRecordSet, FieldByName, MoveNext etc;
and a lot of brackets and quotes to type as you access fields by name or position.

In Python, when you do a query, you just grab some rows and get back a nested
structure like this    (the last item is a date object)

((1, 'John', 'Smith', datetime.date(1975, 1, 12)),
 (2, 'Jane', 'Bloggs', datetime.date(1977, 2, 1)),
 (3, 'Yamanda', 'Taro', datetime.date(1980, 3, 10)),
 (4, 'Nai', 'Gor', datetime.date(1985, 5, 20)))

If you're just looping over the data, this is often all you need.  You can access
things by indexing (thus, above, rows[0][2] is 'Smith'), but also easily loop
and unpack into named variables.  Thus, in an HTMl or RML template, this works:

{{for (id, firstName, surname, DOB) in rows}}
  <tr>
    <td>{{id}}</td>
    <td>{{firstName}}</td>
    ....
  </tr>
{{}}

Note that if you are coming from something like Crystal Reports, you are NOT
tied to one result set, or a fixed subquery structure.  You can grab any data
you like and assemble it into a any structure that helps, as you have a 
full-blown programming language at your disposal.  For example, you might want
to go off and do queries for related info on some rows but not others; if it's
a line or two, it can be done in the template easily.


If you have a more complex data set with several record types and columns, sometimes 
it's nice to create a lightweight 'objects' which you can access by attribute...
    print obj.firstName, obj.surname


The dynamic nature of the language means you can do this in a few lines of code
and don't need a class for every table in your database.  We used this pattern
below.

If doing more sophisticated database work regularly, you might end up using an
Object-Relational Mapper (ORM) designed to save you time on queries.  Thus,
if generating PDF inside a Django project, you'd be free to use Django's ORM
to fetch some objects and then pass these into our templates.   Or, you might
be using an independent ORM like SQL Alchemy.


When creating report templates (or web pages with data), the goal is usually
to keep the template as readable as possible.  Thus, accessing fields by name
is usually good.  And if you find yourself writing many lines of code to
(say) format someone's exam grade, you might be better making a Student
class with a method to compute that result, so that the template stays as
simple as

<td>{{student.displayGrade()}}</td> 


"""

import MySQLdb
import preppy
from rlextra.rml2pdf import rml2pdf
from rlextra.ers import fetchobj


def main():
    #connect to the database
    db = MySQLdb.connect(user="root", passwd="", db="rldb")
    #map the friends table into something we can use in python

    #fetch my friends, represented as objects with named attributes
    friends = fetchobj.queryToObjects(db,'select * from friends')
    
    #load the RML template into preppy
    template = preppy.getModule('rmltemplate.prep')
    
    #Now loop through the database results.
    for friend in friends:
        #pass the object into the preppy template to create an RML file
        rmlText = template.get(friend)
        
        #Now create the PDF by passing the RML file into RML2PDF
        pdfFileName = friend.firstName + '.pdf'
        rml2pdf.go(rmlText, outputFileName=pdfFileName)
        print('saved %s' % pdfFileName)
    
if __name__=='__main__':
    main()
    
