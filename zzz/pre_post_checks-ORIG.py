from pypsrp.client import Client
from pypsrp.powershell import PowerShell, RunspacePool
from pypsrp.wsman import WSMan
from pprint import pprint
import os
import json
from os.path import expanduser
import csv

class Checks():
    def __init__(self, csv_file, directory, user, password, csv_dm, dhcp_dm, type, dhcp_svr):
        self.directory = directory
        self.csv_file = csv_file
        self.user = user
        self.password = password
        self.csv_dm = csv_dm
        self.dhcp_dm = dhcp_dm
        self.type = type
        self.dhcp_svr = dhcp_server
        # Full paths created from the temp variables names
        self.temp_json = os.path.join(self.directory, temp_json)
        self.temp_csv = os.path.join(self.directory, temp_csv)
        self.win_dir = os.path.join(win_dir, temp_csv)

        # WSman connection used to run powershell cmds on windows servers
        self.wsman_conn = WSMan(self.dhcp_svr, username=self.user, password=self.password, ssl=False)
        self.client_conn = Client(self.dhcp_svr, username=self.user, password=self.password, ssl=False)

###################################### FAILFAST ######################################
    # Check if scopes exist on DHCP server, if DNS zone exists, if ISE group exists if not failfast
    def failfast(self):
        bad_scopes = []
        # Fails if any of the scopes does not exisit on the DHCP server
        for csv_dict in self.csv_dm:
            for scope in csv_dict.keys():
                # Get list of all reservations in the scope
                with RunspacePool(self.wsman_conn) as pool:
                    ps = PowerShell(pool)
                    # The powershell cmd is "Get-DhcpServerv4Reservation -scopeid 192.168.200.0"
                    ps.add_cmdlet("Invoke-Expression").add_parameter("Command", "Get-DhcpServerv4Reservation -scopeid {}".format(scope))
                    ps.add_cmdlet("Out-String").add_parameter("Stream")
                    ps.invoke()
                    dhcp_reserv = ps.output
                if len(dhcp_reserv) != 0:
                    bad_scopes.append(scope)

        if bad_scopes != 0:
            print('!!! Error - These scopes dont exist on the DHCP server: {}'.format(bad_scopes))
            exit()

###################################### DHCP Checks ######################################
    def dhcp(self):
        # On a per-scope gets all the current DHCP addresses that will then be compared to those in the CSV
        for csv_dict in self.csv_dm:
            for scope in csv_dict.keys():
                # Get list of all reservations in the scope
                with RunspacePool(self.wsman_conn) as pool:
                    ps = PowerShell(pool)
                    # The powershell cmd is "Get-DhcpServerv4Reservation -scopeid 192.168.200.0"
                    ps.add_cmdlet("Invoke-Expression").add_parameter("Command", "Get-DhcpServerv4Reservation -scopeid {}".format(scope))
                    ps.add_cmdlet("Out-String").add_parameter("Stream")
                    ps.invoke()
                    dhcp_reserv = ps.output[3:-2]     # Elimates headers and blank lines

                # From the output create DHCP DM of scope: [[IP], [mac], [name], [(IP, MAC, name)]]
                dhcp_ip_name_mac = []
                for r in dhcp_reserv:
                    dhcp_ip_name_mac.append((r.split()[0], r.split()[3][:17].lower(), r.split()[2].lower()))

                self.dhcp_dm.append({scope: dhcp_ip_name_mac})
        self.dhcp_verify()

    def dhcp_verify(self):
        csv_ip, csv_name, csv_mac, dhcp_ip, dhcp_name, dhcp_mac, dhcp_ip_name_mac = ([] for i in range(7))
        #Create a list of IPs, domain names and MACs from each DM
        for dict_scope in self.csv_dm:
            for all_values in dict_scope.values():
                for each_value in all_values:
                    csv_ip.append(each_value[0])
                    csv_name.append(each_value[1][:17])     # Needed as windows limits name returned to 17 characters
                    csv_mac.append(each_value[2])
        for dict_scope in self.dhcp_dm:
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

        dhcp = {'type': self.pre_check, 'num_reserv': (len(dhcp_ip_name_mac)), 'used_reserv': tuple(used_reserv)}
        json.dump(dhcp, open(self.temp_json,'w'))
        return(used_reserv)         # Used by pytest

    def dhcp_reformat_csv(self):
        # Creates a new list from the CSV with prefix removed from the scope
        new_csv = []
        with open(self.csv_file, 'r') as x:
            csv_read = csv.reader(x)
            for row in csv_read:
                if len(row) == 0 or all(0 == len(s) for s in row):      #If it is a blank line skips or all blank columns
                    continue
                else:
                    row[0] = (row[0].split('/')[0])         # Removes prefix from the scope
                    new_csv.append(row)
        # Writes the new list to a temp csv file
        with open(self.temp_csv, 'w') as x:
            writer = csv.writer(x)
            for row in new_csv:
                writer.writerow(row)
        self.dhcp_create()

    def dhcp_create(self):
        # Copy the new CSV File onto DHCP server, script will fail if it cant !!! Possibly give user option to rectify
        try:
            self.client_conn.copy(self.temp_csv, self.win_dir)
        except Exception as e:              # If login fails loops to begining displaying this error message
            print("!!! Error - Could not copy CSV file to DHCP server, investigate the below error before rerunning the script.\n{}".format(e))
            exit()
        # Import the DHCP entries
        with RunspacePool(self.wsman_conn) as pool:
            ps = PowerShell(pool)
            # Import-Csv -Path "C:\tools\ap-reservation.csv" | Add-DhcpServerv4Reservation
            ps.add_cmdlet("Import-Csv").add_argument("{}".format(self.win_dir)).add_cmdlet("Add-DhcpServerv4Reservation")
            ps.invoke()
        dhcp1 = {'type': self.pre_check, 'config_error': ps.had_errors, 'resv_error': ps.streams.error}
        json.dump(dhcp1, open(self.temp_json,'a'))

        self.dhcp()








