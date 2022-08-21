FROM python:3
RUN apt-get -y update
# RUN apt-get -y install xyzpackage

COPY . /primoco-toolbox

WORKDIR /primoco-toolbox

RUN pip install -r requirements.txt

RUN wget https://dl.influxdata.com/influxdb/releases/influxdb2-client-2.4.0-linux-amd64.tar.gz
RUN tar xvzf influxdb2-client-2.4.0-linux-amd64.tar.gz
RUN \cp -r influxdb2-client-2.4.0-linux-amd64/influx /usr/local/bin/
RUN rm influxdb2-client-2.4.0-linux-amd64.tar.gz

RUN influx config rm primoco-influx.conf
RUN influx config create --config-name primoco-influx.conf \
  --host-url http://influxdb:8086 \
  --org $INFLUXDB_ORG \
  --token $INFLUXDB_TOKEN \
  --active
