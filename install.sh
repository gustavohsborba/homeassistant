#!/bin/bash

# -----------------------
# INSTALA AS DEPENDÊNCIAS
# -----------------------

apt-get install openssh-server
apt-get install python3 python3-venv python3-pip
apt-get install mosquitto mosquitto-auth-plugin
apt-get install vlc-nox espeak
apt-get install p7zip-full

sudo apt-get install build-essential \
    python3-dev python3-pip python3-venv \
    libasound2-dev libpulse-dev swig \
    portaudio19-dev libttspico-utils \
    libtcl8.6 libatlas-dev libatlas-base-dev
sudo apt-get install liblapack-dev liblapack3 \
    libopenblas-base libopenblas-dev libatlas-base-dev \
    libportaudio2 libasound-dev libportaudio2 \
    libportaudiocpp0 ffmpeg libav-tools \
    libjack0 libjack-dev portaudio19-dev


# -----------------------------------------------------
# CRIA O USUÁRIO HOMEASSISTANT E AS PASTAS DA APLICAÇÃO
# -----------------------------------------------------

useradd -rm homeassistant -G gpio

mkdir /opt/cefetmg
chown homeassistant:homeassistant /opt/cefetmg
chmod 755 -R /opt/cefetmg


# ---------------------------------------------------------------
# CRIA AMBIENTE VIRTUAL COMO USUÁRIO HOMEASSISTANT E INSTALA TUDO
# ---------------------------------------------------------------

exec sudo -u homeassistant /bin/sh - << EOF
    mkdir /opt/cefetmg/venv
    cd /opt/cefetmg/venv
    python3 -m venv .
    source bin/activate
    python3 -m pip install wheel
    pip3 install homeassistant
    pip3 install pyaudio webrtcvad pyttsx3
    python3 -m pip install https://github.com/Kitt-AI/snowboy/archive/v1.3.0.tar.gz

    # BAIXA DO GIT E MOVE AS COISAS PRA PASTA DE CONFIGURAÇÃO
    cd /home/homeassistant
    git clone https://github.com/gustavohsborba/homeassistant.git
    mv homeassistant .homeassistant
    cd .homeassistant/data/pocketsphinx/pt-br-picado/
    7za x language-model.lm.7z
    cd ~/.homeassistant
    cp ~/.homeassistant/data /opt/cefetmg
EOF

# FIM, COMO USUÁRIO HOMEASSISTANT


# -----------------------
# CONFIGURA OS MICROFONES
# -----------------------

sed -i 'defaults.pcm.card 0/defaults.pcm.card 1/' /usr/share/alsa/alsa.conf
sed -i 'defaults.ctl.card 0/defaults.ctl.card 1/' /usr/share/alsa/alsa.conf

cat <<EOT >> .asoundrc
pcm.!default {
    type hw
    card 1
}

ctl.!default {
    type hw
    card 1
}
EOT
mv .asoundrc /home/homeassistant/.asoundrc
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