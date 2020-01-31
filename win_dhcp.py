#!/usr/bin/env python

from pypsrp.client import Client
from pypsrp.powershell import PowerShell, RunspacePool
from pypsrp.wsman import WSMan
from pprint import pprint
import os
from os.path import expanduser
import csv

class Dhcp():
    def __init__(self, dhcp_svr, user, password, csv_dhcp_dm):
        self.dhcp_svr = dhcp_svr
        self.user = user
        self.password = password
        self.csv_dhcp_dm = csv_dhcp_dm

        # WSman connection used to run powershell cmds on windows servers
        self.wsman_conn = WSMan(self.dhcp_svr, username=self.user, password=self.password, ssl=False)
        self.client_conn = Client(self.dhcp_svr, username=self.user, password=self.password, ssl=False)

###################################### FAILFAST ######################################
    # Check if scopes exist on DHCP server
    def failfast(self):
        bad_scopes = []
        for csv_dict in self.csv_dhcp_dm:
            for scope in csv_dict.keys():
                print('-',scope)
                # Get list of all reservations in the scope
                with RunspacePool(self.wsman_conn) as pool:
                    ps = PowerShell(pool)
                    # The powershell cmd is "Get-DhcpServerv4Reservation -scopeid 192.168.200.0"
                    ps.add_cmdlet("Invoke-Expression").add_parameter("Command", "Get-DhcpServerv4Scope -scopeid {}".format(scope))
                    ps.add_cmdlet("Out-String").add_parameter("Stream")
                    ps.invoke()
                    dhcp_reserv = ps.output

                if len(dhcp_reserv) == 0:
                    bad_scopes.append(scope)
        # If any of the scopes dont not exist values are returned to main.py (which also casues script to exit)
        if len(bad_scopes) != 0:
            return '!!! Error - The following scopes dont exist on the DHCP server: \n{}'.format(bad_scopes)

###################################### Get DHCP reservations ######################################
    def get_entries(self):
        dhcp_dm = []
        # On a per-scope gets all the current DHCP addresses that will then be compared to those in the CSV
        for csv_dict in self.csv_dhcp_dm:
            for scope in csv_dict.keys():
                # Get list of all reservations in the scope
                with RunspacePool(self.wsman_conn) as pool:
                    ps = PowerShell(pool)
                    # The powershell cmd is "Get-DhcpServerv4Reservation -scopeid 192.168.200.0"
                    ps.add_cmdlet("Invoke-Expression").add_parameter("Command", "Get-DhcpServerv4Reservation -scopeid {}".format(scope))
                    ps.add_cmdlet("Out-String").add_parameter("Stream")
                    ps.invoke()
                    dhcp_reserv = ps.output[3:-2]     # Elimates headers and blank lines

                # From the ps output create a DHCP DM of scope: [[IP], [mac], [name], [(IP, MAC, name)]]
                ip_name_mac = []
                if len(dhcp_reserv) == 0:                # skips if no DHCP reservations in the scope
                    pass
                else:
                    for r in dhcp_reserv:
                        ip_name_mac.append((r.split()[0], r.split()[3][:17].lower(), r.split()[2].lower()))
                    dhcp_dm.append({scope: ip_name_mac})
        return dhcp_dm

