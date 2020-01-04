from pypsrp.client import Client
from pypsrp.powershell import PowerShell, RunspacePool
from pypsrp.wsman import WSMan

user = "Administrator"
password = "mango12!"
server = "10.30.10.81"

wsman = WSMan(server, username=user, password=password,ssl=False)

with RunspacePool(wsman) as pool:
    ps = PowerShell(pool)
    # Get-DhcpServerv4Reservation -IPAddress 192.168.200.45
    ps.add_cmdlet("Invoke-Expression").add_parameter("Command", "Get-DhcpServerv4Reservation -IPAddress 192.168.200.45")
    ps.add_cmdlet("Out-String").add_parameter("Stream")
    ps.invoke()
    print("\n".join(ps.output))

with RunspacePool(wsman) as pool:
    ps = PowerShell(pool)
    # Get-DhcpServerv4Reservation -scopeid 192.168.200.0
    ps.add_cmdlet("Invoke-Expression").add_parameter("Command", "Get-DhcpServerv4Reservation -scopeid 192.168.200.0")
    ps.add_cmdlet("Out-String").add_parameter("Stream")
    ps.invoke()
    print("\n".join(ps.output))

with RunspacePool(wsman) as pool:
    ps = PowerShell(pool)
    # Get-DhcpServerv4FreeIPAddress -scopeid 192.168.200.0      # Next free IP address
    ps.add_cmdlet("Get-DhcpServerv4FreeIPAddress").add_parameter("scopeid", "192.168.200.0")
    ps.invoke()
    print(ps.output)
