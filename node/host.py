# MIT License
#
# Copyright (c) 2022 iammehdib
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from threading import Thread
import simplejson as json
from os import path
from uuid import uuid4

from node.utils import json_dumps
from node.action.host_info import ownhost_info

### VERSION
VERSION = 0.2

class thread_listen(Thread):
    def __init__(self, c, ip: int, port: int):
        Thread.__init__(self)
        self.c = c
        self.ip = ip
        self.port = port
        self.statut = False

    def run(self):
        try:
            while True:
                data = self.c.recv(config['recv-data'])
                if data:
                    Thread(target=self.process_data(json.loads(data.decode('utf-8')))).start()

            del USER_BY_ID[self.c]
            self.c.close()
        except Exception as e:
            return
        except ConnectionResetError as e:
            return 
            
    def process_data(self, data: dict):
        if 'auth_user_id' in data:
            self.connect_user_id(data)
        elif 'register_pass' in data:
            self.register_user_id(data)
        elif 'send_data_to' in data:
            self.send_data_to_user_id(data)
        elif 'hostinfo' in data:
            self.c.send(HOSTINFO)

    def register_user_id(self, data: dict):

        user_id = uuid4().hex
        
        not path.isfile(f'db/{user_id}.ownn')
        with open(f'db/{user_id}.ownn', 'w') as f:

            writedata = {
                'user_uuid': user_id,
                'pswd': data['register_pass']
                        }

            # WORKING
            # writedata = {
            #     "user_uuid": user_id,
            #     "pswd": data["register_pass"],
            #     "cloud": {
            #         'default': {
            #             "name": 'oknet',
            #             "ip": 'localhost',
            #             "port": config['port'],
            #             "block": 'test'
            #                 }
            #             }
            #         }

            json.dump(writedata, f, indent=2)

            self.send_json_data({'user_id_register': user_id})
            USER_BY_ID[user_id], self.user_id, self.statut = self.c, user_id, True

    def connect_user_id(self, data: dict):

        user_id = data['auth_user_id']
        
        path.isfile(f'db/{user_id}.ownn')
        
        with open(f'db/{user_id}.ownn', 'r') as f:
            fd = json.load(f)
            if data['pswd'] == fd['pswd']:
                USER_BY_ID[user_id], self.user_id, self.statut = self.c, data['auth_user_id'], True
            elif data['pswd'] != fd['pswd']:
                self.c.close()

    def send_data_to_user_id(self, data: dict):
        if USER_BY_ID[data['send_data_to']] and self.statut == True:
            d_to_sender = {
                'from_id': self.user_id,
                'get-data': data['data']
                }
            self.c.sendto(json_dumps(d_to_sender).encode(), USER_BY_ID[data['send_data_to']])
        elif self.statut == False:
            return
    
    def echo_info(self, info: int):
        info = {'echo_info' : str(info)}
        self.c.send(json_dumps(info).encode('utf-8'))

    def send_info(self, info: str):
        info = {'info' : info}
        self.c.send(json_dumps(info).encode('utf-8'))

    def send_json_data(self, d: dict):
        self.c.send(json_dumps(d).encode('utf-8'))


def setup_host():

    print('Reading config.json ...')
    try:
        global config
        with open('config.json', 'r') as f:
            config = json.load(f)
    except json.decoder.JSONDecodeError as e:
        print('Not correct writing in config.json')
        return

    print('Create global variables ...')
    global USER_BY_ID
    USER_BY_ID = {}
    global HOSTINFO
    HOSTINFO = json.dumps(ownhost_info(config['name_host'], config['logo'])).encode('utf-8')

    with socket(AF_INET, SOCK_STREAM) as s:
        s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        s.bind((config['host'], config['port']))
        s.listen(config['listen'])

        print('OwnNetworkHost is started on', str(config['port']) + '. (Baobapp Network', str(VERSION) + ')')
        while True:
            (c, (ip, port)) = s.accept()
            c.setblocking(1)
            thr = thread_listen(c, ip, port)
            thr.start()

        s.close()

if __name__ == '__main__':
    setup_host()
