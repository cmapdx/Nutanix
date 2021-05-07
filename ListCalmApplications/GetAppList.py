# Author: Corey Anson
# This script will print the name and UUID for applications deployed using Calm
# The UUID can be used to trigger services such as ScaleOut 
# Example code for calling a function provided at the end

import requests
import json
import getpass
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
 
def make_request(ip_address,user,passwd,call_type,data_list):
    header = {"content-type": "application/json"}
    auth = HTTPBasicAuth(user, passwd)
    url_list = "https://{0}:9440/api/nutanix/v3/{1}".format(ip_address,call_type)
    try:
        res_list = requests.post(url=url_list, data=json.dumps(data_list), auth=auth, headers=header, verify=False)
        return res_list
    except Exception as ex:
        print ("There was an issue requesting the VM list.")
        print (ex.args)

ip_address = input ("Prism IP or DNS name: ")
user = input ("User ID for Prism: ")
password = getpass.getpass('Password for Prism: ')

payload = {'kind':'app'}
app_list = make_request(ip_address,user,password,"apps/list",payload)

if app_list.ok:
    for app in json.loads(app_list.content)['entities']:
            app_name = app['status']['name']
            app_uuid = app['status']['uuid']
            print ("\nApp Name: {:20s}  App UUID: {:70s}".format(app_name,app_uuid))

# This section of code uses the UUID from an application listed above to call the ScaleOut function
#payload = {'name':'ScaleOut'}
#app_call = make_request(ip_address,user,password,"apps/f98fc27c-cc89-4953-834d-e6fc339d203f/actions/run",payload) 
#print (json.dumps(json.loads(app_call.content), indent=4))
#
# Sample Output from the ScaleOut call above
# {
#    "runlog_uuid": "012c2a85-b8fe-409f-b15e-b82a80041117"
# }
