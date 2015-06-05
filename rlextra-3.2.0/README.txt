=====================================
README 
=====================================

(C) Copyright ReportLab Inc. 2000-2013.
See ``LICENSE.txt`` for license details.

This is the ReportLab Commercial Distribution, "ReportLab PLUS(tm)". 
It allows rapid development of rich PDF document workflows, and 
also creation of charts in a variety of bitmap and vector formats.  
Key items within the package are:
- Report Markup Language, our tool for creating PDFs
- PageCatcher, our library for using existing PDF files as
  resources
- Diagra, our framework for generating data aware charts
- various related utilities and examples.

1. Licensing
============
This is commercial software.  It is made available for evaluation
and to customers paying a license fee; current terms are available
on our web site.

Certain functions require a valid license file before they will work fully.
Specifically, documents and charts generated will display a 'nag line'.
Evaluators are encouraged to try the software fully and are free to
develop their applications, but are expected to buy a license before 
the system is used in production.

Some files within this distribution are shipped in bytecode-compiled
form.  This makes it more difficult to reproduce and copy the functionality
of our products and/or to interfere with the license mechanism.  It is 
expressly forbidden to decompile these modules.  If you need full source
access for a technical reason, please contact us.

2. Installation
=============== 
Full installation instructions are set out on our web site.  In brief,
the prerequisites are:

 - Python Imaging Library compiled with Freetype support
 - 'reportlab' open source package
 - 'preppy' templating system
 - 'pyRXP' validating XML parser

We recommend installing using `virtualenv`.  All of the above packages
can be installed with 'easy_install' or 'pip install'.

The `rlextra` package is pure python code; it can be installed with
`python setup.py install`, or you can symlink/copy the 'src/rlextra'
directory onto your Python path. This distribution also contains docs,
demos and tests which do not need to be installed but are invaluable for
learning.

3. Testing
==========
Since rlextra depends heavily on reportlab, it is advisable to run the test
suites for both packages.  The `reportlab` package contains a test directory
and a `runAll.py` script.  The `rlextra` package also contains a test directory
and a `testall` script.  A successful test run looks like this::

    $ cd rlextra/tests/
    tests andy$ python testall.py 
    ....................................................................................
    ----------------------------------------------------------------------
    Ran 84 tests in 12.623s

    OK



The RML test cases, also visible on our web site, are key pieces of documentation.
They can be found in rlextra/tests/rml2pdf, and after running the suite, you should
have many matched pairs of RML and PDF files to inspect.

4. Documentation
================
All of our documentation is available on our web site, including some utilities
such as the RML DTD browser which work better in HTML.

Since our package makes PDF files, we generate our own documentation as part of
the test run.  The criterion for our "Release 1.0" was being able to generate our
own manual - and the manuals provide good examples of how to code long documents.

After running the tests, several PDF manuals will be present in the 'docs' directory.
Additional manuals for Diagra are in the docs/diagra subdirectory.

5. Support
==========
Commercial customers can email support@reportlab.com for prompt help.  If you
have a reproducible bug in RML, please try to capture and send the RML to help
us fix it quickly.  For general 'how to' enquiries, the best approach is to
show us some sort of mockup of what you are trying to achieve and we will advise how
to do it.

  