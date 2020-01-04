#!/usr/bin/env python

# run using python main.py ~/test2.csv

from sys import argv
import os
from os.path import expanduser
import csv
from ipaddress import ip_address
from ipaddress import ip_network
import sys
import re
from pprint import pprint
from getpass import getpass
from pypsrp.client import Client
from collections import defaultdict

################# CSV format #################
# ScopeId,IPAddress,Name,ClientId,Description
# 10.10.10.0,10.10.10.10,Computer1.stesworld.com,1a-1b-1c-1d-1e-1f,Reserved for Computer1
# 20.20.20.0,20.20.20.11,Computer2.stesworld.com,2a-2b-2c-2d-2e-2f,Reserved for Computer2

################# Variables to change dependant on environment #################
# Where script will look for the csv, by default is the users home directory
directory = expanduser("~")
# domain_name expected for DHCP and DNS entries (must be upto last.)
domain_name = "stesworld.com"

# Servers that the script will run against
dhcp_server = "10.30.10.81"
dns_server = "10.30.10.81"
ise_admin = "10.30.10.81"
servers = {'dhcp': dhcp_server, 'dns': dns_server, 'ise': ise_admin }

################# Santiy check CSV #################
class validate():
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.csv_output = []                            # Create a new list
        self.csv_output1 = []                            # TEMP
# 2. Open CSV file and create a list of scopes and a list of tuples (ip_add, domain_name)
    def read_csv(self):
        with open(self.csv_file, 'r') as x:
            csv_read = csv.reader(x)

        # Checks CSV format is correct and creates lists of scope, (ip, dom) and mac
            for row in csv_read:
                if len(row) == 0:                       # If it is a blank line skips it
                    continue
                elif all(0 == len(s) for s in row):     # If all columns in a row are blank skips it
                    continue
                elif len(row) != 5:                     # If there are not 5 columns in every row script fails
                    print("!!!ERROR - The CSV is in invalid, check every row has 5 columns and rerun")
                    exit()
                # As long as all columns have values creates a list of dicts (scope) with value being a tuple (ip, name, mac, description)
                elif all(0 != len(s) for s in row):
                    self.csv_output.append({row[0]: (row[1], row[2].lower(), row[3].lower())})      # makes sure mac and domain are lowercase
                    self.csv_output1.append({row[0]: [[row[1]], [row[2].lower()], [row[3].lower()]]})      # TEMP
                else:                                   # If any column is empty script fails
                    print("!!!ERROR - The CSV is in invalid, check for empty columns and rerun")
                    exit()
        self.csv_output = self.csv_output[1:]           # Removes the header column
        self.csv_output1 = self.csv_output1[1:]           # TEMP
        return self.csv_output                          # Used for pytest

################# Santiy check contents of data model #################
# 3. Make sure that the details in the CSV are in a valid correct format, if not ends the script fails
    def verify(self):
        scope_error, ip_error, dom_error, mac_error, ip_in_net_error = ([] for i in range(5))    # Lists to store invalid elements

        # Validates the CSV contents are valid, creating lists of non-valid elements
        for x in self.csv_output:
            # Checks the scopes are in a valid IPv4 network address format
            try:
                ip_network(list(x.keys())[0])        # Convert to a list as dict_keys object does not support indexing
            except ValueError as errorCode:
                scope_error.append(str(errorCode))
            # Checks the IP addresses are in a valid IPv4 address format
            try:
                ip_address(list(x.values())[0][0])    # Convert to a list as dict_values object does not support indexing
            except ValueError as errorCode:
                ip_error.append(str(errorCode))
            # Checks domain names are in a valid format (ends with domain_name variable)
            domain = '.'.join(list(x.values())[0][1].split('.')[1:])      # Gets everything after first .
            if domain != domain_name:
                dom_error.append(list(x.values())[0][1])
            # Checks if MAC address is in a valid format (xx-xx-xx-xx-xx-xx) with valid characters (0-9, a-f)
            try:
                re.match(r'([a-fA-F0-9]{2}-){5}([a-fA-F0-9]{2})', list(x.values())[0][2]).group()
            except:
                mac_error.append(list(x.values())[0][2])
            # Checks the IP address is within the scopes network address
            if len(scope_error) == 0 and len(ip_error) == 0:
                if ip_address(list(x.values())[0][0]) not in ip_network(list(x.keys())[0]):
                    ip_in_net_error.append(list(x.values())[0][0] +  ' not in ' + list(x.keys())[0])

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
            print("!!!ERROR - Invalid Domain names entered !!!")
            for x in dom_error:
                print(x)
        if len(mac_error) != 0:
            print("!!!ERROR - Invalid MAC addresses entered !!!")
            for x in mac_error:
                print(x)
        if len(ip_in_net_error) != 0:
            print("!!!ERROR - IP address not a valid IP address in DHCP scope !!!")
            for x in ip_in_net_error:
                print(x)

        if len(scope_error) != 0 or len(ip_error) != 0 or len(dom_error) != 0 or len(mac_error) != 0 or len(ip_in_net_error) !=0:
            exit()

