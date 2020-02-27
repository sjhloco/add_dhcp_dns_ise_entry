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
from win_dns import Dns

##################################  CSV format ##################################
# ScopeId,IPAddress,Name,ClientId,Description,ttl
# 10.10.10.0/24,10.10.10.10,Computer1.stesworld.com,1a-1b-1c-1d-1e-1f,Reserved for Computer1,00:00:22
# 20.20.20.0/24,20.20.20.11,Computer2.stesworld.com,2a-2b-2c-2d-2e-2f,Reserved for Computer2,

######################## Variables to change dependant on environment ########################
# Where script will look for the csv, by default is the users home directory
directory = expanduser("~")
# list of domain_names expected for DHCP and DNS entries (must be upto last.)
domain_name = ["stesworld.com", "stesworld.co.uk", "example.co.uk", "example.com"]
default_ttl = '01:00:00'      # hh:mm:ss, default is 1 hour

# Servers that the script will run against
dhcp_svr = "10.30.10.81"
dns_svr = "10.30.10.81"
ise_adm = "10.30.10.81"

# Temp files used by DHCP or DNS deployment
temp_csv = os.path.join(directory, 'temp_csv.csv')                  # CSV used to deploy DHCP/DNS
win_dir = os.path.join('C:\\temp', os.path.split(temp_csv)[1])      # Location on DHCP/DNS server csv run from

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
                elif '/' not in row[0]:
                    print("!!!ERROR - The CSV is in invalid, you must have /prefix in the scope column")
                    exit()
                elif len(row) != 6:                     # If there are not 6 columns in every row script fails
                    print("!!!ERROR - The CSV is in invalid, check every row has 6 columns and rerun")
                    exit()
                elif len(row[5]) == 0:                  # Adds default TTL value if blank
                    row[5] = default_ttl
                    csv_temp.append(row)
                else:
                    csv_temp.append(row)

            # As long as all columns have values creates variables from the CSV to be used by the different modules
            for row in csv_temp:
                if all(0 != len(s) for s in row):
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
        scope_error, ip_error, mac_error, ip_in_net_error, all_domains, dom_error, ttl_error, ip_dupl, mac_dupl = ([] for i in range(9))    # Lists to store invalid elements

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
            # Checks if MAC address is in a valid format (xx-xx-xx-xx-xx-xx) with valid characters (0-9, a-f)
            try:
                assert re.match(r'([a-fA-F0-9]{2}-){5}([a-fA-F0-9]{2})', list(x.values())[0][2])
            except:
                mac_error.append(x)
            # Checks the IP address is within the scopes network address
            if len(scope_error) == 0 and len(ip_error) == 0:
                if ip_address(list(x.values())[0][0]) not in ip_network(list(x.keys())[0]):
                    ip_in_net_error.append(list(x.values())[0][0] +  ' not in ' + list(x.keys())[0])
            # Adds all domain names to a list
            domain = '.'.join(list(x.values())[0][1].split('.')[1:])      # Gets everything after first.
            all_domains.append(domain)
        # Checks domain names are in a valid format (ends with domain_name variable) by finding none duplicate elements
        dom_error1 = set(all_domains) - set(domain_name)
        if dom_error1 != 0:
            for x in csv_dhcp_output:
                for y in dom_error1:
                    if y in list(x.values())[0][1]:
                        dom_error.append(x)
        # Checks if TTL is in a valid format (hh:mm:ss) with valid characters (max of 23:59:59)
        for x in csv_dns_fw_output:
            try:
                assert re.match(r'^[0-2][0-3]:[0-5][0-9]:[0-5][0-9]', list(x.values())[0][2])
            except:
                ttl_error.append(x)
        # Checks that there are no duplicate MAC or IP addresses
        for x in csv_dhcp_output:
            ip_dupl.append(list(x.values())[0][0])
            mac_dupl.append(list(x.values())[0][2])
        ip_dupl = set([x for x in ip_dupl if ip_dupl.count(x) > 1])
        mac_dupl = set([x for x in mac_dupl if mac_dupl.count(x) > 1])

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
        if len(ttl_error) != 0:
            print("!!!ERROR - The TTL is not in a valid format, must be hh:mm:ss upto a maximum of 23:59:59 !!!")
            for x in ttl_error:
                print(x)
        if len(ip_dupl) != 0:
            print("!!!ERROR - The following IP addresses have duplicate entries in the CSV !!!")
            for x in ip_dupl:
                print(x)
        if len(mac_dupl) != 0:
            print("!!!ERROR - The following MAC addresses have duplicate entries in the CSV !!!")
            for x in mac_dupl:
                print(x)
        if len(scope_error) != 0 or len(ip_error) != 0 or len(dom_error) != 0 or len(mac_error) != 0 or len(ip_in_net_error) !=0 or len(ttl_error) !=0 or len(ip_dupl) !=0 or len(mac_dupl) !=0:
            exit()

