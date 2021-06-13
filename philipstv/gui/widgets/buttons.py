from time import time
from kivy.clock import Clock
from kivy.factory import Factory

class LongPressButton(Factory.Button):
    __events__ = 'on_long_press',

    long_press_time = Factory.NumericProperty(1.0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__clockev = None
        self.__long_fired = False

    def on_state(self, instance, value):
        if value == 'down':
            self.__clockev = Clock.schedule_once(self._do_long_press, self.long_press_time)
        elif self.__clockev is not None:
            self.__clockev.cancel()
        self.__long_fired = False

    def on_touch_up(self, touch):
        if not self.__long_fired or touch.grab_current is not self:
            return super().on_touch_up(touch)

        touch.ungrab(self)
        self.last_touch = touch

        if (not self.always_release and not self.collide_point(*touch.pos)):
            self._do_release()
            return

        self._do_release()
        return True

    def _do_long_press(self, dt):
        self.__long_fired = True
        self.dispatch('on_long_press')

    def on_long_press(self, *largs):
        pass


class RepeatButton(Factory.Button):

    initial_delay = Factory.NumericProperty(1.0)
    repeat_time = Factory.NumericProperty(0.1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__clockev = None

    def on_state(self, instance, value):
        if value == 'down':
            self.__clockev = Clock.schedule_once(self._do_repeat, self.initial_delay)
        elif self.__clockev is not None:
            self.__clockev.cancel()

    def _do_repeat(self, dt):
        self.dispatch('on_release')
        self.__clockev = Clock.schedule_once(self._do_repeat, self.repeat_time)
        self.dispatch('on_press')
