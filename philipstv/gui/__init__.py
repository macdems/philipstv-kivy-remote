import os
import re
# import asyncio

from kivy.app import App
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.uix.settings import SettingString

from .widgets.toast import toast

from ..api import PhilipsAPI
from .resources import S

BASE_PATH = os.path.dirname(os.path.abspath(__file__))

window_width = Window.size[0]
Window.size = window_width, 2 * window_width


class DisplayModeButton(Factory.ToggleButton):
    def on_release(self):
        App.get_running_app().select_display_mode(self)


class ApplicationButton(Factory.Button):
    def on_release(self):
        App.get_running_app().launch_application(self)


class SettingMac(SettingString):
    def _validate(self, instance):
        self._dismiss()
        value = self.textinput.text.strip().upper()
        if value == '' or re.match("[0-9a-f]{2}([-:]?)[0-9A-F]{2}(\\1[0-9A-F]{2}){4}$", value):
            self.value = value


class SettingPairButton(Factory.Button):
    def __init__(self, panel):
        super().__init__(text="Pair")

    def on_release(self):
        App.get_running_app().pair()


class PhilipsTVApp(App):
    def __init__(self):
        super().__init__()
        self.api = PhilipsAPI()

    def build(self):
        self.icon = os.path.join(BASE_PATH, 'data', 'remote.png')
        self.api.host = self.config.get('philipstv', 'host')
        self.api.mac = self.config.get('philipstv', 'mac')
        self.api.user = self.config.get('philipstv', 'user')
        self.api.passwd = self.config.get('philipstv', 'passwd')

    def build_config(self, config):
        config.setdefaults('philipstv', {'host': '', 'mac': '', 'user': '', 'passwd': ''})

    def build_settings(self, settings):
        jsondata = """
        [
            {
                "type": "string",
                "title": "IP Address",
                "desc": "IP address of the Philips TV",
                "section": "philipstv",
                "key": "host"
            },
            {
                "type": "mac_address",
                "title": "MAC Address",
                "desc": "MAC address of the Philips TV used for wakeup",
                "section": "philipstv",
                "key": "mac"
            },
            {
                "type": "pair_button"
            }
        ]
        """
        settings.register_type('pair_button', SettingPairButton)
        settings.register_type('mac_address', SettingMac)
        settings.add_json_panel(S('TV Connection'), self.config, data=jsondata)

    def on_config_change(self, config, section, key, value):
        if section != 'philipstv':
            return
        if key == 'host':
            self.api.host = value
        if key == 'mac':
            self.api.mac = value

    def pair(self):
        data = self.api.pair_request()
        if data is not None:

            def on_pin_entered(instance):
                try:
                    self.api.pair_confirm(pin=instance.ids.pin_value.text, **data)
                except Exception as err:
                    toast(S(err), 4.0)
                else:
                    self.config.set('philipstv', 'user', self.api.user)
                    self.config.set('philipstv', 'passwd', self.api.passwd)
                    try:
                        self.config.set('philipstv', 'mac', self.api.set_mac())
                    except Exception as err:
                        toast(S(err), 4.0)
                    self.config.save()

            popup = Factory.PinPopup()
            popup.bind(on_dismiss=on_pin_entered)
            popup.open()

    def keypress(self, key):
        try:
            self.api.send_key(key)
        except Exception as err:
            toast(S(err), 4.0)

    def fill_display_modes(self, widget):
        try:
            res = self.api.get_current_settings(2131230858)
            items = res['values'][0]['value']['data']
            selected_item = items['selected_item']
            widget.data = [{
                'text': S(item['string_id']),
                'group': 'display_modes',
                'enum_id': item['enum_id'],
                'state': 'down' if item['enum_id'] == selected_item else 'normal',
                'allow_no_selection': False,
            } for item in items['enum_values'] if item['available']]
        except Exception as err:
            toast(S(err), 4.0)
            widget.data = []

    def select_display_mode(self, widget):
        try:
            self.api.set_current_setting(2131230858, {'selected_item': widget.enum_id})
        except Exception as err:
            toast(S(err), 4.0)

    def fill_applications(self, widget):
        data = []
        try:
            apps = self.api.get_applications()
            app_types = list(sorted(set(app['type'] for app in apps)))
            for app_type in app_types:
                data += [{
                    'text': app['label'],
                    'package_name': app['intent']['component']['packageName'],
                    'class_name': app['intent']['component']['className'],
                    'action': app['intent']['action']
                } for app in apps if app['type'] == app_type]
        except Exception as err:
            toast(S(err), 4.0)
        widget.data = data

    def launch_application(self, widget):
        try:
            self.api.launch_application(package_name=widget.package_name, class_name=widget.class_name, action=widget.action)
        except Exception as err:
            toast(S(err), 4.0)


def run():
    global app
    app = PhilipsTVApp()
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(
    #     app.async_run(async_lib='asyncio'))
    # loop.close()
    app.run()
