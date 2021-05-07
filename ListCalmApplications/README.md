# Get List of Calm Applications

When creating an event trigger in Playbooks that calls a function such as Scale Out you will need the Application UUID from the deployed blueprint.  This script will call Prism Central and list out all the deployed applications and their UUID.

There is an example at the bottom of the script for how to call the ScaleOut function for an application.  

You will need to install any missing modules needed to run this script.

Inputs:
* User ID for Prism Central
* Password for Prism Central
* Prism Central IP or DNS name

Sample Output:

    Prism IP or DNS name: 10.48.71.98
    User ID for Prism: admin
    Password for Prism:

    App Name: CMA-Linux3T           App UUID: f98fc27c-cc89-4953-834d-e6fc339d203f

    App Name: CMA-LAMP-Deployment   App UUID: bace73c0-68f4-4b76-b046-0cd061d9af3f

    App Name: Escript               App UUID: 5a99cc8d-41b2-467b-9693-cdde9519b998
   
   If you uncomment the last few lines and use an App UUID you will see additional output like this:
    
    {
       "runlog_uuid": "012c2a85-b8fe-409f-b15e-b82a80041117"
    }

Example video showing how to create a Playbook with CPU Contention trigger and a ScaleOut repsone:

https://www.youtube.com/watch?v=PoPN7QRZdYg

