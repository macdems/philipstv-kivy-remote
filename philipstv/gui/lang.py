from kivy.lang import Observable

from .strings import STRINGS


DEFAULT = 'en_US'


class Lang(Observable):
    _observers = []
    lang = None

    def __init__(self, lang=DEFAULT):
        super(Lang, self).__init__()
        self.lang = lang

    def tr(self, text):
        string = str(text)
        try:
            return STRINGS.get(self.lang, STRINGS[DEFAULT])[string]
        except KeyError:
            return STRINGS[DEFAULT].get(string, string)

    def fbind(self, name, func, args, **kwargs):
        if name == "tr":
            self._observers.append((func, args, kwargs))
        else:
            return super().fbind(name, func, *args, **kwargs)

    def funbind(self, name, func, args, **kwargs):
        if name == "tr":
            key = (func, args, kwargs)
            if key in self._observers:
                self._observers.remove(key)
        else:
            return super().funbind(name, func, *args, **kwargs)

    def switch_lang(self, lang):
        self.lang = lang
        for func, largs, kwargs in self._observers:
            func(largs, None, None)


l = Lang(DEFAULT)
