# From the named script import the functions to be tested
from win_dhcp import Dhcp
import os

################# Variables to change dependant on environment #################
csv_file = os.path.join(os.path.dirname(__file__), 'csv_files', 'test_csv.csv')
temp_csv = os.path.join(os.path.dirname(__file__), 'csv_files', 'temp_csv.csv')

user = None
password = None
pre_check = None
dhcp_svr = '1.1.1.1'

# Using entries that have duplicate elements in different parts of the entries
csv_dm = [{'10.10.10.0': [('10.10.10.5', 'computer5.steswor', '5a-5b-5c-5d-5e-5f'), ('10.10.10.10', 'computer10.steswo', '1f-1f-1f-1f-1f-1f')]},
          {'10.10.20.0': [('10.10.20.6', 'computer6.steswor', '6a-6b-6c-6d-6e-6f')]}]
dhcp_dm = [{'10.10.10.0': [('10.10.10.5', 'computer6.steswor', '6a-6b-6c-6d-6e-6f')]},
          {'10.10.20.0': [('10.10.20.6', 'computer5.steswor', '5a-5b-5c-5d-5e-5f'), ('10.10.20.10', 'computer99.steswo', '1a-1a-1a-1a-1a-1a')]}]


def test_verify_csv_vs_dhcp():
    test = Dhcp(dhcp_svr, user, password, csv_dm)
    x = test.verify_csv_vs_dhcp(dhcp_dm)
    # Had to split up as had to use sorted to stop the order of 'used_reserv' changing each time
    assert x['len_csv'] == 3, 'Error with detected number of used reservations (CSV vs DHCP server)'
    assert x['missing_resv'] == {'10.10.10.10'}, 'Error with detecting missing reservations'
    assert sorted(x['used_reserv']) == [('10.10.10.5', 'computer6.steswor', '6a-6b-6c-6d-6e-6f'), ('10.10.20.6', 'computer5.steswor', '5a-5b-5c-5d-5e-5f')
                                       ], 'Error with detecting used reservations'

def test_create_new_csv():
    test = Dhcp(dhcp_svr, user, password, csv_dm)
    x = test.create_new_csv(csv_file, temp_csv)
    assert x == [['ScopeId', 'IPAddress', 'Name', 'ClientId', 'Description'],
                 ['10.10.10.0', '10.10.10.1', 'Computer1.stesworld.com', '1a-1b-1c-1d-1e-1f', 'Reserved for Computer1'],
                 ['10.10.10.0', '10.10.11.1', 'Computer2.stesworld.com', '1a-1b-1c-1d-1e-1f', 'Reserved for Computer1'],
                 ['10.10.20.0', '10.10.20.1', 'Computer3.stesworld.org', '1a-1b-1c-1d-1e-1f', 'Reserved for Computer1']
                 ], 'Error with format of the new CSV file'
    os.remove(temp_csv)