#!/usr/bin/env python

from pypsrp.client import Client
from pypsrp.powershell import PowerShell, RunspacePool
from pypsrp.wsman import WSMan
from pprint import pprint
import os
from os.path import expanduser
import csv

class Dns():
    def __init__(self, dns_svr, user, password, csv_dns_fw_dm, csv_dns_rv_dm):
        self.dns_svr = dns_svr
        self.user = user
        self.password = password
        self.csv_dns_fw_dm = csv_dns_fw_dm
        self.csv_dns_rv_dm = csv_dns_rv_dm

        # WSman connection used to run powershell cmds on windows servers
        self.wsman_conn = WSMan(self.dns_svr, username=self.user, password=self.password, ssl=False)
        self.client_conn = Client(self.dns_svr, username=self.user, password=self.password, ssl=False)

###################################### FAILFAST ######################################
    # Check if zones exist on DNS server
    def failfast(self):
        all_zones, bad_zones = ([] for i in range(2))
        # Create combined list of all forward and reverse zones
        for csv_dict in self.csv_dns_fw_dm:
            for zone in csv_dict.keys():
                all_zones.append(zone)
        for csv_dict in self.csv_dns_rv_dm:
            for zone in csv_dict.keys():
                all_zones.append(zone)

    # Interate through all zones and see if exist on DNS server
        for zone in all_zones:
            with RunspacePool(self.wsman_conn) as pool:
                print(zone)
                ps = PowerShell(pool)
                # The powershell cmd is "Get-DhcpServerv4Reservation -scopeid 192.168.200.0"
                ps.add_cmdlet("Invoke-Expression").add_parameter("Command", "Get-DnsServerZone {}".format(zone))
                ps.add_cmdlet("Out-String").add_parameter("Stream")
                ps.invoke()
                dns_zones = ps.output

            if len(dns_zones) == 0:
                bad_zones.append(zone)
        # If any of the scopes dont not exist values are returned to main.py (which also casues script to exit)
        if len(bad_zones) != 0:
            return '!!! Error - These zones dont exist on the DNS server: {}'.format(bad_zones)

###################################### Get DNS reservations ######################################
    def get_record(self):
        dns_fw_dm, dns_rv_dm = ([] for i in range(2))

        # On a per-zone basis gets all the current DNS entries that will then be compared to those in the CSV
        for csv_dns_fw in self.csv_dns_fw_dm :
            for domain in csv_dns_fw.keys():
                with RunspacePool(self.wsman_conn) as pool:
                    ps = PowerShell(pool)
                    # The powershell cmd is "Get-DnsServerResourceRecord -ZoneName stesworld.com -RRType A"
                    ps.add_cmdlet("Invoke-Expression").add_parameter("Command", "Get-DnsServerResourceRecord -ZoneName {} -RRType A".format(domain))
                    ps.add_cmdlet("Out-String").add_parameter("Stream")
                    ps.invoke()
                    dns_fw_records = ps.output

                # From the ps output create a list for the dns_fw DM dict value [('ip', 'name', ttl)]
                ip_name_ttl = []
                if len(dns_fw_records) == 0:                # skips if no A records in the zone
                    pass
                else:
                    for a in dns_fw_records[3:-2]:          # Elimates headers and trailing blank lines
                        a = a.split()
                        ip_name_ttl .append((a[-1], a[0].lower(), a[-2]))
                    # Add the list as the value for for a dict where the zone name is the key [{fw_zone: [(ip, name, ttl)]}]
                    dns_fw_dm.append({domain: ip_name_ttl})

        # On a per-reverse-zone basis gets all the current DNS entries that will then be compared to those in the CSV
        for csv_dns_rv in self.csv_dns_rv_dm:
            for rev_zone in csv_dns_rv.keys():
                with RunspacePool(self.wsman_conn) as pool:
                    ps = PowerShell(pool)
                    ps.add_cmdlet("Invoke-Expression").add_parameter("Command", "Get-DnsServerResourceRecord -ZoneName {} -RRType PTR".format(rev_zone))
                    ps.add_cmdlet("Out-String").add_parameter("Stream")
                    ps.invoke()
                    dns_rv_records = ps.output

                hst_name = []
                if len(dns_rv_records) == 0:    # skips if no PTR records in the zone
                    pass
                else:
                    for ptr in dns_rv_records[3:-2]:
                        ptr = ptr.split()
                        hst_name.append((ptr[0], ptr[-1].lower()))
                dns_rv_dm.append({rev_zone: hst_name})      # creates DM where rv_zone name is the key [{rv_zone: [(host, domain_name)]}]

        return [dns_fw_dm, dns_rv_dm]

