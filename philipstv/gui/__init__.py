import os

# import asyncio

import kivy.utils
from kivy.app import App
from kivy.core.window import Window
from kivy.clock import mainthread
from kivy.factory import Factory
from kivy.properties import ObjectProperty, StringProperty
from kivy.resources import resource_add_path
from kivy.uix.settings import SettingsWithNoMenu
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.behaviors import ButtonBehavior

from .settings import SettingMac, SettingButton, SettingHelp
from .widgets.toast import toast

from . import resources
from .resources import S
from ..api import PhilipsAPI, NotAuthorized
from ..api.discover import PhilipsTVDiscover

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
resource_add_path(os.path.join(BASE_PATH, 'data'))

APP_ICONS = {
    'app': '[font=FontAwesome]\uf108[/font]   ',
    'game': '[font=FontAwesome]\uf11b[/font]   ',
}

if kivy.utils.platform != 'android':
    window_width = Window.size[0]
    Window.size = window_width, 2 * window_width


class DiscoverButton(Factory.Button):
    host = StringProperty()

    def on_release(self):
        app = App.get_running_app()
        app.api.host = str(self.host)
        app.api.mac = None
        try:
            app.config.set('philipstv', 'host', app.api.host)
            app.config.set('philipstv', 'mac', '')
            app.config.write()
            app.setup_auth()
            app.root.current = 'remote'
            try:
                app.api.get_applications()
            except NotAuthorized:
                app.pair(app.set_mac)
            else:
                app.set_mac()
        except Exception as err:
            toast(S(err), 4.0)


class ControlButton(Factory.ToggleButton):
    settings = ObjectProperty()

    def on_release(self):
        api = App.get_running_app().api
        try:
            for node, data in self.settings.items():
                api.update_setting(node, data)
        except Exception as err:
            toast(S(err), 4.0)


class ApplicationButton(Factory.Button):
    def on_release(self):
        App.get_running_app().launch_application(self)


