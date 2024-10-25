#!/user/bin/env python

"""
The purpose of this script is to load base rules into Flow Security policies

This will add rules when missing, leave existing rules as they are.
All base rules must use Address and Services.  This script DOES NOT add services or IPs directly.
It is best practice to use Address and Service entries to make updates easier.

Author: Corey Anson
Date: 10/25/2024
Email: corey.anson@nutanix.com
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

def send_update(ip_address,user,passwd,uuid,data_list):
    '''
    Function to make update call
    '''
    header = {"content-type": "application/json"}
    auth = HTTPBasicAuth(user, passwd)
    url_list = "https://{0}:9440/api/nutanix/v3/{1}".format(ip_address,uuid)
    try:
        status = requests.put(url=url_list, data=json.dumps(data_list), auth=auth, headers=header, verify=False)
        if status.ok:
            writeLog ("Info","Update request made. Waiting for update task to complete.",logfile)
            task_uuid = json.loads(status.text)['status']['execution_context']['task_uuid']
            #wait for task to complete and print out status
            get_task_status(ip_address,user,passwd,task_uuid)

        else:
            writeLog ("Warn","Status not OK",logfile)
            writeLog ("Warn",status.text,logfile)
            writeLog("ERROR"," - - - - - - Payload - - - - - - - - -",logfile)
            writeLog("ERROR",json.dumps(data_list, indent=4),logfile)
    except Exception as ex:
        writeLog ("Error","There was an issue performing the update.",logfile)
        writeLog ("Error",ex.args,logfile)
        writeLog("ERROR"," - - - - - - Payload - - - - - - - - -",logfile)
        writeLog("ERROR",json.dumps(data_list, indent=4),logfile)

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
logfile_name = file_path + '\\BasePolicyRules.' + log_time + '.log'
print (f'Logfile: {logfile_name}')
logfile = open(logfile_name, 'w')

base_rules_file = file_path + '\\BaseRules.json'
with open(base_rules_file) as base_json:
    base_data = json.load(base_json)

for rules in base_data['rules']:
    #The name field is to help idenity what each rule is for to the humans
    writeLog ("INFO",f'Read in rule named: {rules['name']}',logfile)

# # # # # # # Pull a list of security rules # # # # # #
#The maximum responses per call is 500 with v3 of the API
max_in_response = 500
#starting the loop at zero. This is to handle more than 500 responses.
offset = 0
call_type = 'network_security_rules/list'
kind = 'network_security_rule'

payload = {'kind': kind,'length': max_in_response,'offset': offset}
resp = make_request(PC_address, PC_user, PC_pass, call_type, payload)

# Verify the call worked.  Otherwise error out, and print the response.
if resp.ok:
    #Get the count of how many responses the system has
    resp_count = json.loads(resp.content)['metadata']['total_matches']
    number_in_request = json.loads(resp.content)['metadata']['length']

    #Set how many loops are needed to work through all the VMs 
    iterations = math.ceil((resp_count - number_in_request) / max_in_response)
    iterator = 0

    while iterator <= iterations:
        #Loop through the JSON content checking each VM
        for value in json.loads(resp.content)['entities']:
            value_name = value['spec']['name']
            value_uuid = value['metadata']['uuid']
            
            if 'quarantine_rule' not in value['spec']['resources']:
                #Skip if the rule a quarantine rule
                writeLog ("INFO",f"Policy Name: {value_name}",logfile)

                new_policy = copy.deepcopy(value)
                tracker_base_rules = copy.deepcopy(base_data)
                writeLog ("INFO",f"Tracker Reset",logfile)

                if 'status' in new_policy:
                    del new_policy['status']

                # Rules have (app_rule):
                #  { action: monitor
                #    Inbound_allow_list [ { dict }, { dict } ],
                #    Outbound_allow_list [ { dict }, { dict } ],
                #    target_group: { center stuff } }

                for api_inbound in value['spec']['resources']['app_rule']['inbound_allow_list']:
                    if api_inbound['peer_specification_type'] == 'ALL':
                        #Allow all traffic inbound, solo rule, delete and replace
                        writeLog ("INFO","\tAllow all inbound traffic.",logfile)
                        new_policy['spec']['resources']['app_rule']['inbound_allow_list'].clear()
                        
                        
                        
                    elif api_inbound['peer_specification_type'] == 'IP_SUBNET' :
                        #Inbound rule that filters by IP or by Address entry
                        writeLog ("INFO","\tInbound Filter by IP or Address.",logfile)
                        if 'address_group_inclusion_list' in api_inbound:
                            for ip_address in api_inbound['address_group_inclusion_list']:
                                ip_uuid = ip_address['uuid']
                                for tracker_rules in tracker_base_rules['rules']:
                                    for tracker_inbound_rule in tracker_rules['inbound_rules']:
                                        if tracker_inbound_rule['type'] == 'address':
                                            for tracker_address_list in tracker_inbound_rule['address_list']:
                                                if ip_uuid == tracker_address_list['uuid']:
                                                    writeLog("INFO",f"Inbound rule type IP match for base rule: {tracker_rules['name']}",logfile)
                                                    
                                                    #Address found, now check if the services are also in the list
                                                    for tracker_base_service in tracker_inbound_rule['service_list']:
                                                        for api_inbound_service in api_inbound['service_group_list']:
                                                            if api_inbound_service['uuid'] == tracker_base_service['uuid']:
                                                                tracker_inbound_rule['service_list'].remove(tracker_base_service)
                                                    if not tracker_inbound_rule['service_list']:
                                                        tracker_inbound_rule['address_list'].remove(tracker_address_list)
                        else:                               
                            writeLog ("INFO","\tRule is IP based, skipping.",logfile)
                    elif api_inbound['peer_specification_type'] == 'FILTER' :
                        #Inbound rules have been set
                        writeLog ("INFO","\tInbound Filter by Category.",logfile)
                        for in_categories,in_value in api_inbound['filter']['params'].items():
                            writeLog ("INFO",f"\tCategory: {in_categories}  Value: {in_value[0]}",logfile)
                            for tracker_rules in tracker_base_rules['rules']:
                                for tracker_inbound_rule in tracker_rules['inbound_rules']:
                                    if tracker_inbound_rule['type'] == 'category':
                                        if tracker_inbound_rule['lookup_category'] == in_categories and tracker_inbound_rule['lookup_value'] == in_value[0]:
                                            writeLog("INFO",f"Inbound rule type Category match for base rule: {tracker_rules['name']}",logfile)
                                            
                                            for tracker_base_service in tracker_inbound_rule['service_list']:
                                                for api_inbound_service in api_inbound['service_group_list']:
                                                    if api_inbound_service['uuid'] == tracker_base_service['uuid']:
                                                        tracker_inbound_rule['service_list'].remove(tracker_base_service)

                                        
                                        if not tracker_inbound_rule['service_list']:
                                            #All service lists entries are gone, can remove the inbound rule
                                            tracker_rules['inbound_rules'].remove(tracker_inbound_rule)      
                       
                    else:
                        writeLog ("ERROR",f"\tUnknown filter type: {api_inbound['peer_specification_type']}.",logfile)
                        exit(1)
                #End of the inbound rules
                
                #Start of the outboud rules
                for api_outbound in value['spec']['resources']['app_rule']['outbound_allow_list']:
                    if api_outbound['peer_specification_type'] == 'ALL':
                        #Allow all traffic outbound, solo rule, delete and replace
                        writeLog ("INFO","\tAllow all outbound traffic.",logfile)
                        new_policy['spec']['resources']['app_rule']['outbound_allow_list'].clear()
                        
                    elif api_outbound['peer_specification_type'] == 'IP_SUBNET' :
                        #Outbound rules have been set
                        writeLog ("INFO","\tOutbound Filter by IP or Address.",logfile)
                        if 'address_group_inclusion_list' in api_outbound:
                            for api_ip_address in api_outbound['address_group_inclusion_list']:
                                ip_uuid = api_ip_address['uuid']
                                for tracker_rules in tracker_base_rules['rules']:
                                    for tracker_outbound_rule in tracker_rules['outbound_rules']:
                                        if tracker_outbound_rule['type'] == 'address':
                                            for tracker_address_list in tracker_outbound_rule['address_list']:
                                                if ip_uuid == tracker_address_list['uuid']:
                                                    writeLog("INFO",f"Outbound rule type IP match for base rule: {tracker_rules['name']}",logfile)
                                                    
                                                    #Address found, now check if the services are also in the list
                                                    for tracker_base_service in tracker_outbound_rule['service_list']:
                                                        for api_outbound_service in api_outbound['service_group_list']:
                                                            if api_outbound_service['uuid'] == tracker_base_service['uuid']:
                                                                tracker_outbound_rule['service_list'].remove(tracker_base_service)
                                                    
                                                    if not tracker_outbound_rule['service_list']:
                                                        tracker_outbound_rule['address_list'].remove(tracker_address_list)
                        else:
                            writeLog ("INFO","\tRule is IP based, skipping.",logfile)
                    elif api_outbound['peer_specification_type'] == 'FILTER' :
                        #Outbound rules have been set
                        writeLog ("INFO","\tOutbound Filter by Category.",logfile)
                        for out_categories,out_value in api_outbound['filter']['params'].items():
                            writeLog ("INFO",f"\tCategory: {out_categories}  Value: {out_value[0]}",logfile)
                            for tracker_rules in tracker_base_rules['rules']:
                                for tracker_outbound_rule in tracker_rules['outbound_rules']:
                                    if tracker_outbound_rule['type'] == 'category':
                                        if tracker_outbound_rule['lookup_category'] == out_categories and tracker_outbound_rule['lookup_value'] == out_value[0]:
                                            writeLog("INFO",f"Outbound rule type Category match for base rule: {tracker_rules['name']}",logfile)
                                            
                                            for tracker_base_service in tracker_outbound_rule['service_list']:
                                                for api_outbound_service in api_outbound['service_group_list']:
                                                    if api_outbound_service['uuid'] == tracker_base_service['uuid']:
                                                        writeLog("INFO",f"Outbound rule type FILTER match for SERVICE rule: {tracker_rules['name']}",logfile)
                                                        tracker_outbound_rule['service_list'].remove(tracker_base_service)
                                            if not tracker_outbound_rule['service_list']:
                                                tracker_rules['outbound_rules'].remove(tracker_outbound_rule)

                    else:
                        writeLog ("ERROR",f"\tUnknown filter type: {api_outbound['peer_specification_type']}.",logfile)
                        exit(1)
                #End of the outbound rules

                #Look for overlapping categories and values between base policies and security policy, remove from base if same category and value
                for new_category,new_value in new_policy['spec']['resources']['app_rule']['target_group']['filter']['params'].items():
                    for tracker_rules in tracker_base_rules['rules']:
                        for tracker_inbound_rule in tracker_rules['inbound_rules']:
                            if tracker_inbound_rule['type'] == 'category':
                                if tracker_inbound_rule['lookup_category'] == new_category and tracker_inbound_rule['lookup_value'] == new_value[0]:
                                    writeLog("INFO",f"Inbound rule matches security policy, will remove because matching categories is not allowed.",logfile)
                                    tracker_rules['inbound_rules'].remove(tracker_inbound_rule)
                        for tracker_outbound_rule in tracker_rules['outbound_rules']:
                            if tracker_outbound_rule['type'] == 'category':
                                if tracker_outbound_rule['lookup_category'] == new_category and tracker_outbound_rule['lookup_value'] == new_value[0]:
                                    writeLog("INFO",f"Outbound rule matches security policy, will remove because matching categories is not allowed.",logfile)
                                    tracker_rules['outbound_rules'].remove(tracker_outbound_rule)

                #Add the rules that are still in the tracker variable, all overlapping rules have been removed.
                for tracker_rules in tracker_base_rules['rules']:
                    #Loop through the rules read from the config file
                    for tracker_inbound_rule in tracker_rules['inbound_rules']:
                        new_inbound = {}  #empty dictionary to build the new inbound rules
                        new_address_inclusion = []  #empty list to build the new address inclusion component
                        new_service_inclusion = []  #empty list to build the new services component
                                
                        if tracker_inbound_rule['type'] == 'address':
                            # Data Types that get loaded into the JSON payload.
                            #{ address_group_inclusion_list: [ { kind, uuid }, { kind, uuid } ],
                            #  peer_specification_type: IP_SUBNET,
                            #  service_group_list: [ { kind, uuid }, { kind, uuid } ] }        
                            for tracker_service_group in tracker_inbound_rule['service_list']:
                                #updating the tracker directly will break the for loop
                                copy_service_group = copy.deepcopy(tracker_service_group)
                                if 'name' in copy_service_group.keys():  #name is in the input file to make it easier to read, not used in payload
                                    del copy_service_group['name']
                                new_service_inclusion.append(copy_service_group)
                                tracker_inbound_rule['service_list'].remove(tracker_service_group)
                                    
                            for tracker_address_list in tracker_inbound_rule['address_list']:
                                copy_address_list = copy.deepcopy(tracker_address_list)
                                if 'name' in copy_address_list.keys():
                                    del copy_address_list['name']
                                new_address_inclusion.append(copy_address_list)
                                tracker_inbound_rule['address_list'].remove(tracker_address_list)
                            if new_address_inclusion and new_service_inclusion:
                                # address_group_inclusion_list: [ { kind, uuid }, { kind, uuid } ]
                                new_inbound["address_group_inclusion_list"] = new_address_inclusion
                                # peer_specification_type: IP_SUBNET,
                                new_inbound['peer_specification_type'] = "IP_SUBNET"
                                # service_group_list: [ { kind, uuid }, { kind, uuid } ]
                                new_inbound["service_group_list"] = new_service_inclusion
                                #Add the new rules to the policy.
                                new_policy['spec']['resources']['app_rule']['inbound_allow_list'].append(new_inbound)
                                #Remove the rule from the tracker since they are now included in the payload.
                                tracker_rules['inbound_rules'].remove(tracker_inbound_rule)
                            elif new_address_inclusion:
                                # TODO - future version to handle this
                                writeLog("ERROR",f"Empty inbound SERVICE, Address has data that was not added: {new_address_inclusion}",logfile)
                            elif new_service_inclusion:
                                # TODO - future version to handle this
                                writeLog("ERROR",f"Empty inbound ADDRESS, Service has data that was not added: {new_service_inclusion}",logfile)
                            else:
                                #Empty variables because all the rules were already in the policy.
                                writeLog("INFO",f"Empty Address and Service, no Inbound rule to add.",logfile)
                            
                        elif tracker_inbound_rule['type'] == 'category':
                            #{ filter: { kind_list: [ "vm" ], params: { category: [ value ] }, dict}
                            #  peer_specification_type: FILTER,
                            #  service_group_list: [ { kind, uuid }, { kind, uuid } ] }
                            #
                            #Filter is dict: dict: list, dict, dict, list, dict

                            #{ filter: { kind_list: [ "vm" ], params: { category: [ value ] }, dict }
                            base_category = tracker_inbound_rule['lookup_category']
                            base_value = tracker_inbound_rule['lookup_value']
                            new_inbound['filter'] = {'kind_list': ["vm"], 'params': { base_category: [base_value]}, 'type':'CATEGORIES_MATCH_ALL' }
                            #  peer_specification_type: FILTER,
                            new_inbound['peer_specification_type'] = "FILTER"
                                    
                            for tracker_service_group in tracker_inbound_rule['service_list']:
                                copy_service_group = copy.deepcopy(tracker_service_group)
                                if 'name' in copy_service_group.keys():
                                    del copy_service_group['name']
                                new_service_inclusion.append(copy_service_group)
                                tracker_inbound_rule['service_list'].remove(tracker_service_group)
                            new_inbound["service_group_list"] = new_service_inclusion

                            new_policy['spec']['resources']['app_rule']['inbound_allow_list'].append(new_inbound)
                            tracker_rules['inbound_rules'].remove(tracker_inbound_rule)
                              
                            #This is how it looks in the API call, plus services
                            #"filter": {
                            #"kind_list": [
                            #    "vm"
                            #],
                            #"params": {
                            #    "Apps-S-Z": [
                            ##        "SOLARW"
                            #   ]
                            #},
                            #"type": "CATEGORIES_MATCH_ALL"
                            #},
                        else:
                            writeLog("ERROR","Unknown type in config file in INBOUND section.",logfile)
                            exit(1)    
                    #Loop through the outbound rules and add any still in the tracker
                    for tracker_outbound_rule in tracker_rules['outbound_rules']:
                        new_outbound = {}  
                        new_address_inclusion = []
                        new_service_inclusion = []
                                
                        if tracker_outbound_rule['type'] == 'address':
                            for tracker_service_group in tracker_outbound_rule['service_list']:
                                copy_service_group = copy.deepcopy(tracker_service_group)
                                if 'name' in copy_service_group.keys():
                                    del copy_service_group['name']
                                new_service_inclusion.append(copy_service_group)
                                tracker_outbound_rule['service_list'].remove(tracker_service_group)
                            for tracker_address_list in tracker_outbound_rule['address_list']:
                                copy_address_list = copy.deepcopy(tracker_address_list)
                                if 'name' in copy_address_list.keys():
                                    del copy_address_list['name']
                                new_address_inclusion.append(copy_address_list)
                                tracker_outbound_rule['address_list'].remove(tracker_address_list)
                            if new_address_inclusion and new_service_inclusion:        
                                new_outbound["address_group_inclusion_list"] = new_address_inclusion
                                new_outbound['peer_specification_type'] = "IP_SUBNET"
                                new_outbound["service_group_list"] = new_service_inclusion
                                new_policy['spec']['resources']['app_rule']['outbound_allow_list'].append(new_outbound)
                                tracker_rules['outbound_rules'].remove(tracker_outbound_rule)
                            elif new_service_inclusion:
                                writeLog("ERROR",f"Empty outbound Address, Service has data that was not added: {new_service_inclusion}",logfile)
                            elif new_address_inclusion:
                                writeLog("ERROR",f"Empty outbound Service, Address has data that was not added: {new_address_inclusion}",logfile)
                            else:
                                writeLog("INFO",f"Empty Address and Service, no outbound data to add, skipping.",logfile)

                        elif tracker_outbound_rule['type'] == 'category':
                            base_category = tracker_outbound_rule['lookup_category']
                            base_value = tracker_outbound_rule['lookup_value']
                            new_outbound['filter'] = {'kind_list': ["vm"], 'params': { base_category: [base_value]}, 'type':'CATEGORIES_MATCH_ALL' }
                            new_outbound['peer_specification_type'] = "FILTER"
                                    
                            for tracker_service_group in tracker_outbound_rule['service_list']:
                                copy_service_group = copy.deepcopy(tracker_service_group)
                                if 'name' in copy_service_group.keys():
                                    del copy_service_group['name']
                                new_service_inclusion.append(copy_service_group)
                                tracker_outbound_rule['service_list'].remove(tracker_service_group)

                            new_outbound["service_group_list"] = new_service_inclusion

                            new_policy['spec']['resources']['app_rule']['outbound_allow_list'].append(new_outbound)
                            tracker_rules['outbound_rules'].remove(tracker_outbound_rule)
                        else:
                           writeLog("ERROR","Unknown type in config file in OUTBOUND section.",logfile)
                           exit(1)
                
                #make_update = input ("Update Policy with Base Rules (Y/N): ")
                # THIS LINE MAKES THE UPDATE, comment out for a dry run.  Wrap with user input to select which policies to update.
                result = send_update(PC_address,PC_user,PC_pass,"network_security_rules/"+value_uuid,new_policy)
                
                # The below lines are to see what updates will be made, written in the logfile and to the screen.
                #writeLog("INFO"," - - - - - - UPDATED POLICY - - - - - - - - -",logfile)
                #writeLog("INFO",json.dumps(new_policy, indent=4),logfile)
                
                del new_policy
                del tracker_base_rules

        iterator += 1
        offset += number_in_request
        #Loop through the remaining payloads up to 500 at a time, system will not return more than 500
        payload = {'kind': kind,'length': max_in_response,'offset': offset}
        resp = make_request(PC_address, PC_user, PC_pass, call_type, payload)
   
else:
    writeLog("ERROR","Something went wrong.", logfile)
    writeLog("ERROR",resp.content, logfile)
    logfile.close()
    exit(1)


logfile.close()

exit(0)