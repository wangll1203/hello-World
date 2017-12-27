#!/usr/bin/env python
#coding:utf-8

import boto3
import sys
import datetime
import ConfigParser

class GetMetric(object):
    currentTime = datetime.datetime.utcnow()
    region_name = 'us-east-1'
    configPaht = '/usr/local/zabbix/scripts/awsinfo.conf'

    def __init__(self, rdsname,metricname):
        self.rdsName = rdsname
        self.metricName = metricname
        self.client = boto3.client('rds', region_name=GetMetric.region_name)
        self.client_cloudWatch = boto3.client('cloudwatch', region_name=GetMetric.region_name)
        self.StartTime = (GetMetric.currentTime - datetime.timedelta(minutes=5)).strftime('%Y-%m-%dT%H:%M:%S')
        self.EndTime = GetMetric.currentTime.strftime('%Y-%m-%dT%H:%M:%S')


    def getcloudwatchvalues(self):
        dic_cloudwatch = self.client_cloudWatch.get_metric_statistics(
            Period=300,
            StartTime=self.StartTime,
            EndTime=self.EndTime,
            Namespace="AWS/RDS",
            MetricName=self.metricName,
            Statistics=['Maximum'],
            Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': self.rdsName}])

        list_cloudwatch = dic_cloudwatch['Datapoints']
        if list_cloudwatch:
            cloudwatchvalues_dic = {'cloud_unit':list_cloudwatch[0]['Unit'],'value_max':self.unitConversion(list_cloudwatch[0]['Unit'],list_cloudwatch[0]['Maximum'])}
            return cloudwatchvalues_dic




    def getrdsuserdata(self):
        dic_rds = self.client.describe_db_instances(DBInstanceIdentifier=self.rdsName)
        list_rds = dic_rds['DBInstances']
        for list in range(0, len(list_rds)):
            if list_rds[list]['Engine'] == 'mysql':
                rdsvalues_dic = {'rds_storage':list_rds[list]['AllocatedStorage'], 'rds_class':list_rds[list]['DBInstanceClass']}
                return rdsvalues_dic

    def unitConversion(self,unit_kinds,unit_storage):
        if unit_kinds == 'Bytes':
            conGigabyte = round(unit_storage/1024/1024/1024,5)
            return conGigabyte
        if unit_kinds == 'Percent':
            return unit_storage
        if unit_kinds == 'Count':
            return unit_storage
        else:
            return None

    def getrdsclassinfo(self, classname):
        config = ConfigParser.ConfigParser()
        config.read(GetMetric.configPaht)
        getvalue = float(config.get("DB", classname))
        return getvalue


    def conversionpercent(self):
        getcloudwatchvalues = self.getcloudwatchvalues()
        getrdsvalues = self.getrdsuserdata()
        if self.metricName == 'FreeStorageSpace':
            StoragePercentAvailable = (1-(round((getcloudwatchvalues['value_max']/getrdsvalues['rds_storage']), 3)))*100
            return StoragePercentAvailable
        if self.metricName == 'DatabaseConnections':
            ConnectionsValues = getcloudwatchvalues['value_max']
            return ConnectionsValues
        if self.metricName == 'CPUUtilization':
            CpuUtilizaionValue = getcloudwatchvalues['value_max']
            return CpuUtilizaionValue
        if self.metricName == 'FreeableMemory':
            if self.getrdsclassinfo(getrdsvalues['rds_class']):
                classMemValues = self.getrdsclassinfo(getrdsvalues['rds_class'])
                MemoryPercentAvailable = (1-(round((getcloudwatchvalues['value_max']/classMemValues),3)))*100
                return MemoryPercentAvailable

    def main(self):
        return self.conversionpercent()

try:
    loadMan = GetMetric(sys.argv[1], sys.argv[2])
    print loadMan.main()
except IOError:
    pass