################# Creates the data model for DNS reverse lookup zone #################
    # 4. From the scope and prefix, creates the the reverse lookup and host address list of dict key:reverse_zone value:(host_ip, name)
    def dns_rv(self):
        global csv_dns_rv_output
        csv_dns_rv_output = []
        for entry in self.csv_dns_rv_output1:
            net, host = ([] for i in range(2))
            #NETWORK: Get network address, split each octet up and remove the prefix
            net1 = re.split(r'\.|/', str(ip_network(entry[0], strict=False)))
            #HOST: Split each octet up and remove the prefix
            host1 = re.split(r'\.|/', entry[0])
            # Dependant on the prefix length creates the reverse lookup zone and host address octets
            if int(net1[4]) >= 24:      # 24 or greater
                # reverse lookup zone created by adding first 3 octets in reverse order
                net.append('.'.join([net1[2], net1[1], net1[0], 'in-addr.arpa']))
                host.append(host1[3])
            elif int(net1[4]) >= 16:        # 16 or greater
                net.append('.'.join([net1[1], net1[0], 'in-addr.arpa']))
                host.append('.'.join([host1[3], host1[2]]))
            elif int(net1[4]) >= 8:     # 8 or greater
                net.append('.'.join([net1[0], 'in-addr.arpa']))
                host.append('.'.join([host1[3], host1[2], host1[1]]))
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
    def __init__(self, csv_dhcp_dm, csv_dns_dm):
        self.csv_dhcp_dm = csv_dhcp_dm
        self.csv_dns_dm = csv_dns_dm

    # 6. Collects login detais and tests that they are correct Assumed if works on one device will work on all
    def login(self):
        self.complete = False                        # Used to keep loop going if entered credentials are wrong
        while not self.complete:
            try:
                self.user = input("Enter your username: ")
                self.password = getpass()
                # Test credentials by running simple cmd on the DHCP server
                conn = Client(dhcp_svr, username=self.user, password=self.password,ssl=False)
                conn.execute_cmd('ipconfig')
                self.menu()       # Runs next function (6)

            except Exception as e:              # If login fails loops to begining displaying this error message
                print(e)

    # 7. Main menu. The options user can select which will run the required tasks in other (imported) scripts
    def menu(self):
        self.complete = True                 # Kills the loop for login
        print('''
What type of task is being performed?
1. Add DNS Entry
2. Add DHCP Entry
3. Add DNS and DHCP Entry
4. Delete DNS entry
5. Delete DHCP Entry
6. Delete DHCP & DNS entry
''')
        menu_opt = input("Enter a number: ")
        while True:
            if menu_opt == '1':
                dns_verify_pre = self.task_verify('add', 'DNS')
                self.task_config(dns_verify_pre, 'add', 'DNS')
                break
            elif menu_opt == '2':
                dhcp_verify_pre = self.task_verify('add', 'DHCP')
                self.task_config(dhcp_verify_pre, 'add', 'DHCP')
                break
            elif menu_opt == '3':
                dns_verify_pre = self.task_verify('add', 'DNS')
                dhcp_verify_pre = self.task_verify('add', 'DHCP')
                self.task_config(dns_verify_pre, 'add', 'DNS')
                self.task_config(dhcp_verify_pre, 'add', 'DHCP')
                break
            elif menu_opt == '4':
                dns_verify_pre = self.task_verify('remove', 'DNS')
                self.task_config(dns_verify_pre, 'remove', 'DNS')
                break
            elif menu_opt == '5':
                dhcp_verify_pre = self.task_verify('remove', 'DHCP')
                self.task_config(dhcp_verify_pre, 'remove', 'DHCP')
                break
            elif menu_opt == '6':
                dns_verify_pre = self.task_verify('remove', 'DNS')
                dhcp_verify_pre = self.task_verify('remove', 'DHCP')
                self.task_config(dns_verify_pre, 'remove', 'DNS')
                self.task_config(dhcp_verify_pre, 'remove', 'DHCP')
                break
            else:
                menu_opt = input("Not recognised, enter a valid number: ")

