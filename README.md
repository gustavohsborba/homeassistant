---
layout: page
title: "Configuração do HomeAssistant para utilização do Gênio"
description: "Instructions on how to setup Home Assistant to launch on boot using systemd."
date: 2018-9-1
sidebar: true
comments: false
sharing: true
footer: true
---


# Instalação e Configuração do Gênio

A presente página irá guiar o usuário na instalação da aplicação HomeAssistant, principal engine do Gênio, e softwares auxiliares.


## Procedimentos pré-instalação

Manual adaptado da página https://www.home-assistant.io/docs/installation/raspberry-pi/

Com o sistema operacional Raspbian instalado no Raspberry Pi, o primeiro passo foi instalar ssh:
```bash
$ sudo apt-get install openssh
```

A partir daí, foi possível acessar remotamente, permitindo independência da interface gráfica.

```bash
$ ssh pi@192.168.0.154
```

Após acessar o servidor, o sistema foi atualizado:

```bash
$ sudo apt-get update
$ sudo apt-get upgrade -y
```

E foram instaladas as dependências da plataforma HomeAssistant:

```bash
$ sudo apt-get install python3 python3-venv python3-pip
```

Para executar a aplicação, é recomendável utilizar um usuário do sistema, de forma que ela possa ser daemonizada.
Uma conta do tipo usuário do sistema de nome homeassistant foi adicionada no S.O., com um diretório home, e adicionada ao grupo de gpio (permitindo que ela acesse os pinos do Raspberry. Nesse projeto não é estritamente necessário, mas isso permite à conta um controle mais amplo de todas as possibilidades do hardware, e futuros aprimoramentos do assistente) 
O argumento adicional `-m` indica o nome da pasta home do usuário, e -G adiciona-o ao grupo indicado. 

```bash
$ sudo useradd -rm homeassistant -G gpio
```

Criou-se um diretório para a aplicação homeassistant, e suas permissões de dono foi alterado para a conta `homeassistant`.

```bash
$ cd /srv
$ sudo mkdir homeassistant
$ sudo chown homeassistant:homeassistant homeassistant
```

## Instalando o home assistant no debian

Para instalar a aplicação, foi criado um ambiente virtual.
Para que ela funcione corretamente com o usupário do sistema criado, é necessário que seu ambiente virtual seja criada por esse mesmo usuário:

```bash
$ sudo -u homeassistant -H -s
$ cd /srv/homeassistant
$ python3 -m venv .
$ source bin/activate
```

Com o ambiente virutal ativado, foi possível instalar as dependências do python e a própria aplicação:

```bash
(homeassistant) homeassistant@genio:/srv/homeassistant $ python3 -m pip install wheel
(homeassistant) homeassistant@genio:/srv/homeassistant $ pip3 install homeassistant
```

A aplicação HomeAssistant pode ser iniciada uma primeira vez. Quando executada pela primeira vez, esse comando cria o diretório `/home/homeassistant/.homeassistant`, que configura a aplicação, e instala as demais dependências.

```bash
(homeassistant) $ hass
```

Entretanto, não é desejável acessar o servidor via SSH e iniciar a aplicação por um comando sempre que ligá-lo. Assim, é preciso daemonizar o serviço, de forma que ele inicie-se automaticamente com o sistema.


## Configurando o HA para iniciar com o sistema


Distribuições mais recentes de linux têm migrado para a utilização do serviço systemd para gerenciar daemons.
A existência desse serviço pode ser verificada com o comando abaixo:
```bash
$ ps -p 1 -o comm=
systemd
```

Uma vez verificado o serviço, bastou criar um arquivo de serviço para controlar o HA com o systemd.
O nome do arquivo é importante: ele é localizado na pasta `/etc/systemd/system/`, e deve obrigatoriamente seguir a sintaxe `nome-do-servico@usuario.service`, onde usuario será o usuário que executa a aplicação (nesse caso, homeassistant).

```shell
$ ps -p 1 -o comm=
$ sudo apt-get update
$ sudo apt-get upgrade -y
$ sudo -u homeassistant -H -s
$ sudo touch /etc/systemd/system/home-assistant@homeassistant.service
$ sudo nano -w /etc/systemd/system/home-assistant@homeassistant.service
```

O arquivo de serviço escrito contém os seguintes registros:

```
[Unit]
Description=Home Assistant
After=network-online.target

[Service]
Type=simple
User=%i
ExecStart=/usr/bin/hass

[Install]
WantedBy=multi-user.target
```

Finalmente, o serviço foi ativado e o servidor reiniciado:

You need to reload `systemd` to make the daemon aware of the new configuration.

```bash
$ sudo systemctl --system daemon-reload
$ sudo systemctl enable home-assistant@[your user]
$ sudo reboot
```

## Instalando o servidor MQTT

A aplicação HA utiliza um servidor MQTT, que pode ser no mesmo servidor físico ou não. Para deixar o hub de automação mais completo optou-se pelo servidor integrado.

```bash
$ sudo apt-get install mosquitto mosquitto-auth-plugin
```


## Instalando a biblioteca de Text-To-Speech (TTS):


Para execução do Text-To-Speech o sistema necessita, inicialmente, de um plugin de execução de audio. 
O plugin padrão para distribuições linux (que já vem instalado automaticamente na maioria dos sistemas) é o VLC-NOX. Como o sistema operacional Raspbian não é preparado para execução de audio em geral, esse plugin não vem instalado por padrão. 
Também é necessário que o usuário que executa a aplicação tenha acesso a tal plugin.:

Atualmente existem algumas ferramentas de TTS de utilização gratuita. Muitas delas, entretanto, necessitam acesso a um servidor remoto, ou estão disponíveis apenas em forma de API. As poucas que restam apresentam pouco suporte para a língua portuguesa. Mantendo a filosofia de um sistema opensource, a engine de TTS escolhida foi a espeak por ser completamente aberta e pautada em software livre e com suporte para o idioma.

```bash
$ sudo apt-get update && sudo apt-get install vlc-nox espeak
$ sudo usermod -a -G audio homeassistant
```

Para a configuração dos serviços no homeassistant, é necessário instlar a biblioteca espeak também no ambiente virtual da aplicação:

```bash
$ sudo -u homeassistant -H -s
$ cd /srv/homeassistant
$ python3 -m venv .
$ source bin/activate
(homeassistant) homeassistant@genio:/srv/homeassistant $ pip3 install pyttsx3
```
