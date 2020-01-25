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
    # Check if scopes exist on DHCP server
    def failfast(self):
        pass
###################################### Get DNS reservations ######################################
    def get_record(self):
        dns_fw_dm, dns_rv_dm = ([] for i in range(2))

        # On a per-scope gets all the current DHCP addresses that will then be compared to those in the CSV
        for csv_dns_fw in self.csv_dns_fw_dm :
            for domain in csv_dns_fw.keys():
                # Get list of all reservations in the scope
                with RunspacePool(self.wsman_conn) as pool:
                    ps = PowerShell(pool)
                    # The powershell cmd is "Get-DhcpServerv4Reservation -scopeid 192.168.200.0"
                    ps.add_cmdlet("Invoke-Expression").add_parameter("Command", "Get-DnsServerResourceRecord -ZoneName {} -RRType A".format(domain))
                    ps.add_cmdlet("Out-String").add_parameter("Stream")
                    ps.invoke()
                    dns_fw_records = ps.output

                # From the ps output create a list for the dns_fw DM dict value [('ip', 'name', ttl)]
                ip_name_ttl = []
                if len(dns_fw_records) == 0:                # creates dummy objects if no entries in the rv zone
                    ip_name_ttl.append(('dummy', 'dummy'))
                else:
                    for a in dns_fw_records[4:-2]:          # Elimates headers and trailing blank lines
                        a = a.split()
                        ip_name_ttl .append((a[-1], a[0].lower(), a[-2]))
                    # Add the list as the value for for a dict where the zone name is the key [{fw_zone: [(ip, name, ttl)]}]
                    dns_fw_dm.append({domain: ip_name_ttl})

        for csv_dns_rv in self.csv_dns_rv_dm:
            for rev_zone in csv_dns_rv.keys():
                # Get list of all reservations in the scope
                with RunspacePool(self.wsman_conn) as pool:
                    ps = PowerShell(pool)
                    # The powershell cmd is "Get-DhcpServerv4Reservation -scopeid 192.168.200.0"
                    ps.add_cmdlet("Invoke-Expression").add_parameter("Command", "Get-DnsServerResourceRecord -ZoneName {} -RRType PTR".format(rev_zone))
                    ps.add_cmdlet("Out-String").add_parameter("Stream")
                    ps.invoke()
                    dns_rv_records = ps.output

                    # From the ps output create a list for the dns_rv DM dict value [(host, domain_name)]
                    hst_name = []
                    if len(dns_rv_records) == 0:    # creates dummy objects if no entries in the rv zone
                        hst_name.append(('dummy', 'dummy'))
                    else:
                        for ptr in dns_rv_records[3:-2]:        # Elimates headers and trailing blank lines
                            ptr = ptr.split()
                            hst_name.append((ptr[0], ptr[-1].lower()))
                    # Add the list as the value for for a dict where the rv_zone name is the key [{rv_zone: [(host, domain_name)]}]
                    dns_rv_dm.append({rev_zone: hst_name})

        pprint(dns_rv_dm)
        pprint(dns_fw_dm)

###################################### Compare new Vs current resv ######################################
    def verify_csv_vs_dhcp(self, dhcp_dm):
        pass

###################################### Creates new CSV with no scope prefix  ######################################
    def create_new_csv(self,csv_file, temp_csv):
        pass

###################################### Adds or Removes the DHCP reservations ######################################
    def deploy_csv(self, type, temp_csv, win_dir):
        pass

######################################################### TESTING #########################################################

dns_svr = "10.30.10.81"
user = "ste"
password = "pa55w0rd!"
csv_dns_fw_dm = [{'stesworld.com': [('10.10.10.43', 'computer43', 3600),
                                ('20.20.20.44', 'computer44', 3600),
                                ('10.10.10.45', 'computer45', 3600),
                                ('172.16.48.5', 'computer46', 3600)]}]




csv_dns_rv_dm = [{'10.10.10.in-addr.arpa': [('43', 'computer43.stesworld.com.'),
                                        ('45', 'computer45.stesworld.com.')]},
             {'20.20.20.in-addr.arpa': [('44', 'computer44.stesworld.com.')]},
             {'16.172.in-addr.arpa': [('16.5', 'computer46.stesworld.com.')]}]
# csv_file = "/Users/mucholoco/test.csv"
# type = "add"
# temp_csv = "/Users/mucholoco/temp_csv.csv"
# win_dir = os.path.join('C:\\temp', os.path.split(temp_csv)[1])

dns = Dns(dns_svr, user, password, csv_dns_fw_dm, csv_dns_rv_dm)
dns.get_record()
# create(csv_file, type, temp_csv, win_dir)
