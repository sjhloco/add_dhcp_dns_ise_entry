#!/usr/bin/env python

import csv
import os
from pprint import pprint


class Dns():
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

###################################### Get DHCP reservations ######################################
    def get_resv(self):

###################################### Compare new Vs current resv ######################################
    def verify_csv_vs_dhcp(self, dhcp_dm):

###################################### Creates new CSV with no scope prefix  ######################################
    def create_new_csv(self,csv_file, temp_csv):

###################################### Adds or Removes the DHCP reservations ######################################
    def deploy_csv(self, type, temp_csv, win_dir):


######################################################### TESTING #########################################################

dns_svr = "10.30.10.81"
 dhcp_svr = "10.30.10.81"
# user = "Administrator"
# password = ""
# csv_dhcp_dm = [{'10.10.10.0': [('10.10.10.1', 'computer1.stesworld.com', '1a-1b-1c-1d-1e-1f'), ('10.10.10.3', 'computer3.stesworld.com', '3a-3b-3c-3d-3e-3f'), ('10.10.10.5', 'computer5.stesworld.com', '5a-5b-5c-5d-5e-5f')]},
#           {'20.20.20.0': [('20.20.20.2', 'computer2.stesworld.com', '2a-2b-2c-2d-2e-2f'), ('20.20.20.4', 'computer4.stesworld.com', '4a-4b-4c-4d-4e-4f'), ('20.20.20.8', 'computer8.stesworld.com', '8a-8b-8c-8d-8e-8f')]},
#           {'30.30.30.0': [('30.30.30.6', 'computer6.stesworld.com', '6a-6b-6c-6d-6e-6f'), ('30.30.30.7', 'computer7.stesworld.com', '7a-7b-7c-7d-7e-7f')]}]
# dhcp_dm = [{'10.10.10.0': [('10.10.10.5', 'computer5.steswor', '5a-5b-5c-5d-5e-5f'), ('10.10.10.10', 'computer10.steswo', '1f-1f-1f-1f-1f-1f')]},
#            {'20.20.20.0': [('20.20.20.4', 'computer4.steswor', '4a-4b-4c-4d-4e-4f'), ('20.20.20.10', 'computer20.steswo', '1e-1e-1e-1e-1e-1e')]},
#            {'30.30.30.0': [('30.30.30.6', 'computer6.steswor', '6a-6b-6c-6d-6e-6f'), ('30.30.30.10', 'computer30.steswo', '1d-1d-1d-1d-1d-1d')]}]
# csv_file = "/Users/mucholoco/test.csv"
# type = "add"
# temp_csv = "/Users/mucholoco/temp_csv.csv"
# win_dir = os.path.join('C:\\temp', os.path.split(temp_csv)[1])

# dhcp = Dhcp(dhcp_svr, user, password, csv_dhcp_dm)
# dhcp.verify(dhcp_dm)
# create(csv_file, type, temp_csv, win_dir)
