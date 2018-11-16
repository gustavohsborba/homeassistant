#!/bin/bash

# ------------------------------------
# GARANTE A EXECUÇÃO COMO SUPERUSUÁRIO
# ------------------------------------

if [[ "$(id -u)" -ne 0 ]]; then
        echo 'Esse script deve ser rodado como root!' >&2
        echo 'Execute sudo $0' >&2
        exit 1
fi

# -----------------------
# INSTALA AS DEPENDÊNCIAS
# -----------------------

# utilitários
apt-get install -y python3 python3-venv python3-pip build-essential python3-dev
apt-get install -y openssh-server
apt-get install -y mosquitto mosquitto-auth-plugin
apt-get install -y vlc vlc-nox espeak
apt-get install -y p7zip-full

# Para as bibliotecas de voz: snowboy
# apt-get install -y libjack0 libjack-dev
apt-get install -y python-dev swig
apt-get install -y portaudio19-dev libjack-jackd2-dev
apt-get install -y libasound2-dev libpulse-dev
apt-get install -y libtcl8.6
apt-get install -y libatlas-dev libatlas-base-dev

# Para as bibliotecas de voz: vlc, pyttsx
apt-get install -y vlc pulseaudio
apt-get install -y libttspico-utils ffmpeg
apt-get install -y libportaudio2 libav-tools
apt-get install -y libasound-dev libportaudiocpp0

# Para as bibliotecas de voz: PocketSphinx e SpeechRecognition
apt-get install -y liblapack-dev liblapack3 \
    libopenblas-base libopenblas-dev libatlas-base-dev


# -----------------------------------------------------
# CRIA O USUÁRIO HOMEASSISTANT E AS PASTAS DA APLICAÇÃO
# -----------------------------------------------------

useradd -rm homeassistant -G gpio,www-data,audio,ssh,voice,video

mkdir /opt/cefetmg
chown homeassistant:homeassistant /opt/cefetmg
chmod 755 -R /opt/cefetmg


# ---------------------------------------------------------------
# CRIA AMBIENTE VIRTUAL COMO USUÁRIO HOMEASSISTANT E INSTALA TUDO
# ---------------------------------------------------------------

exec sudo -u homeassistant /bin/bash - << EOT
    mkdir /opt/cefetmg/venv
    cd /opt/cefetmg/venv
    python3 -m venv .
    source bin/activate
    pip3 install wheel
    pip3 install homeassistant
    pip3 install colorlog
    pip3 install pyaudio webrtcvad pyttsx3 SpeechRecognition
    python3 -m pip install https://github.com/Kitt-AI/snowboy/archive/v1.3.0.tar.gz

    # BAIXA DO GIT E MOVE AS COISAS PRA PASTA DE CONFIGURAÇÃO
    cd /home/homeassistant
    mkdir .homeassistant
    cd .homeassistant
    git clone https://github.com/gustavohsborba/homeassistant.git .
    cd .homeassistant/data/pocketsphinx/pt-br-picado/
    7za x language-model.lm.7z
    cd ~
    cp -R ~/.homeassistant/data /opt/cefetmg
    cp -R /opt/cefetmg/data/pocketsphinx/* /opt/cefetmg/venv/lib/python3.5/site-packages/speech_recognition/pocketsphinx-data/
EOT

# FIM, COMO USUÁRIO HOMEASSISTANT


# -----------------------
# CONFIGURA OS MICROFONES
# -----------------------

sed -i 'defaults.pcm.card 0/defaults.pcm.card 1/' /usr/share/alsa/alsa.conf
sed -i 'defaults.ctl.card 0/defaults.ctl.card 1/' /usr/share/alsa/alsa.conf

cat <<EOT >> .asoundrc
pcm.!default {
  type asym
   playback.pcm {
     type plug
     slave.pcm "hw:0,0"
   }
   capture.pcm {
     type plug
     slave.pcm "hw:1,0"
   }
}
EOT
cp .asoundrc /home/homeassistant/.asoundrc
chown homeassistant:homeassistant /home/homeassistant/.asoundrc


# -------------------
# DAEMONIZA O SERVIÇO
# -------------------

touch /etc/systemd/system/home-assistant@homeassistant.service
cat <<EOT >> /etc/systemd/system/home-assistant@homeassistant.service
[Unit]
Description=Home Assistant
After=network-online.target

[Service]
Type=simple
User=%i
ExecStart=/opt/cefetmg/venv/bin/hass -c "/home/homeassistant/.homeassistant"

[Install]
WantedBy=multi-user.target
EOT

systemctl --system daemon-reload
systemctl enable home-assistant@homeassistant


# ------------------
# REINICIA O SISTEMA
# ------------------

reboot