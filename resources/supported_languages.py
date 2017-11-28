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

conversation = {

}


class STTLanguageCommand:

    def __init__(self):
        self.interactive_dictation = interactive_dictation
        self.conversation = conversation

    def __call__(self, mode, language):

        if isinstance(language, str):
            if mode == 'interactive_dictation':
                return interactive_dictation[language]
            elif mode == 'conversation':
                return conversation[language]
            else:
                raise ValueError("Please select mode 'interactive_dictation' or 'conversation'")
        else:
            raise TypeError("language must be type of string")




# https://docs.microsoft.com/en-us/azure/cognitive-services/speech/api-reference-rest/bingvoiceoutput


class TTSSupportedLocales:

    def __init__(self, locale, gender, service_name_map):
        self.locale = locale
        self.gender = gender
        self.service_name_map = service_name_map

    def __str__(self):

        return "%s: %s: %s" % (self.locale, self.gender, self.service_name_map)


mode = [
    TTSSupportedLocales("de-DE", "Female", "Microsoft Server Speech Text to Speech Voice (de-DE, Hedda)"),
    TTSSupportedLocales("de-DE", "Male", "Microsoft Server Speech Text to Speech Voice (de-DE, Stefan, Apollo)"),

    TTSSupportedLocales("en-US", "Female", "Microsoft Server Speech Text to Speech Voice (en-US, ZiraRUS)"),
    TTSSupportedLocales("en-US", "Male", "Microsoft Server Speech Text to Speech Voice (en-US, BenjaminRUS)"),

    TTSSupportedLocales("en-AU", "Female", "Microsoft Server Speech Text to Speech Voice (en-AU, Catherine)"),

    TTSSupportedLocales("en-GB", "Female", "Microsoft Server Speech Text to Speech Voice (en-GB, Susan, Apollo)"),
    TTSSupportedLocales("en-GB", "Male", "Microsoft Server Speech Text to Speech Voice (en-GB, George, Apollo)"),

    TTSSupportedLocales("es-ES", "Female", "Microsoft Server Speech Text to Speech Voice (es-ES, Laura, Apollo)"),
    TTSSupportedLocales("es-ES", "Male", "Microsoft Server Speech Text to Speech Voice (es-ES, Pablo, Apollo)")
]


class TTSLanguageCommand:

    def __init__(self):
        self.modes = [mode]

    def __call__(self, locale, gender):

        for m in self.modes:
            for c in m:
                if c.locale == locale and c.gender == gender:
                    return c.service_name_map


if __name__ == '__main__':
   d = TTSLanguageCommand()
   print(d(locale='de-DE', gender='Male'))
   sst = STTLanguageCommand()
   print(sst(mode='interactive_dictation', language='germany'))