# From the named script import the functions to be tested
from pre_post_checks import checks

################# Variables to change dependant on environment #################
user = None
password = None
pre_check = None
servers = {'dhcp': '1.1.1.1'}
# Using entries that have duplicate elements in different parts of the entries
csv_dm = [{'10.10.10.0': [('10.10.10.5', 'computer5.steswor', '5a-5b-5c-5d-5e-5f'), ('10.10.10.10', 'computer10.steswo', '1f-1f-1f-1f-1f-1f')]},
          {'10.10.20.0': [('10.10.20.6', 'computer6.steswor', '6a-6b-6c-6d-6e-6f')]}]

dhcp_dm = [{'10.10.10.0': [('10.10.10.5', 'computer6.steswor', '6a-6b-6c-6d-6e-6f')]},
          {'10.10.20.0': [('10.10.20.6', 'computer5.steswor', '5a-5b-5c-5d-5e-5f'), ('10.10.20.10', 'computer99.steswo', '1a-1a-1a-1a-1a-1a')]}]

# Tests the IP addresses are combined under scopes in the new data model
def test_data_model():
    test = checks(user, password, csv_dm, dhcp_dm, pre_check, servers)
    x = sorted(list(test.dhcp_verify()))            # Have to do as 2 asserts due to /n that cant strip in output
    assert x[0] == ('10.10.10.5', 'computer6.steswor', '6a-6b-6c-6d-6e-6f'), 'Not capturing just duplicate reservations'
    assert x[1] == ('10.10.20.6', 'computer5.steswor', '5a-5b-5c-5d-5e-5f'), 'Not capturing just duplicate reservations'
