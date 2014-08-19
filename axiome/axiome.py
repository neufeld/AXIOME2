#!/usr/bin/env python

#AXIOME2 main intro function

from .modules import AxiomeAnalysis
from os.path import dirname, abspath
import argparse
import ui
import utils as util

source_dir = dirname(abspath(__file__))

def main():
    #Argument handling
    parser = argparse.ArgumentParser(prog='axiome')
    subparsers = parser.add_subparsers(title='subcommands',description='the following subcommands are possible: ui, process, utility', dest='subparser_name')
    ui_parser = subparsers.add_parser("ui")
    ui_parser.add_argument("-i", metavar="input", help="Optional .ax file to edit", type=str)
    process_parser = subparsers.add_parser("process")
    process_parser.add_argument("-i", metavar="input", help=".ax file to process", required=True, type=str)
    utility_parser = subparsers.add_parser("utility")
    utility_parser.add_argument("action", choices=["mapping_template", "sample_data"], help="mapping_template: generates a file mapping template in the current directory, which can be opened in a spreadsheet program; sample_data: copies AXIOME sample data into the current directory")
    args = parser.parse_args()

    #Argparse ensures that we meet the requirements
    if args.subparser_name == "ui":
        App = ui.AXIOMEUI(args.i)
        App.run()
    elif args.subparser_name == "process":
        axiome_analysis = AxiomeAnalysis(args.i)
        working_directory = axiome_analysis.working_directory
        print "AXIOME file processed\nDirectory '%s' created\nRun command `make` in directory '%s'" % (working_directory, working_directory)
    elif args.subparser_name == "utility":
        if args.action == "sample_data":
            util.copySampleAxData()
            print "Successfully copied sample.ax and sample_file_mapping.tsv to current directory\nRun `axiome process -i sample.ax` to process sample file"
        elif args.action == "mapping_template":
            util.generateMappingTemplate(AxiomeAnalysis(None))
            
if __name__ == "__main__":
    main()