################# Creates data model used in pre_post_checks script used to check if entry already exists #################
# 4. Combines all addresses with the same scope as values (ip, name, mac) under that Key (scope)
    def data_model(self):
        global csv_dm                   # New DM that wll be used in pre_post_checks
        csv_dm, csv_dm1, csv_ip, csv_mac, csv_name, csv_ip_name_mac = ([] for i in range(6))
        csv_dm2 = defaultdict(list)      # Temp defaultdict list. Has to be defaultdict or will fail if key is not found in the dictionary

        # Creates 1 big dictionary of the new data model (rather than being list of dicts per scope)
        scopes = []
        for x in self.csv_output:
            for key, value in x.items():
                # key = key.split('/')[0]             # strips prefix from the scope
                csv_dm2[key].append(value)          # Removes duplicate keys, although dont know how?
                # scopes.append(key)
        # scopes = set(scopes)                # makes set to remove duplicates
        # print(self.csv_output1)


        # print(csv_dm2)
        # for x, y in zip(scopes, csv_dm2.items()):
        #     if x == y[0]:
        #         for z in y[1]:
        #            pprint(z[0])
            # print(k)
            # print(y)
        # for y in csv_dm2.items():
        #     print(type(y))
        # pprint(csv_dm2)

        #         print(y)
        # for x, y in zip(scopes, csv_dm2.items()):
        #     # if x == y.keys():
        #     #     print('YESY')
        #

        # # Splits the 1 big dictionary into a list different dictionaries (per-scope), removes the prefix and creates list of scopes
        for (k,v) in csv_dm2.items():
            k = k.split('/')[0]
            csv_dm1.append({k:v})
            scopes.append(k)

        csv_ip2, csv_name2, csv_mac2 = ([] for i in range(3))
        csv_ip3, csv_name3, csv_mac3 = ([] for i in range(3))

        for x in enumerate(csv_dm1, start=1):
            for k, v in x[1].items():
                for vv in v:
                    if x[0] == 1:
                        csv_ip.append(vv[0])
                        csv_name.append(vv[1])
                        csv_mac.append(vv[2])
                        x[1][k] = [csv_ip, csv_name, csv_mac]
                        # csv_ip, csv_name, csv_mac = ([] for i in range(3))
                    elif x[0] == 2:
                        csv_ip2.append(vv[0])
                        csv_name2.append(vv[1])
                        csv_mac2.append(vv[2])
                        x[1][k] = [csv_ip, csv_name, csv_mac]
                    elif x[0] == 3:
                        csv_ip3.append(vv[0])
                        csv_name3.append(vv[1])
                        csv_mac3.append(vv[2])
                        x[1][k] = [csv_ip, csv_name, csv_mac]
        pprint(self.csv_output1)
        # print(scopes)
        # for x, y in zip(scopes, csv_dm1):
        # # pprint(csv_dm1)
        #     print(y.keys())
        #         # print(y.values())

        # for x in scopes:
        #     for y in csv_dm1.keys():
        #         if x == y:
        #             pprint(csv_dm2.values())
        #         # print(y)

        # # On a per-scope basis creates CSV DM of scope: [[IP], [mac], [name], [(IP, MAC, name)]]
        # for scope in scopes:
        #     a = csv_dm2[scope]
        #         # for vv in v:
        #         #     if scope == k:
        #         #         csv_ip.append(vv[0])
        #         # if scope == k:

        # print(csv_ip)
        # print(a)
            # scope_dict['yest']: 'yes'
            # print(scope_dict)
        # pprint(csv_dm1)
        # for (k,v) in csv_dm2.items():
        #     k = k.split('/')[0]
        #     csv_dm1.append({k:v})


        # # pprint(self.csv_output)
        # # pprint(csv_dm2)
        # csv_dm3 = {}
        # for scope_dict, v in csv_dm2.items():
        #     for vv in v:
        #         if scope_dict == scope_dict:
        #             # csv_dm3[scope_dict] = vv[0]
        #             csv_ip.append(vv[0])
        #     # pprint(scope_dict)
        #     # pprint(v)
        # # pprint(csv_ip)

        # pprint(csv_ip)
        # pprint(csv_dm1)


            # for k, v in scope_dict.items():
            #     for vv in v:
            #         b = {k:csv_ip.append(vv[0])}
            #         a = {k: csv_ip}
            # for k, v in scope_dict.items():
            #     for vv in v:
            #         a = {k:csv_ip.append(vv[0])}
                # a = {k:csv_ip}
                    # print(k, vv[0])
            # print(scope_dict.values()[0])
            #
                # print(k)
        #         for vv in v:
        #             csv_ip.append(vv[0])
        #         csv_dm.append({k:csv_ip})
        # pprint(csv_dm1)


        #     dhcp_ip.append((r.split()[0]))
        #     dhcp_name.append((r.split()[3].lower()))
        #     dhcp_mac.append((r.split()[2].lower()))
        #     dhcp_ip_name_mac.append((r.split()[0], r.split()[3].lower(), r.split()[2].lower()))

        # self.dhcp_dm.append({scope:[dhcp_ip, dhcp_name, dhcp_mac, dhcp_ip_name_mac]})

        #     for vv in v:
        #         csv_ip.append(vv[0])
        #         csv_name.append(vv[1])
        #         csv_mac.append(vv[2])
        #         csv_ip_name_mac = [vv[0], vv[1], vv[2]]
        #         csv_dm.append({k:[csv_ip, csv_name, csv_mac, csv_ip_name_mac]})

            #
        # return csv_dm                       # Used for pytest
        # pprint(csv_ip)
