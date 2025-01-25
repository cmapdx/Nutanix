<#
.SYNOPSIS
  Cleanup of snapshots.
.DESCRIPTION
  Using the v3 API on Prism Element, list and delete snapshots the same way the backup software does.  Use this to remove old snapshots. 
.PARAMETER help
  Displays a help message (seriously, what did you think this was?)
.PARAMETER history
  Displays a release history for this script (provided the editors were smart enough to document this...)
.PARAMETER log
  Specifies that you want the output messages to be written in a log file as well as on the screen.
.PARAMETER debugme
  Turns off SilentlyContinue on unexpected error messages.
.EXAMPLE
.\VM_Snapshot_Cleanup.ps1
.LINK
  http://www.nutanix.com/services
.NOTES
  Author: Corey Anson (corey.anson@nutanix.com)
  Revision: January 24th 2025
#>

#region parameters
Param
(
    #[parameter(valuefrompipeline = $true, mandatory = $true)] [PSObject]$myParam1,
    [parameter()] [switch]$help,
    [parameter()] [switch]$history,
    [parameter()] [switch]$log,
    [parameter()] [switch]$debugme,
    [parameter()] [string]$prismelement,
    [parameter()] [System.Management.Automation.PSCredential]$prismCredentials,
    [parameter()] [string]$LogFile,
    [parameter()] [string]$config = "$($PSScriptRoot)\config.json"
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


#this function loads a powershell module
function LoadModule {
    #tries to load a module, import it, install it if necessary
    <#
.SYNOPSIS
Tries to load the specified module and installs it if it can't.
.DESCRIPTION
Tries to load the specified module and installs it if it can't.
.NOTES
Author: Stephane Bourdeaud
.PARAMETER module
Name of PowerShell module to import.
.EXAMPLE
PS> LoadModule -module PSWriteHTML
#>
    param 
    (
        [string] $module
    )

    begin {
        
    }

    process {   
        Write-LogOutput -Category "INFO" -LogFile $LogFile -Message "Trying to get module $($module)..."
        if (!(Get-Module -Name $module)) {
            #we could not get the module, let's try to load it
            try {
                #import the module
                Import-Module -Name $module -ErrorAction Stop
                Write-LogOutput -Category "SUCCESS" -LogFile $LogFile -Message "Imported module '$($module)'!"
            }#end try
            catch {
                #we couldn't import the module, so let's install it
                Write-LogOutput -Category "INFO" -LogFile $LogFile -Message "Installing module '$($module)' from the Powershell Gallery..."
                try {
                    #install module
                    Install-Module -Name $module -Scope CurrentUser -Force -ErrorAction Stop
                }
                catch {
                    #could not install module
                    Write-LogOutput -Category "ERROR" -LogFile $LogFile -Message "Could not install module '$($module)': $($_.Exception.Message)"
                    exit 1
                }

                try {
                    #now that it is intalled, let's import it
                    Import-Module -Name $module -ErrorAction Stop
                    Write-LogOutput -Category "SUCCESS" -LogFile $LogFile -Message "Imported module '$($module)'!"
                }#end try
                catch {
                    #we couldn't import the module
                    Write-LogOutput -Category "ERROR" -LogFile $LogFile -Message "Unable to import the module $($module).psm1 : $($_.Exception.Message)"
                    Write-LogOutput -Category "WARNING" -LogFile $LogFile -Message "Please download and install from https://www.powershellgallery.com"
                    Exit 1
                }#end catch
            }#end catch
        }
    }

    end {

    }
}


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


function Get-PrismElementObjectList {
    #retrieves multiple pages of Prism REST objects v3
    [CmdletBinding()]
    param 
    (
        [Parameter(mandatory = $true)][string] $pc,
        [Parameter(mandatory = $true)][string] $object,
        [Parameter(mandatory = $true)][string] $kind
    )

    begin {
        if (!$length) { $length = 100 } #we may not inherit the $length variable; if that is the case, set it to 100 objects per page
        $total, $cumulated, $first, $last, $offset = 0 #those are used to keep track of how many objects we have processed
        [System.Collections.ArrayList]$myvarResults = New-Object System.Collections.ArrayList($null) #this is variable we will use to keep track of entities
        $url = "https://{0}:9440/api/nutanix/v3/{1}/list" -f $pc, $object
        $method = "POST"
        $content = @{
            kind   = $kind;
            offset = 0;
            length = $length
        }
        $payload = (ConvertTo-Json $content -Depth 4) #this is the initial payload at offset 0
    }
    
    process {
        Do {
            try {
                $resp = Invoke-PrismAPICall -method $method -url $url -payload $payload -credential $prismCredentials
                
                if ($total -eq 0) { $total = $resp.metadata.total_matches } #this is the first time we go thru this loop, so let's assign the total number of objects
                $first = $offset #this is the first object for this iteration
                $last = $offset + ($resp.entities).count #this is the last object for this iteration
                if ($total -le $length) {
                    #we have less objects than our specified length
                    $cumulated = $total
                }
                else {
                    #we have more objects than our specified length, so let's increment cumulated
                    $cumulated += ($resp.entities).count
                }
                
                Write-LogOutput -Category "INFO" -LogFile $LogFile -Message "Processing results from $(if ($first) {$first} else {"0"}) to $($last) out of $($total)"
                if ($debugme) { Write-LogOutput -Category "DEBUG" -LogFile $LogFile -Message "Response Metadata: $($resp.metadata | ConvertTo-Json)" }
    
                #grab the information we need in each entity
                ForEach ($entity in $resp.entities) {                
                    $myvarResults.Add($entity) | Out-Null
                }
                
                $offset = $last #let's increment our offset
                #prepare the json payload for the next batch of entities/response
                $content = @{
                    kind   = $kind;
                    offset = $offset;
                    length = $length
                }
                $payload = (ConvertTo-Json $content -Depth 4)
            }
            catch {
                $saved_error = $_.Exception.Message
                # Write-Host "$(Get-Date) [INFO] Headers: $($headers | ConvertTo-Json)"
                if ($payload) { Write-LogOutput -Category "INFO" -LogFile $LogFile -Message "Payload: $payload" }
                Throw "$(get-date) [ERROR] $saved_error"
            }
            finally {
                #add any last words here; this gets processed no matter what
            }
        }
        While ($last -lt $total)
    }
    
    end {
        return $myvarResults
    }
}



#region prepwork
$HistoryText = @'
Maintenance Log
Date       By   Updates (newest updates at the top)
---------- ---- ---------------------------------------------------------------
01/24/2023 ca   Initial release.
################################################################################
'@
$myvarScriptName = ".\VM_Snapshot_Cleanup.ps1"

if ($help) { get-help $myvarScriptName; exit }
if ($History) { $HistoryText; exit }

$myvarElapsedTime = [System.Diagnostics.Stopwatch]::StartNew() #used to store script begin timestamp

$myjsonfile = Get-Content $config | ConvertFrom-Json -AsHashtable
$prismelement = $myjsonfile.PrismElement
if ($myjsonfile.ContainsKey('UserName')) { $prismUser = $myjsonfile.UserName }
if ($myjsonfile.ContainsKey('Password')) { $prismPass = $myjsonfile.Password }
$LogDate = Get-Date -Format "yyyyMMdd.HHmm"
if ($myjsonfile.ContainsKey('Logfile')) {
    $LogFile = $myjsonfile.Logfile
    $LogFile += "${LogDate}.log"
}
else {
    $LogFile = "${PSScriptRoot}\VM_Snapshot_Cleanup.${LogDate}.log"
}

if (!$prismPass) {
    #No password provided in config file
    Write-LogOutput -Category "ERROR" -LogFile $LogFile -Message "No password found in configuration file, unable to continue."
    exit 1
} 
    
$username = $prismUser
$PrismSecurePassword = ConvertTo-SecureString $prismPass -AsPlainText -Force
$prismCredentials = New-Object PSCredential ($username, $PrismSecurePassword)
#################################################################################################################
# End Environment Setup
#################################################################################################################

Write-LogOutput -Category "INFO" -LogFile $LogFile -Message "Get a list of Snapshots."
Write-Host " THE DEFAULT ACTION IS TO DELETE.  No Input will delete the snapshot.  Enter n to keep."
$url = "https://$($prismelement):9440/api/nutanix/v3/vm_snapshots/list"
$method = "POST"
$content = @{ 
    kind = "vm_snapshot" 
}
$payload = (ConvertTo-Json $content -Depth 4)
$myvar_resp = Invoke-PrismAPICall -method $method -url $url -credential $prismCredentials -payload $payload

foreach ($snapshot in $myvar_resp.entities) {
    $myvar_snapUUID = $snapshot.metadata.uuid
    $url = "https://$($prismelement):9440/api/nutanix/v3/vm_snapshots/$($myvar_snapUUID)"
    $method = "GET"
    $content = @{}
    $payload = (ConvertTo-Json $content -Depth 4)
    $myvar_snapDetails = Invoke-PrismAPICall -method $method -url $url -credential $prismCredentials -payload $payload
    if ($myvar_snapDetails) {
        Write-Host "Snapshot Name: $($myvar_snapDetails.spec.name)"
        Write-Host "Snapshot Creation Date: $($myvar_snapDetails.metadata.creation_time)"
        Write-Host "Snapshot Owner: $($myvar_snapDetails.metadata.owner_reference.name)"
        $myvar_vmUUID = $myvar_snapDetails.spec.resources.entity_uuid
        $url = "https://$($prismelement):9440/PrismGateway/services/rest/v2.0/vms/$($myvar_vmUUID)"
        $myvar_vmDetails = Invoke-PrismAPICall -method $method -url $url -credential $prismCredentials -payload $payload
        if ($myvar_vmDetails) {
            Write-Host "VM Name: $($myvar_vmDetails.name)"
        } else {
            Write-Host "VM NOT FOUND"
        }
        
    } else {
        Write-LogOutput -Category "ERROR" -LogFile $LogFile -Message "Missing Snapshot Info for Name: $($snapshot.spec.name)"
    }
    $userInput = Read-Host "Delete Snapshot [Y/n]"
    if ($userInput -ne 'n') {
        $url = "https://$($prismelement):9440/api/nutanix/v3/vm_snapshots/$($myvar_snapUUID)"
        $method = "DELETE"
        $myvar_delResp = Invoke-PrismAPICall -method $method -url $url -credential $prismCredentials -payload $payload

        if ($myvar_delResp) {
            Write-LogOutput -Category "INFO" -LogFile $LogFile -Message "Delete called with status: $($myvar_delResp.status.state)"
            $myvar_delUUID = $myvar_delResp.status.execution_context.task_uuid
            $url = "https://$($prismelement):9440/PrismGateway/services/rest/v2.0/tasks/$($myvar_delUUID)"
            $method = "GET"
            $myvar_taskPayload = Invoke-PrismAPICall -method $method -url $url -credential $prismCredentials -payload $payload
            Write-LogOutput -Category "INFO" -LogFile $LogFile -Message "Delete Task status is: $($myvar_taskPayload.progress_status)"
            while ($myvar_taskPayload.percentage_complete -lt 100) {
                Write-LogOutput -Category "INFO" -LogFile $LogFile -Message "Delete Task complete percentage is: $($myvar_taskPayload.percentage_complete)"
                Start-Sleep 1
                $myvar_taskPayload = Invoke-PrismAPICall -method $method -url $url -credential $prismCredentials -payload $payload
            }
            Write-LogOutput -Category "INFO" -LogFile $LogFile -Message "Delete Task has completed with status: $($myvar_taskPayload.progress_status)"
        } else {
            Write-LogOutput -Category "ERROR" -LogFile $LogFile -Message "No response with status after delete request."
        }
    } else {
        Write-LogOutput -Category "INFO" -LogFile $LogFile -Message "Skipping Delete of Snapshot: $($myvar_snapDetails.spec.name)"
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
