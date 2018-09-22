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
import logging
import asyncio

import voluptuous as vol

from homeassistant.const import CONF_NAME, EVENT_HOMEASSISTANT_STOP
from homeassistant.helpers import config_validation as cv

_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['snowboy==1.2.0b1']

DOMAIN = 'pln_snowboy'

# ------
# Config
# ------

CONF_MODEL = 'model'
CONF_SENSITIVITY = 'sensitivity'
CONF_AUDIO_GAIN = 'audio_gain'

# ----------------------
# Configuration defaults
# ----------------------

DEFAULT_NAME = 'pln_snowboy'
DEFAULT_SENSITIVITY = 0.5
DEFAULT_AUDIO_GAIN = 1.0

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_NAME, DEFAULT_NAME): cv.string,
        vol.Required(CONF_MODEL): cv.string,
        vol.Optional(CONF_SENSITIVITY, DEFAULT_SENSITIVITY): float,
        vol.Optional(CONF_AUDIO_GAIN, DEFAULT_AUDIO_GAIN): float
    })
}, extra=vol.ALLOW_EXTRA)

# --------
# Services
# --------

SERVICE_LISTEN = 'listen'
# Not doing anything
STATE_IDLE = 'idle'
# Listening for the hotword
STATE_LISTENING = 'listening'
# Fired when the hotword is detected
EVENT_HOTWORD_DETECTED = 'hotword_detected'


# -----------------------------------------------------------------------------

# TODO: Fazer o serviço que vai registrar os intents via callback


def callback_ligar():
    pass


def callback_desligar():
    pass


@asyncio.coroutine
def async_setup(hass, config):

    @asyncio.coroutine
    def async_listen(call):
        pass

    hass.services.async_register(DOMAIN, SERVICE_LISTEN, async_listen)

    # Make sure snowboy terminates property when home assistant stops
    @asyncio.coroutine
    def async_terminate(event):
        pass

    hass.bus.async_listen(EVENT_HOMEASSISTANT_STOP, async_terminate)

    _LOGGER.info('Started')

    return True