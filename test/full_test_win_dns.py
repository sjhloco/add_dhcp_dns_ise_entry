# This isnt run as part of pytest, is run independantly as need to the following setup in the DNS server
# FW zones: example.com, example.co.uk, RV Zones: 255.255.10.in-addr-arpa, 254.255.10.in-addr-arpa

# When running use --show-capture=no to stop warning messages. For example: pytest test/full_test_win_dns.py --show-capture=no -vv

import os
import pytest
from win_dns import Dns

################# Variables to change dependant on environment #################
csv_dns_dm = [[{'example.com': [('10.255.255.11', 'computer11', '01:00:00'),
                                ('10.255.255.12', 'computer12', '01:00:00')]},
               {'example.co.uk': [('10.255.254.30', 'computer30', '01:00:00'),
                                  ('10.255.254.31', 'computer31', '01:00:00')]}],
                [{'255.255.10.in-addr.arpa': [('11', 'computer11.example.com.'),
                                              ('12', 'computer12.example.com.')]},
                 {'254.255.10.in-addr.arpa': [('30', 'computer30.example.co.uk.'),
                                              ('31', 'computer31.example.co.uk.')]}]]

temp_csv = os.path.join(os.path.dirname(__file__), 'csv_files', 'temp_csv.csv')
win_dir = os.path.join('C:\\temp', os.path.split(temp_csv)[1])
csv_file = None

# DNS server that is being tested against
dns_svr = "10.30.10.81"
user = 'ste'
password = 'pa55w0rd!'

def test_failfast(capsys):
    # Needs its own DMs as replicates missing scopes and DNS zones
    csv_dns_dm = [[{'example.com': [('10.255.99.11', 'computer11', '01:00:00')]},
                   {'example.co.uk': [('10.255.254.30', 'computer30', '01:00:00'),
                                      ('10.255.254.31', 'computer31', '01:00:00')]}],
                   [{'99.255.10.in-addr.arpa': [('11', 'computer11.example.com.')]},
                   {'254.255.10.in-addr.arpa': [('30', 'computer30.example.co.uk.')]}]]
    test = Dns(dns_svr, user, password, csv_dns_dm)
    try:
        failed = test.failfast()
    except SystemExit:
        pass
    assert capsys.readouterr().out == ('- example.com\n' '- example.co.uk\n' '- 99.255.10.in-addr.arpa\n' '- 254.255.10.in-addr.arpa\n'
                                      ), 'Error with printing DNS failfast scopes'
    assert failed == ('!!! Error - The following zones dont exist on the DNS server: \n' "['99.255.10.in-addr.arpa']"
                     ), 'Error testing whether the DNS zones exist on the DHCP server'

def test_verify_pre():
    test = Dns(dns_svr, user, password, csv_dns_dm)
    server_dm = test.get_entries()
    verify_pre = test.verify_csv_vs_svr(server_dm)
    assert verify_pre == {'len_csv': '0/0',
                          'missing_entries': [('example.co.uk', 'computer30.example.co.uk'),
                                              ('example.co.uk', 'computer31.example.co.uk'),
                                              ('example.com', 'computer11.example.com'),
                                              ('example.com', 'computer12.example.com'),
                                              ('254.255.10.in-addr.arpa', 'computer30.example.co.uk.'),
                                              ('254.255.10.in-addr.arpa', 'computer31.example.co.uk.'),
                                              ('255.255.10.in-addr.arpa', 'computer11.example.com.'),
                                              ('255.255.10.in-addr.arpa', 'computer12.example.com.')],
                          'used_entries': []}, "Error gathering and comparing DNS server entries agaisnt CSV entries (pre-verify)"

def test_create():
    type = 'add'
    test = Dns(dns_svr, user, password, csv_dns_dm)
    test.create_new_csv(type, csv_file, temp_csv)
    output = test.deploy_csv(type, temp_csv, win_dir)
    assert output == ['4/4', [False], [[]]], 'Error creating the DNS entries on the server'

def test_verify_post():
    test = Dns(dns_svr, user, password, csv_dns_dm)
    server_dm = test.get_entries()
    verify_post = test.verify_csv_vs_svr(server_dm)
    assert verify_post == {'len_csv': '4/4',
                           'missing_entries': [],
                           'used_entries': [('example.co.uk', 'computer30.example.co.uk'),
                                            ('example.co.uk', 'computer31.example.co.uk'),
                                            ('example.com', 'computer11.example.com'),
                                            ('example.com', 'computer12.example.com'),
                                            ('254.255.10.in-addr.arpa', 'computer30.example.co.uk.'),
                                            ('254.255.10.in-addr.arpa', 'computer31.example.co.uk.'),
                                            ('255.255.10.in-addr.arpa', 'computer11.example.com.'),
                                            ('255.255.10.in-addr.arpa', 'computer12.example.com.')]
                                            }, "Error gathering and comparing DNS server entries agaisnt CSV entries (post-verify)"

def test_delete():
    type = 'remove'
    test = Dns(dns_svr, user, password, csv_dns_dm)
    test.create_new_csv(type, csv_file, temp_csv)
    output = test.deploy_csv(type, temp_csv, win_dir)
    assert output == ['4/4', [False, False], [[], []]], 'Error deleting the DNS entries from the server'