import os
import pickle
import shutil
from datetime import datetime

import yaml


def load_data() -> dict: #Todo: Testes
    """
    Carrega o banco de dados do algoritmo.
    """

    with open('database.yaml', 'r') as f:
        database = yaml.safe_load(f)

    return database


def load_model() -> tuple: #Todo: Testes
    """
    Carrega modelo e vetorizador.
    """

    with open('assets/model/model.pkl', 'rb') as file:
        model = pickle.load(file)
    with open('assets/model/vectorizer.pkl', 'rb') as file:
        vectorizer = pickle.load(file)

    return (model, vectorizer)


def backup(file: str) -> None: #Todo: Testes
    """
    Função utilizada para criar backup de arquivo.

    Parâmetros:
    ----------
    file: str
        Caminho do arquivo que será criado o backup
    
    Retorna:
    --------
    None
    """

    # Criando pasta de backup se não existir
    date = datetime.now().strftime('%Y-%m-%d')
    if not os.path.exists(f'assets/backups/{date}'):
        os.mkdir(f'assets/backups/{date}')

    # Criando cópia
    filename = file.split('/')[-1]
    shutil.copy(file, f'assets/backups/{date}/{filename}')
