'''
Pré-requisitos:
sudo apt-get update && sudo apt-get install espeak
pip install pywin32 pypiwin32 pyttsx3
'''

import pyttsx3 # importamos o modulo pytts

# meotodo init seleciona um ending de sintetização, no caso o espeak
engine = pyttsx3.init()

engine.setProperty('voice', 'brazil')  # mudamos a propriedade setando pelo id para pt-br
rate = engine.getProperty('rate') # pega a taxa de palavras por minuto da engine de fala
engine.setProperty('rate', rate-40) # diminui um pouco a taxa para a fala ficar fluida


text = data.get('message') # Texto a ser falado. Parâmetro passado pelo HA
engine.say(message) # Prepara a mensagem para falar
engine.runAndWait() # inicia a engine para falar o texto.
