This sample project is a simple demonstration of how to harness ReportLab's Report Markup Language (RML) from inside TurboGears2, allowing you to create PDFs with dynamic content by using RML templates with TurboGears's templating system, Genshi.

To run the demonstration, you need a working installation of TurboGears2, along with the open source ReportLab toolkit, pyRXP, and the ReportLab PLUS bundle, which you can download by registering at http://www.reportlab.com

RML is an XML-style language for describing the layout of a document.  The RML is converted to PDF using a python module named rml2pdf.pyc

Because the RML is a just a text file, it can be manipulated dynamically very easily from inside any language or framework.  This example reads the template file 'hello.rml' into memory, and then substitutes a particular string using Genshi.  It then uses the rml2pdf python module's 'go' method to create a PDF from the RML.  The resulting PDF is turned into a byte stream and returned to the browser.

RML2PDF and RML are part of the ReportLab PLUS software package.  For further information and extensive documentation, please see our website at http://www.reportlab.com/software

Installation and Setup
======================

1. Create a sample project in TurboGears2 using the 'paster quickstart' command in your virtualenv directory, as described in the tutorial at http://www.turbogears.org/2.0/docs/main/QuickStart.html.  Name the new project 'rptlab-rml-sample', and ensure that you can run the project as described on that web page.

2. cd to rptlab-rml-sample/rptlabrmlsample/.  Backup the file controllers/root.py, then copy controllers/root.py from the sample directory into the controllers directory in your new project.  Also copy templates/hello.rml and templates/makepdf.html into your new project's templates directory.

3. Make sure that reportlab, pyRXPU and rlextra are visible on the PYTHONPATH from inside your turbogears environment or virtualenv.  

4. cd back to the rptlab-rml-sample directory and start the paste http server:

    $ paster serve development.ini

5. Browse to http://localhost:8080/


