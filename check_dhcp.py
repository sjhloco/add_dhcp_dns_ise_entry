from pypsrp.client import Client
from pypsrp.powershell import PowerShell, RunspacePool
from pypsrp.wsman import WSMan

user = "Administrator"
password = "mango12!"
dhcp_server = "10.30.10.81"

wsman = WSMan(dhcp_server, username=user, password=password,ssl=False)


##### The following tests have to be run per scope.   ####
# Need to re write first scrot to change format so is list of dicts with scopes the key and a value of (ip, domain, mac)


# Get list of all reservations in the scope
with RunspacePool(wsman) as pool:
    ps = PowerShell(pool)
    # Get-DhcpServerv4Reservation -scopeid 192.168.200.0
    ps.add_cmdlet("Invoke-Expression").add_parameter("Command", "Get-DhcpServerv4Reservation -scopeid 192.168.200.0")
    ps.add_cmdlet("Out-String").add_parameter("Stream")
    ps.invoke()
    before_reserv = ps.output[3:-2]     # Elimates headers and blank lines
#### !!! NEED TO USE A LIST of scopes and join together
# count of the number of lines, so reservations
before_cnt = len(before_reserv)

# From the output create lists of reservation IPs, names and tuple of both.
dhcp_ipadd = []
dhcp_domain = []
dhcp_ip_domain = []
for r in before_reserv:
    dhcp_ipadd.append((r.split()[0]))
    dhcp_domain.append((r.split()[3]))
    dhcp_ip_domain.append((r.split()[0], r.split()[3]))

# For testing temp tuple of ip to
dhcp_ipadd = ['192.168.200.210', '192.168.200.45', '192.168.200.200']
dhcp_domain = ['stetest1', 'stetest2', 'stetest3']
dhcp_ip_domain = [('192.168.200.210', 'stetest1'), ('192.168.200.45', 'stetest2'), ('192.168.200.200', 'stetest3')]
csv_ipadd = ['192.168.200.110', '192.168.200.45', '192.168.200.100']
csv_domain = ['stetest1', 'stetest4', 'stetest5']


##### Comparing IP & name got from CSV with IP and name got from DHCP server ####

# Create list of any already used reservatiosn or names
used_ipadd = set(dhcp_ipadd) & set(csv_ipadd)
used_domain = set(dhcp_domain) & set(csv_domain)

# Gets list of all used reservations based on IP address
if used_ipadd != 0:
    list_from_ip = []
    for x in used_ipadd:
        for y in dhcp_ip_domain:
            if x == y[0]:
                list_from_ip.append(y)
# Gets list of all used reservations based on name
if used_domain != 0:
    list_from_domain = []
    for x in used_domain:
        for y in dhcp_ip_domain:
            if x == y[1]:
                list_from_domain.append(y)

# Creates a list of used reservations removing any duplicates
used_reserv = set(list_from_ip) | set(list_from_domain)
print(used_reserv)



# ADD to notes or examples !!!!!!!!!
Due to issue on pythpn3.7 with dict_keys and dict_values
either create a list or set of keys or values
newdict = {1:0, 2:0, 3:0}
list_keys = [*newdict.keys()]
list_values = [*newdict.values()]
set_keys = {*newdict.keys()}
set_values = {*newdict.values()}

For a list of dicts:
newdict = [{1:0}, {2:0}, {3:0}]
key_list = []
value_list = []
for x in newdict:
    key_list.append([*x.keys()][0])
    value_list.append([*x.values()][0])
key_list

Also add about using *args so can use multiple for inputs when running a script. Add to the inputs document
https://www.geeksforgeeks.org/args-kwargs-python/

# ADD to notes or examples !!!!!!!!!