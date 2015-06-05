"""generate the rml source for rml userguide using 2 preppy passes"""
import sys
# this should be integrated into rml2pdf somehow
SHOW_PAGE_NO = 0

f = "rml_user_guide_generated.rml"

def gen(filename="test_newconstructs.rml"):
    print("using file", filename)
    # testing hack to try new paragraphs
    if 1:
        print("abusing paragraphs :c)")
        from rlextra.radxml import para
    print("running rml2pdf")
    from rlextra.rml2pdf import rml2pdf
    import os
    dtddir = os.path.abspath("..")
    from time import time
    now = time()
    rml2pdf.go(open(filename).read(), dtdDir=dtddir, verbose=1, ignoreDefaults=0)
    print("elapsed", time()-now)
    #print rml2pdf.__file__
    print("pdf generation complete")

profiling = 0
if __name__=="__main__":
    if profiling:
        import profile
        print("profiling")
        profile.run("gen()")
    else:
        #gen2(showPageNo=SHOW_PAGE_NO)
        gen()
