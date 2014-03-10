#!/bin/python

##################################################
#               Reading portfolio                #
##################################################
import sys
import csv

data_dir = "/Users/Chris/Documents/26 UC Berkeley/03 Courses/STAT 222/stat_222_chris_carmona/data/"
port_file = "port_2013-12.csv"

port = open(data_dir+port_file)
port.close