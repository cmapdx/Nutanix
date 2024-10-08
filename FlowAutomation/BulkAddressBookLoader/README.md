# For loading a bunch of IPs into the Flow Security Address Book

The script in this directory and other files combine to make it easy to upload large address lists

Explanaition of how to use these scripts:
* BulkAddressBook.ps1 is the script, arguments are optional when combined with the config file
* config.json contains the PC IP and user details for logging in, can also have Log file override details
* address.txt contains the name on the 1st line, description on 2nd line, and 3rd line and above are IPs
  
Script was tested with PC 2024.1.0.1, Powershell 5