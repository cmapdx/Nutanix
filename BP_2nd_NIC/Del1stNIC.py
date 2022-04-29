#This script is used to add a 2nd NIC to a new VM
#The 2nd NIC will be in the VLAN of the users choosing
#

def get_list (pc_user,pc_pass,type,payload):
    # Set the headers, url, and payload
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    url     = ("https://@@{PC_Address}@@:9440/api/nutanix/v3/{}/list".format(type))
    
    # Make the request
    resp = urlreq(url, verb='POST', auth='BASIC', user=pc_user, passwd=pc_pass, params=json.dumps(payload), headers=headers)

    # If the request went through correctly, return the json body.  Otherwise error out, and print the response.
    if resp.ok:
        return(resp)
        exit(0)
    else:
        print ("Post request failed getting list of {}: {}".format(type,resp.content))
        exit(1)

def update_vm(pc_user,pc_passwd,vm_uuid,data_list):
    '''
    Function that update the NIC VLAN of an existing VM
    '''
    headers = {"content-type": "application/json"}
    url     = ("https://@@{PC_Address}@@:9440/api/nutanix/v3/vms/{0}".format(vm_uuid))

    resp = urlreq(url, verb='PUT', auth='BASIC', user=pc_user, passwd=pc_pass, params=json.dumps(data_list), headers=headers)
    if resp.ok:
        return(resp)
        exit(0)
    else:
        print ("Put request failed updating VM: {}".format(resp.content))
        exit(1)
    

##########################################################################
#   MAIN  #
pc_user = '@@{PC_Creds.username}@@'
pc_pass = '@@{PC_Creds.secret}@@'

VM_Name = "@@{VM_Name}@@"

payload_length=500
payload_offset=0
payload={"kind":"vm","offset":payload_offset,"length":payload_length}
resp = get_list(pc_user,pc_pass,"vms",payload)
#print json.dumps(json.loads(resp.content), indent=4)

vm_count = json.loads(resp.content)['metadata']['total_matches']
print ("Number of VMs: {}".format(vm_count))
remaining_vms=500

while remaining_vms > 0:
    #Loop through the response
    remaining_vms=vm_count-payload_length
    for vm in json.loads(resp.content)['entities']:
        if vm['status']['name'] == VM_Name:
            # Get UUID for the VM to be cloned
            vm_uuid = vm['metadata']['uuid']
            print ("VM UUID: {}".format(vm_uuid))
            del vm['status']
            vm['spec']['resources']['nic_list'].pop(0)
            update_vm(pc_user, pc_pass,vm_uuid,vm)
            remaining_vms=0
    
    if remaining_vms > 0:
        payload_offset+=payload_length
        if remaining_vms > payload_length:
            remaining_vms-=payload_length
            payload={"kind":"vm","offset":payload_offset,"length":payload_length}
            resp = get_list(pc_user,pc_pass,"vms",payload)
        else:
            payload={"kind":"vm","offset":payload_offset,"length":remaining_vms}
            resp = get_list(pc_user,pc_pass,"vms",payload)
