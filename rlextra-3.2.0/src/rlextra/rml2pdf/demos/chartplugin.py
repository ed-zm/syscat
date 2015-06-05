
"example plug in flowable for a bar chart in RML"

from reportlab.lib import colors
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.shapes import Drawing

def sample1bar(data=[(13, 5, 20, 22, 37, 45, 19, 4),
                     (5, 20, 22, 37, 45, 19, 4, 13),
                     (20, 22, 37, 45, 19, 4, 13, 5)]):
    # sanity check:
    for d in data:
        if len(d)!=8:
            raise ValueError("bar chart data must have 8 elements "+repr(data))
    drawing = Drawing(400, 200)
    
    bc = VerticalBarChart()
    bc.x = 50
    bc.y = 50
    bc.height = 125
    bc.width = 300
    bc.data = data

    bc.strokeColor = colors.black

    bc.valueAxis.valueMin = 0
    bc.valueAxis.valueMax = 60
    bc.valueAxis.valueStep = 15
    
    bc.categoryAxis.labels.boxAnchor = 'ne'
    bc.categoryAxis.labels.dx = 8
    bc.categoryAxis.labels.dy = -2
    bc.categoryAxis.labels.angle = 30

    catNames = 'Jan Feb Mar Apr May Jun Jul Aug'.split()
    catNames = [n+'-99' for n in catNames]
    bc.categoryAxis.categoryNames = catNames
    drawing.add(bc)

    return drawing

def sample1line(datastring="""
	1997 1998 1999 2000 2001 ,
	pink -10 11 40 22 30 ,
	blue 11 40 22 30 -10,
	cyan 40 22 30 -10 11
"""):
    # parse the data
    lines = datastring.split(",")
    titlestring = lines[0]
    titles = titlestring.split()
    data = []
    alldata = []
    linecolors = []
    for dataline in lines[1:]:
        sline = dataline.split()
        linecolor = sline[0]
        numbers = list(map(float, sline[1:]))
        linecolors.append(linecolor)
        data.append(numbers)
        alldata.extend(numbers)
    drawing = Drawing(400, 200)
    
    bc = HorizontalLineChart()
    bc.x = 25
    bc.y = 50
    bc.height = 125
    bc.width = 300
    bc.data = data

    bc.strokeColor = colors.black

    bc.valueAxis.valueMin = min(0, min(alldata)-5) #-10
    bc.valueAxis.valueMax = max(20, max(alldata)+5) #40
    bc.valueAxis.valueStep = 10
    bc.valueAxis.visibleGrid = 1
    bc.valueAxis.gridStrokeColor = colors.blue
    bc.valueAxis.gridStart = 0
    bc.valueAxis.gridEnd = 300
    bc.valueAxis.labelTextFormat ="%s%%"
    #bc.valueAxis.joinAxisPos = -10
    
    bc.categoryAxis.labels.boxAnchor = 'ne'
    bc.categoryAxis.labels.dx = 8
    bc.categoryAxis.labels.dy = -2
    bc.categoryAxis.labels.angle = 0
    bc.categoryAxis.joinAxis = bc.valueAxis
    bc.categoryAxis.joinAxisMode = "bottom"
    bc.categoryAxis.visibleGrid = 1
    
    #bc.lines[0].strokeColor = colors.pink
    #bc.lines[1].strokeColor = colors.lavender
    #bc.lines[2].strokeColor = colors.skyblue
    linenumber = 0
    for colorname in linecolors:
        bc.lines[linenumber].strokeColor = getattr(colors, colorname)
        bc.lines[linenumber].strokeWidth = 3
        linenumber = linenumber+1

    catNames = titles
    bc.categoryAxis.categoryNames = catNames
    drawing.add(bc)

    return drawing

lineChartFlowable = sample1line

def chartFlowable(datastring):
    "convert the string, then make the chart"
    #return sample1line()
    datalist = datastring.split()
    data = list(map(float, datalist))
    alldata = [data]
    return sample1bar(alldata)

if __name__=="__main__":
    # just check to make sure code runs, don't save anything
    test = chartFlowable("13 5 20 22 37 45 19 4")
    print(test.getProperties(recur=1))
