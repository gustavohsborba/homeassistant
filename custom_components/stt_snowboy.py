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
DEFAULT_TIMEOUT = 10.0
DEFAULT_MODELS = ['']
DEFAULT_INTENT_TEXTS = ['']

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


# -----------------------------------------------------------------------------

def setup(hass, config):
    # Parametric Configuration
    name = config[DOMAIN].get(CONF_NAME, DEFAULT_NAME)
    models_json = config[DOMAIN].get(CONF_MODELS, DEFAULT_MODELS)
    texts_json = config[DOMAIN].get(CONF_INTENT_TEXTS, DEFAULT_INTENT_TEXTS)
    sensitivity = config[DOMAIN].get(CONF_SENSITIVITY, DEFAULT_SENSITIVITY)
    audio_gain = config[DOMAIN].get(CONF_AUDIO_GAIN, DEFAULT_AUDIO_GAIN)
    timeout = config[DOMAIN].get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
    state_attrs = {'friendly_name': 'Snowboy STT', 'icon': 'mdi:microphone'}
    terminated = False

    models = []
    texts = [t for t in texts_json]
    assert len(models_json) == len(texts), 'Assign exactly one text for each model'
    for model in models_json:
        assert os.path.exists(model), 'Model does not exist'
        models.append(str(model))
    indexed_models = dict(zip(texts, models))
    _LOGGER.info("MODELS LOADED: %s" % str(indexed_models))

    # Main Functionality Registered in HomeAssistant
    def detect(call):

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
                detected_text('unknown command')
                return True
            return interrupted or terminated

        # Fire detected event to HomeAssistant
        def detected_text(text):
            nonlocal interrupted
            hass.states.async_set(OBJECT_SNOWBOY, STATE_IDLE, state_attrs)
            hass.bus.async_fire(EVENT_SPEECH_RECORDED, {'name': name})
            hass.bus.async_fire(EVENT_SPEECH_TO_TEXT, {
                'name': name,  # name of the component
                'model': indexed_models.get(text, text),  # model used
                'text': text  # text
            })
            _LOGGER.info("SERVICE SNOWBOY STT DETECTED: %s" % text)
            interrupted = True

        from snowboy import snowboydecoder
        hass.states.async_set(OBJECT_SNOWBOY, STATE_LISTENING, state_attrs)

        detector = snowboydecoder.HotwordDetector(
            models, sensitivity=sensitivity, audio_gain=audio_gain)
        callbacks = [lambda: detected_text(t) for t in texts]
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

