"""Example of a custom component exposing a service."""
'''
Pré-requisitos:
sudo apt-get update && sudo apt-get install espeak
pip install pyttsx3
'''
import pyttsx3
import logging
import voluptuous as vol
from homeassistant.helpers import config_validation as cv

REQUIREMENTS = ['pyttsx3']
_LOGGER = logging.getLogger(__name__)

DOMAIN = 'speech'
ATTR_MESSAGE = 'message'
CONF_VOICE = 'voice'
DEFAULT_VOICE = 'brazil'
SERVICE_SPEAK = 'speak'

# ------
# Config
# ------

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_VOICE, DEFAULT_VOICE): cv.string
    })
}, extra=vol.ALLOW_EXTRA)



def setup(hass, config):
    voice = config[DOMAIN].get(CONF_VOICE, DEFAULT_VOICE)

    def speak(call):

        message = call.data[ATTR_MESSAGE]
        _LOGGER.info('Speech received data: ' + message)

        engine = pyttsx3.init()  # seleciona um ending de sintetização, default = espeak

        engine.setProperty('voice', voice)  # mudamos a propriedade voice para pt-br
        # rate = engine.getProperty('rate')   # taxa de palavras por minuto
        # newrate = int(rate) - 40
        engine.setProperty('rate', 70)  # Diminui a velocidade da fala, para ficar mais fluido
        engine.say(message)
        engine.runAndWait()
        _LOGGER.info('Speech Spoken Successfully: ' + message)

    # Registra o serviço no HomeAssistant

    hass.services.register(DOMAIN, SERVICE_SPEAK, speak)
    _LOGGER.info('Started')
    # Retorna um booleano indicando que a inicialização foi um sucesso
    return True
