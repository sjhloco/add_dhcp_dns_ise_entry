

=A Records
HostName                  RecordType Type       Timestamp            TimeToLive      RecordData
--------                  ---------- ----       ---------            ----------      ----------
@                         A          1          09/01/2020 05:00:00  00:10:00        10.30.10.81
computer1                 A          1          0                    01:00:00        10.10.10.1
dc1                       A          1          0                    01:00:00        10.30.10.81
DomainDnsZones            A          1          09/01/2020 05:00:00  00:10:00        10.30.10.81
ForestDnsZones            A          1          09/01/2020 05:00:00  00:10:00        10.30.10.81
win10-domain              A          1          25/11/2017 12:00:00  00:20:00        10.10.20.135
WIN7-DOMAIN               A          1          25/11/2017 12:00:00  00:20:00        10.10.20.134

=PTR records
HostName                  RecordType Type       Timestamp            TimeToLive      RecordData
--------                  ---------- ----       ---------            ----------      ----------
1                         PTR        12         0                    01:00:00        computer1.stesworld.com.
99                        PTR        12         0                    01:00:00        computer10.

2. Create pre-checks with an eye on them also being post_checks. Once again pull all records from DNS server
Get-DnsServerResourceRecord -ZoneName stesworld.com -RRType A
Get-DnsServerResourceRecord -ZoneName 10.10.10.in-addr.arpa -RRType PTR

3. Create failfast, use zones from new data structures in step 1
Get-DhcpServerv4Scope 10.10.10.0
Get-DnsServerZone <name>	        For a and ptr zones

4. Workout how new CSV should look, hopefully can use existing as matches on column name, if not just delte columns not needed
Hopefully can add/remove only A record and will sort out PTR. Two options:

a. Use dnscmd:
CSV
name    ip  type    zone    dnsserver

import-CSV -Path "c:\DNSEntries.csv" |
ForEach-Object {
  dnscmd.exe $_.dnsserver /RecordAdd $_.zone $_.name /createPTR $_.type $_.IP

dnscmd.exe <DNSServer> /RecordAdd <DNSZone> <NewEntryName> /CreatePTR A <IPAddress>
dnscmd $DNSServer /RecordDelete $DNSZone $recordName $recordType $recordAddress /fa

b. Use Add-DNSServerResourceRecordA
There was a header row with HostName and IPAddress as columns and then dozens of lines entries that needed to become DNS A Records on our server.

Import-CSV C:\Scripts\DNSentries.csv | %{ Add-DNSServerResourceRecordA -ZoneName adatum.com.au -Name $_."HostName" -IPv4Address $_."IPAddress" }
Import-CSV C:\Scripts\DNSentries.csv | %{ Remove-DnsServerResourceRecord -ZoneName "adatum.com.au" -RRType "A" -Name $_."HostName" -RecordData $_."IPAddress" }

Cmd to add 1 entry is:
Add-DnsServerResourceRecordA -Name "host23" -ZoneName "contoso.com" -IPv4Address "172.18.99.23" -TimeToLive 01:00:00 -CreatePtr



#Is already a module for DNS:
#https://docs.ansible.com/ansible/latest/modules/win_dns_record_module.html#win-dns-record-module

#But not for DHCP. Could try and write but has to be in powershell
#https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_general_windows.html#developing-modules-general-windows

