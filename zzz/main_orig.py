#!/usr/bin/env python

import os
from os.path import expanduser
import csv
from ipaddress import ip_address
from ipaddress import ip_network
import sys
import re

################# CSV format #################
# ScopeId,IPAddress,Name,ClientId,Description
# 10.10.10.0,10.10.10.10,Computer1.stesworld.com,1a-1b-1c-1d-1e-1f,Reserved for Computer1
# 20.20.20.0,20.20.20.11,Computer2.stesworld.com,2a-2b-2c-2d-2e-2f,Reserved for Computer2

################# Variables to change dependant on environment #################
# Sets it has users home directory
directory = expanduser("~")
# domain_name expected for DHCP and DNS entries (must be upto last.)
domain_name = "stesworld.com"

################# Santiy check CSV #################
# 1. Open CSV file and create a list of scopes and a list of tuples (ip_add, domain_name)

def read_csv(csv_file):
    global csv_ipadd_dom, csv_scope, csv_mac                             # Create global variables
    ipadd_dom, scope, mac = ([] for i in range(3))      # Create 3 new lists

    with open(csv_file, 'r') as x:                  # Open file
        csv_read = csv.reader(x)			        # Read the csv file
    # Checks CSV format is correct and creates lists of scope, (ip, dom) and mac
        for row in csv_read:
            if len(row) == 0:                       # If is a blank line skips it
                continue
            elif all(0 == len(s) for s in row):     # If all columns in a row are blank skips it
                continue
            elif len(row) != 5:                     # If not 5 rows in CSV exists
                print("!!!ERROR - The CSV is in invalid format, please check and rerun")
                exit()
            elif all(0 != len(s) for s in row):     # If all elements present builds lists
                ipadd_dom.append((row[1], row[2]))
                scope.append(row[0])
                mac.append(row[3])
            else:                                   # If any element empty fails
                print("!!!ERROR - The CSV is in invalid format, please check and rerun")
                exit()

    # Removes the header column from both lists
    csv_ipadd_dom = ipadd_dom[1:]
    csv_scope = set(scope[1:])      # Delete entires for scope duplicates
    csv_mac = mac[1:]

# 2. Make sure that the IP addresses are in the correct format, if not ends exits script
def verify(csv_ipadd_dom, csv_scope, csv_mac):
    scope_error, ip_error, dom_error, mac_error = ([] for i in range(4))    # Lists to store invalid elements
    # Validates the CSV contents are valid, creating lists of non-valid elements
    for scope in csv_scope:                         # Checks the scopes are in a valid format
        try:
            ip_address(scope)
        except ValueError as errorCode:
            scope_error.append(str(errorCode))
    for ip in csv_ipadd_dom:                        # Checks the IP addresses are in a valid format
        try:
            ip_address(ip[0])
        except ValueError as errorCode:
            ip_error.append(str(errorCode))
    for dom in csv_ipadd_dom:                       # Checks domain names are in a valid format
        dom1 = '.'.join(dom[1].split('.')[1:])      # Gets everything after first .
        if dom1 != domain_name:
            dom_error.append(dom[1])
    for mac in csv_mac:                             # Checks if MAC is in valid format (xx-xx-xx-xx-xx-xx)
        try:
            re.match(r'([a-fA-F0-9]{2}-){5}([a-fA-F0-9]{2})', mac).group()
        except:
            mac_error.append(mac)

    # Exits script listing issues if any of the above conditions cause an error (list not empty)
    if len(scope_error) != 0:
        print("!!!ERROR - Invalid scope addresses entered !!!")
        for x in scope_error:
            print(x)
    if len(ip_error) != 0:
        print("!!!ERROR - Invalid IP addresses entered !!!")
        for x in ip_error:
            print(x)
    if len(dom_error) != 0:
        print("!!!ERROR - Invalid Domian names entered !!!")
        for x in dom_error:
            print(x)
    if len(mac_error) != 0:
        print("!!!ERROR - Invalid MAC  addresses entered !!!")
        for x in mac_error:
            print(x)
    if len(scope_error) != 0 or len(ip_error) != 0 or len(dom_error) != 0 or len(mac_error) != 0:
        exit()

csv_file = os.path.join(directory, "test.csv")
read_csv(csv_file)
verify(csv_ipadd_dom, csv_scope, csv_mac)
