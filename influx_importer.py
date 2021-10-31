#!/usr/bin/env python3

# load environment variables from .env file.
from dotenv import load_dotenv
load_dotenv()

import os
from datetime import timedelta

import pandas as pd
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

class InfluxImporter():
    def __init__(self, filepath):
        self.filepath = filepath
        self.measurement = "bookings"
        # id must be present, so we can ensure, all rows are unique (and be able to be imported)
        self.tagColumns = ['Entry Type']

        self.client = InfluxDBClient(
            url="http://localhost:8086",
            token=os.environ['INFLUXDB_TOKEN'],
            org=os.environ['INFLUXDB_ORG']
        )

    def closeClient(self):
        self.client.close()

    def deleteExistingData(self):
        print("trying to delete bucket " + os.environ['INFLUXDB_BUCKET'])
        buckets_api = self.client.buckets_api()
        bucket = buckets_api.find_bucket_by_name(os.environ['INFLUXDB_BUCKET'])
        if not bucket == None:
            buckets_api.delete_bucket(bucket)
        else:
            print("bucket not found")


        print("create bucket " + os.environ['INFLUXDB_BUCKET'])
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
        dataFrame = pd.read_csv(self.filepath, sep=";", skiprows=1, decimal=",", encoding="utf-8")
        # Use the to_datetime() function to set the timestamp column of dataframe to a datetime object
        dataFrame['Date'] = pd.to_datetime(dataFrame['Date'], format="%d.%m.%Y" )

        # add microseconds to datetime to make sure all entries are unique and imported.
        # https://docs.influxdata.com/influxdb/v2.0/write-data/best-practices/duplicate-points/
        for i in dataFrame.index:
            dataFrame.at[i, 'Date'] = dataFrame.at[i, 'Date'] + timedelta(microseconds=i)

        # add ID column
        dataFrame["id"] = dataFrame.index + 1
        # Set the datetime column as the index of the dataframe
        dataFrame.set_index(['Date'], inplace = True)
        # print table info data
        dataFrame.info()

        # write entries in batches to circumvent timeouts
        print("start writing " + str(len(dataFrame)) + " entries:")
        write_client = self.client.write_api(write_options=SYNCHRONOUS)
        interval = 1000
        start = 0
        end = interval
        while end < len(dataFrame) + interval:
            if end > len(dataFrame):
                end = len(dataFrame)
            print("write " + str(start) + "-" + str(end))
            record = dataFrame.iloc[start:end]
            write_client.write(
                os.environ['INFLUXDB_BUCKET'],
                record=record,
                data_frame_measurement_name=self.measurement,
                data_frame_tag_columns=self.tagColumns
            )
            start = end
            end = end + interval