###################################### Compare new Vs current resv ######################################
    def verify_csv_vs_svr(self, dhcp_dm):
        csv_ip, csv_name, csv_mac, dhcp_ip, dhcp_name, dhcp_mac, dhcp_ip_name_mac = ([] for i in range(7))
        #Create a list of IPs, domain names and MACs from each DM (CSV and from dhcp_srv)
        for dict_scope in self.csv_dhcp_dm:
            for all_values in dict_scope.values():
                for each_value in all_values:
                    csv_ip.append(each_value[0])
                    csv_name.append(each_value[1][:17])     # Needed as windows limits name returned to 17 characters
                    csv_mac.append(each_value[2])
        for dict_scope in dhcp_dm:
            for all_values in dict_scope.values():
                for each_value in all_values:
                    dhcp_ip.append(each_value[0])
                    dhcp_name.append(each_value[1])
                    dhcp_mac.append(each_value[2])
                    dhcp_ip_name_mac.append(each_value)     # Used in user output if conflicts

        # Create list of any already used IPs, names or macs in reservations by removing any unique values
        used_ipadd = set(csv_ip) & set(dhcp_ip)
        used_name = set(csv_name) & set(dhcp_name)
        used_mac = set(dhcp_mac) & set(csv_mac)

        # Creates a list of all used reservations by finding it based on IP, name and mac in original DHCP reservations variable
        list_from_ip, list_from_name, list_from_mac = ([] for i in range(3))
        if used_ipadd != 0:
            for x in used_ipadd:
                for y in dhcp_ip_name_mac:
                    if x == y[0]:
                        list_from_ip.append(y)
        if used_name != 0:
            for x in used_name:
                for y in dhcp_ip_name_mac:
                    if x == y[1]:
                        list_from_name.append(y)
        if used_mac != 0:
            for x in used_mac:
                for y in dhcp_ip_name_mac:
                    if x == y[2]:
                        list_from_mac.append(y)
        # Creates a final list of used reservations removing any duplicates from the ip, name and mac lists
        used_reserv = set(list_from_ip) | set(list_from_name) | set(list_from_mac)
        # Compares IPs in CSV to IPs on DHCP server, will list any in the CSV that are missing from DHCP server
        missing_resv = set(csv_ip) - set(dhcp_ip)

        # What is returned to main.py to kill script if any duplicates. len(csv_name) is used to compare pre and post number of entries
        output = {'len_csv': len(dhcp_ip_name_mac), 'used_entries': sorted(list(used_reserv)), 'missing_entries': sorted(list(missing_resv))}
        return output

###################################### Creates new CSV with no scope prefix  ######################################
    def create_new_csv(self, type, csv_file, temp_csv):
        # # Creates a new list from the CSV with prefix removed from the scope
        new_csv = []
        with open(csv_file, 'r') as x:
            csv_read = csv.reader(x)
            for row in csv_read:
                if len(row) == 0 or all(0 == len(s) for s in row):      #If it is a blank line skips or all blank columns
                    continue
                else:
                    row[0] = (row[0].split('/')[0])         # Removes prefix from the scope
                    new_csv.append(row)
        self.num_new_entries = len(new_csv) - 1                  # Number of reservatiosn to be added
        # Writes the new list to a temp csv file
        with open(temp_csv, 'w') as x:
            writer = csv.writer(x)
            for row in new_csv:
                writer.writerow(row)

        # Used only with pytest to test new CSV file created and the contents are correct
        pytest_csv = []
        with open(temp_csv, 'r') as x:
            csv_read = csv.reader(x)
            for row in csv_read:
                pytest_csv.append(row)
        return pytest_csv

###################################### Adds or Removes the DHCP reservations ######################################
    def deploy_csv(self, type, temp_csv, win_dir):
        # Copy the new CSV File onto DHCP server, script will fail if it cant
        try:
            self.client_conn.copy(temp_csv, win_dir)
        except Exception as e:                  # If copy fails script fails
            print("!!! Error - Could not copy CSV file to DHCP server, investigate the below error before re-running the script.\n{}".format(e))
            exit()

        # Add or remove DHCP entries dependant on the value of the variable 'type'
        with RunspacePool(self.wsman_conn) as pool:
            ps = PowerShell(pool)
            if type == 'add':
                ps.add_cmdlet("Import-Csv").add_argument("{}".format(win_dir)).add_cmdlet("Add-DhcpServerv4Reservation")
            elif type == 'remove':
                ps.add_cmdlet("Import-Csv").add_argument("{}".format(win_dir)).add_cmdlet("Remove-DhcpServerv4Reservation")
            ps.invoke()
        output = [self.num_new_entries, [ps.had_errors], [ps.streams.error]]

        # Cleanup temp files
        os.remove(temp_csv)
        try:
            self.client_conn.execute_cmd("del {}".format(win_dir.replace("/", "\\")))      # Windows wont take / format with the cmd
        except Exception as e:              # If delete fails warns user
            print("!!! Warning - Could not delete temporary file {} off DHCP server, you will have to do manually.\n{}".format(win_dir, e))

        return output
