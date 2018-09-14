
import paho.mqtt.client as mqtt
import snowboydecoder
import sys
import signal
import time
import logging


# VARS and definitions
MODEL = 'genio.pmdl'
_LOGGER = logging.getLogger(__name__)

PUBLISH_TOPIC = 'hermes/hotword/detected'
SUBSCRIBE_WAIT_TOPIC = 'hermes/hotword/wait'
SUBSCRIBE_TOGGLE_TOPIC = 'hermes/hotword/toggleOn'


# O.S. Signal Handling
interrupted = False
def signal_handler(signal, frame):
    global interrupted
    interrupted = True
    _LOGGER.info('Detected word \'Gênio\'')

def interrupt_callback():
    global interrupted
    return interrupted

# capture SIGINT signal, e.g., Ctrl+C
signal.signal(signal.SIGINT, signal_handler) # trocar para SIGQUIT




# MQTT client to send information
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    _LOGGER.info("Connected with result code "+str(rc))
    client.subscribe(SUBSCRIBE_TOGGLE_TOPIC)
    client.subscribe(SUBSCRIBE_WAIT_TOPIC)

def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

mqtt_client.connect_async("localhost", 1883, 60, "snowboymqttclient")
mqtt_client.loop_start()







# Finally, hotword detection:
def genio_callback():
    snowboydecoder.play_audio_file()
    message = "Keyword \'genio\' detected at time: "
    message += time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    _LOGGER.info(message)
    mqtt_client.publish(PUBLISH_TOPIC, message)


detector = snowboydecoder.HotwordDetector(MODEL, sensitivity=0.5)
_LOGGER.info('Snowboy is listening for word \'Gênio\'... ')
print('Snowboy is listening for word \'Gênio\'... ')

# main loop
detector.start(detected_callback=genio_callback,
               interrupt_check=interrupt_callback,
               sleep_time=0.03)


print('Snowboy Received SIGQUIT and is stopping')
_LOGGER.info('Snowboy Received SIGQUIT and is stopping')
mqtt_client.loop_stop(force=True)
detector.terminate()
