#!/usr/bin/env python3

# load environment variables from .env file.
from dotenv import load_dotenv
load_dotenv()

import os

import pandas
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

class InfluxImporter():
    def __init__(self, filepath):
        self.filepath = filepath
        self.measurement = "bookings"
        # id must be present, so we can ensure, all rows are unique (and be able to be imported)
        self.tagColumns = ['id', 'Entry Type']

        self.client = InfluxDBClient(
            url="http://localhost:8086",
            token=os.environ['INFLUXDB_TOKEN'],
            org=os.environ['INFLUXDB_ORG']
        )

    def closeClient(self):
        self.client.close()

    def deleteExistingData(self):
        print("delete bucket " + os.environ['INFLUXDB_BUCKET'])
        buckets_api = self.client.buckets_api()
        bucket = buckets_api.find_bucket_by_name(os.environ['INFLUXDB_BUCKET'])
        buckets_api.delete_bucket(bucket)

        print("create bucket again")
        buckets_api.create_bucket(
            bucket_name=os.environ['INFLUXDB_BUCKET'],
            org=os.environ['INFLUXDB_ORG']
        )

        #delete_api = self.client.delete_api()
        #start = "1970-01-01T00:00:00Z"
        #stop = "2200-01-01T00:00:00Z"

        #delete_api.delete(
        #    start,
        #    stop,
        #    '_measurement="' + self.measurement + '"',
        #    bucket=os.environ['INFLUXDB_BUCKET'],
        #    org=os.environ['INFLUXDB_ORG']
        #)

    def startImport(self):
        dataFrame = pandas.read_csv(self.filepath, sep=";", skiprows=1, decimal=",", encoding="utf-8")
        # Use the to_datetime() function to set the timestamp column of dataframe to a datetime object
        dataFrame['Date'] = pandas.to_datetime(dataFrame['Date'], format="%d.%m.%Y" )
        # add id column with unique IDs, to be able to import all data
        dataFrame["id"] = dataFrame.index + 1
        # Set the datetime column as the index of the dataframe
        dataFrame.set_index(['Date'], inplace = True)
        # print table info data
        dataFrame.info()

        write_client = self.client.write_api(write_options=SYNCHRONOUS)
        write_client.write(
            os.environ['INFLUXDB_BUCKET'],
            record=dataFrame,
            data_frame_measurement_name=self.measurement,
            data_frame_tag_columns=self.tagColumns
        )
