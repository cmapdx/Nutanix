# This script will download Microsoft SQL Server 2014 ISO from Microsoft and install a basic SQL Database Engine.

# The script uses a new unformatted drive to install the database on
# Format the new drive and set variable with drive letter
Get-Disk -Number 1 | Initialize-Disk -ErrorAction SilentlyContinue
New-Partition -DiskNumber 1 -UseMaximumSize -AssignDriveLetter -ErrorAction SilentlyContinue | Format-Volume -Confirm:$false
$DriveLetter = $(Get-Partition -DiskNumber 1 -PartitionNumber 2 | select DriveLetter -ExpandProperty DriveLetter)

#Download the SQL Server 2014 ISO file from Microsoft
$SQL_URL = "http://download.microsoft.com/download/7/9/F/79F4584A-A957-436B-8534-3397F33790A6/SQLServer2014SP3-FullSlipstream-x64-ENU.iso"
$ISO = $DriveLetter+":\SQL2014.iso"
Invoke-WebRequest -Uri $SQL_URL -OutFile $ISO

#Mount the SQL Server 2014 ISO and set drive letter in variable
$mountResult = Mount-DiskImage -ImagePath $ISO -PassThru
$setupDriveLetter = ($mountResult | Get-Volume).DriveLetter

Write-Output "Install ISO mounted on : $setupDriveLetter"

$SA_Password = "nutanix/4u"
$PackageName = "MsSqlServer2014Standard"
$Prerequisites = "Net-Framework-Core"
$silentArgs = "/IACCEPTSQLSERVERLICENSETERMS /Q /ACTION=install /FEATURES=SQLENGINE "
$silentArgs += "/SECURITYMODE=`"SQL`" /SAPWD=`"${SA_Password}`" /SQLSYSADMINACCOUNTS=`"administrator`" "
$silentArgs += "/INSTANCEID=MSSQLSERVER /INSTANCENAME=MSSQLSERVER /UPDATEENABLED=False /TCPENABLED=1 "
$silentArgs += "/INSTALLSQLDATADIR=`"${DriveLetter}:\Microsoft SQL Server`""

$setupPath = $setupDriveLetter+":\setup.exe"
$validExitCodes = @(0)

if ($Prerequisites){
    Install-WindowsFeature -IncludeAllSubFeature -ErrorAction Stop $Prerequisites
}

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

#Cleanup after install
Dismount-DiskImage -ImagePath $ISO
Remove-Item -Path $ISO

