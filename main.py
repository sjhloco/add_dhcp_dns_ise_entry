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
from win_dhcp import Dhcp

##################################  CSV format ##################################
# ScopeId,IPAddress,Name,ClientId,Description
# 10.10.10.0,10.10.10.10,Computer1.stesworld.com,1a-1b-1c-1d-1e-1f,Reserved for Computer1
# 20.20.20.0,20.20.20.11,Computer2.stesworld.com,2a-2b-2c-2d-2e-2f,Reserved for Computer2

######################## Variables to change dependant on environment ########################
# Where script will look for the csv, by default is the users home directory
directory = expanduser("~")
# domain_name expected for DHCP and DNS entries (must be upto last.)
domain_name = "stesworld.com"
default_ttl = 3600      # in seconds

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
        self.csv_dns_rv_output1 = []             # self as DNS reverse zone needs more formatting than others

# 2. Open CSV file, add defaults, removes blank lines and then creates lists used by the other modules
    def read_csv(self):
        global csv_dhcp_output, csv_dns_fw_output
        csv_temp, csv_dhcp_output, csv_dns_fw_output  = ([] for i in range(3))          # Creates the new list
        with open(self.csv_file, 'r') as x:
            csv_read = csv.reader(x)
            next(csv_read)           # Skips the headers
            # Removes blank lines, checks CSV format, TTL is valid and adds a default value for TTL if it is empty
            for row in csv_read:
                if len(row) == 0 or all(0 == len(s) for s in row):      #If it is a blank line skips or all blank columns
                    continue
                elif len(row) != 6:                     # If there are not 5 columns in every row script fails
                    print("!!!ERROR - The CSV is in invalid, check every row has 6 columns and rerun")
                    exit()
                elif len(row[5]) != 0:          # Errors and exits if the TTL is not a decimal value
                    try:
                        row[5] = int(row[5])
                        csv_temp.append(row)
                    except:
                        print("!!!ERROR - The TTL must be a decimal value. Check '{}' in the below entry:\n{}".format(row[5], row))
                elif len(row[5]) == 0:                  # Adds default TTL value if blank
                    row[5] = default_ttl
                    csv_temp.append(row)
                else:
                    csv_temp.append(row)

            # As long as all columns have values creates variables from the CSV to be used by the different modules
            for row in csv_temp:
                if all(0 != len(s) for s in row[:4]):
                    # DHCP: Creates a list of dicts with key:scope, value:(ip, dom and mac) - also makes sure mac and domain are lowercase
                    csv_dhcp_output.append({row[0]: (row[1], row[2].lower(), row[3].lower())})
                    # DNS_FW: Creates a list of dicts with key:DNS_forward_zone, value: (ip, name_no_domain. ttl)
                    csv_dns_fw_output.append({'.'.join(row[2].lower().split('.')[1:]): (row[1], row[2].lower().split('.')[:1][0], row[5])})
                    # DNS_RV: Creates a list of [IP/mask, name + .]
                    self.csv_dns_rv_output1.append([row[1] + '/' + row[0].split('/')[1], row[2].lower() + '.', row[5]])
                else:                                   # If any column is empty script fails
                    print("!!!ERROR - The CSV is in invalid, check for empty columns and rerun")
                    exit()

        return csv_dhcp_output, csv_dns_fw_output, self.csv_dns_rv_output1                           # Used for pytest

# 3. Make sure that the details in the CSV are in a valid correct format, if not ends the script fails
    def verify(self):
        scope_error, ip_error, dom_error, mac_error, ip_in_net_error = ([] for i in range(5))    # Lists to store invalid elements

        # Validates the CSV contents are valid, creating lists of non-valid elements
        for x in csv_dhcp_output:
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

################# Creates the data model for DNS reverse lookup zone #################
    # 4. From the scope and prefix, creates the the reverse lookup and host address list of dict key:reverse_zone value:(host_ip, name)
    def dns_rv(self):
        global csv_dns_rv_output
        csv_dns_rv_output = []
        for entry in self.csv_dns_rv_output1:
            net, host = ([] for i in range(2))
            #NETWORK: Get network address, split each octet up and remove the prefix
            net1 = re.split('\.|/', str(ip_network(entry[0], strict=False)))
            #HOST: Split each octet up and remove the prefix
            host1 = re.split('\.|/', entry[0])
            # Dependant on the prefix length createss the reverse lookup zone and host address octets
            if int(net1[4]) >= 24:
                # reverse lookup zone created by adding first 3 octets in reverse order
                net.append('.'.join([net1[2], net1[1], net1[0], 'in-addr.arpa']))
                # From the difference between (abs) 4th octet network and host address gets host address (just 1 octet)
                host.append(str(abs(int(net1[3])-int(host1[3]))))
            elif int(net1[4]) >= 16:
                net.append('.'.join([net1[1], net1[0], 'in-addr.arpa']))
                host.append('.'.join([str(abs(int(net1[2])-int(host1[2]))), str(abs(int(net1[3])-int(host1[3])))]))
            elif int(net1[4]) >= 8:
                net.append('.'.join([net1[0], 'in-addr.arpa']))
                host.append('.'.join([str(abs(int(net1[1])-int(host1[1]))), str(abs(int(net1[2])-int(host1[2]))), str(abs(int(net1[3])-int(host1[3])))]))
            csv_dns_rv_output.append({net[0]: (host[0], entry[1])})
        return csv_dns_rv_output

