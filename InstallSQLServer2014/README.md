# Install SQL Server 2014 from ISO

This script will install the database engine for Microsoft SQL Server 2014.  The script does the following:
* Format unused drive to be used for downloading and data storage
* Download SQL Svr 2014 ISO from Microsoft
* Mount ISO as a drive
* Verify and install .NET
* Install SQL Server 2014 database engine
* Unmount and remove ISO

This script has been tested and verified to work with Windows Server 2016 and 2019.  The VM settings tested had these specifications:
* 2 vCPUs
* 2 cores
* 6 GiB of RAM
* 50 GiB OS drive
* 100 GiB unformated drive
* 1 NIC
* Powershell v5.1 (included with Windows Server 2016 & 2019)