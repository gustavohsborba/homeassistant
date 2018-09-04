'''
Pré-requisitos:
sudo apt-get update && sudo apt-get install espeak
pip install pyttsx3
'''

import pyttsx3 # importamos o modulo pytts

# meotodo init seleciona um ending de sintetização, no caso o espeak
engine = pyttsx3.init()

engine.setProperty('voice', 'brazil')  # mudamos a propriedade setando pelo id para pt-br
rate = engine.getProperty('rate')
engine.setProperty('rate', rate-40)
engine.say('Seu desejo,') 
engine.runAndWait()
engine.say('e')
engine.runAndWait()
engine.say('uma, ordem!')
engine.runAndWait()