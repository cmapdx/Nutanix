# These scripts are used to load baseline rules into Flow Security Policies

Update the BaseRules.json file with rules that should be in every security policy.
Example base rules:
* Active Directory
* DNS
* NTP
* Security Scanners
* Nutanix Guest Tools
* SCCM

Explanaition of how to use these scripts:
* GetAddressGroups.py - Creates a CSV file with all the Address Groups with their UUID
* GetServiceGroups.py - Creates a CSV file with System Defined, Name, Description, and UUID for all the Service Groups
* BaseRules.json - Update with the rules you want loaded into every policy
* BasePolicyLoader.py - This loads the base rules into every policy and leaves any existing rules in place.
  
  ## BaseRules.json - formating the content

> { Begin and end with braces }
> "description" : "Describe the contents"
* Description is not used in the code, this is option content to describe the content.
> "rules" : [ multiple rules between the brackets ]
* The rules block contains multiple rules between curly braces.
> { Block of rule definitions }
> "name" : "SolarWinds Monitoring"
* This is not used, it is optional to provide a label for the rule
> "inbound_rules" : [ Block of rules, most likely one each ]
* The inbound and outbound rules blocks start with square brackets, one rule per curly brace
> "type" : "value",
* Type can be either "category" or "address"
* Category contains the key and value followed by the services list
* Address contains the addresses defined by kind and uuid, then followed by service list.
> "lookup_category" 
* This is the key value of the category, such as AppType
> "lookup_value"
* This is the value for the category, such as Exchange
> "service_list" : [ block of services contained by curly braces for each ]
* Define the services with kind, uuid, and optionally name.
> "kind": "service_group",
> "uuid": "UUID From the GetServiceGroups CSV output"
> "name": "optional name to track what service it is"
* Multiple services can be added with {kind, uuid}, {kind, uuid}, {kind, uuid}
* Match the name to the name in the services catalog to make tracking easier.

Repeat the rules until all base rules have been defined.  
