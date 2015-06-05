Fill in the US IRS tax form 1040ez.

The PDF source is f1040ez.pdf.  The field locations were derived
automatically from the field information in this pdf file.

This demonstrates the translation of xml input parameters to 
an rml document description and the use of a Page Caught 
existing government tax form.

1040ez was the first step in this effort.  1040 is more automated.


==========================================================================

1040ez: TO USE: Run 

  python makef1040ez.py

OR make your own input

  python makef1040ez.py myexample.xml

and then look at f1040last.pdf

[should write more explanation...]


==========================================================================

For f1040.pdf:

f1040.pdf has been modified using Acrobat to change the form names and add
descriptions.  For example one of the fields was changed from whatever it was
named before to "SocialSecurityNumber" with the description "ssn".  The field
data is extracted using dumpFields.py.  The extracted field data is then used
by makeprep.py to automatically generate a preppy template, using the descriptions
and the alignment, when specified, to determine the formatting of the field.

Proceed as follows...

Catch the pages:

>python ..\..\pageCatcher\pageCatcher.py makeforms --all f1040.pdf -s f1040.storage

Make the fields descriptions:

>python ..\..\pageCatcher\dumpFields.py f1040.pdf > f1040Fields.py

Derive a preppy template from the field descriptions:

>python makeprep.py > f1040template.prep

Test the preppy template (shows field names where placed in style selected):

>python ..\..\rml2pdf\rml2pdf.py f1040template.prep
test.pdf

>start test.pdf

Make the xml example and the DTD...

>python makedtd.py
wrote f1040.dtd and f1040_example.xml

Run the test form...

>python makeform.py
usage: makeform.py formname InputFileName.xml
defaulting to f1040 f1040_example.xml
wrote f1040_example.rml
wrote f1040_example.pdf

C:\repository\rlextra\examples\taxform>start f1040_example.pdf

==========================================================================

For f1040ab.pdf ...

>python ..\..\pageCatcher\dumpFields.py f1040sab.pdf > f1040sabfields.py
>python ..\..\pageCatcher\pageCatcher.py makeforms --all f1040sab.pdf -s f1040sab.storage
>python makeprep.py f1040sab > f1040sabtemplate.prep
>python ..\..\rml2pdf\rml2pdf.py f1040sabtemplate.prep
>start test.pdf
>python makedtd.py f1040sab
>python makeform.py f1040sab f1040sab_example.xml