################# Creates new data model used in pre_post_checks script to check if entry already exists #################

# 5. Combines DMs into a dictionary to group similar elements:
# DHCP - key:scopes, values:(ip, name, mac)
# DNS_FW - key:domain, values:(ip_addr, name, ttl)
# DNS_RV - key:reverse_zone, values:(host_ip, name, ttl)
    def make_data_model(self, csv_dm_input):
        global csv_dm                   # New DM that wll be used in pre_post_checks
        csv_dm = []
        csv_dm1 = defaultdict(list)      # Temp defaultdict list. Has to be defaultdict or will fail if key is not found in the dictionary
        # Creates 1 big dictionary of the new data model (rather than being list of dicts per scope)
        for x in csv_dm_input:
            for key, value in x.items():
                csv_dm1[key].append(value)          # Removes duplicate keys, although dont know how?
        # Splits the 1 big dictionary into a list different dictionaries, removes the prefix and creates list of scopes
        for (k,v) in csv_dm1.items():
            if '/' in k:                            # To remove prefix from DHCP scopes
                k = k.split('/')[0]
            csv_dm.append({k:v})
        return csv_dm

################# Get login details and main menu from which tasks are run #################

class Main_menu():
    def __init__(self, csv_dhcp_dm, csv_dns_fw_dm, csv_dns_rv_dm):
        self.csv_dhcp_dm = csv_dhcp_dm
        self.csv_dns_fw_dm = csv_dns_fw_dm
        self.csv_dns_rv_dm = csv_dns_rv_dm

    # 6. Collects login detais and tests that they are correct Assumed if works on one device will work on all
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

    # 7. Main menu. The options user can select which will run the required tasks in other (imported) scripts
    def task(self):
        self.complete = True                 # Kills the loop for login
        print('''
What type of task is being performed?
1. Add DHCP Entry
2. Delete DHCP entry
3. Add DNS Entry
4. Delete DNS entry
5. Add DHCP & DNS Entry
6. Delete DHCP & DNS entry
''')
        task = input("Enter a number: ")
        print()
        while True:
            if task == '1':
                type = 'add'
                self.task_dhcp(type)
            elif task == '2':
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


