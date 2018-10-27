"""
Provê a funcionalidade para ouvir a hotword via Snowboy
e definir os callbacks para os intents
Pré-requisitos:


sudo apt-get install git build-essential \
    python3 python3-dev python3-pip python3-venv \
    libasound2-dev libpulse-dev swig \
    portaudio19-dev \
    libttspico-utils \
    libtcl8.6 \
    libatlas-dev libatlas-base-dev
sudo apt-get install liblapack-dev liblapack3 \
    libopenblas-base libopenblas-dev libatlas-base-dev \
    libportaudio2 libasound-dev libportaudio2 \
    libportaudiocpp0 ffmpeg libav-tools \
    libjack0 libjack-dev portaudio19-dev
pip install snowboy==1.2.0b1
"""
import os
import logging
import re

import voluptuous as vol

from homeassistant.const import CONF_NAME, EVENT_HOMEASSISTANT_STOP
from homeassistant.helpers import config_validation as cv

_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['snowboy']
DOMAIN = 'stt_snowboy'

# ------
# Config
# ------

CONF_SENSITIVITY = 'sensitivity'
CONF_AUDIO_GAIN = 'audio_gain'
CONF_MODELS = 'models'
CONF_INTENT_TEXTS = 'intent_texts'
CONF_KEYWORDS = 'keywords'
CONF_TIMEOUT = 'timeout'

# ----------------------
# Configuration defaults
# ----------------------

DEFAULT_NAME = 'stt_snowboy'
DEFAULT_SENSITIVITY = 0.5
DEFAULT_AUDIO_GAIN = 1.0
DEFAULT_TIMEOUT = 10.0
DEFAULT_KEYWORDS = ['']
DEFAULT_MODELS = ['']
DEFAULT_INTENT_TEXTS = ['']
DEFAULT_UNKNOWN_COMMAND = 'unknown_command'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_KEYWORDS, DEFAULT_KEYWORDS): cv.ensure_list_csv,
        vol.Required(CONF_MODELS, DEFAULT_MODELS): cv.ensure_list_csv,
        vol.Required(CONF_INTENT_TEXTS, DEFAULT_INTENT_TEXTS): cv.ensure_list_csv,
        vol.Optional(CONF_TIMEOUT, DEFAULT_TIMEOUT): float,
        vol.Optional(CONF_NAME, DEFAULT_NAME): cv.string,
        vol.Optional(CONF_SENSITIVITY, DEFAULT_SENSITIVITY): float,
        vol.Optional(CONF_AUDIO_GAIN, DEFAULT_AUDIO_GAIN): float
    })
}, extra=vol.ALLOW_EXTRA)

# --------
# Services
# --------


SERVICE_DETECT = 'detect_commands'
# Not doing anything
STATE_IDLE = 'idle'
# Listening for the hotword
STATE_LISTENING = 'listening'
# Fired when the hotword is detected
EVENT_SPEECH_RECORDED = 'speech_recorded'
# Fired when decoding has finished
EVENT_SPEECH_TO_TEXT = 'speech_to_text'
# Represents the hotword detector
OBJECT_SNOWBOY = '%s.decoder' % DOMAIN


# -----------------------------------------------------------------------------

def setup(hass, config):
    # Parametric Configuration
    name = config[DOMAIN].get(CONF_NAME, DEFAULT_NAME)
    models_json = config[DOMAIN].get(CONF_MODELS, DEFAULT_MODELS)
    keywords_json = config[DOMAIN].get(CONF_KEYWORDS, DEFAULT_KEYWORDS)
    intents_json = config[DOMAIN].get(CONF_INTENT_TEXTS, DEFAULT_INTENT_TEXTS)
    sensitivity = config[DOMAIN].get(CONF_SENSITIVITY, DEFAULT_SENSITIVITY)
    audio_gain = config[DOMAIN].get(CONF_AUDIO_GAIN, DEFAULT_AUDIO_GAIN)
    timeout = config[DOMAIN].get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
    state_attrs = {'friendly_name': 'Snowboy STT', 'icon': 'mdi:microphone'}
    terminated = False

    models = []
    keywords = [k for k in keywords_json]
    intents = [t for t in intents_json]
    assert len(models_json) == len(keywords), 'Assign exactly one text for each model'
    for model in models_json:
        assert os.path.exists(model), 'Model does not exist'
        models.append(str(model))
    indexed_models = dict(zip(keywords, models))
    sensitivities = [sensitivity]*len(models)
    _LOGGER.info("MODELS LOADED: %s" % str(indexed_models))
    _LOGGER.info("SENSITIVITIES: %s" % str(sensitivities))

    # Main Functionality Registered in HomeAssistant
    def detect(call):

        temp_text = ''

        # Interruption Handling
        interrupted = False
        counter = 0

        def interrupt_second():
            nonlocal interrupted
            nonlocal terminated
            nonlocal counter
            counter += 0.03
            if int(counter) == timeout:
                counter = 0
                detected_text(DEFAULT_UNKNOWN_COMMAND)
                return True
            return interrupted or terminated

        # Detects keyword
        def detect_keyword(word):
            nonlocal temp_text
            temp_text = '%s %s' % (temp_text, word)
            _LOGGER.info("SERVICE SNOWBOY STT TEMP_TEXT: %s" % temp_text)
            _LOGGER.info("SERVICE SNOWBOY STT INTENTS: %s" % str(intents))
            intents_detected = [t for t in intents if re.search(r'\b' + t + r'\b', temp_text)]
            if intents_detected:
                if len(intents_detected) == 1:
                    detected_text(intents_detected[0])
                else:
                    detected_text(DEFAULT_UNKNOWN_COMMAND)

        def lambda_callback_keyword(text):
            return lambda: detect_keyword(text)

        # Fire detected event to HomeAssistant
        def detected_text(text):
            nonlocal interrupted
            hass.states.async_set(OBJECT_SNOWBOY, STATE_IDLE, state_attrs)
            hass.bus.async_fire(EVENT_SPEECH_RECORDED, {'name': name})
            hass.bus.async_fire(EVENT_SPEECH_TO_TEXT, {
                'name': name,  # name of the component
                'text': text  # text
            })
            _LOGGER.info("SERVICE SNOWBOY STT DETECTED: %s" % text)
            interrupted = True

        from snowboy import snowboydecoder
        hass.states.async_set(OBJECT_SNOWBOY, STATE_LISTENING, state_attrs)

        _LOGGER.info("MODELS LOADED: %s" % str(indexed_models))
        _LOGGER.info("MODELS: %s" % models)
        _LOGGER.info("SENSITIVITIES: %s" % str(sensitivities))

        detector = snowboydecoder.HotwordDetector(models,
                                                  sensitivity=sensitivities,
                                                  audio_gain=audio_gain)

        _LOGGER.info("KEYWORDS: %s" % str(keywords))
        callbacks = [lambda_callback_keyword(k) for k in keywords]
        detector.start(detected_callback=callbacks,
                       interrupt_check=interrupt_second,
                       sleep_time=0.03)

        detector.terminate()
        _LOGGER.info("SERVICE SNOWBOY STT COMPLETED")

    # Make sure snowboy terminates property when home assistant stops
    def terminate(event):
        nonlocal terminated
        terminated = True
        hass.bus.async_listen(EVENT_HOMEASSISTANT_STOP, terminate)

    # After defining values and functions, register services in Home Assistant
    hass.services.async_register(DOMAIN, SERVICE_DETECT, detect)
    hass.states.async_set(OBJECT_SNOWBOY, STATE_IDLE, state_attrs)
    _LOGGER.info('Snowboy STT Started')
    return True
