# This script will create an image from a specific VM
#
# Creds
#PE_Creds - Prism Element Login
#
# Variables
#PE_Address - Prism Element IP or DNS name
#VM_Name - name of the VM clone to be delete

def get_vm_list (pe_user,pe_pass,payload):
    # Set the headers, url, and payload
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    url     = "https://@@{PE_Address}@@:9440/PrismGateway/services/rest/v2.0/vms/"

    # Make the request
    resp = urlreq(url, verb='GET', auth='BASIC', user=pe_user, passwd=pe_pass, params=json.dumps(payload), headers=headers)

    # If the request went through correctly, return the json body.  Otherwise error out, and print the response.
    if resp.ok:
        return(resp)
        exit(0)
    else:
        print ("Get request failed retrieving list of VMs: {}".format(resp.content))
        exit(1)

def DELETE_VM (pe_user,pe_pass,uuid):
    # Set the headers, url, and payload
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    url     = "https://@@{PE_Address}@@:9440/PrismGateway/services/rest/v2.0/vms/"+uuid
    payload={}
    # Make the request
    resp = urlreq(url, verb='DELETE', auth='BASIC', user=pe_user, passwd=pe_pass, params=json.dumps(payload), headers=headers)

    # If the request went through correctly, return the json body.  Otherwise error out, and print the response.
    if resp.ok:
        return(resp)
        exit(0)
    else:
        print ("DELETE OF VM FAILED: ".format(resp.content))
        exit(1)

############# MAIN ############################
# Set the credentials
pe_user = '@@{PE_Creds.username}@@'
pe_pass = '@@{PE_Creds.secret}@@'

time = "@@{calm_time("%Y%m%d")}@@"
clone_name = "@@{VM_Name}@@_"+time
print ("Clone Name variable is: {}".format(clone_name))

payload_length=500
payload_offset=0
payload={"kind":"vm","offset":payload_offset,"length":payload_length}
resp = get_vm_list(pe_user,pe_pass,payload)
#print json.dumps(json.loads(resp.content), indent=4)

vm_count = json.loads(resp.content)['metadata']['total_matches']
print ("Number of VMs: {}".format(vm_count))
remaining_vms=500

while remaining_vms > 0:
    #Loop through the response
    remaining_vms=vm_count-payload_length

    for vm_entities in json.loads(resp.content)['entities']:
        if vm_entities['name'].startswith(clone_name):
            # Get UUID for the VM to be deleted
            print ("Full VM Name: {}".format(vm_entities['name']))
            uuid = vm_entities['uuid']
            task_id = DELETE_VM(pe_user,pe_pass,uuid)
            print ("VM being deleted")
            remaining_vms=0
    if remaining_vms > 0:
        payload_offset+=payload_length
        if remaining_vms > payload_length:
            remaining_vms-=payload_length
            payload={"kind":"vm","offset":payload_offset,"length":payload_length}
            resp = get_vm_list(pe_user,pe_pass,payload)
        else:
            payload={"kind":"vm","offset":payload_offset,"length":remaining_vms}
            resp = get_vm_list(pe_user,pe_pass,payload)