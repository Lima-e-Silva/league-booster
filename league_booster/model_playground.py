import winsound

import speech_recognition as sr
from load import *
from loguru import logger
import numpy as np

def user_input_test() -> None:
    """
    Função utilizada para testar a resposta do modelo aos comandos de voz.
    """

    model, vectorizer = load_model()

    r = sr.Recognizer()
    while True:
        with sr.Microphone() as source:
            winsound.PlaySound(
                'assets\\sounds\\listening.wav', winsound.SND_NOSTOP)
            logger.info('Aguardando comando...')
            audio = r.listen(source)
        try:
            command = r.recognize_google(audio, language="pt-BR").lower()
            if 'encerrar' in command:
                break
            command = vectorizer.transform([command]).toarray().astype(np.int8)
            logger.info(f'Comando interpretado: {model.predict(command)}')
        except:
            logger.error('Ocorreu um erro. Tente novamente.')

if __name__ == '__main__':
    user_input_test()