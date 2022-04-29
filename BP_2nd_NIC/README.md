# Read the VLAN information from a CSV file and create a NIC on that VLAN, remove original NIC

These scripts are used in blueprints to read in VLAN information based on the selected VLAN during launch.  The Powershell script will need a Windows VM to run on with a local copy of the CSV file.  This workflow was created to hanlde a segmented network where firewalls make building difficult.  A build NIC is used in an open network to get the build started.  The use of a spreadsheet to set the network variables reduces the number of inputs that can be incorrectly updated.

The Add_2nd_NIC eScript adds a new NIC to the VM with the assigned VLAN.  An OS appropriate script will need to provide the new NIC configuration to make it usable.

The Del1stNIC eScript is used to delete the 1st NIC on the VM. Execution of this script needs to be done after the build NIC is no longer required.

