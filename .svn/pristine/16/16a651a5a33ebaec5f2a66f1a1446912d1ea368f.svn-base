Current Data Center Management System - Documentation
System Overview
The current system tracks dedicated servers and related infrastructure through a tabbed interface with the following main sections: General, Network, Server Control, Hardware, Software, Peripherals, Attachments, Documents, and History.

New system shall be built using Windows VM, Python and Flask


Technical Characteristics
Data Center Identification

Data centers are identified by unique 3-letter codes (e.g., "SFJ")

Data Integrity - Duplication Prevention
The system enforces basic uniqueness constraints on:

IP Addresses: No duplicate IPs allowed across all servers
Physical Location: Only one server per DC + Rack + RU position
Network Ports: Only one server per switch + port combination (both public and private)

Example: Only one server on Switch 4, Port 8
Example: Only one server on Switch 1051, Port 48


Power Ports: Only one server per APC + outlet combination

Critical Design Flaw - Everything is a "Server"
The system uses a single "server" entity for ALL equipment types, creating major problems:
Mixed Equipment/Service Types in One Field
The "Server Type" dropdown conflates two different concepts:

Equipment Types: Switch, TOR Switch, POWER PDU
Service Types: Dedicated, Shared, Reseller, Colocation, Staff, VPS

This means:

A network switch is stored as a "server" with type="Switch"
An APC PDU is stored as a "server" with type="POWER PDU"
Actual servers are stored with types like "Dedicated" or "Shared"
Can't properly identify WHAT something is AND HOW it's used

Resulting Problems

Irrelevant Fields: Switches and PDUs have fields for OS, CPU, RAM, Software that make no sense
Search Nightmare: Finding a specific switch means searching through hundreds of "servers"
Confusing References: Dropdowns reference "Switch 4" or "APC 8" which are actually other "server" entries
Impossible Reporting:

"How many servers?" includes switches and PDUs
"Show all switches" requires filtering through everything
Can't distinguish between a dedicated Dell server vs a shared HP server


Data Pollution: Irrelevant fields either left blank or repurposed for other data

Data Management

Dynamic Dropdowns: Dropdown values are data-driven and can be expanded as needed

Data Centers
Racks
RU positions
Server manufacturers
Other dropdown fields


No Validation Logic: System only checks for duplicates, does not validate:

Whether rack positions exist (can enter RU 999 on a 42U rack)
IP address validity or subnet correctness
Switch port counts or availability
Physical space constraints



PRIMARY REQUIREMENT: Complete IP Address Management (IPAM)
The new system MUST track ALL IP addresses with zero exceptions:
Critical IP Tracking Needs

Every IP must be tracked:

Primary public IPs
Primary private IPs
ALL add-on IPs (public and private)
Virtual IPs (VIPs)
Reserved IPs
Gateway IPs


Duplicate prevention across the board:

No IP can be assigned twice
Check ALL IP fields, not just primary
Block saves if duplicate detected


IP Pool/Subnet Management:

Define owned IP ranges (e.g., 208.76.80.0/24)
Track allocation within each subnet
Show available/used IPs per range
Quick "next available IP" function


VLAN to Subnet Mapping:

Associate VLANs with specific IP ranges
Enforce VLAN/IP relationships


IP Assignment View:

See all IPs assigned to a device
Search by any IP to find what device has it
Visual subnet utilization maps



Other Major Requirements
Zero Network Topology Tracking
Cannot track switch interconnections:

No way to document switch-to-switch connections
Can't track uplinks (distro → core connections)
Don't know which port on distro1 connects to which port on core
Can't document redundant paths between switches
No visibility into network hierarchy (core → distribution → access)

Critical Infrastructure Invisible:

Core switch connections
Distribution switch uplinks/downlinks
Inter-switch links (ISL)
Trunk ports vs access ports
Switch stacking cables

Current Workaround - Observium:

Using Observium monitoring tool to see some topology via port descriptions and CDP/LLDP
Requires jumping between two systems
Port descriptions may be outdated/incorrect
Can't plan or document intended topology
Still no single source of truth

What's NOT Tracked

No VM tracking - Virtual machines are completely absent from the system
Peripherals tab unused - Could be repurposed for storage devices

Data Scale & Performance

~300 total entries (mix of actual servers, switches, PDUs, everything)
Performance is acceptable - No speed issues with current scale
Data integrity is good - No corruption issues reported

How Things Actually Work

Dropdown values are hardcoded - Not dynamically pulled from other entries

"Switch 4" is just a dropdown option, not linked to an actual switch entry
"APC 8" is just a value, not referenced to an APC entry


History tab "sorta works" - Partially functional audit trail

