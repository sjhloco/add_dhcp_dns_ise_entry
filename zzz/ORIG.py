# From the named script import the functions to be tested
from main import read_csv
from main import verify
import os
import pytest

# Tests the CSV data is formatted into the correct data model
def test_csv_format():
    fname = os.path.join(os.path.dirname(__file__), 'test.csv')     # use __file__ as csv in same directory as test scripts
    assert read_csv(fname) == [{'10.10.10.0/24': ('10.10.10.1', 'Computer1.stesworld.com', '1a-1b-1c-1d-1e-1f')}]

# Tests badly formated network (scope) and/or IP address will cause an error
def test_scope_ip():
    with pytest.raises(ValueError):
        csv_output = [{'10.10.10.2/24': ('10.10.10.1', 'Computer1.stesworld.com', '1a-1b-1c-1d-1e-1f')}]
        verify(csv_output)
    with pytest.raises(ValueError):
        csv_output = [{'10.10.10.0/24': ('10.10.10.256', 'Computer1.stesworld.com', '1a-1b-1c-1d-1e-1f')}]
        verify(csv_output)

# Tests badly formated domian name, MAC address or IP not within scope will cause an error
def test_domain_mac_ipinnet():
    csv_output = [{'10.10.10.0/24': ('10.10.20.1', 'Computer1.stesworld.co.uk', '1a-1b-1c-1d-1e-1Z')}]
    assert verify(csv_output) == ('Computer1.stesworld.co.uk', '1a-1b-1c-1d-1e-1Z', '10.10.20.1 not in 10.10.10.0/24')