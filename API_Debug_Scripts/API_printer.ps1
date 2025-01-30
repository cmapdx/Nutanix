<#
.SYNOPSIS
  Dump API content for VMs and Networks from PE and PC.
.DESCRIPTION
  Created this to capture the API details for VMs and Networks from PE and PC for debugging. 
.PARAMETER help
  Displays a help message (seriously, what did you think this was?)
.PARAMETER history
  Displays a release history for this script (provided the editors were smart enough to document this...)
.PARAMETER log
  Specifies that you want the output messages to be written in a log file as well as on the screen.
.PARAMETER debugme
  Turns off SilentlyContinue on unexpected error messages.
.EXAMPLE
.\API_Printer.ps1
.LINK
  http://www.nutanix.com/services
.NOTES
  Author: Corey Anson (corey.anson@nutanix.com)
  Revision: January 30th 2025
#>

#region parameters
Param
(
    #[parameter(valuefrompipeline = $true, mandatory = $true)] [PSObject]$myParam1,
    [parameter()] [switch]$help,
    [parameter()] [switch]$history,
    [parameter()] [switch]$debugme
)
#endregion

#region functions
#this function is used to process output to console (timestamped and color coded) and log file
function Write-LogOutput {
    <#
.SYNOPSIS
Outputs color coded messages to the screen and/or log file based on the category.

.DESCRIPTION
This function is used to produce screen and log output which is categorized, time stamped and color coded.

.PARAMETER Category
This the category of message being outputed. If you want color coding, use either "INFO", "WARNING", "ERROR" or "SUM".

.PARAMETER Message
This is the actual message you want to display.

.PARAMETER LogFile
If you want to log output to a file as well, use logfile to pass the log file full path name.

.NOTES
Author: Corey Anson (corey.anson@nutanix.com)

.EXAMPLE
.\Write-LogOutput -category "ERROR" -message "You must be kidding!"
Displays an error message.

.LINK
https://github.com/cmapdx
#>
    [CmdletBinding(DefaultParameterSetName = 'None')] #make this function advanced

    param
    (
        [Parameter(Mandatory)]
        [ValidateSet('INFO', 'WARNING', 'ERROR', 'SUM', 'SUCCESS', 'STEP', 'DEBUG', 'DATA')]
        [string]
        $Category,

        [string]
        $Message,

        [string]
        $LogFile
    )

    process {
        $Date = get-date #getting the date so we can timestamp the output entry
        $FgColor = "Gray" #resetting the foreground/text color
        switch ($Category) {
            #we'll change the text color depending on the selected category
            "INFO" { $FgColor = "Green" }
            "WARNING" { $FgColor = "Yellow" }
            "ERROR" { $FgColor = "Red" }
            "SUM" { $FgColor = "Magenta" }
            "SUCCESS" { $FgColor = "Cyan" }
            "STEP" { $FgColor = "Magenta" }
            "DEBUG" { $FgColor = "White" }
            "DATA" { $FgColor = "Gray" }
        }

        Write-Host -ForegroundColor $FgColor "$Date [$category] $Message" #write the entry on the screen
        if ($LogFile) {
            #add the entry to the log file if -LogFile has been specified
            Add-Content -Path $LogFile -Value "$Date [$Category] $Message"
            #Suppress screen output for unattended execution.
            #Write-Verbose -Message "Wrote entry to log file $LogFile" #specifying that we have written to the log file if -verbose has been specified
        }
    }

}#end function Write-LogOutput


