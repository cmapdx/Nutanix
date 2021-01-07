#!/user/bin/env python

"""
This script is used to move NICs from one VLAN to another.  
It calls the Prism Central API and parses the JSON to find VMs on the old VLAN.
The script will prompt before making any updates.
Updates add a new NIC for each one it finds in the old VLAN, 
then deletes the NIC in the old VLAN. After submitting the changes a task UUID is returned.
The task UUID is checked every 5 seconds until the task completes.
The VM OS will request a new DHCP IP for the new NIC. 
Author: Corey Anson
Date: 12/30/2020
"""
from dataclasses import dataclass
import requests
import urllib3
import argparse
import getpass
import json
import os
import sys
import math
import time
import copy
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def make_request(ip_address,user,passwd,call_type,data_list):
    '''
    Function that return the response of the REST API call in a JSON object
    '''
    header = {"content-type": "application/json"}
    auth = HTTPBasicAuth(user, passwd)
    url_list = "https://{0}:9440/api/nutanix/v3/{1}/list".format(ip_address,call_type)
    try:
        res_list = requests.post(url=url_list, data=json.dumps(data_list), auth=auth, headers=header, verify=False)
        return res_list
    except Exception as ex:
        print ("There was an issue requesting the VM list.")
        print (ex.args)

def update_vm(ip_address,user,passwd,vm_uuid,data_list):
    '''
    Function that update the NIC VLAN of an existing VM
    '''
    header = {"content-type": "application/json"}
    auth = HTTPBasicAuth(user, passwd)
    url_list = "https://{0}:9440/api/nutanix/v3/vms/{1}".format(ip_address,vm_uuid)
    try:
        status = requests.put(url=url_list, data=json.dumps(data_list), auth=auth, headers=header, verify=False)
        if status.ok:
            print ("NIC has been added to the VM, waiting on task to complete.")
            task_uuid = json.loads(status.text)['status']['execution_context']['task_uuid']
            #wait for task to complete and print out status
            get_task_status(ip_address,user,passwd,task_uuid)

        else:
            print ("Status not OK")
            print (status.text)
    except Exception as ex:
        print ("There was an issue performing the update.")
        print (ex.args)

def get_task_status(ip_address,user,passwd,task_uuid):
    '''
    Function that waits for the task to complete
    '''
    header = {"content-type": "application/json"}
    data_list = {}
    auth = HTTPBasicAuth(user, passwd)
    url_list = "https://{0}:9440/api/nutanix/v3/tasks/{1}".format(ip_address,task_uuid)
    state = "RUNNING"
    try:
        #Loop until task changes status from running
        while state == "RUNNING":
            time.sleep(5)
            task_status = requests.get(url=url_list, data=json.dumps(data_list), auth=auth, headers=header, verify=False)
            if task_status.ok:
                state = json.loads(task_status.content)['status']
                p_complete = json.loads(task_status.content)['percentage_complete']
                print ("Task Status: {0},  Percent Complete: {1}".format(state,p_complete))
                
            else:
                print ("There was an issue requesting the task status. ")
                print (task_status.text)

    except Exception as ex:
        print ("There was an issue requesting the task status.")
        print (ex.args)

    
#Set the credentials
# You can hard code the values to make running again easy, suggest password remain a prompt for security
#PC_user = 'admin'
#This has been tested against both Prism Central and Prism Element with success
PC_address = input ("Prism IP or DNS name: ")
PC_user = input ("User ID for Prism: ")
PC_pass = getpass.getpass('Password for Prism: ')

VLAN_tag = int(input ("Old VLAN tag number: "))
new_VLAN = int(input ("New VLAN tag number: "))
#This script was designed to handle one cluster because the UUID of the VLAN is different between clusters
#If you want to handle multiple clusters then you will need to change the UUID from a single entry to mulitple item list
Cluster_Name = input ("Cluster Name: ")

# # # # # # Get the UUID of the VLAN and cluster for this check # # # # #

#Get the UUID for the old VLAN
payload = {}
call_type = 'subnets'
# Make the request
resp = make_request(PC_address, PC_user, PC_pass, call_type, payload)

