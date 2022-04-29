#This script is used to read a CSV file and update the VLAN variables
#
#The 1st line of the CSV must contain headers that match up with $line.HEADER_VALUE
#Example
# Network,Name,Gateway,DNS1,DNS2,Net_Mask
# 10.0.0.0/24,Server_300,10.0.0.1,10.0.100.10,10.0.100.20,255.255.255.0
#
# For testing local on system
#$var_name = "Server_300"
#
# For Calm usage
$var_name = "@@{Network_Name}@@"
$csv = Import-Csv -Path "C:\Prod Networks.csv"

Foreach ($line in $csv) {
    If ($line.Name -eq $var_name) {
        #Write-Host "Network=$($line.Network)"
        #Write-Host "Network_Name=$($line.Name)"
        Write-Host "Gateway=$($line.Gateway)"
        Write-Host "DNS1=$($line.DNS1)"
        Write-Host "DNS2=$($line.DNS2)"
        Write-Host "Mask=$($line.Net_Mask)"
    }
}


