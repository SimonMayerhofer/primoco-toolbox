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

from influxdb_client import BucketRetentionRules, BucketsService, PatchBucketRequest

class InfluxImporter():
    def __init__(self, filepath):
        self.url = "http://localhost:8086"
        self.token = os.environ['INFLUXDB_TOKEN']
        self.org = os.environ['INFLUXDB_ORG']
        self.bucketName = os.environ['INFLUXDB_BUCKET']

        self.filepath = filepath
        self.measurement = "bookings"
        # CSV Header:
        # Date;Entry Type;Value;Currencs;Category;Person;Account;Counter Account;Group;Note;Recurring;
        self.tagColumns = ['Entry Type', 'Person', 'Category', 'Account', 'Counter Account']

        self.client = InfluxDBClient(
            url=self.url,
            token=self.token,
            org=self.org,
            timeout=120 * 1000 # 120 seconds
        )

    def closeClient(self):
        self.client.close()

    def createBucket(self, bucketName=None):
        if bucketName is None:
            bucketName = self.bucketName

        buckets_api = self.client.buckets_api()
        print("Create bucket " + bucketName)

        buckets_api.create_bucket(
            bucket_name=bucketName,
            org=self.org
        )

    def renameBucket(self, bucketName, newName):
        print("Rename bucket '" + bucketName + "' -> '" + newName + "'")
        buckets_api = self.client.buckets_api()
        service = BucketsService(self.client.api_client)

        bucket = buckets_api.find_bucket_by_name(bucketName)
        request = PatchBucketRequest(name=newName)
        service.patch_buckets_id(bucket_id=bucket.id, patch_bucket_request=request)


    def deleteBucket(self, bucketName=None):
        if bucketName is None:
            bucketName = self.bucketName

        print("Delete bucket " + bucketName)
        buckets_api = self.client.buckets_api()
        bucket = buckets_api.find_bucket_by_name(bucketName)
        if bucket != None:
            buckets_api.delete_bucket(bucket)
        else:
            print("bucket not found")

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

    def writeDataFrameToInflux(self, dataFrame, bucketName=None):
        if bucketName is None:
            bucketName = self.bucketName

        # write entries in batches to circumvent timeouts
        print("start writing " + str(len(dataFrame)) + " entries to " + bucketName)
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
                bucketName,
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

        # create temporary bucket and write all the data to it
        self.deleteBucket(self.bucketName + "_temp")
        self.createBucket(self.bucketName + "_temp")
        self.writeDataFrameToInflux(dataFrame, self.bucketName + "_temp")

        buckets_api = self.client.buckets_api()
        bucket = buckets_api.find_bucket_by_name(self.bucketName)
        if bucket != None:
            self.deleteBucket(self.bucketName + "_old")
            # swith current live bucket with the temporary one
            self.renameBucket(self.bucketName, self.bucketName + "_old")

        self.renameBucket(self.bucketName + "_temp", self.bucketName)

        if bucket != None:
            # delete old bucket data
            self.deleteBucket(self.bucketName + "_old")
