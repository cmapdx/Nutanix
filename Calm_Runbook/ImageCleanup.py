# Get a list of image files and update a specific one
#
# Creds
#PC_Creds - Prism Central login credentials
#
# Variables
#PC_Address - IP or DNS name
#Image_Name - base name for the image
#Number_of_Archives - number of dated images to keep, does not count the fresh image

def get_image_list (pc_user,pc_pass):
    # Set the headers, url, and payload
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    url     = "https://@@{PC_Address}@@:9440/api/nutanix/v3/images/list"
    payload={  "kind": "image",
                "sort_order": "DESCENDING",
                "sort_attribute": "name"}
    # Make the request
    resp = urlreq(url, verb='POST', auth='BASIC', user=pc_user, passwd=pc_pass, params=json.dumps(payload), headers=headers)

    # If the request went through correctly, print it out.  Otherwise error out, and print the response.
    if resp.ok:
        return(resp)
        exit(0)
    else:
        print "Post request failed getting list of images", resp.content
        exit(1)

def delete_image (pc_user,pc_pass,uuid):
    # Set the headers, url, and payload
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    url     = "https://@@{PC_Address}@@:9440/api/nutanix/v3/images/"+uuid
    payload={}
    # Make the request
    resp = urlreq(url, verb='DELETE', auth='BASIC', user=pc_user, passwd=pc_pass, params=json.dumps(payload), headers=headers)

    # If the request went through correctly, print it out.  Otherwise error out, and print the response.
    if resp.ok:
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
#print json.dumps(json.loads(resp.content), indent=4)
number_to_keep = @@{Number_of_Archives}@@
base_archive_name = "@@{Image_Name}@@ - 20"
iteration = 0

for image in json.loads(resp.content)['entities']:
    if image['status']['name'].startswith(base_archive_name) and image['status']['description'].startswith("Archive: "):
        # Get UUID and Image Name
        uuid = image['metadata']['uuid']
        name = image['status']['name']
        create_time = image['metadata']['creation_time']
        iteration +=1
        if iteration > number_to_keep:
            print ("DELETING: UUID: {}  Name: {}  Create Time: {}".format(uuid,name,create_time))
            delete_image(pc_user,pc_pass,uuid)
        else:
            print ("Keeping: UUID: {}  Name: {}  Create Time: {}".format(uuid,name,create_time))
