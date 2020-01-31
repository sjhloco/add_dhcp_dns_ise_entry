# This isnt run as part of pytest, is used indepdantly to check the interactive code agaisnt a windows environment set us as follows:
# DHCP scopes: 10.255.255.0/24, 10.255.254.0/24, domain names: example.com, example.co.uk

# When running use --show-capture=no to stop warning messages. For example: pytest test/full_test_win_dns.py --show-capture=no -vv

import os
import pytest
from win_dhcp import Dhcp

################# Variables to change dependant on environment #################
csv_dhcp_dm = [{'10.255.255.0': [('10.255.255.11', 'computer11.example.com', '1a-1f-1f-1f-1f-1f'),
                                 ('10.255.255.12', 'computer12.example.com', '1b-1f-1f-1f-1f-1f')]},
               {'10.255.254.0': [('10.255.254.30', 'computer30.example.co.uk', '1c-1f-1f-1f-1f-1f'),
                                 ('10.255.254.31', 'computer31.example.co.uk', '1d-1f-1f-1f-1f-1f')]}]

temp_csv = os.path.join(os.path.dirname(__file__), 'csv_files', 'temp_csv.csv')
win_dir = os.path.join('C:\\temp', os.path.split(temp_csv)[1])
csv_file = os.path.join(os.path.dirname(__file__), 'csv_files', 'full_test_win_dhcp.csv')

# DNS server that is being tested against
dhcp_svr = "10.30.10.81"
user = 'ste'
password = 'pa55w0rd!'

def test_failfast(capsys):
    # Need own DMs to replicate missing scopes and DNS zones
    csv_dhcp_dm = [{'10.255.99.0': [('10.10.99.11', 'computer11.example.com', '1a-1f-1f-1f-1f-1f')]},
                   {'10.255.254.0': [('10.255.254.30', 'computer30.example.co.uk', '1b-1f-1f-1f-1f-1f'),
                                     ('10.255.254.31', 'computer31.example.co.uk', '1c-1f-1f-1f-1f-1f')]}]
    test = Dhcp(dhcp_svr, user, password, csv_dhcp_dm)
    try:
        failed = test.failfast()
    except SystemExit:
        pass
    assert capsys.readouterr().out == ('- 10.255.99.0\n- 10.255.254.0\n'), 'Error with printing DNS failfast scopes'
    assert failed == ('!!! Error - The following scopes dont exist on the DHCP server: \n' "['10.255.99.0']"
                     ), 'Error testing whether the DHCP scopes exist on the DHCP server'

def test_verify_pre():
    test = Dhcp(dhcp_svr, user, password, csv_dhcp_dm)
    server_dm = test.get_entries()
    verify_pre = test.verify_csv_vs_svr(server_dm)
    assert verify_pre == {'len_csv': 0,
                          'missing_entries': ['10.255.254.30', '10.255.254.31', '10.255.255.11', '10.255.255.12'],
                          'used_entries': []}, "Error gathering and comparing DHCP server entries agaisnt CSV entries (pre-verify)"

def test_create():
    type = 'add'
    test = Dhcp(dhcp_svr, user, password, csv_dhcp_dm)
    test.create_new_csv(type, csv_file, temp_csv)
    output = test.deploy_csv(type, temp_csv, win_dir)
    assert output == [4, [False], [[]]], 'Error creating the DHCP entries on the server'

def test_verify_post():
    test = Dhcp(dhcp_svr, user, password, csv_dhcp_dm)
    server_dm = test.get_entries()
    verify_post = test.verify_csv_vs_svr(server_dm)
    assert verify_post == {'len_csv': 4,
                           'missing_entries': [],
                           'used_entries': [('10.255.254.30', 'computer30.exampl', '1c-1f-1f-1f-1f-1f'),
                                            ('10.255.254.31', 'computer31.exampl', '1d-1f-1f-1f-1f-1f'),
                                            ('10.255.255.11', 'computer11.exampl', '1a-1f-1f-1f-1f-1f'),
                                            ('10.255.255.12', 'computer12.exampl', '1b-1f-1f-1f-1f-1f')]
                                            }, "Error gathering and comparing DHCP server entries agaisnt CSV entries (post-verify)"

def test_delete():
    type = 'remove'
    test = Dhcp(dhcp_svr, user, password, csv_dhcp_dm)
    test.create_new_csv(type, csv_file, temp_csv)
    output = test.deploy_csv(type, temp_csv, win_dir)
    assert output == [4, [False], [[]]], 'Error deleting the DNS entries from the server'