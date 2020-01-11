# From the named script import the functions to be tested
from main import Validate
import os
import pytest

################# Variables to change dependant on environment #################
directory = os.path.join(os.path.dirname(__file__), 'csv_files')    # CSV file location, use __file__ to start from same directory as test scripts
test_csv_fname = os.path.join(directory, 'test_csv.csv')
test_addr_fname = os.path.join(directory, 'test_scope_ip.csv')
test_other_fname = os.path.join(directory, 'test_dom_mac_ipin.csv')

# from main1 import validate
# def test_csv_format():
#     fname = 'ste'
#     test1 = Validate(fname)
#     assert test1.read_csv() == 'ste', 'FAIL'

# Tests the CSV data is formatted into the correct data model
def test_csv_format():
    test = Validate(test_csv_fname)
    assert test.read_csv() == [{'10.10.10.0/24': ('10.10.10.1', 'computer1.stesworld.com', '1a-1b-1c-1d-1e-1f')},
                               {'10.10.10.0/24': ('10.10.11.1', 'computer2.stesworld.com', '1a-1b-1c-1d-1e-1f')},
                               {'10.10.20.0/24': ('10.10.20.1', 'computer3.stesworld.org', '1a-1b1c-1z-1e-1f')}], 'Error with number of or empty columns'

# Tests badly formated network (scope) or IP address cause script to raise an error
def test_verify_scope_ip(capsys):
    try:
        test = Validate(test_addr_fname)
        test.read_csv()
        test.verify()
    except SystemExit:
        pass
    # Have to split up into list and seperate assert statements as assert output adds /n after x characters and couldnt remove them.
    errors = []
    for x in capsys.readouterr().out.splitlines():
        errors.append(x)
    assert (errors[0],errors[1]) == ('!!!ERROR - Invalid scope addresses entered !!!',
                                     "'10.10.999.0/24' does not appear to be an IPv4 or IPv6 network"), 'Not recognising network address format errors'
    assert (errors[2],errors[3])  ==  ('!!!ERROR - Invalid IP addresses entered !!!',
                                       "'10.999.20.1' does not appear to be an IPv4 or IPv6 address"), 'Not recognising IP address format errors'

# Tests badly formated domain name, MAC address or an IP not to be within the scope cause script to raise an error
def test_verify_dom_mac_ipin(capsys):
    try:
        test = Validate(test_other_fname)
        test.read_csv()
        test.verify()
    except SystemExit:
        pass
    # Have to split up into list and seperate assert statements as assert output adds /n after x characters and couldnt remove them.
    errors = []
    for x in capsys.readouterr().out.splitlines():
        errors.append(x)
    assert (errors[0],errors[1]) == ('!!!ERROR - Invalid Domain names entered !!!', 'computer7.stesworld.org'), 'Not recognising domain name errors'
    assert (errors[2],errors[3])  ==  ('!!!ERROR - Invalid MAC addresses entered !!!', '1a-1z-1c-1f-1e-1f'), 'Not recognising mac address errors'
    assert (errors[4],errors[5])  == ('!!!ERROR - IP address not a valid IP address in DHCP scope !!!',
                                      '10.10.20.1 not in 10.10.10.0/24'), 'Not recognising address not in scope errors'


# Tests the IP addresses are combined under scopes in the new data model
def test_data_model():
    test = Validate(test_csv_fname)
    test.read_csv()
    assert test.data_model() == [{'10.10.10.0': [('10.10.10.1', 'computer1.stesworld.com', '1a-1b-1c-1d-1e-1f'),
                                                 ('10.10.11.1', 'computer2.stesworld.com', '1a-1b-1c-1d-1e-1f')]},
                                 {'10.10.20.0': [('10.10.20.1', 'computer3.stesworld.org', '1a-1b1c-1z-1e-1f')]}], 'Error with combined addresses into scopes formating'


