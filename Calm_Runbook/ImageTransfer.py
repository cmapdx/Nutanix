# This script will create an image from a specific VM
#
#Variables required for input
# Creds
#PE_Creds - login credentials
#PC_Creds - login credentials
#
# Variables
#PE_Address - IP or DNS name of Prism Element
#PC_Address - IP or DNS name of Prism Central
#Image_Name - name of the image

#Call the API to tranfer control of image from PE to PC
def transfer_image (pc_user,pc_pass,image):
    # Set the headers, url, and payload
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    url     = "https://@@{PC_Address}@@:9440/api/nutanix/v3/images/migrate"
 
    # Make the request
    resp = urlreq(url, verb='POST', auth='BASIC', user=pc_user, passwd=pc_pass, params=json.dumps(image), headers=headers)

    # If the request went through correctly, print it out.  Otherwise error out, and print the response.
    if resp.ok:
        return(resp)
        exit(0)
    else:
        print "Post image transfer failed: ", resp.content
        exit(1)

def get_image_list (pe_user,pe_pass):
    # Set the headers, url, and payload
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    url     = "https://@@{PE_Address}@@:9440/PrismGateway/services/rest/v2.0/images/?include_vm_disk_sizes=false&include_vm_disk_paths=false"
    payload={}
    # Make the request
    resp = urlreq(url, verb='GET', auth='BASIC', user=pe_user, passwd=pe_pass, params=json.dumps(payload), headers=headers)

    # If the request went through correctly, print it out.  Otherwise error out, and print the response.
    if resp.ok:
        return(resp)
        exit(0)
    else:
        print "Post request failed getting list of images", resp.content
        exit(1)

def get_cluster_details (pe_user,pe_pass):
    # Set the headers, url, and payload
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    url     = "https://@@{PE_Address}@@:9440/PrismGateway/services/rest/v2.0/cluster/"
    payload={}
    # Make the request
    resp = urlreq(url, verb='GET', auth='BASIC', user=pe_user, passwd=pe_pass, params=json.dumps(payload), headers=headers)

    # If the request went through correctly, print it out.  Otherwise error out, and print the response.
    if resp.ok:
        return(resp)
        exit(0)
    else:
        print "Post request failed getting cluster details", resp.content
        exit(1)

############ MAIN ####################
pe_user = '@@{PE_Creds.username}@@'
pe_pass = '@@{PE_Creds.secret}@@'
pc_user = '@@{PC_Creds.username}@@'
pc_pass = '@@{PC_Creds.secret}@@'

resp = get_image_list(pe_user,pe_pass)
#print json.dumps(json.loads(resp.content), indent=4)

for image in json.loads(resp.content)['entities']:
    if image['name'] == '@@{Image_Name}@@':
        # Get UUID for the image to be transfered
        uuid = image['uuid']
        print ("Image UUID: {}".format(uuid))

image = {}
image_spec={}
image['image_reference_list']=[]

image_spec['kind']="image"
image_spec['name']="@@{Image_Name}@@"
image_spec['uuid']=uuid
image['image_reference_list'].append(image_spec)

image['cluster_reference']={}
#Get the cluster details for where the image is currently
cluster_details = get_cluster_details(pe_user,pe_pass)

image['cluster_reference']['kind']="cluster"
image['cluster_reference']['name']=json.loads(cluster_details.content)['name']
image['cluster_reference']['uuid']=json.loads(cluster_details.content)['uuid']

print ("Transfering image control from PE to PC")
resp = transfer_image(pc_user,pc_pass,image)
