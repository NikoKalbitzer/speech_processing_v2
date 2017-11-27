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
# https://docs.microsoft.com/en-us/azure/cognitive-services/speech/api-reference-rest/bingvoiceoutput


class SupportedLocales:

    def __init__(self, locale, gender, service_name_map):
        self.locale = locale
        self.gender = gender
        self.service_name_map = service_name_map

    def __str__(self):

        return "%s: %s: %s" % (self.locale, self.gender, self.service_name_map)


mode = [
    SupportedLocales("de-DE", "Female", "Microsoft Server Speech Text to Speech Voice (de-DE, Hedda)"),
    SupportedLocales("de-DE", "Male", "Microsoft Server Speech Text to Speech Voice (de-DE, Stefan, Apollo)"),
    SupportedLocales("en-US", "Female", "Microsoft Server Speech Text to Speech Voice (en-US, ZiraRUS)"),
    SupportedLocales("en-US", "Male", "Microsoft Server Speech Text to Speech Voice (en-US, BenjaminRUS)")
]


class LanguageCommand:

    def __init__(self):
        self.modes = [mode]

    def __call__(self, locale, gender):

        for m in self.modes:
            for c in m:
                if c.locale == locale and c.gender == gender:
                    return c.service_name_map


if __name__ == '__main__':
   d = LanguageCommand()
   print(d(locale='de-DE', gender='Male'))