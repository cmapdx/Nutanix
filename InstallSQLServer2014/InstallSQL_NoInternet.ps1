# This script will install SQL Server 2014 from the mounted ISO.  
#  Requirements to run
#    Microsoft SQL Server install ISO
#    Microsoft Server 2016 or 2019 install media or another source for dot Net 3.5

# - - - UPDATE THIS SECTION - - - #
# SQL Server ISO Install media, verify drive letter
$setupPath = "D:\setup.exe"
# OS Install media, verify drive letter
$OS_InstallMedia = "E:\sources\sxs"
# - - - - - - - - - - - - - - - - #

# Password that will be used to access database after install
$SA_Password = "nutanix/4u"

# The script uses a new unformatted drive to install the database 
# Format the new drive and set variable with drive letter
Get-Disk -Number 1 | Initialize-Disk -ErrorAction SilentlyContinue
New-Partition -DiskNumber 1 -UseMaximumSize -AssignDriveLetter -ErrorAction SilentlyContinue | Format-Volume -Confirm:$false
$DriveLetter = $(Get-Partition -DiskNumber 1 -PartitionNumber 2 | Select-Object DriveLetter -ExpandProperty DriveLetter)

# Install dot Net 3.5 from OS media
$Prerequisites = "Net-Framework-Core"
if ($Prerequisites){
    Install-WindowsFeature -IncludeAllSubFeature -ErrorAction Stop $Prerequisites -source $OS_InstallMedia
}

$PackageName = "MsSqlServer2014Standard"

# Install SQL Server with these features and values
$silentArgs = "/IACCEPTSQLSERVERLICENSETERMS /Q /ACTION=install /FEATURES=SQLENGINE "
$silentArgs += "/SECURITYMODE=`"SQL`" /SAPWD=`"${SA_Password}`" /SQLSYSADMINACCOUNTS=`"administrator`" "
$silentArgs += "/INSTANCEID=MSSQLSERVER /INSTANCENAME=MSSQLSERVER /UPDATEENABLED=False /TCPENABLED=1 "
$silentArgs += "/INSTALLSQLDATADIR=`"${DriveLetter}:\Microsoft SQL Server`""

$validExitCodes = @(0)

Write-Output "Installing $PackageName...."

$install = Start-Process -FilePath $setupPath -ArgumentList $silentArgs -Wait -NoNewWindow -PassThru
$install.WaitForExit()

$exitCode = $install.ExitCode
$install.Dispose()

Write-Output "Command [`"$setupPath`" $silentArgs] exited with `'$exitCode`'."
if ($validExitCodes -notcontains $exitCode) {
    Write-Output "Running [`"$setupPath`" $silentArgs] failed. Exit code was '$exitCode'. See log for possible error messages."
    exit 1
}

#Open local firewall to allow outside connections to the SQL server
New-NetFirewallRule -DisplayName "SQL Server" -Direction Inbound -Protocol TCP -LocalPort 1433 -Action allow
New-NetFirewallRule -DisplayName "SQL Admin Connection" -Direction Inbound -Protocol TCP -LocalPort 1434 -Action allow
New-NetFirewallRule -DisplayName "SQL Database Management" -Direction Inbound -Protocol UDP -LocalPort 1434 -Action allow
New-NetFirewallRule -DisplayName "SQL Service Broker" -Direction Inbound -Protocol TCP -LocalPort 4022 -Action allow
New-NetFirewallRule -DisplayName "SQL Debugger/RPC" -Direction Inbound -Protocol TCP -LocalPort 135 -Action allow
New-NetFirewallRule -DisplayName "SQL Browser" -Direction Inbound -Protocol TCP -LocalPort 2382 -Action allow
