# -*- coding: utf-8 -*-
"""Main Controller"""

from tg import expose, response

from rptlabrmlsample.lib.base import BaseController
import io
import os

__all__ = ['RootController']

def makeDoc(q):
	from rlextra.rml2pdf import rml2pdf
        rml = mergeRML(q)  
    
        buf = io.StringIO()
        
        #create the pdf
        rml2pdf.go(rml, outputFileName=buf)
        buf.reset()
        pdfData = buf.read()
        
	return pdfData

def mergeRML(personName):
    
    #merge our template and variable, using the Genshi templating 
    #engine, then return the text.
    from genshi.template import TemplateLoader

    loader = TemplateLoader(os.getcwd() + '/rptlabrmlsample/templates/')
    rml = loader.load('hello.rml')
    return rml.generate(name=personName).render('xml')


class RootController(BaseController):
    """
    The root controller for the rptlab-rml-sample application.
    """

    #@expose('rptlabrmlsample.templates.makepdf')
    @expose()
    def getpdf(self,q):
        """Sample app for RML."""
	a=makeDoc(q)
	response.headers["Content-Type"] = "application/pdf"
	response.headers["Content-disposition"] = "attachment; filename=report.pdf"
	response.headers["Content-Length"] = len(a)

        return a #dict(page='makepdf')

    @expose('rptlabrmlsample.templates.makepdf')
    def default(self):
        """Sample app for RML."""

        return dict(page='makepdf')

