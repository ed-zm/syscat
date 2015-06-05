This folder contains a sample PHP project.



It's a simple demonstration of how to harness ReportLab's Report Markup Language (RML) from within a PHP script.



To run the demonstration, you need a working installation of Python, the open source ReportLab toolkit, and the ReportLab PLUS bundle, which you can download by registering at http://www.reportlab.com



You may need to adjust the paths inside index.php to point to the correct places on your machine.



RML is an XML-style language for describing the layout of a document.  The RML is converted to PDF using a python module named rml2pdf.pyc.



Because the RML is a just a text file, it can be manipulated dynamically very easily from inside any language or framework.  

This example simply reads the template file 'hello.rml' into memory, and then substitutes a particular string.  It then writes the text to a temporary file and uses the PHP exec() function to call the rml2pdf python module with the relevant command line string.  This converts the RML to a PDF, and the file is returned to the browser as a byte stream.



RML2PDF and RML are part of the ReportLab PLUS software package.  For further information and extensive documentation, please see our website at http://www.reportlab.com/software
