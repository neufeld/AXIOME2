#!/usr/bin/env python

from __future__ import print_function
import sys
import argparse
from os.path import isfile

# A simple script to check for common mistakes in the metadata mapping file. 
# We dont use validate_mapping_file.py since it is too picky.

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("metadata_mapping", help="The QIIME metadata mapping file to be checked")
	args = parser.parse_args()

	print("Checking the metadata mapping file...", file=sys.stdout)
	
	if not isfile(args.metadata_mapping):
		print("ERROR: The provided metadata mapping '" + args.metadata_mapping + "' is not a file", file=sys.stderr)
		sys.exit(1)

	with open(args.metadata_mapping) as metaMap:
		
		header = metaMap.readline()
		categories = header.split("\t")
		numColumns = len(categories)
		if numColumns <= 1:
			print("ERROR: The mapping file '" + args.metadata_mapping + "' is not tab delimited", file=sys.stderr)
			sys.exit(1)

		if categories[0] != "#SampleID":
			print("ERROR: The first column must be #SampleID, was given: " + str(categories[0]), file=sys.stderr)
			sys.exit(1)

		lineNum = 1
		for line in metaMap:
			lineNum += 1
			newNumColumns = len(line.split("\t"))
			if newNumColumns != numColumns:
				print("ERROR: Line " + str(lineNum) + " has the incorrect number of columns", file=sys.stderr)
				print("Expected " + str(numColumns) + " columns, but found " + str(newNumColumns), file=sys.stderr)
				print(line, file=sys.stderr)
				sys.exit(1)

	print("Metadata mapping file is okay!", file=sys.stdout)			

if __name__ == "__main__":
	main()

