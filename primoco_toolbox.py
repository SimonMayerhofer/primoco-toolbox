#!/usr/bin/env python3

import sys, getopt, os

from influx_importer import InfluxImporter
from export_downloader import ExportDownloader

def exportDownload():
    ed = ExportDownloader()
    try:
        ed.login()
        ed.download()
    finally:
        # make sure the driver connection is properly closed in any case.
        ed.quitBrowser()

def influxImport():
    importer = InfluxImporter(
        filepath = os.path.join(os.environ['DOWNLOAD_LOCATION'], "bookings-current.csv"),
    )
    try:
        print("Delete existing data...")
        importer.deleteExistingData()
        print("Start import...")
        importer.startImport()
    finally:
        importer.closeClient()

def main(argv):
    try:
        # options: String of option letters that the script wants to recognize.
        #          Options that require an argument should be followed by a colon (:).
        # long_options: List of the string with the name of long options.
        #               Options that require arguments should be followed by an equal sign (=).
        opts, args = getopt.getopt(argv, "hei", ["help", "all", "export-download", "influx-import"])
    except getopt.GetoptError:
        print ('test.py -i <inputfile> -o <outputfile>')
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print ('Supported arguments:')
            print ('-e, --export-download: start CSV export from Primoco')
            print ('-i, --influx-import: start import to InfluxDB')
            sys.exit()

        elif opt == "--export-download":
            #inputfile = arg
            exportDownload()

        elif opt == "--influx-import":
            #inputfile = arg
            influxImport()

        elif opt == "--all":
            exportDownload()
            influxImport()

if __name__ == "__main__":
    main(sys.argv[1:])
