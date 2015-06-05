#Copyright ReportLab Europe Ltd. 2000-2012
#see license.txt for license details
__version__=''' $Id$ '''
from rlextra.utils.zipapp import ZipAppDef, svn_update, findSVNURL, path_join, path_basename, FileSet

class MyZipAppDef(ZipAppDef):
    ####PROJECT SPECIFIC STUFF
    def projectDistro(self,projectPath):
        import sys
        FS = FileSet(projectPath)
        FS.include('./**/*')
        FS.include('../fonts/*.pfb')
        FS.exclude('./**/CVS/*')
        FS.exclude('./**/.svn/**/*')
        FS.exclude('./**/*.cgi')
        FS.exclude('./samples/**/*')
        FS.exclude('./'+path_basename(sys.argv[0]))
        FS.exclude('./**/PROJECT_CVS_TAG')
        FS.exclude('./**/filelist.txt')
        FS.exclude('./test/**/*')
        FS.exclude('./doc/**/*')
        return FS

def main():
    MyZipAppDef(
        EXPLODE_PATTERNS=['rsrc/*'],               #'/' separated glob style patterns for relative files
        moduleName = 'travelplanapp',                  #the module name containing the WebApp class
        appClassName = 'TravelPlanApp',                #the name of the WebApp class
        cgiName = 'travelplan.cgi',                    #the default name of the cgi script
        appName = 'travelplan',          #default base name of the target folder
        EXTRA_VALUES = [
            ('HTTP_PROXY','None','HTTP Proxy (None means NO proxy)'),
            ('LIVE','True','Application is running in live environment'),
            ],
        EXTRA_APP_KEYWORD_ARG_SPECS = ['http_proxy={{RAW}}"{{HTTP_PROXY}}"', 'live={{LIVE}}'],
        LATE_ACTIONS = [
            '''self.showMessage('\\n\\nDirectory "%s" must be made available via HTTP as /rsrc/travelplan' % os.path.join({{RAW}}'{{APPDIR}}','rsrc'))''',
            ],
        ).build()

if __name__=='__main__': #noruntests
    main()