################# Get login details and main menu from which tasks are run #################

class main_menu():
    def __init__(self, csv_dm):
        self.csv_dm = csv_dm

    # 5. Collects login detais and tests that they are correct Assumed if works on one device will work on all
    def login(self):
        complete = False                        # Used to keep loop going if entered credentials are wrong
        while not complete:
            try:
                user = input("Enter your username: ")
                password = getpass()
                # Test credentials by running simple cmd on the DHCP serber
                conn = Client(dhcp_server, username=user, password=password,ssl=False)
                conn.execute_cmd('ipconfig')
                self.task(user, password)       # Runs next function (6)
                complete = True                 # Kills the loop
            except Exception as e:              # If login fails loops to begining displaying this error message
                print(e)

    # 6. Main menu. The options user can select which will run the required tasks in other (imported) scripts
    def task(self, user, password):
        print('''
What type of task is being performed?'
1. Add DHCP and DNS entries
2. Delete DHCP and DNS entries
3. Add DHCP, DNS and ISE entries
4. Delete DHCP, DNS and ISE entries''')
        task = input("Enter a number: ")

        while True:
            if task == '1':
                print(1)
                create = True
                break
            elif task == '2':
                print(2)
                create = False
                break
            elif task == '3':
                print(3)
                create = True
                break
            elif task == '4':
                print(4)
                create = False
                break
            else:
                task = input("Not recognised, enter a valid number: ")

###################################### Run the scripts ######################################
# 1. Starts the script taking input of CSV file name

def main():
    fname = argv[1]                                 # Creates varaible from the arg passed in when script run (csv file)
    csv_file = os.path.join(directory, fname)       # Creates full path to the csv using directory variable
    validation = validate(csv_file)

    # Runs function 2 to validate format of the CSV
    validation.read_csv()
    # Runs function 3 to validate format of the CSV contents
    validation.verify()
    # Runs function 4 to create the new data model from the CSV data
    validation.data_model()

    # Runs function 5 and 6 to get logon credentails and load main menu
    # tasks = main_menu(csv_dm)
    # tasks.login()

if __name__ == '__main__':
    main()








