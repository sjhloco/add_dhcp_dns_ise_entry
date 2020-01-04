# from pypsrp.client import Client

user = "Administrator"
password = "mango12!"
server = "10.30.10.81"

# client = Client(server, username=user, password=password,ssl=False)

# powershell_script_for_getting_zones = """
#         Get-DhcpServerv4Reservation -ComputerName", "10.30.10.81 -IPAddress 192.168.200.45
#         """
# output, streams, had_errors = client.execute_ps(powershell_script_for_getting_zones)
# print(output)
# print(streams.debug)
# print(had_errors)

from pypsrp.client import Client
from pypsrp.powershell import PowerShell, RunspacePool
from pypsrp.wsman import WSMan

wsman = WSMan(server, username=user, password=password,ssl=False)


# So in the end it is up to your how you want to handle objects,
# you can get PowerShell on the remote host to create the output string
# or you can manually parse the objects yourself and create the output in whatever format you desire.

# with RunspacePool(wsman) as pool:
#     ps = PowerShell(pool)
#     ps.add_cmdlet("Get-PSDrive").add_parameter("Name", "C")
#     ps.invoke()
#     # we will print the first object returned back to us
#     print(str(ps.output))
#     assert str(output) == "C"

# with RunspacePool(wsman) as pool:
#     ps = PowerShell(pool)
#     ps.add_cmdlet("Invoke-Expression").add_parameter("Command", "Get-PSDrive -Name C")
#     ps.add_cmdlet("Out-String").add_parameter("Stream")
#     ps.invoke()
#     print("\n".join(ps.output))

##### YIPEE IT WORKS ####
# with RunspacePool(wsman) as pool:
#     ps = PowerShell(pool)
#     ps.add_cmdlet("Invoke-Expression").add_parameter("Command", "Get-DhcpServerv4Reservation -IPAddress 192.168.200.45")
#     ps.add_cmdlet("Out-String").add_parameter("Stream")
#     ps.invoke()
#     print("\n".join(ps.output))

