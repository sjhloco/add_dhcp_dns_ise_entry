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

### 2. pre_post_checks.py: Using DM from main.py to check against DHCP server
-Add failfast function if the DHCP scope does not exist\
-Either return info to main.py or run next script from pre_post_checks.py.\
NEED TO decide!!! This plays into how to get info between scripts, is only option JSON?\
-Write up notes doc on how can use the tools to get info with powershell\
-Create pytests for pre_post_checks

**INPROGRESS**

### 3. create_entries.py: Add the new entries to DHCP
-Reformat CSV to remove /prefix from the scope\
-Add the entries to DHCP

**NOT STARTED**

### 4. pre_post_checks.py
<<<<<<< HEAD
-Check entires added and the total reservations using existing pre_post_checks.py but with pre-check flag = Flase
=======
-Check entires added and the total reservations using existing pre_post_checks.py but with pre-check flag = False
>>>>>>> 7380091533d4b943cb7b9fc7626269592efac2c9

**NOTSTARTED**
