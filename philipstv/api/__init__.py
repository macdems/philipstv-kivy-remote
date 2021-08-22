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
    def __str__(self):
        try:
            return self.response['error_text']
        except:
            return super().__str__()


class PhilipsAPI:
    """Philips TV HTTP API access class.

    This class provides access to Philips API. It can be used without GUI for script access.

    Args:
        host (str, optional): Hostname or IP of the TV. Defaults to None.
        user (str, optional): HTTP user name. Defaults to None.
        passwd (str, optional): HTTP user password. Defaults to None.
        mac (str, optional): MAC address of the TV. Used for Wake on LAN.. Defaults to None.
        timeout (float, optional): Default connection timeout in seconds. Defaults to 0.5.
        waketime (float, optional): Default time to wait after wakeup in seconds. Defaults to 0.5.
        repeats (int, optional): Number of connection attempts. In each try the timeout and waketime are doubled.
                                 You should not make it smaller than 2 or the WoL will not work. Defaults to 3.

    Raises:
        NoHost: No TV address specified.
        NotRechable: TV not reachable.
        NotAuthorized: No authorization.
        ApiError: Some internal API error.
    """

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
        self._timeout = timeout
        self._waketime = waketime
        self._repeats = repeats

        self.mac = mac
        """MAC address of the TV. Used for Wake on LAN."""

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
        """Hostname or IP of the TV."""
        return self._host

    @host.setter
    def host(self, host):
        self._host = host
        self._create_auth()

    @property
    def user(self):
        """HTTP user name."""
        return self._user

    @user.setter
    def user(self, user):
        self._user = user
        self._create_auth()

    @property
    def passwd(self):
        """HTTP password."""
        return self._passwd

    @passwd.setter
    def passwd(self, passwd):
        self._passwd = passwd
        self._create_auth()

    def wakeup(self, waketime=None):
        """Turn on the TV using Wake on LAN.

        Args:
            waketime (float, optional): Time to wait after waking the TV. If None, class defaults are used.
        """
        if waketime is None: waketime = self._waketime
        if self.mac:
            send_magic_packet(self.mac)
            sleep(waketime)

    def _process(self, oper, path, timeout, auth, **kwargs):
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
                resp = oper(f"https://{self._host}:1926/6/{path}", verify=False, auth=auth, timeout=timeout, **kwargs)
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
                    try:
                        return resp.json()
                    except ValueError:
                        return resp.text
                elif resp.status_code == 401:
                    raise NotAuthorized()
                raise ApiError(response=resp)

    def get(self, path, timeout=None, auth=None):
        """Generic GET request.Request

        Args:
            path (str): API path.
            timeout (float, optional): Timeout. If missing, class defauls is used.
            auth (optional): Requests auth object. If False, the request is not authorized.

        Returns:
            Response JSON.
        """
        return self._process(self._session.get, path, timeout, auth)

    def post(self, path, body, timeout=None, auth=None):
        """Generic POST request.Request

        Args:
            path (str): API path.
            timeout (float, optional): Timeout. If missing, class defauls is used.
            auth (optional): Requests auth object. If False, the request is not authorized.

        Returns:
            Response JSON.
        """
        return self._process(self._session.post, path, timeout, auth, json=body)

    def pair_request(self):
        """Initiate pairing process.

        Returns:
            dict: Data required by pair_grant method.
        """
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
        resp = self.post('pair/request', request_data, auth=False, timeout=self._timeout*2)
        if resp is None or resp['error_id'] != 'SUCCESS':
            raise ApiError(response=resp)
        return {'device': device, 'user': user, 'passwd': resp['auth_key'], 'auth_timestamp': resp['timestamp']}

    def pair_grant(self, pin, device, user, passwd, auth_timestamp):
        """Confirm pairing.

        Args:
            pin (str): PIN number as displayed by the TV.
            device, user, passwd, auth_timestamp: Data returned by pair_request
        """
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
        resp = self.post('pair/grant', grant_data, auth=HTTPDigestAuth(user, passwd))
        if resp is None or resp['error_id'] != 'SUCCESS':
            raise ApiError(response=resp)
        self._user = user
        self._passwd = passwd
        self._create_auth()

    def pair(self, callback=lambda: input("Enter PIN: ")):
        """Pair the TV.

        This function is a shorthand for calling pair_request and pair_grant.
        The callback function should be user input that returns PIN displayed by the TV.

        Args:
            callback (function, optional): Function that should return pin number displayed on the TV.
        """
        data = self.pair_request()
        pin = callback()
        self.pair_grant(pin=pin, **data)

    def send_key(self, key):
        """Send TV remote key.

        Args:
            key (str): Key name.

        Key may be one of: Standby, Back, Find, RedColour, GreenColour, YellowColour, BlueColour, Home, VolumeUp, VolumeDown, Mute,
                           Options, Dot, Digit0, Digit1, Digit2, Digit3, Digit4, Digit5, Digit6, Digit7, Digit8, Digit9, Info,
                           CursorUp, CursorDown, CursorLeft, CursorRight, Confirm, Next, Previous, Adjust, WatchTV, Viewmode,
                           Teletext, Subtitle, ChannelStepUp, ChannelStepDown, Source, AmbilightOnOff, Online,
                           PlayPause, Play, Pause, FastForward, Stop, Rewind, Record
        """
        self.post('input/key', {'key': key})

    def get_settings(self, *nodes):
        """Get current value of given settings nodes.

        Returns:
            dict: Dict with node numbers and setting values.
        """
        data = self.post('menuitems/settings/current', {'nodes': [{'nodeid': node} for node in nodes]})
        if not data: return {}
        return {val['value']['Nodeid']: val['value'] for val in data.get('values', [])}

    def update_setting(self, node, data):
        """Update given settings node.

        Args:
            node (int): Settings node number.
            data: Settings value.
        """
        self.post('menuitems/settings/update', {'values': [{'value': {'Nodeid': node, 'data': data}}]})

    def get_system(self):
        """Get system info from your TV.TV

        Returns:
            dict: Dictionary with system info.
        """
        return self.get('system')

    def get_applications(self):
        """Get info on installed applications.

        Returns:
            list: List of application details.
        """
        res = self.get('applications')
        if res is None:
            return []
        return res.get('applications', [])

    def launch_application(self, package_name, class_name, action='empty'):
        """Launch specified application.

        Args:
            package_name (str): Android package name.
            class_name (str): Android class name.
            action (str, optional): Android action descriptor. Defaults to 'empty'.
        """
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
        self.post('activities/launch', {'intent': intent})

    def get_current_network_device(self):
        """Get information on the TV devicenetwork device, this class is attached to.

        Returns:
            str: Current network device details.
        """
        devices = self.get('network/devices')
        hostip = socket.gethostbyname(self._host)
        devices = [dev for dev in devices if dev.get('ip') == hostip]
        if len(devices) > 0: return devices[0]

    def set_mac(self):
        """Automatically set MAC address of the TV.

        Returns:
            str: Detected MAC address.
        """
        device = self.get_current_network_device()
        if device and device['mac']:
            self.mac = device['mac']
            return self.mac

    def get_strings(self, *ids, country='en_US', lang=None):
        """Get translation strings from the TV.

        Args:
            ids (list[str]): String IDs.
            country (str, optional): Country code. Defaults to 'en_US'.
            lang (str, optional): Language code. By default determined from country code.

        Returns:
            dict: Dict with string IDs and retrieved translations.
        """
        if lang is None:
            try:
                lang = country.split('_')[1]
            except:
                lang = 'en'
        data = {'locale': {'country': country, 'language': lang}, 'strings': [{'string_id': s} for s in ids]}
        return {res['string_id']: res['string_translation'] for res in self.post('strings', data)['translations']}

    def get_ambilight_topology(self):
        """Get ambilight topology.

        The returned dictionary contains the following keys:
            layers: string with ambilight layers; usually just '1'
            left, right, top, bottom: number of ambilight zones at each side

        Returns:
            dict: Dictionary with ambilight topology.
        """
        return self.get('ambilight/topology')

    def set_ambilight_expert(self, layers, **sides):
        """Set expert ambilight colors.

        Args:
            layers (str): String with ambilight layers to set.
            sides: Ambilight expert settings for each side.
        """
        data = {}
        for l in str(layers):
            data[f"layer{l}"] = layer = {}
            for side, vals in sides.items():
                if vals: layer[side] = vals
        self.post('ambilight/cached', data)
        self.post('ambilight/mode', {'current': 'expert'})
