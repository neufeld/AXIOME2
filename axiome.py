#!/usr/bin/env python

#Early draft of AXIOME re-write

from axiome_modules_two import AxiomeAnalysis
from os.path import dirname

source_dir = dirname(__file__)

if __name__ == "__main__":
    #**TODO** allow this script to invoke UI and AXIOME steps
    axiome_analysis = AxiomeAnalysis(source_dir + "/res/sample.ax", source_dir + "/res/master.xml", source_dir + "/res/test/Makefile")
