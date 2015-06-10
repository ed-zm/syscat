#copyright ReportLab Europe Limited. 2000-2012
#see license.txt for license details
__version__=''' $Id$ '''
from rlextra.ers.webapp import WebApp
from reportlab.lib.colors import toColor
from rlextra.graphics.quickchart import quickChart, getTestDrawing

class WebChartApp(WebApp):
    "Web test harness / demonstrator for our charts"
    def __init__(self,**kw):
        WebApp.__init__(self,**kw)
        self.viewDir = '.'
        self.defaultAction = 'main'
        
    def action_testImage(self, request, response):
        myChart = getTestDrawing()
        bitmapBytes = myChart.asString('png')
        response.setContentType('image/png')
        response.write(bitmapBytes)

    def action_getLogo(self, request, response):
        "Return reportlab logo"
        bitmapBytes = open('corplogo.gif','rb').read()
        response.setContentType('image/png')
        response.write(bitmapBytes)
        
    def action_image(self, request, response):
        "Generate PNG chart according to input parameters"


        # extract any chart-related parameters, converting
        # from strings to correct data types.  Keep this
        # explicit instead of being clever and dynamic
        params = request.params
        kw = {}
        def getColor(name,kw=kw,params=params):
            color = params.get(name,'None')
            kw[name] = color.upper()!='NONE' and toColor(color) or None

        def getParam(name,kw=kw,params=params):
            if name in params: kw[name] = params[name]

        kw['showBoundaries'] = 'showBoundaries' in params
        kw['chartType'] = params.get('chartType','bar')
        kw['seriesRelation'] = params.get('seriesRelation', 'sidebyside')
        kw['width'] = params.get('width','400')
        kw['height'] = params.get('height','300')

        getParam('data')
        kw['textData'] = params.get('textData',None)
        getParam('categoryNames')
        getParam('seriesNames')

        #chart colours
        if 'chartColors' in params:
            kw['chartColors'] = params['chartColors']
            chartColorText = params['chartColors']
            if chartColorText == 'None':
                chartColors = None
            else:
                chartColors = chartColorText
        else:
            chartColors = None
        kw['chartColors'] = chartColors

        #main title
        getParam('titleText')
        getParam('titleFontName')
        getParam('titleFontSize')
        getParam('titleFontColor')

        #x axis title
        getParam('xTitleText')
        getParam('xTitleFontName')
        getParam('xTitleFontSize')
        getParam('xTitleFontColor')

        #y axis title
        getParam('yTitleText')
        getParam('yTitleFontName')
        getParam('yTitleFontSize')
        getParam('yTitleFontColor')

        #x axis 
        kw['xAxisVisible'] = 'xAxisVisible' in params
        getParam('xAxisFontName')
        getParam('xAxisFontSize')
        getParam('xAxisFontColor')
        getParam('xAxisLabelAngle')

        #y axis 
        kw['yAxisVisible'] = 'yAxisVisible' in params
        getParam('yAxisFontName')
        getParam('yAxisFontSize')
        getParam('yAxisFontColor')
        getParam('yAxisLabelAngle')

        #data labels
        getParam('dataLabelsType')
        getParam('dataLabelsFontName')
        getParam('dataLabelsFontSize')
        getParam('dataLabelsFontColor')
        getParam('dataLabelsAlignment')

        # plot area
        kw['xAxisGridLines'] = 'xAxisGridLines' in params
        kw['yAxisGridLines'] = 'yAxisGridLines' in params
        
        if 'plotColor' in request.params:
            kw['plotColor'] =  request.params['plotColor']
        else:
            kw['plotColor'] =  None

        #if they give us a background colour, use it.
        getColor('bgColor')

        #if they give us a background stroke colour, use it.
        getColor('bgStrokeColor')

        #markers for lines eg, in scatter_lines_markers
        if 'markerType' in params:
            mk = params['markerType']
            if mk == 'None':
                mk = None
            kw['markerType'] = mk

        if 'markerSize' in params:
            ms = params['markerSize']
            if ms == 'None':
                ms = None
            else:
                ms = int(ms)
            kw['markerSize'] = ms

        #legend properties
        if 'legendPos' in params:
            lpos = params['legendPos']
            if lpos == 'None':
                lpos = None
            kw['legendPos'] = lpos

        if 'legendFontName' in params:
            lfont = params['legendFontName']
            if lfont == 'None':
                lfont = None
            kw['legendFontName'] = lfont

        if 'legendFontSize' in params:
            lsize = params['legendFontSize']
            if lsize == 'None':
                lsize = None
            kw['legendFontSize'] = lsize

        if 'legendFontColor' in params:
            lcol = params['legendFontColor']
            if lcol == 'None':
                lcol = None
            kw['legendFontColor'] = lcol

        myChart = quickChart(**kw)
        bitmapBytes = myChart.asString('gif')
        response.setContentType('image/gif')
        response.setHeader('Cache-Control', 'no-cache')
        response.write(bitmapBytes)

if __name__=='__main__':
    WebChartApp().handleCommandLine()
