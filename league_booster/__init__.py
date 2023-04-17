import threading
import winsound
from functools import partial
from time import sleep

import keyboard
import numpy as np
import pythoncom
import speech_recognition as sr
import win32com.client as wincom
from draft_commands import *
from load import *
from log import *


def idle_trigger(r: sr.Recognizer) -> bool | None:  # Todo: Remover
    """
    Verifica se o comando de inicialização do assistente virtual foi executado.
    
    Parâmetros:
    -----------
    r: sr.Recognizer
        Objeto de reconhecimento de fala
    
    Retorna:
    -------
    True: se o comando de inicialização foi fornecido
    None: se o comando de inicialização não foi fornecido
    """

    try:
        with sr.Microphone() as source:
            audio = r.listen(source, timeout=8)
        command = r.recognize_google(audio, language="pt-BR")
        if 'assistente' in command.lower():  # Todo: suporte para inglês
            return True
    except sr.UnknownValueError:
        # Todo: suporte para inglês
        logger.error("Não foi possível interpretar o áudio")
        #Todo: Som de erro
    except sr.RequestError as e:
        logger.error("Não foi possível acessar o serviço de reconhecimento de fala: {}".format(
            e))  # Todo: suporte para inglês
        #Todo: Som de erro
    except sr.WaitTimeoutError:
        return


def button_trigger(event, r: sr.Recognizer | None = None) -> None:
    if event.name == '=':
        command_listener(r, database, model, vectorizer)
        event.name = ''


def command_listener(r: sr.Recognizer, database: dict, model, vectorizer) -> None:
    """
    Interpreta os comandos fornecidos, através do modelo de IA e executa tais comandos.
    
    Parâmetros:
    -----------
    r: sr.Recognizer
        Objeto de reconhecimento de fala
    database: dict
        Banco de dados do algoritmo
    model:
        Modelo de IA
    vectorizer:
        Vetorizador de palavras
    
    Retorna:
    -------
    None
    """

    try:
        with sr.Microphone() as source:
            logger.info('Aguardando comando...')
            winsound.PlaySound(
                'assets\\sounds\\listening.wav', winsound.SND_NOSTOP)
            audio = r.listen(source, timeout=8)

        audio_to_text = r.recognize_google(audio, language="pt-BR")
        audio_to_text = audio_to_text.lower()
        logger.info(f'Commando: {audio_to_text}')
        command = vectorizer.transform(
            [audio_to_text]).toarray().astype(np.int8)
        command = model.predict(command)[0]

        # ─── Funcionalidade: Counters ─────────────────────────────────
        # Instruções: o comando deve conter os seguintes parâmetros:
        #   - "counters"
        #   - NOME DO CAMPEÃO
        #   - ROLE

        if 'counters' in command:
            winsound.PlaySound('assets\\sounds\\success.wav',
                               winsound.SND_NOSTOP)
            command = command.split(' ')
            logger.info('Buscando counters para {} {}'.format(
                command[1], command[2]))  # Todo: suporte para inglês
            counters(' '.join(command[1:3]), display=True)

        # ─── Funcionalidade: Draft ────────────────────────
        # Instruções: o comando deve conter os seguintes parâmetros:
        #   - "draft"
        #   - NOME DO CAMPEÃO
        #   - ROLE
        if 'draft' in command:
            winsound.PlaySound('assets\\sounds\\success.wav',
                               winsound.SND_NOSTOP)
            command = command.split(' ')
            logger.info('Buscando draft para {} {}'.format(
                command[1], command[2]))  # Todo: suporte para inglês
            draft(' '.join(command[1:3]))

        # ─── Funcionalidade: Cooldown De Spell ────────────────────────
        # Instruções: o comando deve conter os seguintes parâmetros:
        #   - SPELL
        #   - ROLE
        if 'spell' in command:
            winsound.PlaySound('assets\\sounds\\success.wav',
                               winsound.SND_NOSTOP)
            command = command.split(' ')
            threading.Thread(target=spell_notification, args=(
                command[1], command[2], database, )).start()
            # Todo: suporte para inglês
            logger.info(
                f'Notificação de {command[1]} do {command[2]} agendada. Você será notificado {database["delay"]}s antes da spell estar disponível.')

    except sr.UnknownValueError:
        # Todo: suporte para inglês
        logger.error("Não foi possível interpretar o áudio")
        #Todo: Som de erro
    except sr.RequestError as e:
        logger.error("Não foi possível acessar o serviço de reconhecimento de fala: {}".format(
            e))  # Todo: suporte para inglês
        #Todo: Som de erro
    except sr.WaitTimeoutError:
        logger.error('Nenhum comando fornecido durante tempo de espera')
        #Todo: Som de erro


def spell_notification(spell: str, role: str, database: dict) -> None:
    """
    Notifica o fim do tempo de recarga de uma spell.
    
    Parâmetros:
    -----------
    spell: str
        Nome do spell
    role: str
        Nome do role
    database: dict
        Banco de dados
    
    Retorna:
    -------
    None
    """

    pythoncom.CoInitialize()
    tts = wincom.Dispatch("SAPI.SpVoice")

    timer = database['spells'][spell]
    sleep(timer - database['delay'])
    # Todo: suporte para inglês
    notification = f'{spell} do {role} estará disponível em breve.'
    logger.info(notification)
    tts.Speak(notification)

    del tts


if __name__ == '__main__':
    # Criando arquivo de log
    create_logfile()

    # Carregando o banco de dados e modelo
    database = load_data()
    model, vectorizer = load_model()
    logger.success('Modelo carregado com sucesso!')

    # Preparando o serviço de reconhecimento de fala
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)

    while True:
        keyboard.on_press(partial(button_trigger, r=r))
        sleep(10)
