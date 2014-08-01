#!/usr/bin/env python

#Early draft of AXIOME re-write

from axiome_modules import AxiomeAnalysis
from os.path import dirname, abspath

source_dir = dirname(abspath(__file__))

if __name__ == "__main__":
    #**TODO** allow this script to invoke UI and AXIOME steps
    axiome_analysis = AxiomeAnalysis(source_dir + "/res/sample/sample.ax")
