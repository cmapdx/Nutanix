#This script is used to Sysprep the machine at the provided IP address
#Because the session to run Sysprep must remain open while it runs, this script must be run on a proxy system
#
# Credentials
#Proxy_Cred - Windows proxy system login credentials, needs to be AD
#
# Variables
#VM_Address - Needs to be DNS name

$secureString = '@@{Proxy_Cred.secret}@@' | ConvertTo-SecureString -AsPlainText -Force
$credential = New-Object pscredential('@@{Proxy_Cred.username}@@', $secureString)

Write-Output "Starting Sysprep"

$sysprep= 'C:\Windows\System32\Sysprep\Sysprep.exe'
$arg = '/generalize /oobe /shutdown /quiet'
$command = { Start-Process -FilePath $sysprep -ArgumentList $arg -Wait }

try {
    Invoke-Command -ComputerName @@{VM_Address}@@ -Credential $credential -ScriptBlock { $command }
}
catch {
    Write-Output "Sysprep has finished"
    Exit 0
}
finally {
    Write-Output "Syprep has finished in the Finally block"
    Exit 0
}