#this function is used to make a REST api call to Prism
function Invoke-PrismAPICall {
    <#
.SYNOPSIS
  Makes api call to prism based on passed parameters. Returns the json response.
.DESCRIPTION
  Makes api call to prism based on passed parameters. Returns the json response.
.NOTES
  Author: Stephane Bourdeaud
.PARAMETER method
  REST method (POST, GET, DELETE, or PUT)
.PARAMETER credential
  PSCredential object to use for authentication.
PARAMETER url
  URL to the api endpoint.
PARAMETER payload
  JSON payload to send.
.EXAMPLE
.\Invoke-PrismAPICall -credential $MyCredObject -url https://myprism.local/api/v3/vms/list -method 'POST' -payload $MyPayload
Makes a POST api call to the specified endpoint with the specified payload.
#>
    param
    (
        [parameter(mandatory = $true)]
        [ValidateSet("POST", "GET", "DELETE", "PUT")]
        [string] 
        $method,
    
        [parameter(mandatory = $true)]
        [string] 
        $url,

        [parameter(mandatory = $false)]
        [string] 
        $payload,
    
        [parameter(mandatory = $true)]
        [System.Management.Automation.PSCredential]
        $credential,
    
        [parameter(mandatory = $false)]
        [switch] 
        $checking_task_status
    )

    begin {
    
    }
    process {
        #if (!$checking_task_status) { Write-LogOutput -Category "INFO" -LogFile $LogFile -Message "Making a $method call to $url" }
        try {
            #check powershell version as PoSH 6 Invoke-RestMethod can natively skip SSL certificates checks and enforce Tls12 as well as use basic authentication with a pscredential object
            if ($PSVersionTable.PSVersion.Major -gt 5) {
                $headers = @{
                    "Content-Type" = "application/json";
                    "Accept"       = "application/json"
                }
                if ($payload) {
                    $resp = Invoke-RestMethod -Method $method -Uri $url -Headers $headers -Body $payload -SkipCertificateCheck -SslProtocol Tls12 -Authentication Basic -Credential $credential -ErrorAction Stop
                }
                else {
                    $resp = Invoke-RestMethod -Method $method -Uri $url -Headers $headers -SkipCertificateCheck -SslProtocol Tls12 -Authentication Basic -Credential $credential -ErrorAction Stop
                }
            }
            else {
                $username = $credential.UserName
                $password = $credential.Password
                $headers = @{
                    "Authorization" = "Basic " + [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($username + ":" + ([System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($password))) ));
                    "Content-Type"  = "application/json";
                    "Accept"        = "application/json"
                }
                if ($payload) {
                    $resp = Invoke-RestMethod -Method $method -Uri $url -Headers $headers -Body $payload -ErrorAction Stop
                }
                else {
                    $resp = Invoke-RestMethod -Method $method -Uri $url -Headers $headers -ErrorAction Stop
                }
            }
            #if (!$checking_task_status) { Write-LogOutput -Category "SUCCESS" -LogFile $LogFile -Message "Call $method to $url succeeded." } 
            if ($debugme) { Write-LogOutput -Category "DEBUG" LogFile $LogFile -Message "Response Metadata: $($resp.metadata | ConvertTo-Json)" }
            #Write-Host "$(Get-Date) [INFO] Response: $($resp | ConvertTo-Json)" -ForegroundColor Yellow
        } catch {
            $saved_error = $($_.Exception.Message)
            Write-Host "$(Get-Date) [INFO] Headers: $($headers | ConvertTo-Json)"
            Write-Host "$(Get-Date) [INFO] Payload: $($payload)" -ForegroundColor Yellow
            Write-Host "$(Get-Date) [INFO] Response: $($resp | ConvertTo-Json)" -ForegroundColor Yellow
            if ($resp) {
                Throw "$(Get-Date) [ERROR] Error code: $($resp.StatusCode) with message: $($resp.message_list.details)"
            } else {
                Throw "$(Get-Date) [ERROR] $($saved_error)"
            } 
        }
        finally {
            #add any last words here; this gets processed no matter what
        }
    } end {
        return $resp
    }    
}


#helper-function Get-RESTError
function Help-RESTError {
    $global:helpme = $body
    $global:helpmoref = $moref
    $global:result = $_.Exception.Response.GetResponseStream()
    $global:reader = New-Object System.IO.StreamReader($global:result)
    $global:responseBody = $global:reader.ReadToEnd();

    return $global:responsebody

    break
}#end function Get-RESTError



#region prepwork
$HistoryText = @'
Maintenance Log
Date       By   Updates (newest updates at the top)
---------- ---- ---------------------------------------------------------------
01/30/2023 ca   Initial release.
################################################################################
'@
$myvarScriptName = ".\API_printer.ps1"

if ($help) { get-help $myvarScriptName; exit }
if ($History) { $HistoryText; exit }

$myvarElapsedTime = [System.Diagnostics.Stopwatch]::StartNew() #used to store script begin timestamp

$prismcentral = Read-Host "Prism Central IP"
$prismelement = Read-Host "Prism Element IP"
$prismUser = Read-Host "User ID"
$prismPass = Read-Host "Password" -AsSecureString

$LogDate = Get-Date -Format "yyyyMMdd.HHmm"
$LogFile = "${PSScriptRoot}\API_printer.${LogDate}.log"
 
# conversion only needed when read from file
#$PrismSecurePassword = ConvertTo-SecureString $prismPass -AsPlainText -Force
#$prismCredentials = New-Object PSCredential ($PrismUser, $PrismSecurePassword)
$prismCredentials = New-Object PSCredential ($prismUser, $prismPass)
#################################################################################################################
# End Environment Setup
#################################################################################################################

