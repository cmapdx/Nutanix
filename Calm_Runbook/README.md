# Calm Runbook related scripts 

The scripts in this repository can be combined in multiple ways.  Each script can be used indepently, or together to create a more complex Runbook.

One example of a Runbook that can be created:
Create an image from an existing VM without changing the VM.  The steps to accomplish this would be:
* Power the VM down using the GracefulShutdown script
* Sleep while the VM powers down
* Clone the VM with the CloneVM eScript
* Sleep for a few seconds to allow the clone to finish
* Power the clone VM up
* Sleep to allow boot 
* Run the Sysprep script from a proxy Windows VM
* Sleep for a few seconds to allow the VM time to finish powering down
* Rename the existing image if archives are being kept
* Create the image from the clone
* Sleep for 10 minutes or so to allow the image task to complete
* Delete the clone VM
* Cleanup archives if prior versions of the image are being kept
* Transfer the image control to Prism Central

Some of the steps can be run in parallel. 