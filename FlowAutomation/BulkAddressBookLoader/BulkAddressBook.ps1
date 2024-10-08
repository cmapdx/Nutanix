<#
.SYNOPSIS
  Create a new address book entry for a security policy.
.DESCRIPTION
  This script creates an address list for use in Flow Security policies. 
.PARAMETER help
  Displays a help message (seriously, what did you think this was?)
.PARAMETER history
  Displays a release history for this script (provided the editors were smart enough to document this...)
.PARAMETER log
  Specifies that you want the output messages to be written in a log file as well as on the screen.
.PARAMETER debugme
  Turns off SilentlyContinue on unexpected error messages.
.EXAMPLE
.\BulkAddressBook.ps1 -cluster ntnxc1.local
Connect to a Nutanix cluster of your choice:
.LINK
  http://www.nutanix.com/services
.NOTES
  Author: Corey Anson (corey.anson@nutanix.com)
  Revision: Oct 7, 2024
#>

#region parameters
Param
(
    #[parameter(valuefrompipeline = $true, mandatory = $true)] [PSObject]$myParam1,
    [parameter()] [switch]$help,
    [parameter()] [switch]$history,
    [parameter()] [switch]$log,
    [parameter()] [switch]$debugme,
    [parameter()] [string]$prismcentral,
    [parameter()] [System.Management.Automation.PSCredential]$prismCredentials,
    [parameter()] [string]$LogFile,
    [parameter()] [string]$config = "$($PSScriptRoot)\config.json",
    [parameter()] [string]$address_list = "$($PSScriptRoot)\address.txt"
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
        if (!$checking_task_status) { Write-LogOutput -Category "INFO" -LogFile $LogFile -Message "Making a $method call to $url" }
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
            if (!$checking_task_status) { Write-LogOutput -Category "SUCCESS" -LogFile $LogFile -Message "Call $method to $url succeeded." } 
            if ($debugme) { Write-LogOutput -Category "DEBUG" LogFile $LogFile -Message "Response Metadata: $($resp.metadata | ConvertTo-Json)" }
        }
        catch {
            $saved_error = $_.Exception.Message
            # Write-Host "$(Get-Date) [INFO] Headers: $($headers | ConvertTo-Json)"
            Write-Host "$(Get-Date) [INFO] Payload: $payload" -ForegroundColor Green
            if ($resp) {
                Throw "$(get-date) [ERROR] Error code: $($resp.code) with message: $($resp.message_list.details)"
            }
            else {
                Throw "$(get-date) [ERROR] $saved_error"
            } 
        }
        finally {
            #add any last words here; this gets processed no matter what
        }
    }
    end {
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
10/07/2024 ca   Initial release.
################################################################################
'@
$myvarScriptName = ".\BulkAddressBook.ps1"

if ($help) { get-help $myvarScriptName; exit }
if ($History) { $HistoryText; exit }

$myjsonfile = Get-Content $config | ConvertFrom-Json -AsHashtable
$prismcentral = $myjsonfile.PrismCentral
if ($myjsonfile.ContainsKey('UserName')) { $prismUser = $myjsonfile.UserName }
if ($myjsonfile.ContainsKey('Password')) { $prismPass = $myjsonfile.Password }
$LogDate = Get-Date -Format "yyyyMMdd.HHmm"
if ($myjsonfile.ContainsKey('Logfile')) {
    $LogFile = $myjsonfile.Logfile
    $LogFile += "${LogDate}.log"
}
else {
    $LogFile = "${PSScriptRoot}\BulkAddressBook.${LogDate}.log"
}
$myvar_address = Get-Content $address_list

if (!$prismPass) {
    #No password provided in config file
    Write-LogOutput -Category "ERROR" -LogFile $LogFile -Message "No password found in configuration file, unable to continue."
    exit 1
} 
    
$username = $prismUser
$PrismSecurePassword = ConvertTo-SecureString $prismPass -AsPlainText -Force
$prismCredentials = New-Object PSCredential ($username, $PrismSecurePassword)

$address_group_string = "["
$my_Object = New-Object 'System.Collections.Generic.List[object]'

$line = 1

ForEach ($myvar_line in $myvar_address) {
    if ($line -eq 1) {
        $myvar_name = $myvar_line
    } elseif ($line -eq 2) {
        $myvar_description = $myvar_line
    } else {
        # This is all the addresses
        $myvar_rawsubnet = $myvar_line
        $myvar_split = $myvar_rawsubnet -split "/"
        $myvar_ip = $myvar_split[0]
        $myvar_length = $myvar_split[1]
        if ($line -gt 3) { 
            $address_group_string += "," 
        }
        $address_group_string += "{ip:" + $myvar_ip + ",prefix_length:" + $myvar_length + ",value:" + $myvar_rawsubnet + "}"
        
        $ip_block = @{
            "ip" = $myvar_ip
            "prefix_length" = [int]$myvar_length
        }
        #$ip_block
        $my_Object.Add($ip_block)
    }
    $line++
}
$address_group_string += "]"
#I have no clue why this fixed the issue instead of printing out the values, but 2 hours 
# of trying to figure out how to get these values to convert and this worked, I will take it
foreach ($ky in $my_Object.Keys) {
    $($my_Object[$ky])
}

$content = @{
    address_group_string = "$($address_group_string)"
    name = "$($myvar_name)"
    ip_address_block_list = $($my_Object)
    description = "$($myvar_description)"
}

Write-LogOutput -Category "INFO" -LogFile $LogFile -Message "Done reading $($line) of text input"
$url = "https://$($prismcentral):9440/api/nutanix/v3/address_groups"
$method = "POST"
$payload = (ConvertTo-Json $content -Depth 4)

$myvar_resp = Invoke-PrismAPICall -method $method -url $url -credential $prismCredentials -payload $payload

Write-LogOutput -Category "INFO" -LogFile $LogFile -Message "Responce from call: $($myvar_resp)"

#cleanup after ourselves and delete all custom variables
Remove-Variable myvar* -ErrorAction SilentlyContinue
Remove-Variable ErrorActionPreference -ErrorAction SilentlyContinue
Remove-Variable help -ErrorAction SilentlyContinue
Remove-Variable history -ErrorAction SilentlyContinue
Remove-Variable log -ErrorAction SilentlyContinue
Remove-Variable debugme -ErrorAction SilentlyContinue
#endregion
