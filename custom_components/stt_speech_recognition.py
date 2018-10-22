"""
Provide functionality to transform speech into text using pocketsphinx.

sudo apt-get install git build-essential \
    python3 python3-dev python3-pip python3-venv
pip3 install SpeechRecognition
"""
import logging
import os
import math
import asyncio
import threading
import wave
import shutil
import tempfile
import subprocess
import io

import voluptuous as vol

from homeassistant.const import CONF_NAME, EVENT_HOMEASSISTANT_STOP
from homeassistant.helpers import intent, config_validation as cv
from homeassistant.components.http import HomeAssistantView

_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['SpeechRecognition', 'pocketsphinx==0.1.15', 'webrtcvad==2.0.10', 'PyAudio>=0.2.8']
DEPENDENCIES = ['http']

DOMAIN = 'stt_speech_recognition'


# Path to pocketsphinx acoustic model (-hmm).
# Probably $RHASSPY_TOOLS/pocketsphinx/cmusphinx-en-us-5.2
CONF_ACOUSTIC_MODEL = 'acoustic_model'

# Path to pocketsphinx language model (-lm).
# Probably $RHASSPY_ASSISTANT/data/mixed.lm
CONF_LANGUAGE_MODEL = 'language_model'

# Path to pocketsphinx word pronunciation dictionary (-dict).
# Probably $RHASSPY_TOOLS/pocketsphinx/cmudict-en-us.dict
CONF_DICTIONARY = 'dictionary'

# Index of the PyAudio device to listen on (-1 for default microphone)
CONF_AUDIO_DEVICE = 'audio_device'

# Microphone sample rate (defaults to 16Khz)
CONF_SAMPLE_RATE = 'sample_rate'

# Size of recording buffer (defaults to 480 or 30 ms at the default sample rate/width).
# *MUST* be 10, 20, or 30 ms for webrtcvad to work.
CONF_BUFFER_SIZE = 'buffer_size'

# Sensitivity of voice activity detection (defaults to 0).
# Ranges from 0-3 where 3 is the most aggressive (fewer false positives).
CONF_VAD_MODE = 'vad_mode'

# Minimum number of seconds of speech to record (defaults to 2).
# Anything below this is ignored (avoids hisses and pops).
CONF_MIN_SEC = 'min_sec'

# Number of seconds of silence to record *after* command (defaults to 0.5 seconds).
# Lets the command listener know when the command is finished.
CONF_SILENCE_SEC = 'silence_sec'

# Total number of seconds to record before timing out (defaults to 30 seconds).
CONF_TIMEOUT_SEC = 'timeout_sec'

# ----------------------
# Configuration defaults
# ----------------------

DEFAULT_NAME = 'stt_pocketsphinx'
DEFAULT_ACOUSTIC_MODEL = '/home/homeassistant/rhasspy-tools/pocketsphinx/cmusphinx-en-us-ptm-5.2'
DEFAULT_LANGUAGE_MODEL = '/home/homeassistant/rhasspy-tools/pocketsphinx/en-70k-0.2-pruned.lm.gz'
DEFAULT_DICTIONARY = '/home/homeassistant/rhasspy-tools/pocketsphinx/cmudict-en-us.dict'

DEFAULT_AUDIO_DEVICE = None
DEFAULT_SAMPLE_RATE = 16000  # 16Khz
DEFAULT_BUFFER_SIZE = 480    # 30 ms (webrtcvad only supports 10,20,30 ms)

DEFAULT_VAD_MODE = 0         # 0-3 (agressiveness)
DEFAULT_MIN_SEC = 2.0        # min seconds that command must last
DEFAULT_SILENCE_SEC = 0.5    # min seconds of silence after command
DEFAULT_TIMEOUT_SEC = 30.0   # max seconds that command can last

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_NAME, DEFAULT_NAME): cv.string,

        vol.Optional(CONF_ACOUSTIC_MODEL, DEFAULT_ACOUSTIC_MODEL): cv.string,
        vol.Optional(CONF_LANGUAGE_MODEL, DEFAULT_LANGUAGE_MODEL): cv.string,
        vol.Optional(CONF_DICTIONARY, DEFAULT_DICTIONARY): cv.string,

        vol.Optional(CONF_AUDIO_DEVICE, DEFAULT_AUDIO_DEVICE): int,
        vol.Optional(CONF_SAMPLE_RATE, DEFAULT_SAMPLE_RATE): int,
        vol.Optional(CONF_BUFFER_SIZE, DEFAULT_BUFFER_SIZE): int,

        vol.Optional(CONF_VAD_MODE, DEFAULT_VAD_MODE): int,
        vol.Optional(CONF_MIN_SEC, DEFAULT_MIN_SEC): float,
        vol.Optional(CONF_SILENCE_SEC, DEFAULT_SILENCE_SEC): float,
        vol.Optional(CONF_TIMEOUT_SEC, DEFAULT_TIMEOUT_SEC): float
    })
}, extra=vol.ALLOW_EXTRA)

# --------
# Services
# --------

# Starts listening for commands on the configured microphone
SERVICE_LISTEN = 'listen'


# Performs speech to text with recorded (or POSTed) WAV data
SERVICE_DECODE = 'decode_wav'

# File path to read WAV data from
ATTR_FILENAME = 'filename'

# Raw WAV data to load directly (includes header, etc.)
ATTR_DATA = 'data'

SCHEMA_SERVICE_DECODE = vol.Schema({
    vol.Optional(ATTR_FILENAME): cv.string,
    vol.Optional(ATTR_DATA): list
})

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

# -----------------------------------------------------------------------------

def setup(hass, config):
    name = config[DOMAIN].get(CONF_NAME, DEFAULT_NAME)
    acoustic_model = os.path.expanduser(config[DOMAIN].get(CONF_ACOUSTIC_MODEL, DEFAULT_ACOUSTIC_MODEL))
    language_model = os.path.expanduser(config[DOMAIN].get(CONF_LANGUAGE_MODEL, DEFAULT_LANGUAGE_MODEL))
    dictionary = os.path.expanduser(config[DOMAIN].get(CONF_DICTIONARY, DEFAULT_DICTIONARY))

    from pocketsphinx import Pocketsphinx

    decoded_phrase = None
    terminated = False
    state_attrs = {
        'friendly_name': 'Speech to Text',
        'icon': 'mdi:comment-text',
        'text': ''
    }

    def listen(call):
        import speech_recognition as sr

        r = sr.Recognizer()
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source)
            try:
                _LOGGER.warning("SPEECH_RECOGNITION: SAY SOMETHING!")
                audio = r.listen(source)

                # TODO: UTILIZAR A GRAMÁTICA JSGF

                # recognize speech using Sphinx
                _LOGGER.warning("Sphinx thinks you said " + r.recognize_sphinx(audio, language='pt-BR'))
            except sr.UnknownValueError:
                _LOGGER.warning("Sphinx could not understand audio")
            except sr.RequestError as e:
                _LOGGER.warning("Sphinx error; {0}".format(e))

    # -------------------------------------------------------------------------

    # Service to record commands
    hass.services.register(DOMAIN, SERVICE_LISTEN, listen)
    hass.states.set(OBJECT_POCKETSPHINX, STATE_IDLE, state_attrs)
    _LOGGER.info('Started')

    return True
