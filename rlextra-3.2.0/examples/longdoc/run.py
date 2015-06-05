#!/usr/bin/env python

"""Long document example generator"""

import random

from optparse import OptionParser

import lipsum

import preppy
from rlextra.rml2pdf import rml2pdf

def parseCommandLine():
    """Examines options and does preliminary checking."""
    parser = OptionParser("run [options]")
    parser.add_option("--chapters", action="store", dest="chapters", default=5, help="How many chapters ? ")
    # parser.add_option("-c", "--colour", action="store_true", dest="colour", default=True, help="Enable colour output.")
    # parser.add_option("-m", "--cropmarks", action="store_true", dest="cropmarks", default=False, help="Enable crop marks.")
    # parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Print information about what is going on.")
    return parser.parse_args()

def getColor(num = 0):
    r = 0x18
    g = 0x1c
    b = 0xe1
    shift = num * 20
    return '#%x%x%x' % (r + shift, g + shift, b)

def getParagraph(g):
    """Return lorem ipsum paragraph."""
    g.paragraph_mean = random.randrange(10,30)
    return g.generate_paragraph(start_with_lorem=True)

def getTitle(g, num):
    """Generate chapter name."""
    # g.sentence_mean = 10
    # return g.generate_sentence().split()[0][:-1]
    # return 'Chapter %d' % num
    return 'Chapter'
    
def createChapter(g, num):
    """Return chapter dictionary"""
    title = getTitle(g, num)

    return {
        'title': title,
		'title_num': "%d. %s" % (num, title),
        'num': num,
        'color': getColor(num),
        'content': [{'type': 'para', 'data': getParagraph(g)} for i in range(random.randrange(5,10))]
        }

def run(options):
    """Generate rml and pdf. """

    g = lipsum.Generator()

    data = {
        'content': [],
        'chapters': [],
        }

    for num in range(1, int(options.chapters) + 1):
        chapter = createChapter(g, num)
        data['content'].append(chapter)
        data['chapters'].append((num, chapter['title'], chapter['title_num'], chapter['color']))

    template = preppy.getModule('rmltemplate.prep')
    
    rmlText = template.get(data, options)
    rmlSource = open('longExample.rml', 'w')
    rmlSource.writelines(rmlText)
    rmlSource.close()

    rml2pdf.go(rmlText, outputFileName='longExample.pdf')

if __name__=='__main__':
    options, args = parseCommandLine()
    run(options)      
    print 'generated longExample.pdf'  
