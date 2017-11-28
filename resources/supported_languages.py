# https://docs.microsoft.com/en-us/azure/cognitive-services/speech/api-reference-rest/supportedlanguages


class STTLanguageCommand:

    def __init__(self):
        self.interactive_dictation = interactive_dictation
        self.conversation = conversation

    def __call__(self, mode, language):

        if isinstance(language, str):
            if (mode == 'interactive') or (mode == 'dictation'):
                return interactive_dictation[language]
            elif mode == 'conversation':
                return conversation[language]
            else:
                raise ValueError("Please select mode 'interactive', 'dictation' or 'conversation'")
        else:
            raise TypeError("language must be type of string")


# Interactive and dictation mode
interactive_dictation = {
    'germany'        : 'de-DE',
    'egypt'          : 'ar-EG',
    'catalan'        : 'ca-ES',
    'denmark'        : 'da-DK',
    'australia'      : 'en-AU',
    'canada'         : 'en-CA',
    'united_kingdom' : 'en-GB',
    'india'          : 'en-IN',
    'new_zealand'    : 'en-NZ',
    'united_states'  : 'en-US',
    'spain'          : 'es-ES',
    'mexico'         : 'es-MX',
    'finland'        : 'fi-FI',
    'canada_french'  : 'fr-CA',
    'france'         : 'fr-FR',
    'hindi'          : 'hi-IN',
    'italy'          : 'it-IT',
    'japan'          : 'ja-JP',
    'korea'          : 'ko-KR',
    'norway'         : 'nb-NO',
    'netherlands'    : 'nl-NL',
    'poland'         : 'pl-PL',
    'brazil'         : 'pt-BR',
    'portugal'       : 'pt-PT',
    'russia'         : 'ru-RU',
    'sweden'         : 'sv-SE',
    'mandarin'       : 'zh-CN',
    'hong_kong'      : 'zh-HK',
    'taiwanese'      : 'zh-TW'
}
# conversation mode
conversation = {
    'egypt'          : 'ar-EG',
    'germany'        : 'de-DE',
    'united_states'  : 'en-US',
    'spain'          : 'es-ES',
    'france'         : 'fr-FR',
    'italy'          : 'it-IT',
    'japan'          : 'ja-JP',
    'brazil'         : 'pt-BR',
    'russia'         : 'ru-RU',
    'mandarin'       : 'zh-CN'
}

##########TextToSpeech#################

# https://docs.microsoft.com/en-us/azure/cognitive-services/speech/api-reference-rest/bingvoiceoutput


class TTSSupportedLocales:

    def __init__(self, country, locale, gender, service_name_map):
        self.country = country
        self.locale = locale
        self.gender = gender
        self.service_name_map = service_name_map

    def __str__(self):

        return "%s: %s: %s: %s" % (self.country, self.locale, self.gender, self.service_name_map)


mode = [
    TTSSupportedLocales("germany", "de-DE", "Female", "Microsoft Server Speech Text to Speech Voice (de-DE, Hedda)"),
    TTSSupportedLocales("germany", "de-DE", "Male", "Microsoft Server Speech Text to Speech Voice (de-DE, Stefan, Apollo)"),

    TTSSupportedLocales("united_states", "en-US", "Female", "Microsoft Server Speech Text to Speech Voice (en-US, ZiraRUS)"),
    TTSSupportedLocales("united_states", "en-US", "Male", "Microsoft Server Speech Text to Speech Voice (en-US, BenjaminRUS)"),

    TTSSupportedLocales("australia", "en-AU", "Female", "Microsoft Server Speech Text to Speech Voice (en-AU, Catherine)"),

    TTSSupportedLocales("united_kingdom", "en-GB", "Female", "Microsoft Server Speech Text to Speech Voice (en-GB, Susan, Apollo)"),
    TTSSupportedLocales("united_kingdom", "en-GB", "Male", "Microsoft Server Speech Text to Speech Voice (en-GB, George, Apollo)"),

    TTSSupportedLocales("spain", "es-ES", "Female", "Microsoft Server Speech Text to Speech Voice (es-ES, Laura, Apollo)"),
    TTSSupportedLocales("spain", "es-ES", "Male", "Microsoft Server Speech Text to Speech Voice (es-ES, Pablo, Apollo)")
]


class TTSLanguageCommand:
    def __init__(self):
        self.modes = [mode]

    def __call__(self, country, gender):

        for m in self.modes:
            for c in m:
                if c.country == country and c.gender == gender:
                    return c.locale, c.service_name_map


if __name__ == '__main__':
   d = TTSLanguageCommand()
   print(d(country='germany', gender='Female'))
   #sst = STTLanguageCommand()
   #print(sst(mode='interactive_dictation', language='germany'))