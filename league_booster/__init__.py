import threading
import webbrowser
import winsound
from time import sleep

import numpy as np
import pyttsx3
import speech_recognition as sr
from load import *
from loguru import logger


def idle_trigger():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)
    try:
        command = r.recognize_google(audio, language="pt-BR")
        if 'assistente' in command.lower():  # Todo: suporte para inglês | Talvez utilizar um comando melhor p/ despertar
            return True
    except sr.UnknownValueError:
        # Todo: suporte para inglês
        logger.error("Não foi possível interpretar o áudio")
        #Todo: Som de erro
    except sr.RequestError as e:
        logger.error("Não foi possível acessar o serviço de reconhecimento de fala: {}".format(
            e))  # Todo: suporte para inglês
        #Todo: Som de erro


def command_listener(database: dict, model, vectorizer) -> None:
    winsound.PlaySound('assets\\sounds\\listening.wav', winsound.SND_NOSTOP)
    logger.info('Aguardando comando...')
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)
    try:
        audio_to_text = r.recognize_google(audio, language="pt-BR")
        command = vectorizer.transform(
            [audio_to_text]).toarray().astype(np.int8)
        command = model.predict(command)[0]

        # ─── Funcionalidade: Counters ─────────────────────────────────
        # Instruções: o comando deve conter os seguintes parâmetros:
        #   - "counters"
        #   - NOME DO CAMPEÃO
        #   - ROLE

        if 'counters' in command:
            #Todo: Som de sucesso
            command = command.split(' ')
            logger.info('Buscando counters para {} {}'.format(
                command[1], command[2]))  # Todo: suporte para inglês
            webbrowser.open(
                f"https://www.op.gg/champions/{command[1]}/{command[2]}/counters?region=global&tier=platinum_plus", new=0, autoraise=True)

        # ─── Funcionalidade: Cooldown De Spell ────────────────────────
        # Instruções: o comando deve conter os seguintes parâmetros:
        #   - SPELL
        #   - ROLE
        if 'spell' in command:
            #Todo: Som de sucesso
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


def spell_notification(spell: str, role: str, database: dict) -> None:  # Todo: Docstring
    tts = pyttsx3.init()

    timer = database['spells'][spell]
    sleep(timer - database['delay'])
    # Todo: suporte para inglês
    notification = f'{spell} do {role} estará disponível em breve.'
    logger.info(notification)
    tts.say(notification)
    tts.runAndWait()
    tts.stop()

    del tts


if __name__ == '__main__':
    # Todo: Pasta p/ logs
    # Carregar o banco de dados e modelo
    database = load_data()
    model, vectorizer = load_model()
    logger.success('Modelo carregado com sucesso!')

    while True:
        if idle_trigger():
            command_listener(database, model, vectorizer)
