#This script will delete the clone VM
#The calls are made to Prism Element
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

def get_image_list (pe_user,pe_pass):
    # Set the headers, url, and payload
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    url     = "https://@@{PE_Address}@@:9440/PrismGateway/services/rest/v2.0/vms/"
    payload={}
    # Make the request
    resp = urlreq(url, verb='GET', auth='BASIC', user=pc_user, passwd=pc_pass, params=json.dumps(payload), headers=headers)

    # If the request went through correctly, return the json body.  Otherwise error out, and print the response.
    if resp.ok:
        return(resp)
        exit(0)
    else:
        print "Get request failed getting list of images", resp.content
        exit(1)

def delete_vm (pe_user,pe_pass,uuid):
    # Set the headers, url, and payload
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    url     = "https://@@{PE_Address}@@:9440/PrismGateway/services/rest/v2.0/vms/"+uuid+"/set_power_state/"
    payload={}
    # Make the request
    resp = urlreq(url, verb='POST', auth='BASIC', user=pe_user, passwd=pe_pass, params=json.dumps(payload), headers=headers)

    # If the request went through correctly, return the json body.  Otherwise error out, and print the response.
    if resp.ok:
        return(resp)
        exit(0)
    else:
        print "Post request failed for power cycle: ", resp.content
        exit(1)

pc_user = '@@{PC_Creds.username}@@'
pc_pass = '@@{PC_Creds.secret}@@'
pe_user = '@@{PE_Creds.username}@@'
pe_pass = '@@{PE_Creds.secret}@@'

resp = get_image_list(pc_user,pc_pass)
#print json.dumps(json.loads(resp.content), indent=4)

time = "@@{calm_time("%Y%m%d")}@@"
clone_name = "@@{VM_Name}@@_"+time
print ("Clone Name variable is: {}".format(clone_name))

for image in json.loads(resp.content)['entities']:
    if image['status']['name'].startswith(clone_name):
        # Get UUID for the VM to be cloned
        uuid = image['metadata']['uuid']
        clone_name = image['status']['name']
        print ("Clone with name {0} has UUID: {1}".format(clone_name,uuid))
        powercycle_vm(pe_user,pe_pass,uuid)
