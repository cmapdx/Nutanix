#This script will clone an existing VM based on the name
#The calls are made to Prism Central
#
#Required variables
#Credentials
#PC_Creds - username and password
#
#Variables
#PC_Address - IP or DNS name for Prism Central
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

def clone_image (pc_user,pc_pass,uuid):
    # Set the headers, url, and payload
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    url     = "https://@@{PC_Address}@@:9440/api/nutanix/v3/vms/"+uuid+"/clone"
    payload={}
    # Make the request
    resp = urlreq(url, verb='POST', auth='BASIC', user=pc_user, passwd=pc_pass, params=json.dumps(payload), headers=headers)

    # If the request went through correctly, return the json body.  Otherwise error out, and print the response.
    if resp.ok:
        return(resp)
        exit(0)
    else:
        print "Post request failed cloning image: ", resp.content
        exit(1)

############## MAIN ##################################
pc_user = '@@{PC_Creds.username}@@'
pc_pass = '@@{PC_Creds.secret}@@'

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
        if image['status']['name'] == '@@{VM_Name}@@':
            # Get UUID for the VM to be cloned
            uuid = image['metadata']['uuid']
        
            print ("VM @@{VM_Name}@@ UUID: {}".format(uuid))
            task_uuid = clone_image(pc_user,pc_pass,uuid)
            print ("VM clone started")
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

