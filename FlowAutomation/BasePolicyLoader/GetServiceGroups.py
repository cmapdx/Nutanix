#!/user/bin/env python

"""
The purpose of this script is to get a list of Service Groups and their UUID

Author: Corey Anson
Date: 10/25/2024
"""
from dataclasses import dataclass
import requests
import urllib3
import getpass
import json
import os
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
    url_list = "https://{0}:9440/api/nutanix/v3/{1}".format(ip_address,call_type)
    try:
        res_list = requests.post(url=url_list, data=json.dumps(data_list), auth=auth, headers=header, verify=False)
        return res_list
    except Exception as ex:
        writeLog ("Error","There was an issue requesting the VM list.",logfile)
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
logfile_name = file_path + '\\GetServiceGroups.' + log_time + '.log'
print (f'Logfile: {logfile_name}')
logfile = open(logfile_name, 'w')

output_file = file_path + '\\ServicesList.' + log_time + '.csv'
print (f'Logfile: {output_file}')
outfile = open(output_file, 'w')

# # # # # # # Pull a list of service groups # # # # # #
#The maximum responses per call is 500 with v3 of the API
max_in_response = 500
#starting the loop at zero. This is to handle more than 500 responses.
offset = 0
call_type = 'service_groups/list'
kind = 'service_group'

payload = {'kind': kind,'length': max_in_response,'offset': offset}
resp = make_request(PC_address, PC_user, PC_pass, call_type, payload)

# Verify the call worked.  Otherwise error out, and print the response.
if resp.ok:
    #Get the count of how many responses the system has
    resp_count = json.loads(resp.content)['metadata']['total_matches']
    if resp_count > max_in_response:
        number_in_request = max_in_response
    else:
        number_in_request = resp_count

    #Set how many loops are needed to work through all the VMs 
    iterations = math.ceil((resp_count - number_in_request) / max_in_response)
    iterator = 0

    outfile.write('SysDefined,Name,Description,UUID\n')

    while iterator <= iterations:
        #Loop through the JSON content checking each VM
        writeLog("INFO","Looping through the content.",logfile)
        for value in json.loads(resp.content)['entities']:
            if 'name' in value['service_group']:
                value_name = value['service_group']['name']
            else:
                value_name = "No Name"
            
            writeLog("INFO",f"Name: {value_name}",logfile) 
            if 'description' in value['service_group']:
                value_description = value['service_group']['description']
            else:
                value_description = "No Description"

            if 'uuid' in value:
                value_uuid = value['uuid']
            else: 
                value_uuid = "No UUID"

            if 'is_system_defined' in value['service_group']:
                defined_by = value['service_group']['is_system_defined']
            else:
                defined_by = "Who defined this?"

            outfile.write(f'{defined_by},{value_name},{value_description},{value_uuid}\n')
            
            
        iterator += 1
        offset += number_in_request
        #Loop through the remaining payloads up to 500 at a time, system will not return more than 500
        payload = {'kind': kind,'length': max_in_response,'offset': offset}
        resp = make_request(PC_address, PC_user, PC_pass, call_type, payload)
   
else:
    writeLog("ERROR","Something went wrong.", logfile)
    writeLog("ERROR",resp.content, logfile)
    logfile.close()
    outfile.close()
    exit(1)


logfile.close()
outfile.close()

exit(0)