# If the request went through correctly
if resp.ok:
    # Cycle through the subnet "entities", and check if its id matches the old VLAN
    for subnet in json.loads(resp.content)['entities']:
        #The lower function remove the case so the compare is not case sensitive
        #If you want the compare to be case sensitive then remove the 2 ".lower()" entries
        if subnet['spec']['cluster_reference']['name'].lower() == Cluster_Name.lower():
            # Get UUID for both old and new VLANs
            if subnet['spec']['resources']['vlan_id'] == VLAN_tag:
                if 'uuid' in subnet['metadata']:
                    UUID = subnet['metadata']['uuid']
                    #Print the UUID to show it was found.
                    print ("VLAN UUID: {}".format(UUID))

            elif subnet['spec']['resources']['vlan_id'] == new_VLAN:
                if 'uuid' in subnet['metadata']:
                    new_VLAN_UUID = subnet['metadata']['uuid']
                    new_VLAN_name = subnet['status']['name']
                    #Print the UUID to show it was found.
                    print ("New VLAN UUID: {}".format(new_VLAN_UUID))
             
# In case the request returns an error
else:
    print ("Post subnets/list request failed", resp.content)
    exit(1)

#Test variables to verify they were set
try:
    UUID
except NameError:
    # UUID did not get set
    print ("old VLAN was not found.")
    print (json.dumps(json.loads(resp.content), indent=4))
    exit(1)

try:
    new_VLAN_UUID
except NameError:
    # new VLAN UUID did not get set
    print ("new VLAN was not found.")
    print (json.dumps(json.loads(resp.content), indent=4))
    exit(1)


# # # # # # # Pull a list of VMs and check if any are on the VLAN listed via UUID compare # # # # # #
#default is 20 VMs without a payload to increase the response number
max_vms_in_response = 500
#starting the loop at zero. This is to handle more than 500 VM systems.
offset = 0
call_type = 'vms'

payload = {'kind':'vm','length': max_vms_in_response,'offset': offset}
resp = make_request(PC_address, PC_user, PC_pass, call_type, payload)

# If the request went through correctly, print it out.  Otherwise error out, and print the response.
if resp.ok:
    #Get the count of how many VMs are hosted in this system
    vm_count = json.loads(resp.content)['metadata']['total_matches']
    vms_in_request = json.loads(resp.content)['metadata']['length']

    #Set how many loops are needed to work through all the VMs 
    iterations = math.ceil((vm_count - vms_in_request) / max_vms_in_response)
    iterator = 0
    nic_list = [0]

    while iterator <= iterations:
        #Loop through the JSON content checking each VM
        for vm in json.loads(resp.content)['entities']:
            vm_name = vm['spec']['name']
            vm_uuid = vm['metadata']['uuid']
            power_state = vm['spec']['resources']['power_state']
            #remove the current VM status section, only configuration items are needed
            del vm['status']
            #VMs can have multiple NICs
            nic_list = ['none']
            nic_cnt = 0
            num_nics = len(vm['spec']['resources']['nic_list'])
            #Chech each NIC for a match
            for nic in vm['spec']['resources']['nic_list']:
                #Check if this NIC is in the old VLAN
                if nic['subnet_reference']['uuid'] == UUID:
                    #Loop through the NICs and build a list
                    nic_list.append(nic_cnt)
                nic_cnt +=1

            #if there was a match then ask if user wants to update VM
            if len(nic_list) > 1:
                #throw out the first value which is none
                nic_list.pop(0)
                print ("\nPower: {:3s}  VM Name: {:70s}  Num of NICs: {}".format(power_state,vm_name,len(nic_list)))
                update = input ("Update to new VLAN? [y/N]: ")
                #only make changes if the user said "y", ignore all other responses
                if update == "y":
                    #Had to use a deep copy here to get the lower keys copied instead of 
                    # being references that would get updated in both new and old versions
                    new_nic = copy.deepcopy(vm['spec']['resources']['nic_list'][0])
                        
                    #Update the new NIC to remove fields it does not need and update the VLAN
                    del new_nic['uuid']
                    del new_nic['mac_address']
                    del new_nic['ip_endpoint_list']
                    new_nic['subnet_reference']['name']=new_VLAN_name
                    new_nic['subnet_reference']['uuid']=new_VLAN_UUID

                    #Add the number of NICs in the old VLAN to the JSON content
                    #Also removes the NICs in the old VLAN from the JSON content
                    for x in range(len(nic_list)):
                        vm['spec']['resources']['nic_list'].append(new_nic)
                        del vm['spec']['resources']['nic_list'][nic_list.pop()]
                        
                    #Update the VM in Prism Central
                    update_vm(PC_address, PC_user, PC_pass,vm_uuid,vm)    
   
        iterator += 1
        offset += vms_in_request
        #Loop through the remaining VMs up to 500 at a time, system will not return more than 500
        payload = {'kind':'vm','length': max_vms_in_response,'offset': offset}
        resp = make_request(PC_address, PC_user, PC_pass, call_type, payload)
   
else:
    print("Something went wrong."), resp.content
    exit(1)

exit(0)