###################################### Compare new Vs current resv ######################################
    def verify_csv_vs_dns(self, dns_fw_dm, dns_rv_dm):
        csv_name, csv_rv_name, dns_fw_name, dns_rv_name, used_fw_fqdn, used_rv_fqdn = ([] for i in range(6))
        # Create a list tuples of all FQDNs from CSV DMs (zone, fqdn)
        for dict_domain in self.csv_dns_fw_dm:
            domain = '.' + list(dict_domain.keys())[0]
            for all_values in dict_domain.values():
                for each_value in all_values:
                    csv_name.append((list(dict_domain.keys())[0], each_value[1] + domain))
        for dict_domain in self.csv_dns_rv_dm:
            for all_values in dict_domain.values():
                for each_value in all_values:
                    csv_rv_name.append((list(dict_domain.keys())[0], each_value[1]))

        # Create a list tuples of all FQDNs from DNS DMs (zone, fqdn)
        for dict_domain in dns_fw_dm:
            domain = '.' + list(dict_domain.keys())[0]
            for all_values in dict_domain.values():
                for each_value in all_values:
                    dns_fw_name.append((list(dict_domain.keys())[0], each_value[1] + domain))
        for dict_domain in dns_rv_dm:
            for all_values in dict_domain.values():
                for each_value in all_values:
                    dns_rv_name.append((list(dict_domain.keys())[0], each_value[1]))

        # Create list of any already used FQDNs in DNS by removing any unique values
        used_fw_fqdn = set(csv_name) & set(dns_fw_name)
        used_rv_fqdn = set(csv_rv_name) & set(dns_rv_name)
        used_fqdn = sorted(list(used_fw_fqdn)) + sorted(list(used_rv_fqdn))

        # Compares FQDNs in CSV to FQDNs on DNS server, will list any in the CSV that are missing from DNS server
        missing_fw_fqdn = set(csv_name) - set(dns_fw_name)
        missing_rv_fqdn = set(csv_rv_name) - set(dns_rv_name)
        missing_fqdn = sorted(list(missing_fw_fqdn)) + sorted(list(missing_rv_fqdn))

        # What is returned to main.py to kill script if any duplicates. len(csv_name) is used to compare pre and post number of entries
        len_csv = str(len(dns_fw_name)) + '/' + str(len(dns_rv_name))       # Number of added records in the format A/PTR
        output = {'len_csv': len_csv, 'used_fqdn': used_fqdn, 'missing_fqdn': missing_fqdn}
        return output

###################################### Creates new CSV with no scope prefix  ######################################
    def create_new_csv(self, type, temp_csv):
        self.num_new_entries = 0
        # Creates a temp csv file with header and format compatible with DNS server import.
        if type == 'add':
            with open(temp_csv, 'w') as x:
                writer = csv.writer(x)
                writer.writerow(['ZoneName','Name','IPAddress','TimeToLive'])
                for dict_domain in self.csv_dns_fw_dm:
                    domain = list(dict_domain.keys())[0]
                    for all_values in dict_domain.values():
                        for each_value in all_values:
                            self.num_new_entries += 1                 # Number of reservatiosn to be added
                            writer.writerow([domain,each_value[1],each_value[0],each_value[2]])
        # Dont add header on these as windows ps cmd wont understand 'ZoneName', luckily can do on position number so no need for header.
        elif type == 'remove':
            self.temp_csv1 = temp_csv.replace(".csv", "1.csv")              # Extra temp file required for removing DNS RV entries
            with open(temp_csv, 'w') as x:
                writer = csv.writer(x)
                writer.writerow(['ZoneName','Name', 'RRType'])
                for dict_domain in self.csv_dns_fw_dm:
                    domain = list(dict_domain.keys())[0]
                    for all_values in dict_domain.values():
                        for each_value in all_values:
                            self.num_new_entries += 1                 # Number of reservatiosn to be added
                            writer.writerow([domain,each_value[1],'A'])
            with open(self.temp_csv1, 'w') as x:
                writer = csv.writer(x)
                writer.writerow(['ZoneName','Name', 'RRType'])
                for dict_domain in self.csv_dns_rv_dm:
                    domain = list(dict_domain.keys())[0]
                    for all_values in dict_domain.values():
                        for each_value in all_values:
                            writer.writerow([domain,each_value[0],'PTR'])

        # Used only with pytest to test new CSV file created and the contents are correct
        pytest_csv = []
        with open(temp_csv, 'r') as x:
            csv_read = csv.reader(x)
            for row in csv_read:
                pytest_csv.append(row)
        if type == 'remove':             # To test both CSVs if remove
            pytest_csv1 = []
            with open(self.temp_csv1, 'r') as x:
                csv_read = csv.reader(x)
                for row in csv_read:
                    pytest_csv1.append(row)
            return [pytest_csv, pytest_csv1]
        else:
            return pytest_csv

