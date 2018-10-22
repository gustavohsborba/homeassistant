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

DOMAIN = "espeak_tts_success"
SERVICE_SPEAK = "tts_success"
REQUIREMENTS = ['pyttsx3']
_LOGGER = logging.getLogger(__name__)

# ----------
# Parameters
# ----------

CONF_VOICE = 'voice'
CONF_RATE = 'rate'

# --------------
# Default values
# --------------

DEFAULT_VOICE = 'brazil'
DEFAULT_RATE = 160
DEFAULT_MESSAGE = ['Seu desejo,', 'e', 'uma, ordem!']

# ----------------
# Calls attributes
# ----------------

ATTR_MESSAGE = 'message'
ATTR_RATE = 'rate'

# ------
# Config
# ------

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_VOICE, DEFAULT_VOICE): cv.string,
        vol.Optional(CONF_RATE, DEFAULT_RATE): int
    })
}, extra=vol.ALLOW_EXTRA)


# ------------------------------------------------------------------------------------------------
# SETUP

def setup(hass, config):

    voice = config[DOMAIN].get(CONF_VOICE, DEFAULT_VOICE)
    rate = config[DOMAIN].get(CONF_RATE, DEFAULT_RATE)

    def speak(call):

        instance_rate = call.data.get(ATTR_RATE, rate)
        messages = call.data.get(ATTR_MESSAGE, DEFAULT_MESSAGE)
        if not isinstance(messages, list):
            messages = [messages]

        engine = pyttsx3.init()
        engine.setProperty('voice', voice)
        engine.setProperty('rate', instance_rate)

        for message in messages:
            engine.say(message)
            engine.runAndWait()

        _LOGGER.info('Spoken Successfully: %s' % ' '.join(messages).replace(',', ''))
        engine.stop()

    # Register our service with Home Assistant.
    hass.services.register(DOMAIN, SERVICE_SPEAK, speak)

    # Return boolean to indicate that initialization was successfully.
    return True
