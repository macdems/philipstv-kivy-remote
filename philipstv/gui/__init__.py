import os
import re
# import asyncio

import kivy.utils

from kivy.app import App
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.clock import Clock
from kivy.uix.settings import SettingString, SettingsWithNoMenu

from .widgets.toast import toast

from . import resources
from .resources import S
from ..api import PhilipsAPI

BASE_PATH = os.path.dirname(os.path.abspath(__file__))

if kivy.utils.platform != 'android':
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
        super().__init__(text=S("Pair"))

    def on_release(self):
        App.get_running_app().pair()


class PhilipsTVApp(App):
    use_kivy_settings = False

    def __init__(self):
        super().__init__()
        self.api = PhilipsAPI()

    def load_kv(self, filename=None):
        resources.LANG = self.config.get('interface', 'lang')
        super().load_kv(filename)

    def build(self):
        self.settings_cls = SettingsWithNoMenu
        self.icon = os.path.join(BASE_PATH, 'data', 'icon.png')
        self.api.host = self.config.get('philipstv', 'host')
        self.api.mac = self.config.get('philipstv', 'mac')
        self.api.user = self.config.get('philipstv', 'user')
        self.api.passwd = self.config.get('philipstv', 'passwd')
        Window.bind(on_keyboard=self.on_keyboard_back)
        self.clean_hello()

    def clean_hello(self):
        if self.api.host:
            self.root.ids.remote.remove_widget(self.root.ids.hello)

    def build_config(self, config):
        config.setdefaults('philipstv', {'host': '', 'mac': '', 'user': '', 'passwd': ''})
        config.setdefaults('interface', {'lang': 'English'})

    def build_settings(self, settings):
        connection = """
        [
            {{
                "type": "title",
                "title": "{interface}"
            }},
            {{
                "type": "options",
                "title": "{lang}",
                "desc": "{lang_desc}",
                "section": "interface",
                "key": "lang",
                "options": ["{lang_options}"]
            }},
            {{
                "type": "title",
                "title": "{connection}"
            }},
            {{
                "type": "string",
                "title": "{ip}",
                "desc": "{ip_desc}",
                "section": "philipstv",
                "key": "host"
            }},
            {{
                "type": "mac_address",
                "title": "{mac}",
                "desc": "{mac_desc}",
                "section": "philipstv",
                "key": "mac"
            }},
            {{
                "type": "pair_button"
            }}
        ]
        """.format(
            interface=S('Interface'),
            lang=S('Language'),
            lang_desc=S('Language of the application (needs restart)'),
            lang_options='", "'.join(lang for lang in resources.STRINGS.keys()),
            connection=S('TV Connection'),
            ip=S('IP Address'),
            ip_desc=S('IP address of the Philips TV'),
            mac=S('MAC Address'),
            mac_desc=S('MAC address of the Philips TV used for wakeup')
        )
        settings.register_type('pair_button', SettingPairButton)
        settings.register_type('mac_address', SettingMac)
        settings.add_json_panel(S('Settins'), self.config, data=connection)

    def display_settings(self, settings):
        panel = self.root.ids.settings
        if settings not in panel.children:
            panel.add_widget(settings, 1)
        self.root.current = 'settings'
        return True

    def close_settings(self, *largs):
        if self.root.current == 'settings':
            self.root.current = 'remote'
            if self.set_mac():
                settings = self._app_settings
                panel = self.root.ids.settings
                panel.remove_widget(settings)
                self.destroy_settings()
            return True

    def set_mac(self, *largs):
        if self.api.mac == '':
            try:
                self.config.set('philipstv', 'mac', self.api.set_mac())
            except:
                pass
            else:
                self.config.write()
                return True
        return False

    def on_config_change(self, config, section, key, value):
        if section != 'philipstv':
            return
        if key == 'host':
            self.api.host = value
        if key == 'mac':
            self.api.mac = value

    def on_keyboard_back(self, window, key, *largs):
        if key == 27:
            if self.root.current != 'remote':
                self.root.current = 'remote'
                return True

    def pair(self):
        try:
            data = self.api.pair_request()
        except Exception as err:
            toast(S(err), 4.0)
            return

        if data is not None:

            def on_pin_entered(instance):
                try:
                    self.api.pair_confirm(pin=instance.ids.pin_value.text, **data)
                except Exception as err:
                    toast(S(err), 4.0)
                else:
                    self.config.set('philipstv', 'user', self.api.user)
                    self.config.set('philipstv', 'passwd', self.api.passwd)
                    self.config.write()

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
