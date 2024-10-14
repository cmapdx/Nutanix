#!/user/bin/env python

"""
The purpose of this script is to fix category assignments on VMs
To keep the overall AppType category from being overloaded the Apps were broken into sections.
    Apps_A-C
    Apps_D-K
    Apps-L-R
    Apps-S-Z
For the Flow Security policies to work the VMs need both AppType and the Apps above assigned.  
This script is to fix the missing AppType assignment, will find the assigned name from the above list.

Author: Corey Anson
Date: 10/10/2024
"""
from dataclasses import dataclass
import requests
import urllib3
import getpass
import json
import os
import math
import time
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
        writeLog ("Error","There was an issue requesting the VM list.",logfile)
        writeLog ("Error",ex.args,logfile)

def update_vm(ip_address,user,passwd,vm_uuid,data_list):
    '''
    Function to update the VM
    '''
    header = {"content-type": "application/json"}
    auth = HTTPBasicAuth(user, passwd)
    url_list = "https://{0}:9440/api/nutanix/v3/vms/{1}".format(ip_address,vm_uuid)
    try:
        status = requests.put(url=url_list, data=json.dumps(data_list), auth=auth, headers=header, verify=False)
        if status.ok:
            writeLog ("Info","VM has been updated, waiting on task to complete.",logfile)
            task_uuid = json.loads(status.text)['status']['execution_context']['task_uuid']
            #wait for task to complete and print out status
            get_task_status(ip_address,user,passwd,task_uuid)

        else:
            writeLog ("Warn","Status not OK",logfile)
            writeLog ("Warn",status.text,logfile)
    except Exception as ex:
        writeLog ("Error","There was an issue performing the update.",logfile)
        writeLog ("Error",ex.args,logfile)

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
                writeLog ("Info","Task Status: {0},  Percent Complete: {1}".format(state,p_complete),logfile)
                
            else:
                writeLog ("Error","There was an issue requesting the task status. ",logfile)
                writeLog ("Error",task_status.text,logfile)

    except Exception as ex:
        writeLog ("Error","There was an issue requesting the task status.",logfile)
        writeLog ("Error",ex.args,logfile)

def writeLog (level,info,logfile):
    #Write output to screen and html log for color output
    level = level.upper()
    logfile.write(f'[{level}]: {info}\n')
    if level == 'INFO':
        prGreen(info)
    elif level == "WARN":
        prYellow(info)
    elif level == "ERROR":
        prRed(info)

def prRed(skk): print("\033[91m {}\033[00m" .format(skk))
 
def prGreen(skk): print("\033[92m {}\033[00m" .format(skk))
 
def prYellow(skk): print("\033[93m {}\033[00m" .format(skk))


#Set the credentials
# You can hard code the values to make running again easy, suggest password remain a prompt for security
# # # Command Prompt Input # # #
PC_address = input ("Prism IP or DNS name: ")
PC_user = input ("User ID for Prism: ")
PC_pass = getpass.getpass('Password for Prism: ')

#Log the output
file_path = os.path.dirname(__file__)
log_time = time.strftime('%Y%m%d.%H%M')
logfile_name = file_path + '\\FixCategories.' + log_time + '.log'
print (logfile_name)
logfile = open(logfile_name, 'w')

# # # # # # # Pull a list of VMs to compare the Categories # # # # # #
#default is 20 VMs without a payload to increase the response number
max_vms_in_response = 500
#starting the loop at zero. This is to handle more than 500 VM systems.
offset = 0
call_type = 'vms'

payload = {'kind':'vm','length': max_vms_in_response,'offset': offset}
resp = make_request(PC_address, PC_user, PC_pass, call_type, payload)
app_categories = ['Apps_A-C','Apps_D-K','Apps-L-R','Apps-S-Z']
# If the request went through correctly, print it out.  Otherwise error out, and print the response.
if resp.ok:
    #Get the count of how many VMs are hosted in this system
    vm_count = json.loads(resp.content)['metadata']['total_matches']
    vms_in_request = json.loads(resp.content)['metadata']['length']

    #Set how many loops are needed to work through all the VMs 
    iterations = math.ceil((vm_count - vms_in_request) / max_vms_in_response)
    iterator = 0

    while iterator <= iterations:
        #Loop through the JSON content checking each VM
        for vm in json.loads(resp.content)['entities']:
            vm_name = vm['spec']['name']
            vm_uuid = vm['metadata']['uuid']
            found_apptype = ''
            found_application = ''

            for categories,value in vm['metadata']['categories'].items():
                if categories == 'AppType':
                    found_apptype = value
                if categories in app_categories:
                    found_application = categories

            if found_application in app_categories:
                if not found_apptype:
                    writeLog ("WARN","AppType was missing, will add AppType:{:10s} to VM: {:40s}".format(found_application,vm_name),logfile)
                    #remove the current VM status section, only configuration items are needed
                    del vm['status']
                    new_catmap = [found_application]
                    vm['metadata']['categories']['AppType'] = found_application
                    vm['metadata']['categories_mapping']['AppType'] = new_catmap
                    
                    #Update the VM in Prism Central
                    update_vm(PC_address, PC_user, PC_pass,vm_uuid,vm)  

                elif found_application != found_apptype:
                    writeLog ("ERROR","AppType mismatch on VM: {:20s}  AppType is: {:15s} and Application Group is: {:15s} MANUAL FIX NEEDED".format(vm_name,found_apptype,found_application),logfile)
                elif found_application == found_apptype:
                    writeLog ("INFO","No action needed for VM: {:20s}  AppType is: {:15s} and Application Group is: {:15s}".format(vm_name,found_apptype,found_application),logfile)
                else:
                    writeLog ("ERROR","Nothing matched on VM: {:20s}  AppType is: {:15s} and Application Group is: {:15s} INVESTIGATE".format(vm_name,found_apptype,found_application),logfile)  
                     
        iterator += 1
        offset += vms_in_request
        #Loop through the remaining VMs up to 500 at a time, system will not return more than 500
        payload = {'kind':'vm','length': max_vms_in_response,'offset': offset}
        resp = make_request(PC_address, PC_user, PC_pass, call_type, payload)
   
else:
    prRed("Something went wrong."), resp.content
    exit(1)


logfile.close()

exit(0)
