# This Python program takes json files generated by the Franklin Co Court Scraper and converts them into sets of relational csvs, ready to be imported into a database repository like Redivis
# ++++++ In progress ++++++

import sys
import os
import argparse
import csv
import json

def convert(json_file, destination_dir):
	try:
		json_dict = json.load('json_file','r')
	except:
		print(f'Error: Could not find json file named "{json_file}."')
		return


if __name__ = '__main__':

	parser = argparse.ArgumentParser()
    parser.add_argument('--json_file', type=str, required=True)
    parser.add_argument('--destination_dir', type=str, required=True)
    args = parser.parse_args()