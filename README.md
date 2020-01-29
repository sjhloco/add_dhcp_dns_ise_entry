# Add DHCP, DNS and ISE entries from CSV

### 1. main.py: Take the CSV file and validate:
-Check all the IPs are valid IP address\
-Check all the domain names end in .fos.org.uk\
-Check the scopes are a legitamate range\
-Check the addresses are legit IPs within that range\
-Test username and password\
-Create new data model to be used by pre and post-checks\
-Present the user with a main menu\
-Reformat CSV to remove /prefix from the scope
**COMPLETED**

### 2a. win_dhcp.py: Using DM from main.py to check against DHCP server
-Add failfast function if the DHCP scope does not exist
-Add pre-checks/ post-checks to verify if entries shouldnt exist (add DHCP) or should exist (remove DHCP)
-Pytests for functions
**COMPLETED**


### 2b. win_dhcp.py: Add or remove entries to DHCP
-Reformat CSV to remove /prefix from the scope
-Add/remove entries DHCP from DHCP server
-Pytests for functions (only the reformatting of the CSV)
!!! If the name, IP or mac already exists in DHCP it wont let you add the entry !!!!
**COMPLETED**

### 3a. win_dns.py: check against DNS server
-Have edited main.py so returns correct DMs for fowrad and reverse zones
-Basic cmds for connected to DSN server
-Add pre-checks/ post-checks to verify if A Record PTR entries shouldnt exist (add DNS) or should exist (remove DNS)
-Add failfast function if the DNS or PTR zone do not exist
-Create pytests
**COMPLETED**

### 3b. win_dns.py: Add or remove the new entries to DNS
-Add/remove entries DNS from DNS server
-Create pytests

### 4. main.py: Main menu
-Add dns to main menu option
**COMPLETED**

**NOT STARTED**
-Need to refactor it so have all the different options but not too complicated and DRY!!!!!

### 3a. cisco_ise.py: check against ISE

**NOT STARTED**
-Build test ISE lab
-Add failfast function, need ot decide what???
-Add pre-checks/ post-checks to verify if what???
-Create pytests


### 3b. win_dns.py: Add or remove the new entries to ISE

**NOT STARTED**
-Add/remove endhost entries in ISE
-Create pytests



TODO
add to notes on pysrp
write up the DNS menu in main
Move menus to own scripts and write pytest (if can)