################# TASKS - runs external modules #################

    # def task_dhcp_add(self, type):
        # dhcp = Dhcp(dhcp_svr, self.user, self.password, self.csv_dm)
    #     # dns = Dns(dns_svr, user, password, self.csv_dm)
    #     # Fails if Scopes or Domains do not exist
    #     dhcp_failfast = dhcp.failfast()
    #     dns_failfast = None     # change to when DNS is done dns.failfast()
    #     if dhcp_failfast != None or dns_failfast != None:
    #         print(dhcp_failfast, '\n', dns_failfast)
    #         exit()
    #     # Fails if any of the new reservations or DNS entries already exist
    #     dhcp_verify_pre = dhcp.verify()
    #     dns_verify_pre = {'DNS': []}     # change to when DNS is done dns.verify()
    #     if len(dhcp_verify_pre[1]['DHCP']) != 0 or len(dns_verify_pre['DNS']) != 0:
    #         print("!!! Error - These entries already exist, you must delete the duplicates before can run the script.")
    #         pprint(dhcp_verify_pre[1])
    #         pprint(dns_verify_pre)
    #         exit()
    #     # Create DHCP entries and verify
    #     dhcp_create = dhcp.create(csv_file, type, temp_csv, win_dir)
    #     # Error handling based on the DHCP cmds run
    #     if dhcp_create[1] is True:
    #         "!!! Warning - Was maybe an issue with the config commands sent to the DHCP server."
    #     if dhcp_create[2] != 0:
    #         "!!! Error - Was maybe an issue with the reservations/ CSV file sent to the DHCP server."
    #     # Verification and error handling based current entries on DHCP server
    #     dhcp_verify_post = dhcp.verify()
    #     print("Check and confirm the numbers below add up.")
    #     print("Num Entries in CSV: {}, Num Reservations Before: {}, Num Reservations After: {}".format(dhcp_create[0], dhcp_verify_pre[0], dhcp_verify_post[0]))
    #     if len(dhcp_verify_post[2]) != 0:
    #         print("!!! Error - the following new DHCP reservations are missing on the DHCP server")
    #         pprint(dhcp_verify_post[2])
    #     else:
    #         print("The script has verified all IP addresses in the CSV are now DHCP reservations.")
    #     exit()

    def task_dhcp(self, type):
        dhcp = Dhcp(dhcp_svr, self.user, self.password, self.csv_dhcp_dm)
        # Fails if Scopes or Domains do not exist
        dhcp_failfast = dhcp.failfast()
        if dhcp_failfast != None:
            print(dhcp_failfast)
            exit()

        # Fails if any of the reservations exist ('add') or dont already exist ('remove')
        dhcp_dm = dhcp.get_resv()
        dhcp_verify_pre = dhcp.verify_csv_vs_dhcp(dhcp_dm)
        if type == 'add':
            if len(dhcp_verify_pre['used_reserv']) != 0:    # List of CSV entries that are currently in DHCP should be 0
                print("!!! Error - These entries already exist, you must delete the duplicates before can run the script.")
                pprint(dhcp_verify_pre['used_reserv'])
                exit()
        elif type == 'remove':
            if len(dhcp_verify_pre['missing_resv']) != 0:       # List of CSV entires missing from DHCP server should be 0
                print("!!! Error - These entries do not exist, you must remove from CSV before you can run the script.")
                pprint(dhcp_verify_pre['missing_resv'])
                exit()

        # Add or remove DHCP entires and verify outcome is as expected compared with DHCP state before the change
        error = 'NO'
        dhcp.create_new_csv(csv_file, temp_csv)
        dhcp_create = dhcp.deploy_csv(type, temp_csv, win_dir)
        if dhcp_create[1] is True:          # Error handling based on output returned from DHCP server
            "!!! Warning - Was maybe an issue with the config commands sent to the DHCP server."
        if dhcp_create[2] != 0:             # Error handling based on output returned from DHCP server
            "!!! Warning - Was maybe an issue with the reservations/ CSV file sent to the DHCP server."
        # Verification that all reservations have been added ('add') or removed('remove')
        dhcp_dm = dhcp.get_resv()
        dhcp_verify_post = dhcp.verify_csv_vs_dhcp(dhcp_dm)
        print("DHCP: Check and confirm the numbers below add up to what you would expect.")
        print("DHCP: Num Entries in CSV: {}, Num Reservations Before: {}, Num Reservations After: {}".format(dhcp_create[0], dhcp_verify_pre['len_csv'], dhcp_verify_post['len_csv']))
        if type == 'add':
            if len(dhcp_verify_post['missing_resv']) != 0:       # Checking (by IP) number CSV entires missing from DHCP server is 0
                print("!!! Warning - The following new DHCP reservations are missing from the DHCP server, check the DHCP server.")
                pprint(dhcp_verify_post['missing_resv'])
                error = 'YES'
        elif type == 'remove':
            if len(dhcp_verify_post['missing_resv']) != dhcp_create[0]:      # Number of missing entires (by IP) on DHCP server should equal number in CSV
                print("!!! Error - The following DHCP reservations are still used on the DHCP server, check the DHCP server.")
                pprint(dhcp_verify_post['missing_resv'])
                error = 'YES'

        if error == 'NO':
            print("DHCP server transaction completed successfully")
            exit()




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
    # Runs function 4 to create reverse lookup DM format from CSV data
    validation.dns_rv()

    # Runs function 5 to create the new combineed  dictionary DMs for DHCP and DNS that are used for pre/post checks
    csv_dhcp_dm = validation.make_data_model(csv_dhcp_output)
    csv_dns_fw_dm = validation.make_data_model(csv_dns_fw_output)
    csv_dns_rv_dm = validation.make_data_model(csv_dns_rv_output)

    # Runs function 6 and 7 to get logon credentails and load main menu
    tasks = Main_menu(csv_dhcp_dm, csv_dns_fw_dm, csv_dns_rv_dm)
    tasks.login()




if __name__ == '__main__':
    main()



# To do in pytests
# read_csv now returning 3 vlaues
# ead_csv test for TTL fail
# Add dns_rv_format to pytests