# # PRISM ELEMENT # #
$url = "https://$($prismelement):9440/PrismGateway/services/rest/v2.0/vms/"
$method = "GET"
#$content = @{ 
#    kind = "vm" 
#}
$content = @{}
$payload = (ConvertTo-Json $content -Depth 4)
Write-LogOutput -Category "INFO" -LogFile $LogFile -Message "Getting list of VMs"
$myvar_resp = Invoke-PrismAPICall -method $method -url $url -credential $prismCredentials -payload $payload

$VM_List = "${PSScriptRoot}\PE_VMS_List.${LogDate}.json"
Add-Content -Path $VM_List -Value "$($myvar_resp | ConvertTo-Json -Depth 9)"

foreach ($vms in $myvar_resp.entities) {
    $myvar_vmsUUID = $vms.uuid
    $url = "https://$($prismelement):9440/PrismGateway/services/rest/v2.0/vms/$($myvar_vmsUUID)"
    Write-LogOutput -Category "INFO" -LogFile $LogFile -Message "Getting Details for VM: $($vms.name)"
    $myvar_vmsDetails = Invoke-PrismAPICall -method $method -url $url -credential $prismCredentials -payload $payload
    if ($myvar_vmsDetails) {
        $VM_Details = "${PSScriptRoot}\PE_VM_$($myvar_vmsDetails.name).${LogDate}.json"
        Add-Content -Path $VM_Details -Value "$($myvar_vmsDetails | ConvertTo-Json -Depth 9)"
        Write-LogOutput -Category "INFO" -LogFile $LogFile -Message "Getting NIC Details for VM: $($vms.name)"
        $url = "https://$($prismelement):9440/PrismGateway/services/rest/v2.0/vms/$($myvar_vmsUUID)/nics/"
        $myvar_vmsNicDetails = Invoke-PrismAPICall -method $method -url $url -credential $prismCredentials -payload $payload
        if ($myvar_vmsNicDetails) {
            $VM_NicDetails = "${PSScriptRoot}\PE_VM_NIC_$($myvar_vmsDetails.name).${LogDate}.json"
            Add-Content -Path $VM_NicDetails -Value "$($myvar_vmsNicDetails | ConvertTo-Json -Depth 9)"
        }
        
    } else {
        Write-LogOutput -Category "ERROR" -LogFile $LogFile -Message "Missing Details for Name: $($vms.name)"
    }
}

$url = "https://$($prismelement):9440/PrismGateway/services/rest/v2.0/networks/"
$method = "GET"
#$content = @{ 
#    kind = "vm" 
#}
$content = @{}
$payload = (ConvertTo-Json $content -Depth 4)
Write-LogOutput -Category "INFO" -LogFile $LogFile -Message "Getting Network List"
$myvar_resp = Invoke-PrismAPICall -method $method -url $url -credential $prismCredentials -payload $payload

$VM_List = "${PSScriptRoot}\PE_Networks_List.${LogDate}.json"
Add-Content -Path $VM_List -Value "$($myvar_resp | ConvertTo-Json -Depth 9)"

foreach ($vms in $myvar_resp.entities) {
    $myvar_vmsUUID = $vms.uuid
    $url = "https://$($prismelement):9440/PrismGateway/services/rest/v2.0/networks/$($myvar_vmsUUID)"
    Write-LogOutput -Category "INFO" -LogFile $LogFile -Message "Getting Details for Network: $($vms.name)"
    $myvar_vmsDetails = Invoke-PrismAPICall -method $method -url $url -credential $prismCredentials -payload $payload
    if ($myvar_vmsDetails) {
        $VM_Details = "${PSScriptRoot}\PE_Network_$($myvar_vmsDetails.name).${LogDate}.json"
        Add-Content -Path $VM_Details -Value "$($myvar_vmsDetails | ConvertTo-Json -Depth 9)"
        $url = "https://$($prismelement):9440/PrismGateway/services/rest/v2.0/networks/$($myvar_vmsUUID)/addresses/"
        Write-LogOutput -Category "INFO" -LogFile $LogFile -Message "Getting Network Addresses for Network: $($vms.name)"
        $myvar_vmsNicDetails = Invoke-PrismAPICall -method $method -url $url -credential $prismCredentials -payload $payload
        if ($myvar_vmsNicDetails) {
            $VM_NicDetails = "${PSScriptRoot}\PE_Networks_Addresses_$($myvar_vmsDetails.name).${LogDate}.json"
            Add-Content -Path $VM_NicDetails -Value "$($myvar_vmsNicDetails | ConvertTo-Json -Depth 9)"
        }
        
    } else {
        Write-LogOutput -Category "ERROR" -LogFile $LogFile -Message "Missing Details for Network Name: $($vms.name)"
    }
}