Server Relationships

ROLES SERVED/RECEIVED used for tracking:

Remote backup server relationships
Database replication (slave SQL)
Web server replication (slave Apache)
Other server-to-server dependencies



Biggest Pain Points

IP TRACKING IS COMPLETELY BROKEN

Public IPs: Primary IP prevents duplicates only
Private IPs: Primary IP prevents duplicates only
Add-on IPs ARE NOT TRACKED AT ALL:

Can assign same add-on IP to multiple servers
No duplicate checking on additional IPs (public or private)
No inventory of these IPs whatsoever


No subnet management: Can't track IP ranges or allocations
No VLAN tracking: VLAN field exists but does nothing
No available IP discovery: No way to find free IPs
No IP pool management: Don't know what ranges you own
No validation: Can enter invalid IPs like 999.999.999.999
Can't see allocation: No view of what's used/available in a subnet


System is outdated - Needs modernization
Search/organization nightmare - Due to everything being lumped as "servers"
Can't properly categorize equipment - Mix of equipment and service types in one field

Data Fields by Tab
General Tab

Tag: Text field (example: "dedicated6611")
WHMCS User ID: Text field (example: "Ded_6611")
Server Name: Text field (example: "dedicated6611")
Server Host Name: Text field (example: "server.eallen.webservice.team")
Manufacturer: Dropdown field with "details" link (shown: "Dell")
Server Model: Text field (example: "Dell R420")
Server Type: Dropdown field (shown: "Dedicated")
SSH / RDP Port: Dropdown field (shown: "39292")
In Service Date: Date field (example: "9/10/2025")
Data Center: Dropdown field (shown: "SFJ")
Rack: Dropdown field (shown: "38")
RU: Text field (shown: "38")
Notes: Large text area (contains build ticket URLs and port information)
Checkboxes: Available, Infrastructure, Managed
Sections for:

ROLES SERVED (for other servers) - Table with columns: Role, Server Name, Public IP, Private IP
ROLES RECEIVED (by other servers) - Same table structure



Network Tab

Public IP: Text field (example: "208.76.80.215")
Public Switch: Dropdown field (shown: "4")
Public Switch Port: Dropdown field (shown: "8")
Vlan Tag: Text field (shown: "2")
Public Add On IP Addresses: Section showing "IPv4 Address" with expandable list
Private IP: Text field (example: "10.10.6.215")
Private Switch: Text field (shown: "1051")
Private Switch Port: Dropdown field (shown: "48")
DNS: Text field
Private Add On IP Addresses: Section showing "IPv4 Address" with ability to add/edit/delete entries

Server Control Tab

APC Number: Dropdown field (shown: "8")
APC IP Address: Dropdown field (shown: "8 10.10.4.36")
APC Port: Dropdown field (shown: "8")
IDRAC - IP: Text field (example: "10.10.4.216")
IDRAC - Version: Dropdown field (shown: "IDRAC Enterprise V7")
IDRAC - Notes: Text field

Hardware Tab
General Section:

RAM: Text field with dropdown (shown: "32768")
Memory Speed: Dropdown field
Raid Card: Text field

CPU / Motherboard Section:

CPU Type: Dropdown field (shown: "Intel(R) Xeon(R) CPU E5-2470 v2 @ 2.40G")
CPU Manufacturer: Dropdown field (shown: "Intel dual xeons")
CPU Socket: Text field
CPU count: Text field (shown: "2")
CPU Cores: Text field with dropdown (shown: "40")
GHz: Text field with dropdown (shown: "2")

Power Supply Section:

Power Supply: Text field (shown: "Dell 750W Redundant")
PS Watts: Text field with dropdown (shown: "750")
PS Size: Text field (shown: "1U")

Storage Section:

NB Make: Text field (shown: "Dell")
NB Model: Text field (shown: "R420 SFF")
MB Size: Text field

Video Section:

Display Adapter: Text field
Adapter Version: Text field
Driver Date: Date dropdown field
Adapter RAM: Text field with dropdown

Software Tab
Operating System Details Section:

OS: Dropdown field (shown: "Alma Linux")
OS Version: Text field (shown: "9.6")
OS Architecture: Text field
OS Serial no.: Text field
OS Product Key: Text field

Software Inventory Section:

Radio buttons: "Software Detected on this Computer" and "Software Allocated to this Computer"
Table with columns: Software Product, Version, Last Updated, Product Key
Shows "No data to display" when empty
Has Flag and Clear Flag buttons at bottom

Additional Interface Elements

Save & Close button (green checkmark)
Cancel button (red X)
Web Tracks Audit Updates these Fields note at bottom
Enterprise Edition 9.1.1.1 version indicator
