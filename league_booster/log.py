import os
from datetime import datetime

from loguru import logger


def create_logfile():
    """
    Cria o arquivo de log.
    """

    month = datetime.now().strftime("%B, %Y")
    day = datetime.now().strftime("%d")
    time = datetime.now().strftime("%Hh%M")

    # Checando se o diretório de logs existe
    if not os.path.exists('logs'):
        os.mkdir('logs')

    # Checando se o diretório de logs do mês existe
    if not os.path.exists(f'logs/{month}'):
        os.mkdir(f'logs/{month}')

    # Criando o arquivo de log
    logger.add(
        f'logs/{month}/Day {day} {time}.log',
    )
