import requests
import socket

from zeroconf import ServiceBrowser, Zeroconf

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class PhilipsTVListener:

    def __init__(self, on_add=None, on_remove=None, timeout=1.0):
        self.on_add = on_add
        self.on_remove = on_remove
        self._hosts = {}
        self._timeout = timeout

    def remove_service(self, zeroconf, service_type, service_name):
        try:
            ip, name = self._hosts.pop(service_name)
        except KeyError:
            pass
        else:
            if self.on_remove is not None:
                self.on_remove(name, ip)

    def add_service(self, zeroconf, service_type, service_name):
        info = zeroconf.get_service_info(service_type, service_name)
        if info:
            ip = socket.inet_ntoa(info.addresses[0])
            try:
                r = requests.get(f"https://{ip}:1926/6/system", verify=False, timeout=self._timeout)
                if r.status_code == 200:
                    name = r.json()['name']
                else:
                    raise ValueError(r.text)
            except Exception as err:
                pass
            else:
                self._hosts[service_name] = ip, name
                if self.on_add is not None:
                    self.on_add(name, ip)


class PhilipsTVDiscover():

    def __init__(self, on_add=None, on_remove=None, timeout=1.0):
        self.on_add = on_add
        self.on_remove = on_remove
        self.timeout = timeout
        self._zeroconf = None

    def start(self):
        self._zeroconf = Zeroconf()
        listener = PhilipsTVListener(self.on_add, self.on_remove, self.timeout)
        self._browser = ServiceBrowser(self._zeroconf, ["_androidtvremote._tcp.local.", "_androidtvremote2._tcp.local."], listener)

    def stop(self):
        if self._zeroconf is not None:
            self._zeroconf.close()
            self._zeroconf = None
            del self._browser

    def __enter__(self):
        self.start()

    def __exit__(self, type, value, traceback):
        self.stop()


if __name__ == '__main__':

    def add(name, ip):
        print(f"Add: {name} @ {ip}")

    def remove(name, ip):
        print(f"Remove: {name} @ {ip}")

    with PhilipsTVDiscover(add, remove):
        input("Press enter to exit...\n\n")
