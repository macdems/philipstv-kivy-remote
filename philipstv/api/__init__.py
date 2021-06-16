import random
import string
import socket
import requests

from time import sleep
from base64 import b64encode, b64decode
# from Crypto.Hash import SHA, HMAC
from requests.auth import HTTPDigestAuth

from .wol import send_magic_packet

class NoHost(Exception):
    def __init__(self, msg=None):
        if msg is None:
            msg = "No host. Please set IP of your TV."
        super().__init__(msg)

class NotRechable(Exception):
    def __init__(self, msg=None):
        if msg is None:
            msg = "Cannot reach TV. Make sure you have set correct IP and Wake-on-Lan on your TV is on."
        super().__init__(msg)

class NotAuthorized(Exception):
    def __init__(self, msg=None):
        if msg is None:
            msg = "Remote not authorized. Please pair again."
        super().__init__(msg)


class ApiError(requests.RequestException):
    pass


class PhilipsAPI:

    SECRET = "YEl03N2zQVwjtlip3ECCksCGR3WaigEIRpFJSiEtNrPTQBpJWscNSkyntqTk3E3frjHacFSQfqDleUxOkCE0RPNG"

    def __init__(self, host=None, user=None, passwd=None, mac=None, timeout=0.5, waketime=0.5, repeats=3):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.mac = mac
        self._timeout = timeout
        self._waketime = waketime
        self._repeats = repeats

        requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
        self._session = requests.Session()
        self._session.verify = False
        self._session.mount('https://', requests.adapters.HTTPAdapter(pool_connections=1))

    def wakeup(self, waketime=None):
        if waketime is None: waketime = self._waketime
        if self.mac is not None:
            send_magic_packet(self.mac)
            sleep(waketime)

    def _get(self, path, timeout=None):
        if not self.host: raise NoHost()
        if timeout is None: timeout = self._timeout
        waketime = self._waketime
        last = self._repeats - 1
        for i in range(self._repeats):
            try:
                resp = self._session.get(
                    'https://{host}:1926/6/{path}'.format(host=self.host, path=path),
                    verify=False,
                    auth=HTTPDigestAuth(self.user, self.passwd),
                    timeout=timeout
                )
            except requests.Timeout as err:
                if i != last:
                    self.wakeup(waketime)
                    timeout *= 2
                    waketime *= 2
                else:
                    raise NotRechable() from err
                continue
            except requests.ConnectionError as err:
                raise NotRechable() from err
            else:
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 401:
                    raise NotAuthorized()
                raise requests.APIError(response=resp)

    def _post(self, path, body, timeout=None, userpass=None):
        if not self.host: raise NoHost()
        if timeout is None: timeout = self._timeout
        waketime = self._waketime
        if userpass is None: userpass = self.user, self.passwd
        last = self._repeats - 1
        for i in range(self._repeats):
            try:
                resp = self._session.post(
                    'https://{host}:1926/6/{path}'.format(host=self.host, path=path),
                    json=body,
                    verify=False,
                    auth=HTTPDigestAuth(*userpass) if userpass else None,
                    timeout=timeout
                )
            except requests.Timeout as err:
                if i != last:
                    self.wakeup(waketime)
                    timeout *= 2
                    waketime *= 2
                else:
                    raise NotRechable() from err
                continue
            except requests.ConnectionError as err:
                raise NotRechable() from err
            else:
                if resp.status_code == 200:
                    return resp.json() if resp.text else None
                elif resp.status_code == 401:
                    raise NotAuthorized()
                raise requests.APIError(response=resp)

    # def _create_signature(self, to_sign):
    #     sign = HMAC.new(b64decode(self.SECRET), to_sign, SHA)
    #     return b64encode(sign.digest()).decode()

    def pair_request(self):
        user = ''.join(
            random.SystemRandom().choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(16)
        )
        device = {
            'device_name': 'heliotrope',
            'device_os': 'Android',
            'app_id': 'app.id',
            'app_name': 'PhilipsTV Kivy Remote',
            'type': 'native',
            'id': user
        }
        request_data = {'scope': ['read', 'write', 'control'], 'device': device}
        resp = self._post('pair/request', request_data, userpass=False)
        if resp is None or resp['error_id'] != 'SUCCESS':
            raise ApiError(response=resp)
        return {'device': device, 'user': user, 'passwd': resp['auth_key'], 'auth_timestamp': resp['timestamp']}

    def pair_confirm(self, device, user, passwd, pin, auth_timestamp):
        pin = str(pin)
        auth = {
            'auth_AppId': '1',
            'pin': pin,
            'auth_timestamp': auth_timestamp,
            # 'auth_signature': self._create_signature(str(auth_timestamp).encode() + pin.encode())
            'auth_signature': 'authsignature'
        }
        grant_data = {'auth': auth, 'device': device}
        self._post('pair/grant', grant_data, userpass=(user, passwd))
        self.user = user
        self.passwd = passwd
        print(user, passwd, sep=':')

    def pair(self, callback):
        data = self.pair_request()
        pin = callback()
        return self.pair_confirm(pin=pin, **data)

    def send_key(self, key):
        self._post('input/key', {'key': key})

    def get_current_settings(self, *nodes):
        return self._post('menuitems/settings/current', {'nodes': [{'nodeid': node} for node in nodes]})

    def set_current_setting(self, node, data):
        self._post('menuitems/settings/update', {'values': [{'value': {'Nodeid': node, 'data': data}}]})

    def get_applications(self):
        res = self._get('applications')
        if res is None:
            return []
        return res.get('applications', [])

    def launch_application(self, package_name, class_name, action):
        if action == 'empty':
            action = ''
        else:
            action = ' act=' + action
        intent = {
            'action':
            "Intent {{ {action} cmp={package_name}/{class_name} flg=0x20000000 }}".format(
                package_name=package_name, class_name=class_name, action=action
            ),
            'component': {
                "packageName": package_name,
                "className": class_name,
            }
        }
        self._post('activities/launch', {'intent': intent})

    def get_current_network_device(self):
        devices = self._get('network/devices')
        hostip = socket.gethostbyname(self.host)
        devices = [dev for dev in devices if dev.get('ip') == hostip]
        if len(devices) > 0: return devices[0]

    def set_mac(self):
        device = self.get_current_network_device()
        if device and device['mac']:
            self.mac = device['mac']
            return self.mac
