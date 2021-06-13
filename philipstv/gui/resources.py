LANG = 'Polish'


def S(string):
    string = str(string)
    try:
        return STRINGS.get(LANG, STRINGS['English'])[string]
    except KeyError:
        return STRINGS['English'].get(string, string)


STRINGS = {
    'English': {
        'org.droidtv.ui.strings.R.string.MISC_AI': 'Automatic',
        'org.droidtv.ui.strings.R.string.MAIN_PERSONAL': 'Personal',
        'org.droidtv.ui.strings.R.string.MAIN_VIVID': 'Vivid',
        'org.droidtv.ui.strings.R.string.MAIN_NATURAL': 'Natural',
        'org.droidtv.ui.strings.R.string.MAIN_STANDARD': 'Standardo',
        'org.droidtv.ui.strings.R.string.MAIN_MOVIE': 'Film',
        'org.droidtv.ui.strings.R.string.MAIN_GAME': 'Game',
        'org.droidtv.ui.strings.R.string.MAIN_MONITOR': 'Monitor',
        'org.droidtv.ui.strings.R.string.MISC_HDR_AI': 'Automatic HDR',
        'org.droidtv.ui.strings.R.string.MAIN_HDR_PERSONAL': 'Personal HDR',
        'org.droidtv.ui.strings.R.string.MAIN_HDR_VIVID': 'Vivid HDR',
        'org.droidtv.ui.strings.R.string.MAIN_HDR_NATURAL': 'Natural HDR',
        'org.droidtv.ui.strings.R.string.MAIN_HDR_STANDARD': 'Standard HDR',
        'org.droidtv.ui.strings.R.string.MAIN_HDR_MOVIE': 'Film HDR',
        'org.droidtv.ui.strings.R.string.MAIN_HDR_GAME': 'Game HDR',
        'org.droidtv.ui.strings.R.string.MAIN_HDR_MONITOR': 'Monitor HDR',
        'org.droidtv.ui.strings.R.string.MAIN_HDR_DOLBY_VISION_BRIGHT': "Dolby Vision HDR Bright",
        'org.droidtv.ui.strings.R.string.MAIN_HDR_DOLBY_VISION_DARK': "Dolby Vision HDR Vark",
        'org.droidtv.ui.strings.R.string.MAIN_ISF_DAY': "ISF Day",
        'org.droidtv.ui.strings.R.string.MAIN_ISF_NIGHT': "ISF Night",
    },
    'Polish': {
        'org.droidtv.ui.strings.R.string.MISC_AI': 'Automatyczne',
        'org.droidtv.ui.strings.R.string.MAIN_PERSONAL': 'Osobiste',
        'org.droidtv.ui.strings.R.string.MAIN_VIVID': 'Jaskrawe',
        'org.droidtv.ui.strings.R.string.MAIN_NATURAL': 'Naturalne',
        'org.droidtv.ui.strings.R.string.MAIN_STANDARD': 'Standardowe',
        'org.droidtv.ui.strings.R.string.MAIN_MOVIE': 'Film',
        'org.droidtv.ui.strings.R.string.MAIN_GAME': 'Gra',
        'org.droidtv.ui.strings.R.string.MAIN_MONITOR': 'Monitor',
        'org.droidtv.ui.strings.R.string.MISC_HDR_AI': 'Automatyczne HDR',
        'org.droidtv.ui.strings.R.string.MAIN_HDR_PERSONAL': 'Osobiste HDR',
        'org.droidtv.ui.strings.R.string.MAIN_HDR_VIVID': 'Jaskrawe HDR',
        'org.droidtv.ui.strings.R.string.MAIN_HDR_NATURAL': 'Naturalne HDR',
        'org.droidtv.ui.strings.R.string.MAIN_HDR_STANDARD': 'Standardowe HDR',
        'org.droidtv.ui.strings.R.string.MAIN_HDR_MOVIE': 'Film HDR',
        'org.droidtv.ui.strings.R.string.MAIN_HDR_GAME': 'Gra HDR',
        'org.droidtv.ui.strings.R.string.MAIN_HDR_MONITOR': 'Monitor HDR',
        'org.droidtv.ui.strings.R.string.MAIN_HDR_DOLBY_VISION_BRIGHT': "Dolby Vision HDR jasne",
        'org.droidtv.ui.strings.R.string.MAIN_HDR_DOLBY_VISION_DARK': "Dolby Vision HDR ciemne",
        'org.droidtv.ui.strings.R.string.MAIN_ISF_DAY': "ISF dzień",
        'org.droidtv.ui.strings.R.string.MAIN_ISF_NIGHT': "ISF noc",
        'Back': "Wstecz",
        'Applications': "Aplikacje",

        'Cannot reach TV. Make sure you have set correct IP and Wake-on-Lan on your TV is on.':
            "Nie można połączyć się z telewizorem. Upewnij się, że masz ustawiony prawidłowy adres IP, "
            "a funkcja Wake-on-Lan na telewizorze jest włączona. ",
        'Remote not authorized. Please pair again.': "Pilot nie posiada autoryzacji. Sparuj go ponownie.",
    }
}
