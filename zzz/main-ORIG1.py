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
from pre_post_checks import Dhcp

##################################  CSV format ##################################
# ScopeId,IPAddress,Name,ClientId,Description
# 10.10.10.0,10.10.10.10,Computer1.stesworld.com,1a-1b-1c-1d-1e-1f,Reserved for Computer1
# 20.20.20.0,20.20.20.11,Computer2.stesworld.com,2a-2b-2c-2d-2e-2f,Reserved for Computer2

######################## Variables to change dependant on environment ########################
# Where script will look for the csv, by default is the users home directory
directory = expanduser("~")
# domain_name expected for DHCP and DNS entries (must be upto last.)
domain_name = "stesworld.com"

# Servers that the script will run against
dhcp_svr = "10.30.10.81"
dns_svr = "10.30.10.81"
ise_adm = "10.30.10.81"

# Temp files used by DHCP
temp_csv = os.path.join(directory, 'temp_csv.csv')                  # CSV with DHCP scope with prefixes removed
win_dir = os.path.join('C:\\temp', os.path.split(temp_csv)[1])      # Location on DHCP server csv run from

##################################  Santiy check CSV and its contents ##################################
class Validate():
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.csv_output = []                            # Create a new list

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
                else:                                   # If any column is empty script fails
                    print("!!!ERROR - The CSV is in invalid, check for empty columns and rerun")
                    exit()
        self.csv_output = self.csv_output[1:]           # Removes the header column
        return self.csv_output                          # Used for pytest

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

################# Creates new data model used in pre_post_checks script used to check if entry already exists #################

# 4. Combines all addresses with the same scope as values (ip, name, mac) under that Key (scope)
    def data_model(self):
        global csv_dm                   # New DM that wll be used in pre_post_checks
        csv_dm = []
        csv_dm1 = defaultdict(list)      # Temp defaultdict list. Has to be defaultdict or will fail if key is not found in the dictionary

        # Creates 1 big dictionary of the new data model (rather than being list of dicts per scope)
        for x in self.csv_output:
            for key, value in x.items():
                csv_dm1[key].append(value)          # Removes duplicate keys, although dont know how?

        # # Splits the 1 big dictionary into a list different dictionaries (per-scope), removes the prefix and creates list of scopes
        for (k,v) in csv_dm1.items():
            k = k.split('/')[0]
            csv_dm.append({k:v})

        return csv_dm                       # Used for pytest

################# Get login details and main menu from which tasks are run #################

