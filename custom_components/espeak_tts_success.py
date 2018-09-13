"""Example of a custom component exposing a service."""
'''
Pré-requisitos:
sudo apt-get update && sudo apt-get install espeak
pip install pyttsx3
'''

import pyttsx3 # importamos o modulo pytts
import logging

# Domínio do componente. Deve ser igual ao nome escrito na configuração do HA
DOMAIN = "espeak_tts_success"
_LOGGER = logging.getLogger(__name__)


def setup(hass, config):
    
    def speak(call):
        engine = pyttsx3.init()  # seleciona um ending de sintetização, default = espeak
        engine.setProperty('voice', 'brazil')  # mudamos a propriedade voice para pt-br
        rate = engine.getProperty('rate')  # taxa de palavras por minuto
        engine.setProperty('rate', rate-40)  # Diminui a velocidade da fala, para ficar mais fluido
        
        engine.say('Seu desejo,')
        engine.runAndWait()
        engine.say('e')
        engine.runAndWait()
        engine.say('uma, ordem!')

        _LOGGER.info('Spoken Successfully: Seu desejo é uma ordem!')

    # Registra o serviço no HomeAssistant
    hass.services.register(DOMAIN, 'tts_success', speak)

    # Retorna um booleano indicando que a inicialização foi um sucesso
    return True