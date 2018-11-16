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

DOMAIN = "speech"
SERVICE_SPEAK = "speak"
EVENT_TEXT_TO_SPEECH = 'text_to_speech'
REQUIREMENTS = ['pyttsx3']
_LOGGER = logging.getLogger(__name__)

# ----------
# Parameters
# ----------

CONF_VOICE = 'voice'
CONF_SPEECH_RATE = 'speech_rate'

# --------------
# Default values
# --------------

DEFAULT_VOICE = 'brazil'
DEFAULT_SPEECH_RATE = 160
DEFAULT_MESSAGE = ['Seu desejo,', 'e', 'uma, ordem!']

# ----------------
# Calls attributes
# ----------------

ATTR_MESSAGE = 'message'
ATTR_SPEECH_RATE = 'speech_rate'

# ------
# Config
# ------

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_VOICE, DEFAULT_VOICE): cv.string,
        vol.Optional(CONF_SPEECH_RATE, DEFAULT_SPEECH_RATE): int
    })
}, extra=vol.ALLOW_EXTRA)


# ------------------------------------------------------------------------------------------------
# SETUP

def setup(hass, config):

    voice = config[DOMAIN].get(CONF_VOICE, DEFAULT_VOICE)
    speech_rate = config[DOMAIN].get(CONF_SPEECH_RATE, DEFAULT_SPEECH_RATE)

    def speak(call):

        instance_speech_rate = call.data.get(ATTR_SPEECH_RATE, speech_rate)
        messages = call.data.get(ATTR_MESSAGE, DEFAULT_MESSAGE)
        if not isinstance(messages, list):
            messages = [messages]

        engine = pyttsx3.init()
        engine.setProperty('voice', voice)
        engine.setProperty('rate', instance_speech_rate)
        spoken_message = ' '.join(messages).replace(',', '')

        _LOGGER.warning('Speaking: %s' % spoken_message)
        for message in messages:
            engine.say(message)
            engine.runAndWait()

        _LOGGER.warning('Spoken Successfully: %s' % spoken_message)
        hass.bus.async_fire(EVENT_TEXT_TO_SPEECH, {
            'name': '%s.%s' % (DOMAIN, SERVICE_SPEAK),  # domain and name of the service
            'message': spoken_message  # text
        })
        engine.stop()

    # Register our service with Home Assistant.
    hass.services.register(DOMAIN, SERVICE_SPEAK, speak)

    # Return boolean to indicate that initialization was successfully.
    return True