# # PRISM CENTRAL # #
$url = "https://$($prismcentral):9440/api/nutanix/v3/vms/list"
$method = "POST"
$content = @{ 
    kind = "vm" 
}
$payload = (ConvertTo-Json $content -Depth 4)
Write-LogOutput -Category "INFO" -LogFile $LogFile -Message "Getting list of VMs from PC"
$myvar_resp = Invoke-PrismAPICall -method $method -url $url -credential $prismCredentials -payload $payload

$VM_List = "${PSScriptRoot}\PC_VMS_List.${LogDate}.json"
Add-Content -Path $VM_List -Value "$($myvar_resp | ConvertTo-Json -Depth 9)"

foreach ($vms in $myvar_resp.entities) {
    $myvar_vmsUUID = $vms.metadata.uuid
    $url = "https://$($prismcentral):9440/api/nutanix/v3/vms/$($myvar_vmsUUID)"
    $method = "GET"
    $content = @{}
    $payload = (ConvertTo-Json $content -Depth 4)
    Write-LogOutput -Category "INFO" -LogFile $LogFile -Message "Getting PC Details for VM: $($vms.spec.name)"
    $myvar_vmsDetails = Invoke-PrismAPICall -method $method -url $url -credential $prismCredentials -payload $payload
    if ($myvar_vmsDetails) {
        $VM_Details = "${PSScriptRoot}\PC_VM_$($myvar_vmsDetails.spec.name).${LogDate}.json"
        Add-Content -Path $VM_Details -Value "$($myvar_vmsDetails | ConvertTo-Json -Depth 9)"
               
    } else {
        Write-LogOutput -Category "ERROR" -LogFile $LogFile -Message "Missing Details for Name: $($vms.spec.name)"
    }
}
#    Subnets   #
$url = "https://$($prismcentral):9440/api/nutanix/v3/subnets/list"
$method = "POST"
$content = @{ 
    kind = "subnet" 
}
$payload = (ConvertTo-Json $content -Depth 4)
Write-LogOutput -Category "INFO" -LogFile $LogFile -Message "Getting list of subnets from PC"
$myvar_resp = Invoke-PrismAPICall -method $method -url $url -credential $prismCredentials -payload $payload

$VM_List = "${PSScriptRoot}\PC_Subnet_List.${LogDate}.json"
Add-Content -Path $VM_List -Value "$($myvar_resp | ConvertTo-Json -Depth 9)"

foreach ($vms in $myvar_resp.entities) {
    $myvar_vmsUUID = $vms.metadata.uuid
    $url = "https://$($prismcentral):9440/api/nutanix/v3/subnets/$($myvar_vmsUUID)"
    $method = "GET"
    $content = @{}
    $payload = (ConvertTo-Json $content -Depth 4)
    Write-LogOutput -Category "INFO" -LogFile $LogFile -Message "Getting PC Details for Subnet: $($vms.spec.name)"
    $myvar_vmsDetails = Invoke-PrismAPICall -method $method -url $url -credential $prismCredentials -payload $payload
    if ($myvar_vmsDetails) {
        $VM_Details = "${PSScriptRoot}\PC_Subnet_$($myvar_vmsDetails.spec.name).${LogDate}.json"
        Add-Content -Path $VM_Details -Value "$($myvar_vmsDetails | ConvertTo-Json -Depth 9)"
               
    } else {
        Write-LogOutput -Category "ERROR" -LogFile $LogFile -Message "Missing Details for Subnet Name: $($vms.spec.name)"
    }
}


#let's figure out how much time this all took
Write-LogOutput -Category "SUM" -LogFile $LogFile -Message "total processing time: $($myvarElapsedTime.Elapsed.ToString())"

#cleanup after ourselves and delete all custom variables
Remove-Variable myvar* -ErrorAction SilentlyContinue
Remove-Variable ErrorActionPreference -ErrorAction SilentlyContinue
Remove-Variable help -ErrorAction SilentlyContinue
Remove-Variable history -ErrorAction SilentlyContinue
Remove-Variable log -ErrorAction SilentlyContinue
Remove-Variable debugme -ErrorAction SilentlyContinue
#endregion
