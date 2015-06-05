#Copyright ReportLab Europe Ltd. 2000-2014
#see license.txt for license details
import os, sys, glob, shutil
platform = sys.platform
pjoin = os.path.join
abspath = os.path.abspath
isfile = os.path.isfile
isdir = os.path.isdir
dirname = os.path.dirname
basename = os.path.basename
if __name__=='__main__':
    pkgDir=dirname(sys.argv[0])
else:
    pkgDir=dirname(__file__)
if not pkgDir:
    pkgDir=os.getcwd()
elif not os.path.isabs(pkgDir):
    pkgDir=os.path.abspath(pkgDir)

from setuptools import setup, find_packages

def get_version():
    #try source
    FN = pjoin(pkgDir,'src','rlextra','__init__')
    for l in open(pjoin(FN+'.py'),'r').readlines():
        if l.startswith('Version'):
            l = l.split('=',1)
            if len(l)==2:
                return eval(l[1].strip(),locals())
    raise ValueError('Cannot determine rlextra Version')

def main():
    setup(
        name="rlextra",
        version=get_version(),
        license="BSD license (see license.txt for details), Copyright (c) 2000-2015, ReportLab Inc.",
        description="The ReportLabPLUS Toolkit",
        long_description="""The ReportLabPLUS Toolkit. Python library for generating PDFs and graphics.""",

        author="Robinson, Watters, Lee, Precedo, Becker and many more...",
        author_email="info@reportlab.com",
        url="http://www.reportlab.com/",
        packages = find_packages("src"),
        package_dir = {'rlextra': "src/rlextra"},
        package_data = {'rlextra':[
                                'rml2pdf/00README.txt',
                                'rml2pdf/*.dtd',
                                'pageCatcher/00REAME.txt',
                                'pageCatcher/replogo.bmp',
                                'pageCatcher/testfile.pdf',
                                'security/*.txt',
                                'graphics/guiedit/sample.csv',
                                ],
                        },
        entry_points = dict(
                            console_scripts = [
                                'rml2pdf=rlextra.rml2pdf.rml2pdf:main',
                                'pagecatcher=rlextra.pageCatcher.pageCatcher:scriptInterp',
                                'pdfexplorer=rlextra.pageCatcher.pdfexplorer:test',
                                ],
                            gui_scripts = [
                                'diagra=rlextra.graphics.guiedit.guiedit:mainApp',
                                ],
                            ),
        install_requires=[
            'reportlab>=3.2.0',
            'Pmw>=2.0.0',
            'preppy>=2.3.4',
            'pyRXP>=2.1.0',
            ],
        )

if __name__=='__main__':
    main()
