# Ocarina Controlled Smart Home

## Outline
This project proposes a unique integration of music and home automation by utilizing an ocarina-controlled smart home system. The core of the system is an app that identifies Legend of Zelda songs played on an Ocarina and sends corresponding commands to various smart home devices. 

## Video explanation
A video explaining this project is available [here](https://www.youtube.com/watch?v=LKvm6-ijO8s&t=289s&ab_channel=WyattDrew).

## Components
* client_actuators.ino: An MQTT client designed for a node mcu esp8266. It controls the actuators responsible for causing song effects
* client_song_analyzer.py: An MQTT client designed for a Raspberry Pi 3B+ which is responsible for audio analysis

## Key Features
* Circuit design/implementation
* FFT implementation for audio analysis
* IFTTT implementation for signaling
* MQTT implementation for signaling

![image](https://github.com/Wyatt-Drew/Ocarina-of-Time-Song-Recognizer/assets/98035850/0046e07b-3bcb-48a5-a404-7f4a2d33966c)
(Figure 1: Overview of implementation)