###################################### Adds or Removes the DHCP reservations ######################################
    def deploy_csv(self, type, temp_csv, win_dir):
        win_dir1 = win_dir.replace(".csv", "1.csv")              # Extra temp file required for removing DNS RV entries
        self.num_new_entries = str(self.num_new_entries) + '/' + str(self.num_new_entries)      # To make it A/PTR records, should be same as deployed in the 1 cmd
        # Copy the new CSV File onto DHCP server, script will fail if it cant
        try:
            self.client_conn.copy(temp_csv, win_dir)
            if type == 'remove':
                self.client_conn.copy(self.temp_csv1, win_dir1)
        except Exception as e:              # If copy fails script fails
            print("!!! Error - Could not copy CSV file to DNS server, investigate the below error before re-running the script.\n{}".format(e))
            exit()

        # Add DNS entries
        if type == 'add':
            with RunspacePool(self.wsman_conn) as pool:
                ps = PowerShell(pool)
                ps.add_cmdlet("Import-Csv").add_argument("{}".format(win_dir)).add_cmdlet("Add-DNSServerResourceRecordA").add_parameter("-CreatePtr")
                ps.invoke()
            output = [self.num_new_entries, [ps.had_errors], [ps.streams.error]]

        # Remove DNS entries, have to spilt into multiple cmds due to bug with "Remove-DNSServerResourceRecord" where cant use RRtype from CSV
        elif type == 'remove':
            with RunspacePool(self.wsman_conn) as pool:
                ps = PowerShell(pool)
                ps.add_cmdlet("Import-Csv").add_argument("{}".format(win_dir)).add_cmdlet("Remove-DNSServerResourceRecord").add_parameter("RRtype", "A").add_parameter("-Force")
                ps.invoke()
            output = [self.num_new_entries, [ps.had_errors], [ps.streams.error]]      # adds the errors as lists so can add outputs from next cmd
            with RunspacePool(self.wsman_conn) as pool:
                ps = PowerShell(pool)
                ps.add_cmdlet("Import-Csv").add_argument("{}".format(win_dir1)).add_cmdlet("Remove-DNSServerResourceRecord").add_parameter("RRtype", "PTR").add_parameter("-Force")
                ps.invoke()
            output[1].append(ps.had_errors)
            output[2].append(ps.streams.error)

        # Cleanup temp files
        try:
            os.remove(temp_csv)
            self.client_conn.execute_cmd("del {}".format(win_dir.replace("/", "\\")))      # Windows wont take / format with the cmd
            if type == 'remove':
                os.remove(self.temp_csv1)
                self.client_conn.execute_cmd("del {}".format(win_dir1.replace("/", "\\")))      # Windows wont take / format with the cmd
        except Exception as e:              # If delete fails warns user
            print("!!! Warning - Could not delete temporary files off DNS server, you will have to do manually.\n{}".format(e))

        return output

######################################################### TESTING #########################################################

# dns_svr = "10.30.10.81"
# user = "ste"
# password = "pa55w0rd!"
# csv_dns_fw_dm = [{'stesworld.com': [('10.10.10.43', 'computer43', '01:00:00'),
#                                 ('20.20.20.44', 'computer44', '01:00:00'),
#                                 ('10.10.10.45', 'computer45', '01:00:00')]},
#                 {'stesworld.co.uk': [('172.16.48.5', 'computer46', '01:00:00')]}]


# csv_dns_rv_dm = [{'10.10.10.in-addr.arpa': [('43', 'computer43.stesworld.com.'),
#                                         ('45', 'computer45.stesworld.com.')]},
#              {'20.20.20.in-addr.arpa': [('44', 'computer44.stesworld.com.')]},
#              {'16.172.in-addr.arpa': [('5.48', 'computer46.stesworld.co.uk.')]}]
# csv_file = "/Users/mucholoco/test_dns.csv"
# type = "add"
# temp_csv = "/Users/mucholoco/temp_csv.csv"
# win_dir = os.path.join('C:\\temp', os.path.split(temp_csv)[1])
# temp_csv1 = "/Users/mucholoco/temp_csv1.csv"
# win_dir1 = os.path.join('C:\\temp', os.path.split(temp_csv1)[1])
# type = 'add'
# # type = 'remove'

# dns = Dns(dns_svr, user, password, csv_dns_fw_dm, csv_dns_rv_dm)
# dns.failfast()
# dns_dm = dns.get_record()
# a = dns.verify_csv_vs_dns(dns_dm[0], dns_dm[1])
# pprint(a)
# dns.create_new_csv(type, temp_csv,temp_csv1)
# dns.deploy_csv(type, temp_csv, win_dir, temp_csv1, win_dir1)

