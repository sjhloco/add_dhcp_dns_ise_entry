# Add DHCP, DNS and ISE entries from CSV

### 1. main.py: Take the CSV file and validate:
-all the IPs are valid IP address\
-all the domain names end in .fos.org.uk\
-The scopes are a legitamate range\
-The addresses are legit IPs within that range\
-Test username and password\
-Create new data model to be used by pre and post checks\
-Present user with main menu\
-Reformat CSV to remove /prefix from the scope               >>>> Do when do create_entries.py script

**COMPLETED**

### 2. pre_post_checks.py using this new output format to check agianst DHCP serrver
-Add fail fast if DHCP scope does not exist\
-Either return info to main.py or run next script from pre_post_checks. NEED TO decide - also how to get ifno between scripts, is it only JSON?\
-Write up notes from bottom of these notes on how can use the tools to get info with powershell\
-Create pytests for pre_post_checks

**INPROGRESS**

### 3. create_entries.py: Add the new entries to DHCP
-Reformat CSV to remove /prefix from the scope\
-Add the entries to DHCP

**NOT STARTED**

### 4. pre_post_checks.py
-Check entires added and the totla number is x more than started using post check flag

**NOTSTARTED**
