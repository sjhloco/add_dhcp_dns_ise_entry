# Add/Remove DHCP, DNS and ISE entries from CSV

Has been tested on Microsoft server 2012 adding upto 200 enties in one go.
Support for ISE is still a work in progress.

The package is structured in to the following modules:

- **main.py -** The main engine that performs the pre/post checks on the CSV and then calls the other modules to perform checks against those systems before adding or removing entries
- **win_dhcp.py -** Uses *pypsrp* and *powershell* to interact with Microsoft DHCP server gather information on and add/ remove DHCP reservations
- **win_dns.py -** Uses *pypsrp* and *powershell* to interact with Microsoft DNS server to gather information on and add/ remove DNS A and PTR records
- **ise_nac.py -** Not yet created
- **device_template.py -** Template for adding new systems

The packaged has been designed in a modular fashion so that any of the current systems could be replaced by other vendors as long as the output returned by the module to the engine is in the same data model format.

Not *idempotent*: Duplicate entries that already exist will be alerted on, but these must be rectified before the script can add any new entries.\
*part-atomic*: The pre-checks are first done on all the systems (DHCP, DNS, ISE). Only if ALL system pre-checks pass will it proceed to perform the desired actions.

## Prerequisites

The only extra package required is *pypsrp* which is used for communications with the Microsoft devices. https://pypi.org/project/pypsrp/

```bash
pip install -r requirements.txt
```

## Package settings (variables)

These variables can be found at the start of *main.py*. At a bare minimum you must set the DHCP, DNS and ISE server address as well as the expected domain name or names.

- **directory:** Location where the script will look for the csv (default is the users home directory)
- **domain_name:** A list of *domain names* that are zones in DNS and form part of the devices FQDN
- **default_ttl:** The TTL value used if none is specified in the CSV (default is 1 hour)
- **dhcp_svr:** The DHCP server that *win_dhcp.py* will run against
- **dns_svr:** The DNS server that *win_dns.py* will run against
- **ise_adm:** The ISE server that *ise_nac.py* will run against
- **temp_csv:** Name of the temporary file created and used to deploy DHCP/DNS
- **win_dir:** Location on the Windows DHCP/DNS server that the csv is copied to and run from

## CSV format and validation

The CSV has to be in the following format. All columns are mandatory except for TTL which if left blank will use the default value as set in the package settings.

```bash
ScopeId,IPAddress,Name,ClientId,Description,ttl
10.10.10.0/24,10.10.10.10,Computer1.stesworld.com,1a-1b-1c-1d-1e-1f,Reserved Computer1,00:00:22
20.20.20.0/24,20.20.20.11,Computer2.stesworld.com,2a-2b-2c-2d-2e-2f,Reserved Computer2,
```

The first thing the script will do is to validate the CSV is formatted correctly and that the data within it is in the correct format for that type of data.
- **Columns & Blank Lines:** Must have 6 columns, all blank lines will automatically be removed
- **Scope:** Must have a prefix and be a valid network address
- **IP Address:** Must be a valid IP address that is within the DHCP scope
- **Domain Name:** The domain name part of the FQDN must match those entered in the package settings
- **MAC Address:** Must use valid characters (*0-9*, *a-f*) and be separated by hyphens (*xx-xx-xx-xx-xx-xx*)
- **TTL:** Must be in the format *hh:mm:ss* up to a maximum of *23:59:59*
- **Duplicate IPs or MACs:** No MAC or IP address can be in the CSV more than once

## Usage

When running the script you only need to name the CSV file, o need for the full path. It will automatically look for this file in the location set in the package settings (by default users home directory).

```bash
python main.py name_of_csv.csv
```

### Enter credentials and choose task

Only if the CSV validation checks have passed will a user be prompted for credentials and get to the main menu. Tasks can be run individually or all together.

<img width="903" alt="Screenshot 2020-02-27 at 21 24 14" src="https://user-images.githubusercontent.com/33333983/75488046-87bde100-59a7-11ea-9988-e3f37b49785e.png">

### Validation against the server

Before performing any action (*add* or *remove*) the script will validate that either the CSV entries do not exist (*add*) or do exist (remove) for all the systems before moving onto performing the action. If these checks fail they must be rectified (either in CSV or the server) before re-running the script.

<img width="903" alt="Screenshot 2020-02-27 at 21 26 34" src="https://user-images.githubusercontent.com/33333983/75488271-ebe0a500-59a7-11ea-8878-c4780b9905df.png">

### Add/ remove entries

In the initial pre-checks the script grabs the number of entries for each system before any change has been made. This same action is performed at post-check and these figures are cross referenced against the number of entries in the CSV to validate the action completed with the desired result.

<img width="909" alt="Screenshot 2020-02-27 at 21 25 53" src="https://user-images.githubusercontent.com/33333983/75488286-f602a380-59a7-11ea-91e1-7081f3b8abcd.png">

## Unit Testing

The unit testing is performed only on the parts of the script that require no remote device interaction using dummy CSVs in the directory *test/csv_files*. There is a separate test file for each module and normally a test for each method.

```bash
pytest -v
pytest test/test_main.py -v
pytest test/test_win_dhcp.py -v
pytest test/test_win_dns.py -v
pytest test/test_win_dns.py -v
```

There are also unit-tests for testing against remote devices but these need to be run manually. To be able to test you need to create these zones and scopes within your environment used specifically for this test:\
-*10.255.255.0/24, example.com, 255.255.10.in-addr.arpa*\
-*10.255.254.0/24, example.co.uk, 254.255.10.in-addr.arpa*\

Alternatively you can edit the variables *csv_dhcp_dm/csv_dns_dm* and *assert statements* to match your environment. If these are not unused scopes and zones *test_verify_pre* and *test_verify_post* will fail as the *assert statements* match on the exact number of entries.

```bash
pytest test/full_test_win_dns.py --show-capture=no -vv
pytest test/full_test_win_dhcp.py --show-capture=no -vv
```

## Still to do

**1a. Check against ISE – main.py**
*NOT STARTED*\
-Build test ISE lab\
-Test API calls using python\
-Add failfast function, need to decide what fails?\
-Add pre-checks/ post-checks to verify. Need to decide what, guess MAC or name exists.\
-Create pytests

**1b. Add or remove the new entries to ISE - ise_mac.py:**
*NOT STARTED*\
-Add/remove endhost entries in ISE\
-Create on-demand pytest

**1b. Add to main menu - main.py:**
*NOT STARTED*\
-Stitch into existing main menu\
-Final pytests