################# TASKS - runs the external modules #################
# Same framework is used to run any of the external modules with the name in the menu_opt used to decide which
# Split into verify and config as want to verify all modules so no configuration doen unless all modules tests pass

    def task_verify(self, task_type, service):
        # Instantizes a module class dependant on the argment passed in from the main menu
        if service == 'DHCP':
            task = Dhcp(dhcp_svr, self.user, self.password, self.csv_dhcp_dm)
        elif service == 'DNS':
            task = Dns(dns_svr, self.user, self.password, self.csv_dns_dm)

        # Fails if DHCP scopes, forward zones or reverse zones do not exist
        print("\n{0} >> Checking the scopes or zones exist on the {0} server...".format(service))
        failfast = task.failfast()
        if failfast != None:
            print(failfast)
            exit()
        # Fails if any of the DHCP reservations or FQDNs exist ('add') or dont already exist ('remove') on DHCP or DNS servers
        print("{0} >> Gathering existing entries from the {0} server...".format(service))
        server_dm = task.get_entries()
        print("{} >> Checking CSV entries against server entries for duplicates...".format(service))
        verify_pre = task.verify_csv_vs_svr(server_dm)
        if task_type == 'add':
            if len(verify_pre['used_entries']) != 0:    # List of CSV entries that are already in scope or zones on server, should be 0
                print("!!! Error - These entries already exist on {} server, you must delete the duplicates before can run the script.".format(service))
                pprint(verify_pre['used_entries'])
                exit()
        elif task_type == 'remove':
            if len(verify_pre['missing_entries']) != 0:       # List of CSV entries that are missing from scope or zones on server, should be 0
                print("!!! Error - These entries do not exist on {} server, you must remove from CSV before you can run the script.".format(service))
                pprint(verify_pre['missing_entries'])
                exit()

        return verify_pre

    def task_config(self, verify_pre, task_type, service):
        # Instantizes a module class dependant on the argment passed in from the main menu
        if service == 'DHCP':
            task = Dhcp(dhcp_svr, self.user, self.password, self.csv_dhcp_dm)
        elif service == 'DNS':
            task = Dns(dns_svr, self.user, self.password, self.csv_dns_dm)

        # Add or remove DHCP or DNS entires
        error = 'NO'
        task.create_new_csv(task_type, csv_file, temp_csv)
        if task_type == 'add':
            print("\n{} >> Adding the new entries...".format(service))
        elif task_type == 'remove':
            print("\n{} >> Removing the entries...".format(service))
        create = task.deploy_csv(task_type, temp_csv, win_dir)
        # Handling of errors returned in output (either error of cmd or error of what cmd tried to do)
        for cmd_err in create[1]:
            if cmd_err is True:
                print("!!! Warning - Possible issues with the configuration commands sent to {} server, investigate the below errors.".format(service))
        for str_err in create[2]:
            if len(str_err) != 0:         # Need this first loop so if more than 1 error the initial warning is only printed once
                error = True
        if error == True:
            print("!!! Warning - Possible issues with entries added/removed on {} server, investigate the below errors.".format(service))
            for str_err in create[2]:
                if len(str_err) != 0:
                    print("\n".join([str(err) for err in str_err]))

        # Verification that all records have been added (task_type = add) or removed (task_type = remove)
        server_dm = task.get_entries()
        verify_post = task.verify_csv_vs_svr(server_dm)
        print("Check and confirm the numbers below add up to what you would expect.")
        if service == 'DNS':
            print("Num A/PTR Entries in CSV: {}, Num Records Before: {}, Num Records After: {}".format(create[0], verify_pre['len_csv'], verify_post['len_csv']))
        elif service == 'DHCP':
            print("Num Entries in CSV: {}, Num Reservations Before: {}, Num Reservations After: {}".format(create[0], verify_pre['len_csv'], verify_post['len_csv']))
        if task_type == 'add':
            if len(verify_post['missing_entries']) != 0:       # The number of CSV entries not on the DHCP/DNS server should be 0, if not lists missing entries
                print("!!! Warning - The following entries should have been added but are not on the {} server, manually check these on the server.".format(service))
                pprint(verify_post['missing_entries'])
                error = 'YES'
        elif task_type == 'remove':
            if len(verify_post['used_entries']) != 0:      #  Should be 0 CSV entries on the DHCP/DNS server, if not lists missing entries
                print("!!! Warning - The following entries should have been deleted but are still on the {} server, manually check these on the server.".format(service))
                pprint(verify_post['used_entries'])
                error = 'YES'

        if error == 'NO':
            print("{} transactions completed successfully. If there was any 'Warning' messages these should be investigated.".format(service))

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

    # # Runs function 5 to create the new combined dictionary DMs for DHCP and DNS that are used for pre/post checks
    csv_dhcp_dm = validation.make_data_model(csv_dhcp_output)
    csv_dns_dm = [validation.make_data_model(csv_dns_fw_output), validation.make_data_model(csv_dns_rv_output)]

    # Runs function 6 and 7 to get logon credentails and load main menu
    tasks = Main_menu(csv_dhcp_dm, csv_dns_dm)
    tasks.login()

if __name__ == '__main__':
    main()


