"""
Provide functionality to transform speech into text using pocketsphinx.

sudo apt-get install git build-essential \
    python3 python3-dev python3-pip python3-venv
pip3 install SpeechRecognition
"""
import logging
import voluptuous as vol
import speech_recognition as sr
from homeassistant.const import CONF_NAME
from homeassistant.helpers import config_validation as cv

_LOGGER = logging.getLogger(__name__)
REQUIREMENTS = ['SpeechRecognition', 'pocketsphinx', 'webrtcvad==2.0.10', 'PyAudio>=0.2.8']
DOMAIN = 'stt_speech_recognition'


# ----------------------
# Configuration defaults
# ----------------------

DEFAULT_NAME = 'stt_pocketsphinx'
DEFAULT_UNKNOWN_COMMAND = 'unknown_command'


# --------
# Services
# --------

# Starts listening for commands on the configured microphone
SERVICE_LISTEN = 'listen'

# Clears cached decoder (used after re-training)
SERVICE_RESET = 'reset'

# Represents the listener and decoder
OBJECT_POCKETSPHINX = '%s.pocketsphinx' % DOMAIN

# Not listening or decoding
STATE_IDLE = 'idle'

# Loading decoder
STATE_LOADING = 'loading'

# Currently recording a command
STATE_LISTENING = 'listening'

# Currently decoding WAV data (speech to text)
STATE_DECODING = 'decoding'

# Fired when command has finished recording
EVENT_SPEECH_RECORDED = 'speech_recorded'

# Fired when decoding has finished
EVENT_SPEECH_TO_TEXT = 'speech_to_text'


# ------
# Config
# ------

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_NAME, DEFAULT_NAME): cv.string
    })
}, extra=vol.ALLOW_EXTRA)


# -----------------------------------------------------------------------------
# SETUP

def setup(hass, config):

    name = config[DOMAIN].get(CONF_NAME, DEFAULT_NAME)
    state_attrs = {
        'friendly_name': 'Speech to Text',
        'icon': 'mdi:comment-text',
        'text': ''
    }
    hass.states.set(OBJECT_POCKETSPHINX, STATE_LOADING, state_attrs)

    # -------------------------------------------------------------------------
    # DETECTED TEXT CALLBACK

    def detected_text(text):
        hass.states.set(OBJECT_POCKETSPHINX, STATE_IDLE, state_attrs)
        hass.bus.async_fire(EVENT_SPEECH_RECORDED, {'name': name})
        hass.bus.async_fire(EVENT_SPEECH_TO_TEXT, {
            'name': name,  # name of the component
            'text': text  # text
        })
        _LOGGER.info("SERVICE SPEECH_RECOGNITION_STT DETECTED: %s" % text)

    # -------------------------------------------------------------------------
    # SERVICE LISTEN

    def listen(call):
        hass.states.set(OBJECT_POCKETSPHINX, STATE_LISTENING, state_attrs)

        r = sr.Recognizer()
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source)
            try:
                _LOGGER.warning("SPEECH_RECOGNITION: LISTENING TO MICROPHONE")
                audio = r.listen(source)

                # recognize speech using Sphinx
                # speech = r.recognize_sphinx(audio, language='pt-br')
                # speech = r.recognize_sphinx(audio, grammar='/opt/cefetmg/data/gramatica.jsgf')
                speech = r.recognize_sphinx(audio)
                hass.states.set(OBJECT_POCKETSPHINX, STATE_DECODING, state_attrs)
                _LOGGER.warning("SPEECH_RECOGNITION: SPEECH RECOGNIZED: %s" % speech)
                detected_text(speech)

            except sr.UnknownValueError:
                _LOGGER.warning("SPEECH_RECOGNITION: Sphinx could not understand audio")
                detected_text(DEFAULT_UNKNOWN_COMMAND)
            except sr.RequestError as e:
                _LOGGER.warning("SPEECH_RECOGNITION: Sphinx error; {0}".format(e))
                detected_text(DEFAULT_UNKNOWN_COMMAND)

    # -------------------------------------------------------------------------

    # Service to listen and identify commands
    hass.services.register(DOMAIN, SERVICE_LISTEN, listen)
    hass.states.set(OBJECT_POCKETSPHINX, STATE_IDLE, state_attrs)
    _LOGGER.info('Started')

    return True
