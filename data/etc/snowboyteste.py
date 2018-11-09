from snowboy import snowboydecoder
import sys
import signal

interrupted = False


def signal_handler(signal, frame):
    global interrupted
    interrupted = True


def interrupt_callback():
    global interrupted
    return interrupted


if len(sys.argv) == 1:
    print("Error: need to specify model name")
    print("Usage: python demo.py your.model")
    model = '/opt/cefetmg/data/snowboy/genio.pmdl'
else:
    model = sys.argv[1]

# capture SIGINT signal, e.g., Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

detector = snowboydecoder.HotwordDetector(model, sensitivity=0.5)
print('Listening... Press Ctrl+C to exit')

# main loop
detector.start(detected_callback=snowboydecoder.play_audio_file,
               interrupt_check=interrupt_callback,
               sleep_time=0.03)

detector.terminate()



"""
(venv2) ➜  etc git:(master) ✗python snowboyteste.py /opt/cefetmg/data/snowboy/genio.pmdl
Listening... Press Ctrl+C to exit
ALSA lib pcm_dmix.c:1099:(snd_pcm_dmix_open) unable to open slave
ALSA lib pcm.c:2565:(snd_pcm_open_noupdate) Unknown PCM cards.pcm.rear
ALSA lib pcm.c:2565:(snd_pcm_open_noupdate) Unknown PCM cards.pcm.center_lfe
ALSA lib pcm.c:2565:(snd_pcm_open_noupdate) Unknown PCM cards.pcm.side
ALSA lib confmisc.c:1281:(snd_func_refer) Unable to find definition 'cards.USB-Audio.pcm.hdmi.0:CARD=2,AES0=4,AES1=130,AES2=0,AES3=2'
ALSA lib conf.c:4555:(_snd_config_evaluate) function snd_func_refer returned error: No such file or directory
ALSA lib conf.c:5034:(snd_config_expand) Evaluate error: No such file or directory
ALSA lib pcm.c:2565:(snd_pcm_open_noupdate) Unknown PCM hdmi
ALSA lib confmisc.c:1281:(snd_func_refer) Unable to find definition 'cards.USB-Audio.pcm.hdmi.0:CARD=2,AES0=4,AES1=130,AES2=0,AES3=2'
ALSA lib conf.c:4555:(_snd_config_evaluate) function snd_func_refer returned error: No such file or directory
ALSA lib conf.c:5034:(snd_config_expand) Evaluate error: No such file or directory
ALSA lib pcm.c:2565:(snd_pcm_open_noupdate) Unknown PCM hdmi
ALSA lib confmisc.c:1281:(snd_func_refer) Unable to find definition 'cards.USB-Audio.pcm.modem.0:CARD=2'
ALSA lib conf.c:4555:(_snd_config_evaluate) function snd_func_refer returned error: No such file or directory
ALSA lib conf.c:5034:(snd_config_expand) Evaluate error: No such file or directory
ALSA lib pcm.c:2565:(snd_pcm_open_noupdate) Unknown PCM cards.pcm.phoneline:CARD=2,DEV=0
ALSA lib confmisc.c:1281:(snd_func_refer) Unable to find definition 'cards.USB-Audio.pcm.modem.0:CARD=2'
ALSA lib conf.c:4555:(_snd_config_evaluate) function snd_func_refer returned error: No such file or directory
ALSA lib conf.c:5034:(snd_config_expand) Evaluate error: No such file or directory
ALSA lib pcm.c:2565:(snd_pcm_open_noupdate) Unknown PCM cards.pcm.phoneline:CARD=2,DEV=0
ALSA lib confmisc.c:1281:(snd_func_refer) Unable to find definition 'cards.USB-Audio.pcm.modem.0:CARD=2'
ALSA lib conf.c:4555:(_snd_config_evaluate) function snd_func_refer returned error: No such file or directory
ALSA lib conf.c:5034:(snd_config_expand) Evaluate error: No such file or directory
ALSA lib pcm.c:2565:(snd_pcm_open_noupdate) Unknown PCM phoneline
ALSA lib confmisc.c:1281:(snd_func_refer) Unable to find definition 'cards.USB-Audio.pcm.modem.0:CARD=2'
ALSA lib conf.c:4555:(_snd_config_evaluate) function snd_func_refer returned error: No such file or directory
ALSA lib conf.c:5034:(snd_config_expand) Evaluate error: No such file or directory
ALSA lib pcm.c:2565:(snd_pcm_open_noupdate) Unknown PCM phoneline
ALSA lib pcm_dmix.c:1099:(snd_pcm_dmix_open) unable to open slave
INFO:snowboy:Keyword 1 detected at time: 2018-11-08 21:40:05
INFO:snowboy:Keyword 1 detected at time: 2018-11-08 21:40:25
INFO:snowboy:Keyword 1 detected at time: 2018-11-08 21:40:34
INFO:snowboy:Keyword 1 detected at time: 2018-11-08 21:40:36
INFO:snowboy:Keyword 1 detected at time: 2018-11-08 21:40:42
INFO:snowboy:Keyword 1 detected at time: 2018-11-08 21:40:46
INFO:snowboy:Keyword 1 detected at time: 2018-11-08 21:40:54
INFO:snowboy:Keyword 1 detected at time: 2018-11-08 21:40:56
INFO:snowboy:Keyword 1 detected at time: 2018-11-08 21:40:59
INFO:snowboy:Keyword 1 detected at time: 2018-11-08 21:41:01
INFO:snowboy:Keyword 1 detected at time: 2018-11-08 21:41:02
^C%                                                              
"""