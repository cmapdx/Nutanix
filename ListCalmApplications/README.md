# Change VLANs on a VM via API

This script will allow you to move a VM from one VLAN to another.  It reads a list of VMs from the Prism Central API and prompts the user to update each VM based on old VLAN tag and cluster name.

For each update it adds a new NIC to the VM configuration and deletes the NIC currently assigned to the old VLAN. By doing the change this way the OS will see a new NIC and request an IP.

You will need to install any missing modules needed to run this script.

Inputs:
* User ID for Prism Central or Element
* Password for Prism Central or Element
* Prism Central or Element IP or DNS name
* Old VLAN tag number
* New VLAN tag number
* Cluster Name (not case sensitive)

The user must have enough privalages to make changes to VMs.  When using the DNS name, only entry the name, no slashes or http.  The VLAN tags are numeric values that must be present on the cluster.  The script will search through the defined VLANs on a cluster to match input to the numeric value.  This script was written to work with individual clusters since each cluster maintains a unique UUID for the VLANs.  If you wish to work with multiple clusters at once then update the code to use a list instead of single value variable.


Sample Output:

    Prism IP or DNS name: 10.48.70.146
    User ID for Prism: admin
    Password for Prism: 
    Old VLAN tag number: 568
    New VLAN tag number: 567
    Cluster Name: cable
    New VLAN UUID: 0a302a3b-487a-4d32-b04f-401babd980e5
    VLAN UUID: f64409c1-c343-4a81-93b0-a850220addaa

    Power: ON   VM Name: CMA-Win2019                                                             Num of NICs: 1
    Update to new VLAN? [y/N]: y
    NIC has been added to the VM, waiting on task to complete.
    Task Status: RUNNING,  Percent Complete: 0
    Task Status: SUCCEEDED,  Percent Complete: 100

