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
###################################### Get DHCP reservations ######################################
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

        for csv_dns_rv in self.csv_dns_rv_dm :
            for rev_zone in csv_dns_rv.keys():
                # Get list of all reservations in the scope
                with RunspacePool(self.wsman_conn) as pool:
                    ps = PowerShell(pool)
                    # The powershell cmd is "Get-DhcpServerv4Reservation -scopeid 192.168.200.0"
                    ps.add_cmdlet("Invoke-Expression").add_parameter("Command", "Get-DnsServerResourceRecord -ZoneName {} -RRType PTR".format(rev_zone))
                    ps.add_cmdlet("Out-String").add_parameter("Stream")
                    ps.invoke()
                    dns_rv_records = ps.output


        pprint(dns_fw_records)
        pprint(dns_rv_records)

# dns_fw_records = ['',
#  'HostName                  RecordType Type       Timestamp            '
#  'TimeToLive      RecordData                         ',
#  '--------                  ---------- ----       ---------            '
#  '----------      ----------                         ',
#  '@                         A          1          1/16/2020 7:00:00 AM '
#  '00:10:00        10.30.10.81                        ',
#  'computer1                 A          1          0                    '
#  '01:00:00        10.10.10.1                         ',
#  'dc1                       A          1          0                    '
#  '01:00:00        10.30.10.81                        ',
#  'DomainDnsZones            A          1          1/16/2020 7:00:00 AM '
#  '00:10:00        10.30.10.81                        ',
#  'ForestDnsZones            A          1          1/16/2020 7:00:00 AM '
#  '00:10:00        10.30.10.81                        ',
#  'win10-domain              A          1          11/25/2017 12:00:... '
#  '00:20:00        10.10.20.135                       ',
#  'WIN7-DOMAIN               A          1          11/25/2017 12:00:... '
#  '00:20:00        10.10.20.134                       ',
#  '',
#  '']

# dns_rv_records = ['',
#  'HostName                  RecordType Type       Timestamp            '
#  'TimeToLive      RecordData                         ',
#  '--------                  ---------- ----       ---------            '
#  '----------      ----------                         ',
#  '20.200                    PTR        12         0                    '
#  '01:00:00        ste1.steuniverse.com.              ',
#  '',
#  '']






        #         # From the ps output create a DHCP DM of scope: [[IP], [mac], [name], [(IP, MAC, name)]]
        #         ip_name_mac = []
        #         for r in dhcp_reserv:
        #             ip_name_mac.append((r.split()[0], r.split()[3][:17].lower(), r.split()[2].lower()))
        #         dhcp_dm.append({scope: ip_name_mac})
        # return dhcp_dm




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