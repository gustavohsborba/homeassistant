"""Example of a custom component exposing a service."""
'''
Pré-requisitos:
sudo apt-get update && sudo apt-get install espeak
pip install pyttsx3
'''

import pyttsx3 # importamos o modulo pytts
import logging

# The domain of your component. Should be equal to the name of your component.
DOMAIN = "espeak_tts_success"
_LOGGER = logging.getLogger(__name__)


def setup(hass, config):

    def speak(call):
        engine = pyttsx3.init()  # seleciona um ending de sintetização, default = espeak
        engine.setProperty('voice', 'brazil')  # mudamos a propriedade voice para pt-br
        rate = engine.getProperty('rate')  # taxa de palavras por minuto
        engine.setProperty('rate', rate-40)  # Diminui a velocidade da fala, para ficar mais fluido

        engine.say('Seu desejo,')
        engine.runAndWait()
        engine.say('e')
        engine.runAndWait()
        engine.say('uma, ordem!')
        engine.runAndWait()

        _LOGGER.info('Spoken Successfully: Seu desejo é uma ordem!')

    # Register our service with Home Assistant.
    hass.services.register(DOMAIN, 'tts_success', speak)

    # Return boolean to indicate that initialization was successfully.
    return True

