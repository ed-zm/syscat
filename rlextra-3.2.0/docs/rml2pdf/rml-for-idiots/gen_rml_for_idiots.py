#!/usr/bin/env python

"""Long document example generator"""

import glob
import re

from optparse import OptionParser

import preppy
from rlextra.rml2pdf import rml2pdf

regexp = {
    'chapter': re.compile("chapterName\s+\"(.*)\""),
    'section': re.compile("sectionName\s+\"(.*)\""),
    'appendix': re.compile("appendixName\s+\"(.*)\""),
    'part': re.compile("partName\s+\"(.*)\""),
    'slug': re.compile(r'[^A-Za-z0-9-]+')
    }


def parseCommandLine():
    """Examines options and does preliminary checking."""
    parser = OptionParser("run [options]")
    parser.add_option("--dull", action="store", dest="DULL", default=True, help="Dull or not dull ? ")
    # parser.add_option("-c", "--colour", action="store_true", dest="colour", default=True, help="Enable colour output.")
    # parser.add_option("-m", "--cropmarks", action="store_true", dest="cropmarks", default=False, help="Enable crop marks.")
    # parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Print information about what is going on.")
    return parser.parse_args()

def prepareChapter(filename):

    FILE = open(filename, 'r')

    chapter = {
        'name': None,
        'id': None,
        'content': None,
        'part': None,
        'toc_sections': [],
        'sections': []
        }

    section = None
    toc_section = None
    content = ''

    
    while True:
        line = FILE.readline()
        if line:
            line = line.rstrip()
        else:
            if section:
                section['content'] = content
                chapter['sections'].append(section)
                chapter['toc_sections'].append(toc_section)
            elif content:
                chapter['content'] = content
            break

        is_part = regexp['part'].search(line)

        if is_part:
            line = ''
            chapter['part'] = {
                'id': regexp['slug'].sub('_', is_part.group(1)),
                'name': is_part.group(1)
                }

        if not chapter['name']:
            is_chapter = regexp['chapter'].search(line)
            if is_chapter:
                chapter['name'] = is_chapter.group(1)
                chapter['id'] = regexp['slug'].sub('_', chapter['name'])
        else:
            is_section = regexp['section'].search(line)
            if is_section:
                if section:
                    section['content'] = content
                    chapter['sections'].append(section)
                    chapter['toc_sections'].append(toc_section)
                else:
                    chapter['content'] = content
                section = {
                    'name': is_section.group(1),
                    'id': regexp['slug'].sub('_', is_section.group(1)),
                    'num': len(chapter['sections']) + 1
                    }
                toc_section = [section['name'], section['id'], section['num']]
                content = ''
            else:
                content += "%s\n" % line
    return chapter

def prepareAppendix(filename):
    FILE = open(filename, 'r')

    appendix = {
        'name': None,
        'id': None,
        'content': None,
        }

    content = ''
    
    while True:
        line = FILE.readline()
        if line:
            line = line.rstrip()
        else:
            break

        if not appendix['name']:
            is_appendix = regexp['appendix'].search(line)
            if is_appendix:
                appendix['name'] = is_appendix.group(1)
                appendix['id'] = regexp['slug'].sub('_', appendix['name'])
        else:
            content += "%s\n" % line


    appendix['content'] = content
    return appendix

    

def run(options):
    """Generate rml and pdf. """


    data = {
        'chapters_content': [],
        'chapters': [],
        'appendixes': [],
        'appendixes_content': [],
        }

    partInfo = None

    chapter_filenames = glob.glob("chapters/c_*prep")
    chapter_filenames.sort()
   
    for chapter_filename in chapter_filenames:
        chapter = prepareChapter(chapter_filename)
        chapter['num'] = len(data['chapters_content']) + 1
        data['chapters_content'].append(chapter)
        data['chapters'].append((chapter['num'], chapter['name'], chapter['part'], chapter['toc_sections']))

    appendix_filenames = glob.glob("chapters/a_*prep")
    appendix_filenames.sort()
    
    for appendix_filename in appendix_filenames:
        appendix = prepareAppendix(appendix_filename)
        appendix['num'] = len(data['appendixes_content'])
        data['appendixes_content'].append(appendix)
        data['appendixes'].append((appendix['name'], appendix['id']))


    template = preppy.getModule('rmltemplate')
    
    rmlText = template.get(data, options)
    rmlSource = open('rml-for-idiots.rml', 'w')
    rmlSource.writelines(rmlText)
    rmlSource.close()

    rml2pdf.go(rmlText, outputFileName='rml-for-idiots.pdf')

if __name__=='__main__':
    options, args = parseCommandLine()
    run(options)        
    print('created rml-for-idiots.pdf')

