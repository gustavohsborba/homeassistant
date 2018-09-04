
"""Example of a custom component exposing a service."""
'''
Pré-requisitos:
sudo apt-get update && sudo apt-get install espeak
pip install pyttsx3
'''

import pyttsx3 # importamos o modulo pytts
import logging

# The domain of your component. Should be equal to the name of your component.
DOMAIN = "espeak_tts"
_LOGGER = logging.getLogger(__name__)


def setup(hass, config):
    
    def speak(call):
        _LOGGER.info('Received data: ', call.data)
        message = call.data.get('message')
        
        engine = pyttsx3.init()  # seleciona um ending de sintetização, default = espeak

        engine.setProperty('voice', 'brazil')  # mudamos a propriedade voice para pt-br
        rate = engine.getProperty('rate')  # taxa de palavras por minuto
        engine.setProperty('rate', rate-40)  # Diminui a velocidade da fala, para ficar mais fluido
        engine.say(message) 
        engine.runAndWait()
        _LOGGER.info('Spoken Successfully: ', message)

    # Register our service with Home Assistant.
    hass.services.register(DOMAIN, 'speak', speak)

    # Return boolean to indicate that initialization was successfully.
    return True