class PhilipsTVApp(App):
    use_kivy_settings = False

    def __init__(self):
        super().__init__()
        self.api = PhilipsAPI()
        self.auth = {}
        self._ambilight_topology = None
        self._discover = None

    def load_kv(self, filename=None):
        resources.LANG = self.config.get('interface', 'lang')
        super().load_kv(filename)

    def build(self):
        self.settings_cls = SettingsWithNoMenu
        self.icon = 'icon.png'
        self.api.host = self.config.get('philipstv', 'host')
        self.api.mac = self.config.get('philipstv', 'mac')

        auth = self.config.get('philipstv', 'auth')
        if auth:
            try:
                self.auth = {v[0]: (v[1], v[2]) for v in (a.split(':') for a in auth.split(','))}
            except IndexError:
                pass
        else:
            user = self.config.get('philipstv', 'user', fallback=None)
            passwd = self.config.get('philipstv', 'passwd', fallback=None)
            if user is not None:
                self.config.remove_option('philipstv', 'user')
            if passwd is not None:
                self.config.remove_option('philipstv', 'passwd')
            self.save_auth(user, passwd)
        self.setup_auth()

        Window.bind(on_keyboard=self.on_key_press_back, on_key_down=self.on_key_down_vol, on_key_up=self.on_key_up_vol)
        self.clean_hello()

    def clean_hello(self):
        if self.api.host:
            try:
                self.root.ids.remote.remove_widget(self.root.ids.hello)
            except:
                pass


    def start_discovery(self):
        if self._discover is None:
            self._discover = PhilipsTVDiscover(self._discover_add, self._discover_remove)
        self._discover.start()

    def stop_discovery(self):
        self._discover.stop()

    @mainthread
    def _discover_add(self, name, host):
        item = {'text': name, 'host': host}
        container = self.root.ids.discovered
        items = list(container.data)
        if item not in items:
            items.append(item)
            container.data = items
            container.refresh_from_data()

    @mainthread
    def _discover_remove(self, name, host):
        item = {'text': name, 'host': host}
        container = self.root.ids.discovered
        items = list(container.data)
        if item in items:
            items.remove(item)
            container.data = items
            container.refresh_from_data()

    def setup_auth(self):
        self.api.user, self.api.passwd = self.auth.get(self.api.host, (None, None))


    def save_auth(self, user=None, passwd=None):
        if user is not None and passwd is not None:
            self.auth[self.api.host] = user, passwd
        elif self.api.user is not None and self.api.passwd is not None:
            self.auth[self.api.host] = self.api.user, self.api.passwd
        auth = ','.join(f"{k}:{v[0]}:{v[1]}" for (k,v) in self.auth.items())
        self.config.set('philipstv', 'auth', auth)
        self.config.write()

    def build_config(self, config):
        config.setdefaults('philipstv', {'host': '', 'mac': '', 'auth': ''})
        config.setdefaults('interface', {'lang': 'English'})

    def build_settings(self, settings):
        connection = f"""
        [
            {{
                "type": "title",
                "title": "{S('Interface')}"
            }},
            {{
                "type": "options",
                "title": "{S('Language')}",
                "desc": "{S('Language of the application (needs restart)')}",
                "section": "interface",
                "key": "lang",
                "options": ["{'", "'.join(lang for lang in resources.STRINGS.keys())}"]
            }},
            {{
                "type": "title",
                "title": "{S('TV Connection')}"
            }},
            {{
                "type": "help",
                "help": "{S('_advanced_settings_help')}"
            }},
            {{
                "type": "string",
                "title": "{S('IP Address')}",
                "desc": "{S('IP address of the Philips TV')}",
                "section": "philipstv",
                "key": "host"
            }},
            {{
                "type": "mac_address",
                "title": "{S('MAC Address')}",
                "desc": "{S('MAC address of the Philips TV used for wakeup')}",
                "section": "philipstv",
                "key": "mac"
            }},
            {{
                "type": "pair_button",
                "method": "pair",
                "text": "{S('Pair')}"
            }}
        ]
        """
        settings.register_type('pair_button', SettingButton)
        settings.register_type('mac_address', SettingMac)
        settings.register_type('help', SettingHelp)
        settings.add_json_panel(S('Settings'), self.config, data=connection)

    def display_settings(self, settings):
        panel = self.root.ids.settings
        if settings not in panel.children:
            panel.add_widget(settings, 1)
        self.root.current = 'settings'
        return True

    def close_settings(self, *args):
        if self.root.current == 'settings':
            self.root.current = 'discover'
            self.set_mac()
            settings = self._app_settings
            panel = self.root.ids.settings
            panel.remove_widget(settings)
            self.destroy_settings()
            return True

    def set_mac(self, *args):
        if not self.api.mac:
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

    def on_key_press_back(self, window, key, *args):
        if key == 27:
            if self.root.current != 'remote':
                self.root.current = 'remote'
                return True

    def on_key_down_vol(self, window, key, *args):
        if key == 1073741952:
            self.root.ids.volumeup.state = 'down'
            self.root.ids.volumeup.dispatch('on_press')
        elif key == 1073741953:
            self.root.ids.volumedown.state = 'down'
            self.root.ids.volumedown.dispatch('on_press')
        else:
            return False
        return True

    def on_key_up_vol(self, window, key, *args):
        if key == 1073741952:
            self.root.ids.volumeup.state = 'normal'
            self.root.ids.volumeup.dispatch('on_release')
        elif key == 1073741953:
            self.root.ids.volumedown.state = 'normal'
            self.root.ids.volumedown.dispatch('on_release')
        else:
            return False
        return True

    def pair(self, callback=None):
        try:
            data = self.api.pair_request()
        except Exception as err:
            toast(S(err), 4.0)
            return

        if data is not None:

            def on_pin_entered(instance):
                try:
                    self.api.pair_grant(pin=instance.ids.pin_value.text, **data)
                except Exception as err:
                    toast(S(err), 4.0)
                else:
                    self.save_auth()
                    if callback is not None:
                        callback()

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
            items = self.api.get_settings(self.api.PICTURE_STYLE)[self.api.PICTURE_STYLE]['data']
            selected_item = items['selected_item']
            translations = self.api.get_strings(
                *(i['string_id'] for i in items['enum_values']), country=S('_country'), lang=S('_lang')
            )
            widget.data = [{
                'text': translations.get(item['string_id'], item['string_id']),
                'group': 'display_modes',
                'settings': {
                    self.api.PICTURE_STYLE: {
                        'selected_item': item['enum_id']
                    }
                },
                'state': 'down' if item['enum_id'] == selected_item else 'normal',
                'allow_no_selection': False,
            } for item in items['enum_values'] if item['available']]
        except Exception as err:
            toast(S(err), 4.0)
            widget.data = []

    def fill_ambilight(self):
        ids = self.root.ids
        nodes = {
            self.api.AMBILIGHT_MENU_FOLLOW_VIDEO: (ids.ambilight_video, ids.ambilight_video_ac),
            self.api.AMBILIGHT_MENU_FOLLOW_AUDIO: (ids.ambilight_audio, ids.ambilight_audio_ac),
            self.api.AMBILIGHT_MENU_LOUNGE_LIGHT: (ids.ambilight_lounge, ids.ambilight_lounge_ac)
        }
        try:
            settings = self.api.get_settings(
                self.api.AMBILIGHT_STYLE, self.api.AMBILIGHT_OFF, self.api.AMBILIGHT_LIGHTNESS, self.api.AMBILIGHT_SATURATION,
                *nodes.keys()
            )
            current_node = settings[self.api.AMBILIGHT_STYLE]['data']['activenode_id']
            for node in nodes:
                value = settings[node]
                widget = nodes[node][0]
                data = value['data']
                items = {item['enum_id']: item['string_id'] for item in data['enum_values']}
                # Add some unofficial audio styles
                if node == self.api.AMBILIGHT_MENU_FOLLOW_AUDIO:
                    items.update({
                        102: 'org.droidtv.ui.strings.R.string.MAIN_FOLLOW_AUDIO_STYLE_2',
                        106: 'org.droidtv.ui.strings.R.string.MAIN_FOLLOW_AUDIO_STYLE_5',
                        105: 'org.droidtv.ui.strings.R.string.MAIN_FOLLOW_AUDIO_STYLE_4'
                    })
                selected_item = data['selected_item']
                translations = self.api.get_strings(*items.values(), country=S('_country'), lang=S('_lang'))
                widget.data = [{
                    'text': translations[string_id],
                    'group': 'ambilight',
                    'settings': {
                        self.api.AMBILIGHT_STYLE: {
                            'activenode_id': node
                        },
                        node: {
                            'selected_item': enum_id
                        }
                    },
                    'state': 'down' if enum_id == selected_item and node == current_node else 'normal',
                    'allow_no_selection': False,
                } for enum_id, string_id in items.items()]
            if current_node == self.api.AMBILIGHT_MENU_OFF and settings[self.api.AMBILIGHT_OFF]['data']['value']:
                ids.ambilight_off.state = 'down'
            elif current_node in nodes:
                nodes[current_node][1].collapse = False

            ids.ambilight_lightness.value = settings[self.api.AMBILIGHT_LIGHTNESS]['data']['value']
            ids.ambilight_saturation.value = settings[self.api.AMBILIGHT_SATURATION]['data']['value']
        except Exception as err:
            toast(S(err), 4.0)

    def on_ambilight_lightness(self, widget, value):
        try:
            self.api.update_setting(self.api.AMBILIGHT_LIGHTNESS, {'value': value})
        except Exception as err:
            toast(S(err), 4.0)

    def on_ambilight_saturation(self, widget, value):
        try:
            self.api.update_setting(self.api.AMBILIGHT_SATURATION, {'value': value})
        except Exception as err:
            toast(S(err), 4.0)

    def on_ambilight_color(self):
        try:
            if self._ambilight_topology is None:
                self._ambilight_topology = self.api.get_ambilight_topology()
            r, g, b = self.root.ids.ambilight_color.color[:3]
            color = dict(r=int(round(255 * r)), g=int(round(255 * g)), b=int(round(255 * b)))
            values = {
                side: {str(n): color
                       for n in range(self._ambilight_topology[side])}
                for side in ('left', 'top', 'right', 'bottom')
            }
            self.api.set_ambilight_expert(self._ambilight_topology['layers'], **values)
            for tb in ToggleButton.get_widgets('ambilight'):
                tb.state = 'normal'
        except Exception as err:
            toast(S(err), 4.0)

    def fill_applications(self, widget):
        data = []
        try:
            apps = self.api.get_applications()
            app_types = list(sorted(set(app['type'] for app in apps)))
            for app_type in app_types:
                data += [{
                    'text': APP_ICONS.get(app_type, '') + app['label'],
                    'markup': True,
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
