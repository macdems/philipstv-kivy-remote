import re

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.settings import SettingString
from kivy.properties import ObjectProperty


class SettingMac(SettingString):
    def _validate(self, instance):
        self._dismiss()
        value = self.textinput.text.strip().upper()
        if value == '' or re.match("[0-9a-f]{2}([-:]?)[0-9A-F]{2}(\\1[0-9A-F]{2}){4}$", value):
            self.value = value


class SettingButton(Button):
    panel = ObjectProperty(None)

    def __init__(self, panel, method, **kwargs):
        self.panel = panel
        super().__init__(**kwargs)
        self.method = method

    def on_release(self):
        getattr(App.get_running_app(), self.method)()

class SettingHelp(Label):
    panel = ObjectProperty(None)

    def __init__(self, panel, help, **kwargs):
        self.panel = panel
        super().__init__(**kwargs)
        self.text = help
