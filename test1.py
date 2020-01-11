# from pypsrp.client import Client
from pprint import pprint

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

wsman_conn = WSMan(server, username=user, password=password,ssl=False)
client_conn = Client(server, username=user, password=password,ssl=False)

client_conn.copy("test_csv.csv", "C:\\temp\\test_csv.csv")
client_conn.execute_cmd("del C:\\temp\\temp_csv.csv")

with RunspacePool(wsman_conn) as pool:
    ps = PowerShell(pool)
    # Import-Csv -Path "C:\tools\ap-reservation.csv" | Add-DhcpServerv4Reservation
    ps.add_cmdlet("Import-Csv").add_argument("C:\\temp\\test_csv.csv").add_cmdlet("Add-DhcpServerv4Reservation")
    output = ps.invoke()

print(ps.streams.error[0])
# print("HAD ERRORS: %s" % ps.had_errors)
# print("OUTPUT:\n%s" % "\n".join([str(s) for s in output]))
# print("ERROR:\n%s" % "\n".join([str(s) for s in ps.streams.error]))
# print("DEBUG:\n%s" % "\n".join([str(s) for s in ps.streams.debug]))
# print("VERBOSE:\n%s" % "\n".join([str(s) for s in ps.streams.verbose]))

# with RunspacePool(wsman_conn) as pool:
#     ps = PowerShell(pool)
#     ps.add_cmdlet("Invoke-Expression").add_parameter("Command", "Get-DhcpServerv4Reservation -IPAddress 192.168.200.45")
#     ps.add_cmdlet("Out-String").add_parameter("Stream")
#     ps.invoke()
    # print(ps.output)


# The Import-Csv cmdlet creates table-like custom objects from the items in CSV files
# -Path is the parameter, need to lose the -. It is used as the key and the value is path to CSV
# However this didnt work. Can run the cmd without path direct on path so used add_argument and worked.
# ps.add_cmdlet("Import-Csv").add_argument(r"C:\Users\Administrator\test_csv.csv")
# Direct on box use Import-Csv test_csv.csv and will print out the CSV

# Invoke-Expression cmdlet evaluates or runs a specified string as a command suign the cmd parameter
# The only parameter Invoke-Expression has is Command
#  Can use either, do the same thing:
#     ps.add_cmdlet("Import-Csv").add_argument("C:\\temp\\test_csv.csv").add_cmdlet("Add-DhcpServerv4Reservation")
    # ps.add_cmdlet("Invoke-Expression").add_parameter("Command", "Import-Csv -Path C:\\temp\\test_csv.csv | Add-DhcpServerv4Reservation")

# pprint(ps.had_errors)     will say Tru if errors are returned. This is fine if the cmd is wrong, but doesnt truturn True if the entyr already exists
# has 3 outputs, and with stremas can choose type to dispaly:
# output: A string that contains all the output records from the execution
# streams: A object that contains each of the streams (error, verbose, debug, warning, information) which has a list of each stream object created by the script
# Only one of streams that works is errors, now
# had_errors: A boolean that indicates whether a terminating error was thrown, note: this is different from a normal error
# We can see that there is an error entry but had_errors is still False. This is because of the way execute_ps runs the script, only terminating errors, e.g. throw will set this to True. this is why wrong cmd makes it fail but juplicate wont
# Only ever returns the first errors, but that is becasue that is all that the windows CLI does.
# Debugging with JSON log file PYPSRP_LOG_CFG=log.json python3 test1.py


# with RunspacePool(wsman_conn) as pool:
#     ps = PowerShell(pool)
#     # The powershell cmd is "Get-DhcpServerv4Reservation -scopeid 192.168.200.0
#     ps.add_cmdlet("Invoke-Expression").add_parameter("Command", "Get-DhcpServerv4Reservation -scopeid 192.168.200.0")
#     ps.add_cmdlet("Out-String").add_parameter("Stream")
#     ps.invoke()
#     pprint(str(ps.output))



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

