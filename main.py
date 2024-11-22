import os
import yaml
import json
import datetime
import paramiko  


class MainApp:
    def __init__(self):
        self.ip_list = []
        self.login_list = []
        self.sudo_passwd_list = []
        self.found_logins = []

        self.load_data()
        self.connect_to_host()
        self.write_data()
    
    def load_data(self):
        path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(path, "data")
        os.chdir(path)

        with open("ip_list.txt", "r") as file:
            for line in file:
                self.ip_list.append(str(line.strip()))

        with open("login_list.json", "r") as file:
            loaded_file = json.load(file)
            for login in loaded_file['logins']:
                self.login_list.append(
                    {
                        "username": login['username'],
                        "password": login['password']
                    }
                )

        with open("sudo_passwd_list.json", "r") as file:
            loaded_file = json.load(file)
            for sudo_passwd in loaded_file['passwords']:
                self.sudo_passwd_list.append(sudo_passwd)

    def connect_to_host(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        for ip in self.ip_list:
            print(f"Connecting to {ip}")
            found = False

            for login in self.login_list:
                try:
                    ssh.connect(ip, 
                    username=login["username"], 
                    password=login["password"],
                    timeout=5)

                    if login['username'] == 'root':
                        host = {
                            'host': ip, 
                            'hostname': login['username'], 
                            'password': login["password"]
                        }
                    else:
                        host = self.find_sudo(ssh, ip, login)
                    ssh.close()

                    print(f"Login FOUND for {ip}, saving...")
                    self.found_logins.append(host)
                    found = True
                    break

                except paramiko.ssh_exception.NoValidConnectionsError:
                    print('No valid connection, port 22 is closed')

                except TimeoutError:
                    print('Connection timed out')

                except paramiko.SSHException:
                    pass

                except EOFError:
                    pass

            if found == False:
                print(f"Login NOT FOUND for {ip}")

    def find_sudo(self, ssh, ip, login):
        for password in self.sudo_passwd_list:
            stdin, stdout, stderr = ssh.exec_command(f"echo {password} | sudo -S ls")
            if "incorrect password attempt" not in stderr.read().decode():
                host = {
                    'host': ip, 
                    'hostname': login['username'], 
                    'password': login['password'], 
                    'sudo_passwd': password
                    }
                
                return host

    def write_data(self):
        date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(path, 'reports')
        path = os.path.join(path, f"{date}.yaml")

        structure = {
            'all': {
                'hosts': {
                }
            }
        }

        for login in self.found_logins:
            if login['hostname'] == 'root':
                structure['all']['hosts'][login['host']] = {
                    'ansible_user': login['hostname'],
                    'ansible_password': login['password']
                }
            else:
                structure['all']['hosts'][login['host']] = {
                    'ansible_user': login['hostname'],
                    'ansible_password': login['password'],
                    'ansible_become': True,
                    'ansible_become_method': 'sudo',
                    'ansible_become_password': login['sudo_passwd']
                }

        with open(path, "x") as file:
            yaml.dump(structure, file, default_flow_style=False, sort_keys=False)

if __name__ == "__main__":
    app = MainApp()