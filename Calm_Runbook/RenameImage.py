# Get a list of image files and update a specific one
#
# Creds
#PC_Creds - Prism Central login credentials
#
# Variables
#PC_Address - Prism Central IP or DNS Name
#Image_Name - name of existing image, also used for the name of the new image

def get_image_list (pc_user,pc_pass):
    # Set the headers, url, and payload
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    url = "https://@@{PC_Address}@@:9440/api/nutanix/v3/images/list"
    payload = {}

    # Make the request
    resp = urlreq(url, verb='POST', auth='BASIC', user=pc_user, passwd=pc_pass, params=json.dumps(payload), headers=headers)

    # If the request went through correctly, print it out.  Otherwise error out, and print the response.
    if resp.ok:
        return(resp)
        exit(0)
    else:
        print "Post request failed getting list of images", resp.content
        exit(1)

def update_image_name (pc_user,pc_pass,updated_json):
    # Set the headers, url, and payload
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    url = "https://@@{PC_Address}@@:9440/api/nutanix/v3/images/"+uuid
    #payload = {}

    # Make the request
    resp = urlreq(url, verb='PUT', auth='BASIC', user=pc_user, passwd=pc_pass, params=json.dumps(updated_json), headers=headers)

    # If the request went through correctly, print it out.  Otherwise error out, and print the response.
    if resp.ok:
        print ("Name Updated")
        return(resp)
        exit(0)
    else:
        print "Post request failed getting list of images", resp.content
        exit(1)

############# MAIN ############################
# Set the credentials
pc_user = '@@{PC_Creds.username}@@'
pc_pass = '@@{PC_Creds.secret}@@'

resp = get_image_list(pc_user,pc_pass)
# Debug output, prints all JSON output for image list
#print json.dumps(json.loads(resp.content), indent=4)

for image in json.loads(resp.content)['entities']:
    if image['status']['name'] == '@@{Image_Name}@@':
        # Image name matches provided name
        uuid = image['metadata']['uuid']
        print ("Image UUID: {}".format(uuid))
        name=image['spec']['name']+" - @@{calm_now}@@"
        print ("New Name: {}".format(name))
        
        updated_json = {}

        updated_json['spec'] = {}
        updated_json['spec']['name'] = name
        
        updated_json['spec']['resources'] = {}
        updated_json['spec']['resources']['image_type'] = image['spec']['resources']['image_type']
        updated_json['spec']['resources']['source_uri'] = image['spec']['resources']['source_uri']
        
        # Update description to add comment about being previous version
        updated_json['spec']['description'] = "Archive: "+image['spec']['description']

        updated_json['metadata'] = {}
        updated_json['metadata']['last_update_time'] = image['metadata']['last_update_time']
        updated_json['metadata']['kind'] = image['metadata']['kind']
        updated_json['metadata']['uuid'] = image['metadata']['uuid']
        updated_json['metadata']['creation_time'] = image['metadata']['creation_time']
        updated_json['metadata']['spec_version'] = image['metadata']['spec_version']

        print ("Finished creating updated_json dict with existing values")
        output = update_image_name (pc_user,pc_pass,updated_json)
