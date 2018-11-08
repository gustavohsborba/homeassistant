"""
Requires:
pip install paho-mqtt
"""
import logging
import voluptuous as vol
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.helpers import config_validation as cv
import paho.mqtt.client as mqtt

REQUIREMENTS = ['paho-mqtt']
_LOGGER = logging.getLogger(__name__)
DOMAIN = 'intent_table'


# ------
# Config
# ------

CONFIG_PHRASE_LIST = 'prhase_list'
CONFIG_TOPIC_LIST = 'topic_list'
CONFIG_PAYLOAD_LIST = 'payload_list'
CONFIG_MQTT_BROKER = 'mqtt_broker'
CONFIG_MQTT_PORT = 'mqtt_port'
CONFIG_MQTT_COMMAND_NOT_FOUND_TOPIC = 'mqtt_topic_command_not_found'
CONFIG_MQTT_SUCCESS_TOPIC = 'mqtt_success_topic'

ATTR_TEXT = 'text'

# --------
# Services
# --------
SERVICE_PARSE = 'parse'


# ----------------------
# Configuration defaults
# ----------------------

DEFAULT_PHRASE_LIST = []
DEFAULT_TOPIC_LIST = []
DEFAULT_PAYLOAD_LIST = []
DEFAULT_MQTT_BROKER = 'localhost'
DEFAULT_MQTT_PORT = 1883
DEFAULT_MQTT_COMMAND_NOT_FOUND_TOPIC = 'hass/unknown_command'
DEFAULT_MQTT_SUCCESS_TOPIC = 'hass/successful_command'
DEFAULT_UNKNOWN_COMMAND = 'unknown_command'
DEFAULT_SUCCESS_COMMAND = 'succcess'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONFIG_PHRASE_LIST, DEFAULT_PHRASE_LIST): cv.ensure_list_csv,
        vol.Required(CONFIG_TOPIC_LIST, DEFAULT_TOPIC_LIST): cv.ensure_list_csv,
        vol.Required(CONFIG_PAYLOAD_LIST, DEFAULT_PAYLOAD_LIST): cv.ensure_list_csv,
        vol.Optional(CONFIG_MQTT_BROKER, DEFAULT_MQTT_BROKER): cv.string,
        vol.Optional(CONFIG_MQTT_PORT, DEFAULT_MQTT_PORT): int,
        vol.Optional(CONFIG_MQTT_SUCCESS_TOPIC, DEFAULT_MQTT_SUCCESS_TOPIC): cv.string
    })
}, extra=vol.ALLOW_EXTRA)


# -----------------------------------------------------------------------------

def setup(hass, config):
    phrases_json = config[DOMAIN].get(CONFIG_PHRASE_LIST, DEFAULT_PHRASE_LIST)
    topics_json = config[DOMAIN].get(CONFIG_TOPIC_LIST, DEFAULT_TOPIC_LIST)
    payloads_json = config[DOMAIN].get(CONFIG_PAYLOAD_LIST, DEFAULT_PAYLOAD_LIST)
    mqtt_broker = config[DOMAIN].get(CONFIG_MQTT_BROKER, DEFAULT_MQTT_BROKER)
    mqtt_port = config[DOMAIN].get(CONFIG_MQTT_PORT, DEFAULT_MQTT_PORT)
    notfound_topic = config[DOMAIN].get(CONFIG_MQTT_COMMAND_NOT_FOUND_TOPIC, DEFAULT_MQTT_COMMAND_NOT_FOUND_TOPIC)
    success_topic = config[DOMAIN].get(CONFIG_MQTT_SUCCESS_TOPIC, DEFAULT_MQTT_SUCCESS_TOPIC)

    topics = [c for c in topics_json]
    phrases = [p for p in phrases_json]
    payloads = [p for p in payloads_json]
    assert len(topics) == len(phrases), 'Assign exactly one topic for each phrase'
    assert len(topics) == len(payloads), 'Assign exactly one payload for each topic'
    indexed_topics = dict(zip(phrases, topics))
    indexed_payloads = dict(zip(phrases, payloads))
    _LOGGER.info("INTENTS LOADED: %s" % str(indexed_topics))

    def parse(call):
        client = mqtt.Client()
        client.connect(mqtt_broker, mqtt_port, 60)
        _LOGGER.info("INTENT_TABLE: MQTT CLIENT CONNECTED ON %s:%d" % (mqtt_broker, mqtt_port))
        spoken_phrase = call.data.get(ATTR_TEXT, DEFAULT_UNKNOWN_COMMAND)
        _LOGGER.info('INTENT_TABLE RECEIVED DATA: %s' % spoken_phrase)
        if spoken_phrase in indexed_topics.keys() and spoken_phrase in indexed_payloads:
            topic = indexed_topics.get(spoken_phrase)
            payload = indexed_payloads.get(spoken_phrase)
            _LOGGER.info("INTENT FOUND: %s" % spoken_phrase)
            client.publish(topic, payload)
            _LOGGER.info("PUBLISHED %s ON TOPIC %s" % (payload, topic))
            client.publish(success_topic, DEFAULT_SUCCESS_COMMAND)
        else:
            _LOGGER.warning("INTENT NOT FOUND: %s" % spoken_phrase)
            _LOGGER.warning("PUBLISHING : %s ON TOPIC %s" % (spoken_phrase, notfound_topic))
            client.publish(notfound_topic, spoken_phrase)
        client.disconnect()

    # Make sure module terminates property when home assistant stops
    def terminate(event):
        hass.bus.async_listen(EVENT_HOMEASSISTANT_STOP, terminate)

    # After defining values and functions, register services in Home Assistant
    hass.services.async_register(DOMAIN, SERVICE_PARSE, parse)
    _LOGGER.info('INTENT_TABLE STARTED')
    return True

