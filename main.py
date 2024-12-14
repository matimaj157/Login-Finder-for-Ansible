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

                    if host != None:
                        print(f"Login FOUND for {ip}, saving...")
                        self.found_logins.append(host)
                        found = True
                    else:
                        print(f"Root password was NOT FOUND for {ip}")

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
        host = {
            'host': ip, 
            'hostname': login['username'], 
            'password': login['password'], 
        }

        _, stdout, stderr = ssh.exec_command(f"echo "" | sudo -S pwd")
        if '/home' in stdout.read().decode():
            host['sudo_passwd'] = None
            return host

        for password in self.sudo_passwd_list:
            _, stdout, stderr = ssh.exec_command(f"echo {password} | su -c pwd")
            if 'Authentication failure' not in stderr.read().decode():
                host['sudo_passwd'] = password
                host['method'] = 'su'
                return host

            _, stdout, stderr = ssh.exec_command(f"echo {password} | sudo -S pwd")
            if '/home' in stdout.read().decode():
                host['sudo_passwd'] = password
                host['method'] = 'sudo'
                return host

    def write_data(self):
        date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(path, 'reports')
        path_yaml = os.path.join(path, f"{date}.yaml")
        path_csv = os.path.join(path, f"{date}.csv")

        structure = {
            'all': {
                'hosts': {
                }
            }
        }

        for login in self.found_logins:
            try:
                structure['all']['hosts'][login['host']] = {
                    'ansible_user': login['hostname'],
                    'ansible_password': login['password']
                }

                if login['hostname'] != 'root':
                    structure['all']['hosts'][login['host']]['ansible_become'] = True

                    if login['sudo_passwd'] == None:
                        structure['all']['hosts'][login['host']]['ansible_become_method'] = 'sudo'

                    elif login['sudo_passwd'] != None and login['method'] == 'su':
                        structure['all']['hosts'][login['host']]['ansible_become_method'] = 'su'
                        structure['all']['hosts'][login['host']]['ansible_become_password'] = login['sudo_passwd']

                    elif login['sudo_passwd'] != None and login['method'] == 'sudo':
                        structure['all']['hosts'][login['host']]['ansible_become_method'] = 'sudo'
                        structure['all']['hosts'][login['host']]['ansible_become_password'] = login['sudo_passwd']

            except TypeError:
                pass

        with open(path_yaml, "x") as file:
            yaml.dump(structure, file, default_flow_style=False, sort_keys=False)

        with open(path_csv, "x") as file:
            file.write("host,username,password,sudo_password,sudo_method\n")

            for host, data in structure['all']['hosts'].items():
                try:
                    file.write(f"{host},{data['ansible_user']},{data['ansible_password']},{data['ansible_become_password']},{data['ansible_become_method']}\n")
                except KeyError:
                    if 'ansible_become_password' not in data.keys() and 'ansible_become_method' in data.keys():
                        file.write(f"{host},{data['ansible_user']},{data['ansible_password']},-,sudo\n")
                    else:
                        file.write(f"{host},{data['ansible_user']},{data['ansible_password']},-,-\n")


if __name__ == "__main__":
    app = MainApp()
