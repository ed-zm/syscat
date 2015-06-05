This directory contains an example of the ReportLab
tools working together in a simple application.

It demonstrates the basic concepts of the 'preppy'
text preprocessor, used together with Report
Markup Language and 'rml2pdf' to dynamically
create an invoice in PDF format.

The example consists of the following files:

'sample_invoice0.xml' - contains the actual invoice data,
including client name and address, transaction details etc.

'rmltemplate.prep' - this is a 'prep' file containing a
template for the invoice.  It contains an RML script
describing the layout of the invoice, together with
some python script in {{double braces}} which marks
where the dynamic content will be inserted.

Running the data in the 'rmltemplate.prep' and
'sample_invoice0.xml' files through preppy will
merge the data into a single RML file describing
the final PDF.  The RML file is then run through
'rml2pdf', to create the final invoice.

The above steps are all done in the script 'invoice.py'.

To run this example on the command line, navigate to the
directory containing this file and type:

 python invoice.py sample_invoice0.xml

This will create a file called 'sample_invoice0.pdf'
in the current directory.

Note: this uses a well known Python module called
fixedpoint.py to do correct decimal arithmetic.
We checked in a copy to this directory to save
beginners work, but in general you would put this
on your Python path.