# Add DHCP, DNS and ISE entries from CSV

Has been tested on Microsoft server 2012 adding upto 200 entirs in one go.
Support for ISE is still a work in progress.

The package is structured in to the following modules:

- **main.py -** The main engine that performs the pre/post checks on the CSV and then calls the modules to perform checks against the systems and add or remove entries
- **win_dhcp.py -** Uses *pypsrp* and *powershell* to interact with Microsoft DHCP server to gather information on and add or remove DHCP reservations
- **win_dns.py -** Uses *pypsrp* and *powershell* to interact with Microsoft DNS server to gather information on and add or remove DNS A and PTR records
- **ise_nac.py -** Not yet created
- **device_template.py -** Template for adding new systems

It has been created in a modular fashion so that any of the current systems could be replaced by other vendors as long as the output returned by the module to the engine is in the same data model format.

It is not *idempotent*. Duplicate entries that already exist will be alerted on, but these must be rectified before the script can add any new entries.
It is *part-atomic*. The pre-checks are first done on all systems, only if ALL system pre-checks pass will it proceed to perform the desired actions.

## Prerequisites

The only extra package required to run this is *pypsrp*, it is used for communications with the Microsoft devices. https://pypi.org/project/pypsrp/

```bash
pip install -r requirements.txt
```

## Package settings (variables)

These variables can be found at the start of *main.py*. At a bare minimum you must set the DHCP, DNS and ISE server address as well as the expected domain name or names.

- **directory:** Location where the script will look for the csv, by default is the users home directory
- **domain_name:** A list of *domain names* that are zones in DNS and form the devices FQDN.
- **default_ttl:** The default TTL value used if none is specified in the CSV (default is 1 hour)
- **dhcp_svr:** The DHCP server that *win_dhcp.py* will run against
- **dns_svr:** The DNS server that *win_dns.py* will run against
- **ise_adm:** The ISE server that *ise_nac.py*will run against
- **temp_csv:** Name of temporary file created and used to deploy DHCP/DNS
- **win_dir:** Location on the Windows DHCP/DNS server the csv is copied to and run from

## CSV format and validation

The CSV has to be in the following format. All columns are mandatory except for TTL which if left blank will use the default value as set in the package settings.

```bash
ScopeId,IPAddress,Name,ClientId,Description,ttl
10.10.10.0/24,10.10.10.10,Computer1.stesworld.com,1a-1b-1c-1d-1e-1f,Reserved for Computer1,00:00:22
20.20.20.0/24,20.20.20.11,Computer2.stesworld.com,2a-2b-2c-2d-2e-2f,Reserved for Computer2,
```

The first thing the script will do is to perform the following checks to validate the CSV is formatted correctly as well as validate the data entered is in the correct format for that type of data.
- **Columns & Blank Lines:** Must have 6 columns, all blank lines will automatically be removed
- **Scope:** Must have a prefix and be a valid network address
- **IP Address:** Must be a valid IP address and also address an address within the DHCP scope
- **Domain Name:** The domain name part of the FQDN must match those entered in the package settings
- **MAC Address:** Must use valid characters (0-9, a-f) and only accepts MACs separated by hyphens (*xx-xx-xx-xx-xx-xx*)
- **TTL:** Must be in the format *hh:mm:ss* up to a maximum of *23:59:59*
- **Duplicate IPs or MACs:** No MAC or IP address can be in the CSV more than once.

## Usage

When running the script you only need to name the CSV file, it will look for this file in the location set in the package settings (by default users home directory).

```bash
python main.py name_of_csv.csv
```

### Enter credentials and choose task

Only if the CSV validation checks have passed will a user be prompted for credentials and get to the main menu. All tasks can be run together or run individually.

IMAGE

### Validation against the server
Before performing any action (add or remove) it will validate that either entries do not exist (*add*) or do exist (remove) for all modules before moving onto performing the action. If these checks fail they must be rectified (either in CSV or the server) before rerunning the script.

IMAGE

### Add/ remove entries

When checking for duplicates the script grabs the number of entries beforehand which at post-check is then cross referenced against the number of proposed entries in the CSV to validate the action completed with the desired result.

IMAGE

## Unit Testing

The unit testing is performed only on the parts of the script that require no remote device interaction against dummy CSVs in the directory *test/csv_files*. There Is a separate test file for each module and generally a test for each method.

```bash
pytest -v
pytest test/test_main.py -v
pytest test/test_win_dhcp.py -v
pytest test/test_win_dns.py -v
pytest test/test_win_dns.py -v
```

There are also unit-tests for testing against remote devices but these need to be run manually. To be able to test you need to create these zones and scopes within your environment used specifically for this test:
-10.255.255.0/24, example.com, 255.255.10.in-addr.arpa
-10.255.254.0/24, example.co.uk, 254.255.10.in-addr.arpa

Alternatively can edit the variables csv_dhcp_dm/csv_dns_dm and assert statements to match your environment. If it is not unused zones test_verify_pre and test_verify_post will fail as assert matches on the exact number of entries.

```bash
pytest test/full_test_win_dns.py --show-capture=no -vv
pytest test/full_test_win_dhcp.py --show-capture=no -vv
```

## Still to do

### 1a. Check against ISE – main.py

**NOT STARTED**
-Build test ISE lab
-Test API calls using python
-Add failfast function, need to decide what fails?
-Add pre-checks/ post-checks to verify. Need to decide what, guess MAC or name exists.
-Create pytests

### 1b. Add or remove the new entries to ISE - ise_mac.py:

**NOT STARTED**
-Add/remove endhost entries in ISE
-Create on-demand pytest

### 1b. Add to main menu - main.py:

-Stitch into existing main menu
-Final pytests

