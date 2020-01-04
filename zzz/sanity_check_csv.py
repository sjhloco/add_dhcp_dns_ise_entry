#!/usr/bin/env python

import os
from os.path import expanduser
import csv
import ipaddress
import sys

################# Variables to change dependant on environment #################
# Sets it has users home directory
directory = expanduser("~")
# to toggle between windows and linux (used for ping)
WINDOWS = False
# What expect the domain name to be
domain_name = 'fos.org.uk'

################# Makes sure IP addresses are in valid format #################
#### WHAT ABOUT muultiple scopes in the same file????
# CSV File structure should be, need to rework to get info need
# ScopeId,IPAddress,Name,ClientId,Description
# 10.10.10.0,10.10.10.10,Computer1,1a-1b-1c-1d-1e-1f,Reserved for Computer1
# 20.20.20.0,20.20.20.11,Computer2,2a-2b-2c-2d-2e-2f,Reserved for Computer2
# 30.30.30.0,30.30.30.12,Computer3,3a-3b-3c-3d-3e-3f,Reserved for Computer3

# 1. Open CSV file and create a list of tuples (ip_add, domain_name) and list of scopes
ipadd_domain1 = []                          # list to store tuples of (ip, domain)
scope1 = []                                 # list to store all scopes
def read_csv(csv_file):
    with open(csv_file, 'r') as x:          # Open file
        csv_read = csv.reader(x)			# Read the csv file
        for row in csv_read:                # For each row converts to tuple and adds to list
            ipadd_domain1.append((row[1], row[2]))
            scope1.append(row[0])
    ipadd_domain = ipadd_domain1[1:]        # Removes the header column
    scope = scope1[1:]
    # verify(ipadd_domain)                    # Runs 2
    print(scope)
    print(ipadd_domain)

# 2. Make sure that the IP addresses are in the correct format, if not ends exits script
def verify(ipadd_domain):
    ip_error = []                                   # List to store invalid IPs
    for ip in ipadd_domain:
        try:                                    # Checks if IPs are valid, gathers list of non-valid IPs
            ipaddress.ip_address(ip[0])
        except ValueError as errorCode:
            ip_error.append(str(errorCode))     # If invalid adds to list
    # Exits script if there was an ip address error (list not empty)
    if len(ip_error) != 0:                          # If invalid IP list is not empty
        print("!!!ERROR - Invalid IP addresses entered !!!")
        for x in ip_error:
            print(x)                                # Prints bad IPs and stops script
        exit()








# 6. Runs the script
csv_file = os.path.join(directory, "test.csv")
read_csv(csv_file)







# import subprocess





