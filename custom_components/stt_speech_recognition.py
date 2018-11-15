"""
Provide functionality to transform speech into text using pocketsphinx.

sudo apt-get install git build-essential \
    python3 python3-dev python3-pip python3-venv
pip3 install SpeechRecognition
"""
import os
import logging
import voluptuous as vol
import speech_recognition as sr
from homeassistant.const import CONF_NAME
from homeassistant.helpers import config_validation as cv

_LOGGER = logging.getLogger(__name__)
REQUIREMENTS = ['SpeechRecognition', 'pocketsphinx', 'webrtcvad==2.0.10', 'PyAudio>=0.2.8']
DOMAIN = 'stt_speech_recognition'

# ------------------------
# Configuration parameters
# ------------------------

CONF_LANGUAGE = 'pt-br'
CONF_GRAMMAR = 'grammar_path'
CONF_TIMEOUT = 'timeout'


# ----------------------
# Configuration defaults
# ----------------------

DEFAULT_NAME = 'stt_pocketsphinx'
DEFAULT_UNKNOWN_COMMAND = 'unknown_command'
DEFAULT_LANGUAGE = 'pt-br-picado'
DEFAULT_GRAMMAR = '/opt/cefetmg/data/pocketsphinx/gramatica.jsgf'
DEFAULT_TIMEOUT = 4.0

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

# Fired when start recording
EVENT_LISTENING = 'listening_to_microphone'

# Fired when command has finished recording
EVENT_SPEECH_RECORDED = 'speech_recorded'

# Fired when decoding has finished
EVENT_SPEECH_TO_TEXT = 'speech_to_text'


# ------
# Config
# ------

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_NAME, DEFAULT_NAME): cv.string,
        vol.Optional(CONF_TIMEOUT, DEFAULT_TIMEOUT): float,
        vol.Optional(CONF_LANGUAGE, DEFAULT_LANGUAGE): cv.string
    })
}, extra=vol.ALLOW_EXTRA)
state_attrs = {
    'friendly_name': 'Speech to Text',
    'icon': 'mdi:comment-text',
    'text': ''
}

# -----------------------------------------------------------------------------
# SETUP


def setup(hass, config):

    hass.states.set(OBJECT_POCKETSPHINX, STATE_LOADING, state_attrs)
    name = config[DOMAIN].get(CONF_NAME, DEFAULT_NAME)
    timeout = config[DOMAIN].get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
    language = config[DOMAIN].get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
    grammar = config[DOMAIN].get(CONF_GRAMMAR, DEFAULT_GRAMMAR)

    language_dir = os.path.join(os.path.dirname(sr.__file__), "pocketsphinx-data", language)
    acoustic_model_dir = os.path.join(language_dir, "acoustic-model")
    language_model_file = os.path.join(language_dir, "language-model.lm.bin")
    phoneme_dict_file = os.path.join(language_dir, "pronounciation-dictionary.dict")
    assert os.path.exists(grammar), 'Grammar does not exist in path %s' % grammar
    assert os.path.isdir(language_dir), "missing PocketSphinx language data directory: \"%s\"" % language_dir
    assert os.path.isdir(acoustic_model_dir), "Acoustic model directory not found: \"%s\"" % acoustic_model_dir
    assert os.path.exists(language_model_file), 'Language Model File does not exist in path %s' % language_model_file
    assert os.path.exists(phoneme_dict_file), 'Pronunciation Dictionary does not exist in path %s' % phoneme_dict_file

    # -------------------------------------------------------------------------
    # DETECTED TEXT CALLBACK

    def detected_text(text):
        hass.states.set(OBJECT_POCKETSPHINX, STATE_IDLE, state_attrs)
        hass.bus.async_fire(EVENT_SPEECH_TO_TEXT, {'name': name, 'text': text})
        _LOGGER.info("SERVICE SPEECH_RECOGNITION_STT DETECTED: %s" % text)

    # -------------------------------------------------------------------------
    # SERVICE LISTEN

    def listen(call):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source)
            hass.states.set(OBJECT_POCKETSPHINX, STATE_LISTENING, state_attrs)
            hass.bus.async_fire(EVENT_LISTENING, {'name': name, 'state': STATE_LISTENING})
            try:
                _LOGGER.warning("SPEECH_RECOGNITION: LISTENING TO MICROPHONE")
                audio = r.listen(source, timeout=timeout)
                hass.states.set(OBJECT_POCKETSPHINX, STATE_DECODING, state_attrs)
                hass.bus.async_fire(EVENT_SPEECH_RECORDED, {'name': name})

                # recognize speech using Sphinx
                speech = r.recognize_sphinx(audio, language=language, grammar=grammar)
                _LOGGER.warning("SPEECH_RECOGNITION: SPEECH RECOGNIZED: %s" % speech)
                detected_text(speech)

            except sr.UnknownValueError:
                _LOGGER.warning("SPEECH_RECOGNITION: Sphinx could not understand audio")
                detected_text(DEFAULT_UNKNOWN_COMMAND)
            except sr.RequestError as e:
                _LOGGER.warning("SPEECH_RECOGNITION: Sphinx error; {0}".format(e))
                detected_text(DEFAULT_UNKNOWN_COMMAND)
            _LOGGER.info("SERVICE SPEECH_RECOGNITION COMPLETED")

    # -------------------------------------------------------------------------

    # Service to listen and identify commands
    hass.services.register(DOMAIN, SERVICE_LISTEN, listen)
    hass.states.set(OBJECT_POCKETSPHINX, STATE_IDLE, state_attrs)
    _LOGGER.info('Started')

    return True
