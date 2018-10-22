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
SERVICE_SPEAK = 'speak'

# ----------
# Parameters
# ----------

CONF_VOICE = 'voice'
CONF_RATE = 'speech_rate'

# --------------
# Default values
# --------------

DEFAULT_VOICE = 'brazil'
DEFAULT_RATE = 200
DEFAULT_MESSAGE = 'Não entendi'

# ----------------
# Calls attributes
# ----------------

ATTR_MESSAGE = 'message'

# ------
# Config
# ------

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_VOICE, DEFAULT_VOICE): cv.string,
        vol.Optional(CONF_RATE, DEFAULT_RATE): int
    })
}, extra=vol.ALLOW_EXTRA)


# ------------------------------------------------------------------------------------------
# SETUP

def setup(hass, config):
    voice = config[DOMAIN].get(CONF_VOICE, DEFAULT_VOICE)
    rate = config[DOMAIN].get(CONF_RATE, DEFAULT_RATE)

    # ---------
    # MAIN CALL
    # ---------

    def speak(call):
        engine = pyttsx3.init()  # seleciona um engine de sintetização, default = pyttsx3
        engine.setProperty('voice', voice)  # propriedade voice default: pt-br
        engine.setProperty('rate', rate)  # Diminui a velocidade da fala, para ficar mais fluido

        message = call.data.get(ATTR_MESSAGE, DEFAULT_MESSAGE)
        engine.say(message)
        engine.runAndWait()
        _LOGGER.info('Speech Spoken Successfully: %s' % message)
        engine.stop()

    # Registra o serviço no HomeAssistant
    hass.services.register(DOMAIN, SERVICE_SPEAK, speak)
    _LOGGER.info('Started')

    # Retorna um booleano indicando que a inicialização foi um sucesso
    return True
