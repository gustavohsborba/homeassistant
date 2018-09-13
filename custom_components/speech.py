
"""Example of a custom component exposing a service."""
'''
Pré-requisitos:
sudo apt-get update && sudo apt-get install espeak
pip install pyttsx3
'''

import pyttsx3 # importamos o modulo pytts
import logging

# Domínio do componente. Deve ser igual ao nome escrito na configuração do HA
DOMAIN = "speech"
_LOGGER = logging.getLogger(__name__)


def setup(hass, config):
    
    def speak(call):
        _LOGGER.info('Speech received data: ', call.data)
        message = call.data.get('message')
        
        engine = pyttsx3.init()  # seleciona um ending de sintetização, default = espeak

        engine.setProperty('voice', 'brazil')  # mudamos a propriedade voice para pt-br
        rate = engine.getProperty('rate')  # taxa de palavras por minuto
        engine.setProperty('rate', rate-40)  # Diminui a velocidade da fala, para ficar mais fluido
        engine.say(message) 
        engine.runAndWait()
        _LOGGER.info('Spoken Successfully: ', message)

    # Registra o serviço no HomeAssistant
    hass.services.register(DOMAIN, 'speak', speak)

    # Retorna um booleano indicando que a inicialização foi um sucesso
    return True