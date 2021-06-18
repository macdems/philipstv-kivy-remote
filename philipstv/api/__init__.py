import random
import string
import socket
import requests
# from base64 import b64encode, b64decode
# import hashlib, hmac

from time import sleep
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

    PICTURE_STYLE = 2131230858
    AMBILIGHT_STYLE = 2131230766
    AMBILIGHT_MENU_OFF = 2131230767
    AMBILIGHT_MENU_FOLLOW_VIDEO = 2131230768
    AMBILIGHT_MENU_FOLLOW_AUDIO = 2131230769
    AMBILIGHT_MENU_LOUNGE_LIGHT = 2131230770
    AMBILIGHT_MENU_FOLLOW_FLAG = 2131230771
    AMBILIGHT_MENU_FOLLOW_APP = 2131230772
    AMBILIGHT_OFF = 2131230783
    AMBILIGHT_LIGHTNESS = 2131230795
    AMBILIGHT_SATURATION = 2131230796

    def __init__(self, host=None, user=None, passwd=None, mac=None, timeout=0.5, waketime=0.5, repeats=3):
        self._host = host
        self._user = user
        self._passwd = passwd
        self.mac = mac
        self._timeout = timeout
        self._waketime = waketime
        self._repeats = repeats

        self._create_auth()

        requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
        self._session = requests.Session()
        self._session.verify = False
        self._session.mount('https://', requests.adapters.HTTPAdapter(pool_connections=1))

    def _create_auth(self):
        if self._user is not None:
            self._auth = HTTPDigestAuth(self._user, self._passwd)
        else:
            self._auth = None

    @property
    def host(self):
        return self._host

    @host.setter
    def host(self, host):
        self._host = host
        self._create_auth()

    @property
    def user(self):
        return self._user

    @user.setter
    def user(self, user):
        self._user = user
        self._create_auth()

    @property
    def passwd(self):
        return self._passwd

    @passwd.setter
    def passwd(self, passwd):
        self._passwd = passwd
        self._create_auth()

    def wakeup(self, waketime=None):
        if waketime is None: waketime = self._waketime
        if self.mac is not None:
            send_magic_packet(self.mac)
            sleep(waketime)

    def _get(self, path, timeout=None):
        if not self._host: raise NoHost()
        if timeout is None: timeout = self._timeout
        waketime = self._waketime
        last = self._repeats - 1
        for i in range(self._repeats):
            try:
                resp = self._session.get(f"https://{self._host}:1926/6/{path}", verify=False, auth=self._auth, timeout=timeout)
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
                raise ApiError(response=resp)

    def _post(self, path, body, timeout=None, auth=None):
        if not self._host: raise NoHost()
        if timeout is None: timeout = self._timeout
        waketime = self._waketime
        if auth is None:
            auth = self._auth
        elif not auth:
            auth = None
        last = self._repeats - 1
        for i in range(self._repeats):
            try:
                resp = self._session.post(
                    f"https://{self._host}:1926/6/{path}", json=body, verify=False, auth=auth, timeout=timeout
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
                raise ApiError(response=resp)

    def pair_request(self):
        user = ''.join(
            random.SystemRandom().choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(16)
        )
        device = {
            'device_name': 'Kivy',
            'device_os': 'Android',
            'app_id': 'com.macdems.philipstv',
            'app_name': 'PhilipsTV Kivy Remote',
            'type': 'native',
            'id': user
        }
        request_data = {'scope': ['read', 'write', 'control'], 'device': device}
        resp = self._post('pair/request', request_data, auth=False)
        if resp is None or resp['error_id'] != 'SUCCESS':
            raise ApiError(response=resp)
        return {'device': device, 'user': user, 'passwd': resp['auth_key'], 'auth_timestamp': resp['timestamp']}

    def pair_grant(self, device, user, passwd, pin, auth_timestamp):
        pin = str(pin)
        auth = {
            'auth_AppId': '1',
            'pin': pin,
            'auth_timestamp': auth_timestamp,
            # 'auth_signature':
            #   b64encode(hmac.new(b64decode(self.SECRET), (str(auth_timestamp + pin).encode(), hashlib.sha1).digest())
            'auth_signature': 'authsignature'
        }
        grant_data = {'auth': auth, 'device': device}
        self._post('pair/grant', grant_data, auth=HTTPDigestAuth(user, passwd))
        self._user = user
        self._passwd = passwd
        self._create_auth()

    def pair(self, callback):
        data = self.pair_request()
        pin = callback()
        return self.pair_grant(pin=pin, **data)

    def send_key(self, key):
        self._post('input/key', {'key': key})

    def get_settings(self, *nodes):
        data = self._post('menuitems/settings/current', {'nodes': [{'nodeid': node} for node in nodes]})
        if not data: return {}
        return {val['value']['Nodeid']: val['value'] for val in data.get('values', [])}

    def update_setting(self, node, data):
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
            'action': f"Intent {{ {action} cmp={package_name}/{class_name} flg=0x20000000 }}",
            'component': {
                "packageName": package_name,
                "className": class_name,
            }
        }
        self._post('activities/launch', {'intent': intent})

    def get_current_network_device(self):
        devices = self._get('network/devices')
        hostip = socket.gethostbyname(self._host)
        devices = [dev for dev in devices if dev.get('ip') == hostip]
        if len(devices) > 0: return devices[0]

    def set_mac(self):
        device = self.get_current_network_device()
        if device and device['mac']:
            self.mac = device['mac']
            return self.mac

    def get_strings(self, country, lang, ids):
        data = {'locale': {'country': country, 'language': lang}, 'strings': [{'string_id': s} for s in ids]}
        return {res['string_id']: res['string_translation'] for res in self._post('strings', data)['translations']}

    def get_ambilight_topology(self):
        return self._get('ambilight/topology')

    def set_ambilight_expert(self, layers, **sides):
        data = {}
        for l in str(layers):
            data[f"layer{l}"] = layer = {}
            for side, vals in sides.items():
                if vals: layer[side] = vals
        self._post('ambilight/cached', data)
        self._post('ambilight/mode', {'current': 'expert'})
