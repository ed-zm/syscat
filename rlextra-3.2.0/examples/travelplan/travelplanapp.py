# Copyright ReportLab Europe Ltd. 2006
# $Id$
from rlextra.rml2pdf import rml2pdf
import os, string, time
from rlextra.ers import webapp
from . import travel
import preppy
from rlextra.radxml.xmlutils import xml2doctree

class TravelPlanApp(webapp.WebApp):

    def __init__(self, **kw):
        self._setKeywords(**kw)
        webapp.WebApp.__init__(
            self,
            defaultAction='search',
            rsrcUrl='/rsrc/travelplan/',
            pageTemplate='travel_template.html'
            )
    def getRsrcUrl(self,name):
        return self.rsrcUrl+name
    
    def action_makepdf(self,request,response):
        started = time.time()
        params=request.params
        orig = params['orig']
        dest = params['dest']
        oDate = params['oYMD']
        rDate = params['rYMD']
        flightClass = params['flightClass']
        isRoundTrip = params['isRoundTrip']
        numOfAdults = params['numOfAdults']
        customerName = params['customerName']
        tripTitle = params['tripTitle']
        subtitle = params['subtitle']
        if isRoundTrip == 'True': isRT = True
        else: isRT = False
        presaleXML = travel.getPresaleXML(tripTitle,subtitle,customerName,orig, dest,oDate,rDate,flightClass,isRT)
        data=xml2doctree(presaleXML,0)
        module=preppy.getModule('template_presale.prep')
        rmlText=module.getOutput(dict(data=data))
        if int(getattr(self,'SAVE_LASTEST_RML',0)):
            f = open('save_lastest.rml','w')
            f.write(rmlText)
            f.close()
        outfile='presale.pdf'
        pdf=rml2pdf.go(rmlText, outfile, outDir=self.OUTDIR)
        location = '%s/%s' % (self.HTTP_OUTDIR,outfile)
        params=request.params
        finished = time.time()
        timeTaken = finished - started
        params['timeTaken'] = timeTaken
        params['location']= location
        self.runView(request,response,'download')

    def action_makeitinerarypdf(self,request,response):
        started = time.time()
        params=request.params
        ticket_id = params['ticket_id']
        roomBooking_id = params['roomBooking_id']
        numOfAdults = params['numOfAdults']
        customerName = params['customerName']
        tripTitle = params['tripTitle']
        subtitle = params['subtitle']
        itineraryXML = travel.getStep4XML(tripTitle,subtitle,customerName, ticket_id, roomBooking_id)
        data=xml2doctree(itineraryXML,0)
        module=preppy.getModule('template_itinerary.prep')
        rmlText=module.getOutput(dict(data=data))
        outfile='postsale.pdf'
        pdf=rml2pdf.go(rmlText, outfile, outDir=self.OUTDIR)
        location = '%s/%s' % (self.HTTP_OUTDIR,outfile)
        params=request.params
        finished = time.time()
        timeTaken = finished - started
        params['timeTaken'] = timeTaken
        params['location']=location
        self.runView(request,response,'download')
