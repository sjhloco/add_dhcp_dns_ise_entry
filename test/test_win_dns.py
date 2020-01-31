# From the named script import the functions to be tested
from win_dns import Dns
import os

################# Variables to change dependant on environment #################
csv_file = os.path.join(os.path.dirname(__file__), 'csv_files', 'test_csv.csv')
temp_csv = os.path.join(os.path.dirname(__file__), 'csv_files', 'temp_csv.csv')

user = None
password = None
pre_check = None
csv_file = None
dns_svr = '1.1.1.1'

# Using entries that have duplicate elements in different parts of the entries
csv_dns_dm = [[{'stesworld.com': [('10.10.10.43', 'computer43', '01:00:00'),
                                  ('20.20.20.44', 'computer44', '01:00:00'),
                                  ('10.10.10.45', 'computer45', '01:00:00')]},
               {'stesworld.co.uk': [('172.16.48.5', 'computer46', '01:00:00')]}],
             [{'10.10.10.in-addr.arpa': [('43', 'computer43.stesworld.com.'),
                                         ('45', 'computer45.stesworld.com.')]},
              {'20.20.20.in-addr.arpa': [('44', 'computer44.stesworld.com.')]},
              {'16.172.in-addr.arpa': [('5.48', 'computer46.stesworld.co.uk.')]}]]

dns_dm = [[{'stesworld.com': [('10.30.10.81', '@', '00:10:00'),
                              ('10.10.10.43', 'computer43', '01:00:00'),
                              ('20.20.20.54', 'computer54', '01:00:00'),
                              ('10.10.10.55', 'computer55', '01:00:00'),
                              ('10.30.10.81', 'dc1', '01:00:00'),
                              ('10.30.10.81', 'domaindnszones', '00:10:00'),
                              ('10.30.10.81', 'forestdnszones', '00:10:00')]},
            {'stesworld.co.uk': [('172.16.48.5', 'computer46', '01:00:00')]}],
          [{'10.10.10.in-addr.arpa': [('53', 'computer53.stesworld.com.'),
                                      ('45', 'computer45.stesworld.com.')]},
           {'20.20.20.in-addr.arpa': [('44', 'computer44.stesworld.com.')]},
           {'16.172.in-addr.arpa': [('7.48', 'computer47.stesworld.co.uk.')]}]]

def test_verify_csv_vs_svr():
    test = Dns(dns_svr, user, password, csv_dns_dm)
    x = test.verify_csv_vs_svr(dns_dm)

    assert x['len_csv'] == '8/4', 'Error with detected number of used reservations (CSV vs DHCP server)'
    assert x['used_entries'] == [('stesworld.co.uk', 'computer46.stesworld.co.uk'),
                              ('stesworld.com', 'computer43.stesworld.com'),
                              ('10.10.10.in-addr.arpa', 'computer45.stesworld.com.'),
                              ('20.20.20.in-addr.arpa', 'computer44.stesworld.com.')], 'Error with detecting used A/PTR records'
    assert x['missing_entries'] == [('stesworld.com', 'computer44.stesworld.com'),
                                 ('stesworld.com', 'computer45.stesworld.com'),
                                 ('10.10.10.in-addr.arpa', 'computer43.stesworld.com.'),
                                 ('16.172.in-addr.arpa', 'computer46.stesworld.co.uk.')], 'Error with detecting missing A/PTR records'

def test_create_new_csv():
    test = Dns(dns_svr, user, password, csv_dns_dm)
    type = 'add'
    x = test.create_new_csv(type, csv_file, temp_csv)
    assert x == [['ZoneName', 'Name', 'IPAddress', 'TimeToLive'],
                 ['stesworld.com', 'computer43', '10.10.10.43', '01:00:00'],
                 ['stesworld.com', 'computer44', '20.20.20.44', '01:00:00'],
                 ['stesworld.com', 'computer45', '10.10.10.45', '01:00:00'],
                 ['stesworld.co.uk', 'computer46', '172.16.48.5', '01:00:00']], 'Error with the data in test_csv.csv'
    type = 'remove'
    x = test.create_new_csv(type, csv_file, temp_csv)
    assert x[0] == [['ZoneName', 'Name', 'RRType'],
                    ['stesworld.com', 'computer43', 'A'],
                    ['stesworld.com', 'computer44', 'A'],
                    ['stesworld.com', 'computer45', 'A'],
                    ['stesworld.co.uk', 'computer46', 'A']], 'Error with the data in test_csv.csv'
    assert x[1] == [['ZoneName', 'Name', 'RRType'],
                    ['10.10.10.in-addr.arpa', '43', 'PTR'],
                    ['10.10.10.in-addr.arpa', '45', 'PTR'],
                    ['20.20.20.in-addr.arpa', '44', 'PTR'],
                    ['16.172.in-addr.arpa', '5.48', 'PTR']], 'Error with the data in test_csv1.csv'