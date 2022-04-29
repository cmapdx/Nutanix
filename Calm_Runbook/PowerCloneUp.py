#This script will clone an existing VM based on the name
#The calls are made to Prism Central
#
#Required variables
#Credentials
#PC_Creds - username and password
#PE_Creds - username and password
#
#Variables
#PC_Address - IP or DNS name for Prism Central
#PE_Address - IP or DNS name for Prism Element
#VM_Name - Name of the VM to be cloned

def get_image_list (pc_user,pc_pass,payload):
    # Set the headers, url, and payload
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    url     = "https://@@{PC_Address}@@:9440/api/nutanix/v3/vms/list"
    
    # Make the request
    resp = urlreq(url, verb='POST', auth='BASIC', user=pc_user, passwd=pc_pass, params=json.dumps(payload), headers=headers)

    # If the request went through correctly, return the json body.  Otherwise error out, and print the response.
    if resp.ok:
        return(resp)
        exit(0)
    else:
        print "Post request failed getting list of images", resp.content
        exit(1)

def powercycle_vm (pe_user,pe_pass,uuid):
    # Set the headers, url, and payload
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    url     = "https://@@{PE_Address}@@:9440/PrismGateway/services/rest/v2.0/vms/"+uuid+"/set_power_state/"
    payload={"transition":"ON"}
    # Make the request
    resp = urlreq(url, verb='POST', auth='BASIC', user=pe_user, passwd=pe_pass, params=json.dumps(payload), headers=headers)

    # If the request went through correctly, return the json body.  Otherwise error out, and print the response.
    if resp.ok:
        return(resp)
        exit(0)
    else:
        print "Post request failed for power cycle: ", resp.content
        exit(1)

############# MAIN ########################
pc_user = '@@{PC_Creds.username}@@'
pc_pass = '@@{PC_Creds.secret}@@'
pe_user = '@@{PE_Creds.username}@@'
pe_pass = '@@{PE_Creds.secret}@@'

time = "@@{calm_time("%Y%m%d")}@@"
clone_name = "@@{VM_Name}@@_"+time
print ("Clone Name variable is: {}".format(clone_name))

payload_length=500
payload_offset=0
payload={"kind":"vm","offset":payload_offset,"length":payload_length}
resp = get_image_list(pc_user,pc_pass,payload)
#print json.dumps(json.loads(resp.content), indent=4)

vm_count = json.loads(resp.content)['metadata']['total_matches']
print ("Number of VMs: {}".format(vm_count))
remaining_vms=500

while remaining_vms > 0:
    #Loop through the response
    remaining_vms=vm_count-payload_length
    for image in json.loads(resp.content)['entities']:
        if image['status']['name'].startswith(clone_name):
            # Get UUID for the VM to be cloned
            uuid = image['metadata']['uuid']
            clone_name = image['status']['name']
            print ("Clone with name {0} has UUID: {1}".format(clone_name,uuid))
            powercycle_vm(pe_user,pe_pass,uuid)
            remaining_vms=0
    if remaining_vms > 0:
        payload_offset+=payload_length
        if remaining_vms > payload_length:
            remaining_vms-=payload_length
            payload={"kind":"vm","offset":payload_offset,"length":payload_length}
            resp = get_image_list(pc_user,pc_pass,payload)
        else:
            payload={"kind":"vm","offset":payload_offset,"length":remaining_vms}
            resp = get_image_list(pc_user,pc_pass,payload)
