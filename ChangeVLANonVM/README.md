# Change VLANs on a VM via API

This script will allow you to move a VM from one VLAN to another.  It reads a list of VMs from the Prism Central API and prompts the user to update each VM based on old VLAN tag and cluster name.

For each update it adds a new NIC to the VM configuration and deletes the NIC currently assigned to the old VLAN. By doing the change this way the OS will see a new NIC and request an IP.

You will need to install any missing modules needed to run this script.

Sample Output:


