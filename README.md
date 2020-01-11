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
**COMPLETED**

-Redo pytests, need to soemhow mock connecting to DHCP server?
-Write up notes doc on how can use the tools to get info with powershell\
**INPROGRESS**

### 2b. win_dhcp.py: Add or remove entries to DHCP
-Reformat CSV to remove /prefix from the scope
-Add/remove entries DHCP from DHCP server
!!! If the name, IP or mac already exists in DHCP it wont let you add the entry !!!!
**COMPLETED**

**NOT STARTED**
--Do pytests, need to soemhow mock connecting to DHCP server?

### 3a. win_dns.py: check against DNS server
-Add failfast function if the DNS or PTR zone do not exist
-Add pre-checks/ post-checks to verify if A Record PTR entries shouldnt exist (add DNS) or should exist (remove DNS)
-Create pytests
**NOT STARTED**

### 3b. win_dns.py: Add or remove the new entries to DNS
-Add/remove entries DHCP from DHCP server
-Create pytests
**NOT STARTED**

### 4. main.py: Main menu
-Need to refactor it so have all the different options but not too complicated and DRY!!!!!
**NOT STARTED**

### 3a. cisco_ise.py: check against ISE
-Build test ISE lab
-Add failfast function, need ot decide what???
-Add pre-checks/ post-checks to verify if what???
-Create pytests
**NOT STARTED**

### 3b. win_dns.py: Add or remove the new entries to ISE
-Add/remove endhost entries in ISE
-Create pytests
**NOT STARTED**