class Main_menu():
    def __init__(self, csv_dm):
        self.csv_dm = csv_dm

    # 5. Collects login detais and tests that they are correct Assumed if works on one device will work on all
    def login(self):
        self.complete = False                        # Used to keep loop going if entered credentials are wrong
        while not self.complete:
            try:
                self.user = input("Enter your username: ")
                self.password = getpass()
                # Test credentials by running simple cmd on the DHCP serber
                conn = Client(dhcp_svr, username=self.user, password=self.password,ssl=False)
                conn.execute_cmd('ipconfig')
                self.task()       # Runs next function (6)

            except Exception as e:              # If login fails loops to begining displaying this error message
                print(e)

    # 6. Main menu. The options user can select which will run the required tasks in other (imported) scripts
    def task(self):
        self.complete = True                 # Kills the loop for login
        print('''
What type of task is being performed?
1. Add DHCP Entry
2. Delete DHCP entry
''')
# 1. Add DHCP and DNS entries
# 2. Delete DHCP and DNS entries
# 3. Add DHCP, DNS and ISE entries
# 4. Delete DHCP, DNS and ISE entries
        task = input("Enter a number: ")
        print()
        while True:
            if task == '1':
                type = 'add'
                self.task_dhcp_add(type)
            if task == '2':
                type = 'remove'
                self.task_dhcp(type)
            # elif task == '2':
            #     print(2)
            #     create = False
            #     break
            # elif task == '3':
            #     print(3)
            #     create = True
            #     break
            # elif task == '4':
            #     print(4)
            #     create = False
            #     break
            else:
                task = input("Not recognised, enter a valid number: ")

    def task_dhcp_add(self, type):
        dhcp = Dhcp(dhcp_svr, self.user, self.password, self.csv_dm)
        # dns = Dns(dns_svr, user, password, self.csv_dm)
        # Fails if Scopes or Domains do not exist
        dhcp_failfast = dhcp.failfast()
        dns_failfast = None     # change to when DNS is done dns.failfast()
        if dhcp_failfast != None or dns_failfast != None:
            print(dhcp_failfast, '\n', dns_failfast)
            exit()
        # Fails if any of the new reservations or DNS entries already exist
        dhcp_verify_pre = dhcp.verify()
        dns_verify_pre = {'DNS': []}     # change to when DNS is done dns.verify()
        if len(dhcp_verify_pre[1]['DHCP']) != 0 or len(dns_verify_pre['DNS']) != 0:
            print("!!! Error - These entries already exist, you must delete the duplicates before can run the script.")
            pprint(dhcp_verify_pre[1])
            pprint(dns_verify_pre)
            exit()
        # Create DHCP entries and verify
        dhcp_create = dhcp.create(csv_file, type, temp_csv, win_dir)
        # Error handling based on the DHCP cmds run
        if dhcp_create[1] is True:
            "!!! Warning - Was maybe an issue with the config commands sent to the DHCP server."
        if dhcp_create[2] != 0:
            "!!! Error - Was maybe an issue with the reservations/ CSV file sent to the DHCP server."
        # Verification and error handling based current entries on DHCP server
        dhcp_verify_post = dhcp.verify()
        print("Check and confirm the numbers below add up.")
        print("Num Entries in CSV: {}, Num Reservations Before: {}, Num Reservations After: {}".format(dhcp_create[0], dhcp_verify_pre[0], dhcp_verify_post[0]))
        if len(dhcp_verify_post[2]) != 0:
            print("!!! Error - the following new DHCP reservations are missing on the DHCP server")
            pprint(dhcp_verify_post[2])
        else:
            print("The script has verified all IP addresses in the CSV are now DHCP reservations.")
        exit()

    def task_dhcp_remove(self, type):
        dhcp = Dhcp(dhcp_svr, self.user, self.password, self.csv_dm)
        # Fails if Scopes or Domains do not exist
        dhcp_failfast = dhcp.failfast()
        if dhcp_failfast != None:
            print(dhcp_failfast)
            exit()
        # Fails if any of the reservations or DNS entries dont exist
        dhcp_verify_pre = dhcp.verify()
        if len(dhcp_verify_pre[2]) != 0:
            print("!!! Error - These entries do not exist, you must remove from CSV before you can run the script.")
            pprint(dhcp_verify_pre[2])
            # pprint(dns_verify_pre)
            exit()

        # Delete DHCP entries and verify
        dhcp_create = dhcp.create(csv_file, type, temp_csv, win_dir)
        # Error handling based on the DHCP cmds run
        if dhcp_create[1] is True:
            "!!! Warning - Was maybe an issue with the config commands sent to the DHCP server."
        if dhcp_create[2] != 0:
            "!!! Error - Was maybe an issue with the reservations/ CSV file sent to the DHCP server."
        # Verification and error handling based current entries on DHCP server
        dhcp_verify_post = dhcp.verify()
        print("Check and confirm the numbers below add up.")
        print("Num Entries in CSV: {}, Num Reservations Before: {}, Num Reservations After: {}".format(dhcp_create[0], dhcp_verify_pre[0], dhcp_verify_post[0]))
        if len(dhcp_verify_post[2]) != dhcp_create[0]:      # number of missign entires should equal CSV
            print("!!! Error - the following DHCP reservations are still used on the DHCP server")
            pprint(dhcp_verify_post[2])
        else:
            print("The script has verified all IP addresses in the CSV are now DHCP reservations.")
        exit()


################# TASKS - runs external modules #################
# 7. Run the tasks dependant on the user unput.

    # def task_dhcp(self)




###################################### Run the scripts ######################################
# 1. Starts the script taking input of CSV file name

def main():
    fname = argv[1]                                 # Creates varaible from the arg passed in when script run (csv file)
    global csv_file
    csv_file = os.path.join(directory, fname)       # Creates full path to the csv using directory variable
    validation = Validate(csv_file)
    # Runs function 2 to validate format of the CSV
    validation.read_csv()
    # Runs function 3 to validate format of the CSV contents
    validation.verify()
    # Runs function 4 to create the new data model from the CSV data
    validation.data_model()

    # Runs function 5 and 6 to get logon credentails and load main menu
    tasks = Main_menu(csv_dm)
    tasks.login()

if __name__ == '__main__':
    main()








