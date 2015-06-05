#!/usr/home/rptlab/bin/python -u
import sys, os
sys.stderr = sys.stdout
_help='''
gpie?help=1 give this help!

gpie?data=value0,value1,.....,valuen[&option=optionalvalue&.....]
    option      meaning
    data        the comma separated list of data values.
    colors      comma separated list of hex values 0xabcdef representing the colors
                to be used in the pie chart. A standard palette is provided.
    bg          hex value for the background color (default white ie 0xffffff).
    width       width in pixels of the chart.
    height      height in pixels of the chart.
    bdwidth     width of the pie slice borders (default 0.5).
    bdcolor     color of the slice borders (default black = 0x000000) use
                none (or bdwidth=0) for no slice borders.
    startangle  Angle at which to start the first ie 0'th. slice. The default
                is 90 degrees.
    slack       pixels to leave around edge of pie.
    explode     A list of pairs i,d indicating that slice i (zero based) should be
                exploded by d pixels.

    *NB*        for colors use hex number ie #rrggbb or 0xrrggbb or any of the
                standard html color names eg pink, red etc. Please note that the
                # sign is a special character for http and should be rendered
                as %23.

examples:
    HOST/gpie.cgi?data=1,2,3,4&bg=pink&slack=7&explode=0,5&startangle=120&bdwidth=1&bdcolor=none
    HOST/gpie.cgi?data=1,2,3,4&colors=pink,maroon,lightgreen,%23226655
    HOST/gpie.cgi?data=1,2,3,4&colors=0x6666cc,%2300ff00,pink,red,blue
'''

def run():
	# general solution to turn CGI params into a familiar dictionary
	import cgi
	D = {}
	form = cgi.FieldStorage()
	for name in form.keys():
		value = form[name].value
		D[name] = value

	if not len(D):
		print 'Content-Type: text/html\n\n404 Not Found'
		return
	elif D.has_key('help'):
		from rlextra.utils.cgisupport import quoteValue
		print 'Content-Type: text/html\n\n<html><head></head><body>'
		print '<h1><font color=green>Usage</font></h1><pre>'
		print quoteValue(_help)
		print '</pre></body></html>'
		return
	if not D.has_key('data'): raise ValueError('Must have data or help options specified!')

	from reportlab.graphics import renderPM
	from reportlab.graphics.shapes import Drawing, Rect
	from reportlab.graphics.charts.piecharts import Pie
	from reportlab.lib.colors import toColor
	default = {
				'width': '200', 'height': '200', 'bdwidth': '0.5', 'data': None,
				'startangle': '90', 'explode': '()', 'slack': '2',
				'bg': '0xffffff', 'bdcolor': '0x000000',
				'colors': "yellow,red,green,maroon,beige,pink,lime",
				}

	for k in ('width', 'height', 'bdwidth', 'data', 'startangle', 'explode', 'slack'):
		D[k] = eval(D.get(k,default[k]))
	for k in 'bg', 'bdcolor':
		D[k] = D.get(k,default[k])
	bdcolor = D['bdcolor']
	bdcolor = bdcolor not in ('none','None') and toColor(bdcolor) or None
	
	data, colors = D['data'], map(toColor,D.get('colors',default['colors']).split(','))
	SeqTypes = (type([]),type(()))
	if type(data) not in SeqTypes: data = (data,)
	
	width, height, slack, explode = D['width'],D['height'], D['slack'], D['explode']
	d = Drawing(width,height)
	d.add(Pie(),'chart')
	d.background = Rect(0,0,width=width,height=height,fillColor=toColor(D['bg']),strokeColor=None)
	d.chart.data = data
	d.chart.startAngle = D['startangle']
	d.chart.height = height-slack*2
	d.chart.width = width-slack*2
	d.chart.x = d.chart.y = slack
	d.chart.slices.strokeWidth = D['bdwidth']
	d.chart.slices.strokeColor = bdcolor
	for i in xrange(0,len(explode),2):
		d.chart.slices[explode[i]].popout = explode[i+1]
	for i in xrange(len(colors)): d.chart.slices[i].fillColor = colors[i]

	gif_data = renderPM.drawToString(d)
	print 'Content-Type: image/gif'
	print 'Content-Length: %d' % len(gif_data)
	print
	sys.stdout.write(gif_data)

if __name__=='__main__':
	from rlextra.utils import log
	log.apply_wrapper(run,(),errorHandle='html')
