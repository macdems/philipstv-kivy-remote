LANG = 'English'


def S(string):
    string = str(string)
    try:
        return STRINGS.get(LANG, STRINGS['English'])[string]
    except KeyError:
        return STRINGS['English'].get(string, string)


STRINGS = {
    'English': {
        '_country': 'en_US',
        '_lang': 'en'
    },
    'Polski': {
        '_country': 'pl_PL',
        '_lang': 'pl',
        'Back': "Wstecz",
        'Applications': "Aplikacje",
        'Pair': "Paruj",
        'Press Back again to exit': "Proszę nacisnąć Wstecz ponownie aby zakończyć",
        'Interface': "Interfejs",
        'Language': "Język",
        'Language of the application (needs restart)': "Język aplikacji (wymagany restart)",
        'TV Connection': "Połączenie z TV",
        'IP Address': "Adres IP",
        'IP address of the Philips TV': "Adres IP telewizora Philips",
        'MAC Address': "Adres MAC",
        'MAC address of the Philips TV used for wakeup': "Adres MAC telewizora Philips (automatyczne wybudzenie)",
        'Ambilight Off': "Wyłączone",
        'Follow Video': "Śledzenie obrazu",
        'Follow Audio': "Śledzenie dźwięku",
        'Settings': "Ustawienia",
        'Advanced': "Zaawansowane",
        'Lightness': "Jasność",
        'Saturation': "Nasycenie",

        'Cannot reach TV. Make sure you have set correct IP and Wake-on-Lan on your TV is on.':
            "Nie można połączyć się z telewizorem. Upewnij się, że masz ustawiony prawidłowy adres IP, "
            "a funkcja Wake-on-Lan na telewizorze jest włączona. ",
        'Remote not authorized. Please pair again.': "Pilot nie posiada autoryzacji. Proszę spować go ponownie.",
        'No host. Please set IP of your TV.': "Brak zdefiniowanego adresu IP telewizora. Proszę go podać w ustawieniach."
    }
}
