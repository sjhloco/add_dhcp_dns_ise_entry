# Add DHCP, DNS and ISE entries from CSV

### 1. main.py: Take the CSV file and validate:
-Check all the IPs are valid IP address\
-Check all the domain names end in .fos.org.uk\
-Check the scopes are a legitamate range\
-Check the addresses are legit IPs within that range\
-Test username and password\
-Create new data model to be used by pre and post-checks\
-Present the user with a main menu\
-Reformat CSV to remove /prefix from the scope               >>>> Do when do create_entries.py script

**COMPLETED**

### 2a. pre_post_checks.py: Using DM from main.py to check against DHCP server
-Add failfast function if the DHCP scope does not exist
-Create pytests for pre_post_checks
**COMPLETED**

-Either return info to main.py or run next script from pre_post_checks.py.\
NEED TO decide!!! This plays into how to get info between scripts, is only option JSON?\
-Write up notes doc on how can use the tools to get info with powershell\
**INPROGRESS**

### 2b. pre_post_checks.py: check against DNS server
-Add failfast function if the DNS PTR zone do not exist
-Check that PTR or A record dont exist
-Create pytests for pre_post_checks

**NOT STARTED**

### 3a. create_entries.py: Add the new entries to DHCP
-Reformat CSV to remove /prefix from the scope\
-Add the entries to DHCP

**NOT STARTED**

### 3b. create_entries.py: Add the new entries to DNS
-Add the entries to DNS

**NOT STARTED**

### 4. pre_post_checks.py
-Check DHCP entires added and the total reservations using existing pre_post_checks.py but with pre-check flag = Flase
-Check DNS entires added and the total records using existing pre_post_checks.py but with pre-check flag = Flase

**NOTSTARTED**
