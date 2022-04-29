# This script will create an image from a specific VM
#
# Creds
#PE_Creds - Prism Element Login
#
# Variables
#PE_Address - Prism Element IP or DNS name
#Description - Description of the image
#Image_Name - Name of existing image
#VM_Name - name of the VM to be used

#Call Prism Element API to build the image from the VM disk
def build_image (pe_user,pe_pass,image):
    # Set the headers, url, and payload
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    url     = "https://@@{PE_Address}@@:9440/PrismGateway/services/rest/v2.0/images/"
    payload = {}

    # Make the request
    resp = urlreq(url, verb='POST', auth='BASIC', user=pe_user, passwd=pe_pass, params=json.dumps(image), headers=headers)

    # If the request went through correctly, print it out.  Otherwise error out, and print the response.
    if resp.ok:
        return(resp)
        exit(0)
    else:
        print "Post Image Build request failed", resp.content
        exit(1)

def get_vm_list (pe_user,pe_pass,payload):
    # Set the headers, url, and payload
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    url     = "https://@@{PE_Address}@@:9440/PrismGateway/services/rest/v2.0/vms/?include_vm_disk_config=true"

    # Make the request
    resp = urlreq(url, verb='GET', auth='BASIC', user=pe_user, passwd=pe_pass, params=json.dumps(payload), headers=headers)

    # If the request went through correctly, return the json body.  Otherwise error out, and print the response.
    if resp.ok:
        return(resp)
        exit(0)
    else:
        print "Get request failed retrieving list of images: ", resp.content
        exit(1)

def get_storage_containers (pe_user,pe_pass):
    # Set the headers, url, and payload
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    url     = "https://@@{PE_Address}@@:9440/PrismGateway/services/rest/v2.0/storage_containers/"
    payload={}
    # Make the request
    resp = urlreq(url, verb='GET', auth='BASIC', user=pe_user, passwd=pe_pass, params=json.dumps(payload), headers=headers)

    # If the request went through correctly, return the json body.  Otherwise error out, and print the response.
    if resp.ok:
        return(resp)
        exit(0)
    else:
        print "Get request failed retrieving list of containers: ", resp.content
        exit(1)

############# MAIN ############################
# Set the credentials
pe_user = '@@{PE_Creds.username}@@'
pe_pass = '@@{PE_Creds.secret}@@'

image = {}
image['vm_disk_clone_spec'] = {}
image['vm_disk_clone_spec']['disk_address'] = {}

image['annotation'] = "@@{Description}@@"
image['image_import_spec'] = {}
image['vm_disk_clone_spec']['disk_address']['device_bus'] ="SCSI"
image['vm_disk_clone_spec']['disk_address']['device_index'] = 0
image['image_type'] = "DISK_IMAGE"
image['name'] = "@@{Image_Name}@@"

time = "@@{calm_time("%Y%m%d")}@@"
clone_name = "@@{VM_Name}@@_"+time
print ("Clone Name variable is: {}".format(clone_name))

payload_length=500
payload_offset=0
payload={"kind":"vm","offset":payload_offset,"length":payload_length}
resp = get_vm_list(pe_user,pe_pass,payload)
#print json.dumps(json.loads(resp.content), indent=4)

vm_count = json.loads(resp.content)['metadata']['total_entities']
print ("Number of VMs: {}".format(vm_count))
remaining_vms=500

while remaining_vms > 0:
    #Loop through the response
    remaining_vms=vm_count-payload_length
    for vm_entities in json.loads(resp.content)['entities']:
        if vm_entities['name'].startswith(clone_name):
            # Get UUID for the VM to be cloned
            print ("Full VM Name: ".format(vm_entities['name']))

            for disk in vm_entities['vm_disk_info']:
                if disk['disk_address']['device_bus'] == "scsi" and disk['disk_address']['device_index'] == 0:
                    ndfs_filepath = disk['disk_address']['ndfs_filepath']
                    print ("NDFS_FilePath {}".format(ndfs_filepath))
                    image['image_import_spec']['url'] = "nfs://@@{PE_Address}@@"+ndfs_filepath
                    image['vm_disk_clone_spec']['disk_address']['ndfs_filepath'] = ndfs_filepath
                    image['vm_disk_clone_spec']['disk_address']['vmdisk_uuid'] = disk['disk_address']['vmdisk_uuid']
                    
                    image['image_import_spec']['storage_container_uuid'] = disk['storage_container_uuid']
                    sc = get_storage_containers(pe_user,pe_pass)
                    for storage in json.loads(sc.content)['entities']:
                        if storage['storage_container_uuid'] == disk['storage_container_uuid']:
                            image['image_import_spec']['storage_container_id'] = storage['id']
                            image['image_import_spec']['storage_container_name'] = storage['name']
            
                            task_id = build_image(pe_user,pe_pass,image)
                            print ("Image Create Started")
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
