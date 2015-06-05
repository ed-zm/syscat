#!/usr/bin/env python

"""
xcharts.py - a proof-of-concept XML interface to Diagra

This is a demonstration prepared for a customer and may not be fully robust
or secure yet.

"""
import os, sys
import optparse


def run(inFileName, options):
    print("Processing", infilename)

def parseCommandLine():
    return None, None



sample = """
<drawings>
  <drawing module="gridlineplot" class="GridLinePlotDrawing">
  
  </drawing>
</drawings>
"""


if __name__=='__main__':
    options, args = parseCommandLine
    if not args:
        print("usage: xcharts.py infile.xml [..options...]")
    else:
        run(args[0], options)
        

