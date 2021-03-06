# Install SQL Server 2014 from ISO

These scripts will install the database engine for Microsoft SQL Server 2014.  These scripts do the following:
* **InstallSQL2014.ps1**
  * Format unused drive to be used for downloading and data storage
  * Download SQL Svr 2014 ISO from Microsoft
  * Mount ISO as a drive
  * Verify and install .NET
  * Install SQL Server 2014 database engine
  * Open local firewall for database access
  * Unmount and remove ISO

* **InstallSQL_NoInternet.ps1**
  * Format unused drive to be used for downloading and data storage
  * Install dot Net 3.5 from OS install media
  * Install SQL Server 2014 database engine
  * Open local firewall for database access  

This script has been tested and verified to work with Windows Server 2016 and 2019.  The VM settings tested had these specifications:
* 2 vCPUs
* 2 cores
* 6 GiB of RAM
* 50 GiB OS drive
* 100 GiB unformated drive
* 1 NIC