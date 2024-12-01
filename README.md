### Login Finder and Inventory Creator for Ansible ###
This simple tool allows you to provide a list of hosts, logins and sudo passwords. The script will go through all hosts trying to find the correct login for each host. If login is found, program will try to gain root access, using different methods and passwords from the provided list. All found logins are saved to the YAML file which can be used straight away as a ansible inventory.

Requiered dependencies:
- python3
  
Used modules:
- yaml
- json
- paramiko

How to use:
1. Download all files.
2. Navigate to "data" folder and update all lists with your own ips and credentials. 
(Start with root logins, then provide another users' logins)
(DO NOT CHANGE FILE NAMES!)
3. Run "main.py", your report will show up in the "reports" folder.
