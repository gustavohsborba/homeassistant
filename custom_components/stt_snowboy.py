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
import asyncio
import threading

import voluptuous as vol

from homeassistant.const import CONF_NAME, EVENT_HOMEASSISTANT_STOP
from homeassistant.helpers import config_validation as cv

_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['snowboy==1.2.0b1']
DOMAIN = 'stt_snowboy'


# ------
# Config
# ------

CONF_SENSITIVITY = 'sensitivity'
CONF_AUDIO_GAIN = 'audio_gain'
CONF_MODELS = 'models'
CONF_INTENT_TEXTS = 'intent_texts'
CONF_TIMEOUT = 'timeout'

# ----------------------
# Configuration defaults
# ----------------------

DEFAULT_NAME = 'pln_snowboy'
DEFAULT_SENSITIVITY = 0.5
DEFAULT_AUDIO_GAIN = 1.0
DEFAULT_TIMEOUT = 30.0
DEFAULT_MODELS = ['','','','','','','']
DEFAULT_INTENT_TEXTS = ['','','','','','','']

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_MODELS, DEFAULT_MODELS): cv.ensure_list_csv,
        vol.Optional(CONF_INTENT_TEXTS, DEFAULT_INTENT_TEXTS): cv.ensure_list_csv,
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


# ---------------------
# Interruption handling
# ---------------------

interrupted = False
terminated = False


def interrupt_callback():
    global interrupted
    global terminated
    return interrupted or terminated


# -----------------------------------------------------------------------------

def setup(hass, config):
    _LOGGER.info('')
    _LOGGER.info('')
    _LOGGER.info('SETUP INITIALIZED')
    name = config[DOMAIN].get(CONF_NAME, DEFAULT_NAME)
    models = os.path.expanduser(config[DOMAIN].get(CONF_MODELS))
    texts = config[DOMAIN].get(CONF_INTENT_TEXTS, DEFAULT_INTENT_TEXTS)
    sensitivity = config[DOMAIN].get(CONF_SENSITIVITY, DEFAULT_SENSITIVITY)
    audio_gain = config[DOMAIN].get(CONF_AUDIO_GAIN, DEFAULT_AUDIO_GAIN)
    state_attrs = {'friendly_name': 'Snowboy STT', 'icon': 'mdi:microphone'}
    _LOGGER.info('')
    _LOGGER.info('')
    _LOGGER.info('models: ')
    _LOGGER.info(str(models))
    _LOGGER.info('texts: ')
    _LOGGER.info(str(texts))

    for model in models:
        assert os.path.exists(model), 'Model does not exist'
    assert len(models) == len(texts), 'Assign exactly one text for each model'

    def detected_text(text):
        # Fire detected event
        hass.states.async_set(OBJECT_SNOWBOY, STATE_IDLE, state_attrs)
        hass.bus.async_fire(EVENT_SPEECH_RECORDED, {
            'name': name,  # name of the component
            'size': 1  # bytes of recorded audio data
        })
        hass.bus.async_fire(EVENT_SPEECH_TO_TEXT, {
            'name': name,  # name of the component
            'model': model,  # model used
            'text': text  # text
        })

    def detect(call):
        _LOGGER.info('')
        _LOGGER.info('')
        _LOGGER.info('CALLED SNOWBOY STT DETECTION')

        from snowboy import snowboydecoder
        hass.states.async_set(OBJECT_SNOWBOY, STATE_LISTENING, state_attrs)

        detector = snowboydecoder.HotwordDetector(
            models, sensitivity=sensitivity, audio_gain=audio_gain)
        callbacks = [lambda: detected_text(t) for t in texts]
        detector.start(detected_callback=callbacks,
                       interrupt_check=interrupt_callback,
                       sleep_time=0.03)
        detector.terminate()

    hass.services.async_register(DOMAIN, SERVICE_DETECT, detect)
    hass.states.async_set(OBJECT_SNOWBOY, STATE_IDLE, state_attrs)

    # Make sure snowboy terminates property when home assistant stops
    def terminate(event):
        global terminated
        terminated = True
        hass.bus.async_listen(EVENT_HOMEASSISTANT_STOP, terminate)

    _LOGGER.info('Started')

    return True

