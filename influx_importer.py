#!/usr/bin/env python3

# load environment variables from .env file.
from dotenv import load_dotenv
load_dotenv()

import os
from datetime import timedelta
import html

import pandas as pd
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

class InfluxImporter():
    def __init__(self, filepath):
        self.url = "http://localhost:8086"
        self.token = os.environ['INFLUXDB_TOKEN']
        self.org = os.environ['INFLUXDB_ORG']
        self.bucket = os.environ['INFLUXDB_BUCKET']

        self.filepath = filepath
        self.measurement = "bookings"
        # CSV Header:
        # Date;Entry Type;Value;Currencs;Category;Person;Account;Counter Account;Group;Note;Recurring;
        self.tagColumns = ['Entry Type', 'Person', 'Category', 'Account']

        self.client = InfluxDBClient(
            url=self.url,
            token=self.token,
            org=self.org,
            timeout=120 * 1000 # 120 seconds
        )

    def closeClient(self):
        self.client.close()

    def deleteExistingData(self):
        print("trying to delete bucket " + self.bucket)
        buckets_api = self.client.buckets_api()
        bucket = buckets_api.find_bucket_by_name(self.bucket)
        if not bucket == None:
            buckets_api.delete_bucket(bucket)
        else:
            print("bucket not found")


        print("create bucket " + self.bucket)
        buckets_api.create_bucket(
            bucket_name=self.bucket,
            org=self.org
        )

        #delete_api = self.client.delete_api()
        #start = "1970-01-01T00:00:00Z"
        #stop = "2200-01-01T00:00:00Z"

        #delete_api.delete(
        #    start,
        #    stop,
        #    '_measurement="' + self.measurement + '"',
        #    bucket=self.bucket,
        #    org=os.environ['INFLUXDB_ORG']
        #)

    def prepareData(self, dataFrame, columns=['Category', 'Person', 'Account', 'Counter Account', 'Group', 'Note' ]):
        for col in columns:
            for i in dataFrame.index:
                if type(dataFrame.at[i, col]) == str: # only replace string values
                    val = dataFrame.at[i, col]
                    # unescape html escaped symbols
                    val = html.unescape(val)
                    # fix bug which lets the code fail, if " ," is present at a value.
                    # see: https://community.influxdata.com/t/writing-entries-gives-invalid-field-format-error-but-only-if-2-tags-are-added-together-separately-works-fine/22368?u=s3n
                    val = val.replace(' ,', ',')
                    dataFrame.at[i, col] = val

    def prepareTagColumns(self, dataFrame):
        # some special characters need to be escaped
        # https://docs.influxdata.com/influxdb/v2.0/reference/syntax/line-protocol/#special-characters
        for col in self.tagColumns:
            for i in dataFrame.index:
                if type(dataFrame.at[i, col]) == str: # only replace string values
                    val = dataFrame.at[i, col]
                    val = val.replace(' ', '\ ')
                    val = val.replace(',', '\,')
                    val = val.replace('=', '\=')
                    dataFrame.at[i, col] = val

    def writeDataFrameToInflux(self, dataFrame):
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
                self.bucket,
                record=record,
                data_frame_measurement_name=self.measurement,
                data_frame_tag_columns=self.tagColumns
            )
            start = end
            end = end + interval

    def uniquifyDateTimeColumn(self, dataFrame, column='Date'):
        # add microseconds to datetime to make sure all entries are unique and imported.
        # https://docs.influxdata.com/influxdb/v2.0/write-data/best-practices/duplicate-points/
        for i in dataFrame.index:
            dataFrame.at[i, column] = dataFrame.at[i, column] + timedelta(microseconds=i)

    def startImport(self):
        dataFrame = pd.read_csv(self.filepath, sep=";", skiprows=1, decimal=",", encoding="utf-8")
        # Use the to_datetime() function to set the timestamp column of dataframe to a datetime object
        dataFrame['Date'] = pd.to_datetime(dataFrame['Date'], format="%d.%m.%Y" )

        print('Uniquify DateTime Column.')
        self.uniquifyDateTimeColumn(dataFrame)

        print('Preparing the data (e.g. unescaping).')
        self.prepareData(dataFrame)

        print('Prepare tag columns.')
        self.prepareTagColumns(dataFrame)

        # Set the datetime column as the index of the dataframe
        dataFrame.set_index(['Date'], inplace = True)
        # print table info data
        dataFrame.info()

        self.writeDataFrameToInflux(dataFrame)

