# From the named script import the functions to be tested
from main import Validate
import os
import pytest

################# Variables to change dependant on environment #################
directory = os.path.join(os.path.dirname(__file__), 'csv_files')    # CSV file location, use __file__ to start from same directory as test scripts
test_csv_fname = os.path.join(directory, 'test_csv.csv')
test_addr_fname = os.path.join(directory, 'test_scope_ip.csv')
test_other_fname = os.path.join(directory, 'test_dom_mac_ipin.csv')

# Tests the CSV data is formatted into the correct data model
def test_csv_format():
    test = Validate(test_csv_fname)
    assert test.read_csv() == [{'10.10.10.0/24': ('10.10.10.1', 'computer1.stesworld.com', '1a-1b-1c-1d-1e-1f')},
                               {'10.10.10.0/24': ('10.10.11.1', 'computer2.stesworld.com', '1a-1b-1c-1d-1e-1f')},
                               {'10.10.20.0/24': ('10.10.20.1', 'computer3.stesworld.org', '1a-1b-1c-1d-1e-1f')}], 'Error with number of or empty columns'

# Tests badly formated network (scope) or IP address cause script to raise an error
def test_verify_scope_ip(capsys):
    test = Validate(test_addr_fname)
    test.read_csv()
    try:
        test.verify()
    except SystemExit:
        pass
    assert capsys.readouterr().out == ('!!!ERROR - Invalid scope addresses entered !!!\n' "'10.10.999.0/24' does not appear to be an IPv4 or IPv6 network\n"
                                       '!!!ERROR - Invalid IP addresses entered !!!\n' "'10.999.20.1' does not appear to be an IPv4 or IPv6 address\n"
                                       ), 'Error detecting badly formated IP address or scope network address'

# Tests badly formated domain name, MAC address or an IP not to be within the scope cause script to raise an error
def test_verify_dom_mac_ipin(capsys):
    test = Validate(test_other_fname)
    test.read_csv()
    try:
        test.verify()
    except SystemExit:
        pass
    assert capsys.readouterr().out == ('!!!ERROR - Invalid Domain names entered !!!\n' 'computer7.stesworld.org\n'
                                       '!!!ERROR - Invalid MAC addresses entered !!!\n' '1a-1z-1c-1f-1e-1f\n'
                                       '!!!ERROR - IP address not a valid IP address in DHCP scope !!!\n' '10.10.20.1 not in 10.10.10.0/24\n'
                                       ), 'Error detecting badly formated MAC address, domain name or IP not in scope'

# Tests the IP addresses are combined under scopes in the new data model
def test_data_model():
    test = Validate(test_csv_fname)
    test.read_csv()
    assert test.data_model() == [{'10.10.10.0': [('10.10.10.1', 'computer1.stesworld.com', '1a-1b-1c-1d-1e-1f'),
                                                 ('10.10.11.1', 'computer2.stesworld.com', '1a-1b-1c-1d-1e-1f')]},
                                 {'10.10.20.0': [('10.10.20.1', 'computer3.stesworld.org', '1a-1b-1c-1d-1e-1f')]}
                                 ], 'Error with the format of the combined addresses into scopes'


try:
    client_conn.copy(temp_csv, win_dir)
except Exception as e:
    print("!!! Error - Could not copy CSV file to DHCP server, investigate the below error before re-running the script.\n{}".format(e))
    exit()