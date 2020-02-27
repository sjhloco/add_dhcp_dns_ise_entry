# From the named script import the functions to be tested
from main import Validate
import os
import pytest

################# Variables to change dependant on environment #################
directory = os.path.join(os.path.dirname(__file__), 'csv_files')    # CSV file location, use __file__ to start from same directory as test scripts
test_csv_fname = os.path.join(directory, 'test_csv.csv')
test_addr_fname = os.path.join(directory, 'test_scope_ip.csv')
test_other_fname = os.path.join(directory, 'test_dom_mac_ipin_ttl.csv')
csv_dns_rv_output = [{'10.10.in-addr.arpa': ('1.42', 'computer1.stesworld.com.')},
                     {'8.in-addr.arpa': ('8.8.8', 'computer2.stesworld.com.')},
                     {'16.172.in-addr.arpa': ('16.30', 'computer3.stesworld.org.')},
                     {'10.10.10.in-addr.arpa': ('45', 'computer45.stesworld.com.')},
                     {'1.168.192.in-addr.arpa': ('42', 'computer3.stesworld.org.')}]

# Tests the CSV data is formatted into the correct data model
def test_csv_format():
    test = Validate(test_csv_fname)
    output = test.read_csv()
    assert output[0] == [{'10.10.10.0/23': ('10.10.11.42', 'computer1.stesworld.com', '1e-1b-1c-1d-1e-1f')},
                         {'8.0.0.0/8': ('8.8.8.8', 'computer2.stesworld.com', '1d-1b-1c-1d-1e-1f')},
                         {'172.16.32.0/19': ('172.16.48.5', 'computer3.stesworld.org', '1c-1b-1c-1d-1e-1f')},
                         {'172.16.32.0/19': ('172.16.48.30', 'computer3.stesworld.org', '1b-1b-1c-1d-1e-1f')},
                         {'192.168.1.0/24': ('192.168.1.42', 'computer3.stesworld.org', '1a-1b-1c-1d-1e-1f')}]
    assert output[1] == [{'stesworld.com': ('10.10.11.42', 'computer1', '01:00:00')},
                         {'stesworld.com': ('8.8.8.8', 'computer2', '00:20:00')},
                         {'stesworld.org': ('172.16.48.5', 'computer3', '01:00:00')},
                         {'stesworld.org': ('172.16.48.30', 'computer3', '01:00:00')},
                         {'stesworld.org': ('192.168.1.42', 'computer3', '01:00:00')}]
    assert output[2] == [['10.10.11.42/23', 'computer1.stesworld.com.', '01:00:00'],
                         ['8.8.8.8/8', 'computer2.stesworld.com.', '00:20:00'],
                         ['172.16.48.5/19', 'computer3.stesworld.org.', '01:00:00'],
                         ['172.16.48.30/19', 'computer3.stesworld.org.', '01:00:00'],
                         ['192.168.1.42/24', 'computer3.stesworld.org.', '01:00:00']]

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

# Tests badly formated domain name, MAC address, an IP not to be within the scope or duplicate MAC or IP addresses cause script to raise an error
def test_verify_dom_mac_ipin(capsys):
    test = Validate(test_other_fname)
    test.read_csv()
    try:
        test.verify()
    except SystemExit:
        pass
    assert capsys.readouterr().out == ('!!!ERROR - Invalid Domain names entered !!!\n' "{'10.10.10.0/24': ('10.10.20.1', 'computer7.stesworld.org', " "'1a-1z-1c-1f-1e-1f')}\n"
                                       '!!!ERROR - Invalid MAC addresses entered !!!\n' "{'10.10.10.0/24': ('10.10.20.1', 'computer7.stesworld.org', " "'1a-1z-1c-1f-1e-1f')}\n"
                                        '!!!ERROR - IP address not a valid IP address in DHCP scope !!!\n' '10.10.20.1 not in 10.10.10.0/24\n'
                                        '!!!ERROR - The TTL is not in a valid format, must be hh:mm:ss upto a maximum ' 'of 23:59:59 !!!\n'
                                        "{'stesworld.org': ('10.10.20.1', 'computer7', '24:61:71')}\n"
                                        '!!!ERROR - The following IP addresses have duplicate entries in the CSV !!!\n' '10.10.10.10\n'
                                        '!!!ERROR - The following MAC addresses have duplicate entries in the CSV ' '!!!\n' '1a-1b-1c-1f-1e-1f\n'
                                       ), 'Error detecting badly formated MAC address, TTL domain name, IP not in scope or duplicate MAC or IP adddresses'

# Tests that the DM of reverse lookup is in correct format
def test_dns_rv():
    test = Validate(test_csv_fname)
    test.read_csv()
    assert test.dns_rv() == ([{'10.10.in-addr.arpa': ('42.11', 'computer1.stesworld.com.')},
                              {'8.in-addr.arpa': ('8.8.8', 'computer2.stesworld.com.')},
                              {'16.172.in-addr.arpa': ('5.48', 'computer3.stesworld.org.')},
                              {'16.172.in-addr.arpa': ('30.48', 'computer3.stesworld.org.')},
                              {'1.168.192.in-addr.arpa': ('42', 'computer3.stesworld.org.')}]), 'Error with DNS reverse zone formatting'

# Tests the IP addresses are combined under scopes in the new data model
def test_data_model():
    test = Validate(test_csv_fname)
    output = test.read_csv()
    assert test.make_data_model(output[0]) == [{'10.10.10.0': [('10.10.11.42', 'computer1.stesworld.com', '1e-1b-1c-1d-1e-1f')]},
                                               {'8.0.0.0': [('8.8.8.8', 'computer2.stesworld.com', '1d-1b-1c-1d-1e-1f')]},
                                               {'172.16.32.0': [('172.16.48.5', 'computer3.stesworld.org', '1c-1b-1c-1d-1e-1f'),
                                                                ('172.16.48.30', 'computer3.stesworld.org', '1b-1b-1c-1d-1e-1f')]},
                                               {'192.168.1.0': [('192.168.1.42', 'computer3.stesworld.org', '1a-1b-1c-1d-1e-1f')]}], 'Error with DHCP DM formatting'
    assert test.make_data_model(output[1]) == [{'stesworld.com': [('10.10.11.42', 'computer1', '01:00:00'),
                                                                  ('8.8.8.8', 'computer2', '00:20:00')]},
                                               {'stesworld.org': [('172.16.48.5', 'computer3', '01:00:00'),
                                                                  ('172.16.48.30', 'computer3', '01:00:00'),
                                                                  ('192.168.1.42', 'computer3', '01:00:00')]}], 'Error with DNS, FW DM formatting'
    assert test.make_data_model(csv_dns_rv_output) == [{'10.10.in-addr.arpa': [('1.42', 'computer1.stesworld.com.')]},
                                                       {'8.in-addr.arpa': [('8.8.8', 'computer2.stesworld.com.')]},
                                                       {'16.172.in-addr.arpa': [('16.30', 'computer3.stesworld.org.')]},
                                                       {'10.10.10.in-addr.arpa': [('45', 'computer45.stesworld.com.')]},
                                                       {'1.168.192.in-addr.arpa': [('42', 'computer3.stesworld.org.')]}]