# directory = expanduser("~")
# csv_file = os.path.join(directory, 'test.csv')
# user = "Administrator"
# password = "mango12!"
# csv_dm = [{'10.10.10.0': [('10.10.10.1', 'computer1.stesworld.com', '1a-1b-1c-1d-1e-1f'), ('10.10.10.3', 'computer3.stesworld.com', '3a-3b-3c-3d-3e-3f'), ('10.10.10.5', 'computer5.stesworld.com', '5a-5b-5c-5d-5e-5f')]},
#           {'20.20.20.0': [('20.20.20.2', 'computer2.stesworld.com', '2a-2b-2c-2d-2e-2f'), ('20.20.20.4', 'computer4.stesworld.com', '4a-4b-4c-4d-4e-4f'), ('20.20.20.8', 'computer8.stesworld.com', '8a-8b-8c-8d-8e-8f')]},
#           {'30.30.30.0': [('30.30.30.6', 'computer6.stesworld.com', '6a-6b-6c-6d-6e-6f'), ('30.30.30.7', 'computer7.stesworld.com', '7a-7b-7c-7d-7e-7f')]}]
# dhcp_dm = [{'10.10.10.0': [('10.10.10.5', 'computer5.steswor', '5a-5b-5c-5d-5e-5f'), ('10.10.10.10', 'computer10.steswo', '1f-1f-1f-1f-1f-1f')]},
#            {'20.20.20.0': [('20.20.20.4', 'computer4.steswor', '4a-4b-4c-4d-4e-4f'), ('20.20.20.10', 'computer20.steswo', '1e-1e-1e-1e-1e-1e')]},
#            {'30.30.30.0': [('30.30.30.6', 'computer6.steswor', '6a-6b-6c-6d-6e-6f'), ('30.30.30.10', 'computer30.steswo', '1d-1d-1d-1d-1d-1d')]}]
# pre_check = True
# dhcp_server = "10.30.10.81"
# dns_server = "10.30.10.81"
# ise_admin = "10.30.10.81"

# servers = {'dhcp': dhcp_server, 'dns': dns_server, 'ise': ise_admin }







# test = Checks(csv_file, directory, user, password, csv_dm, dhcp_dm, pre_check, servers)
# test.dhcp_create()

# test.dhcp_reformat_csv()
# # test.dhcp()
# test.dhcp_verify()



