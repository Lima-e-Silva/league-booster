import pickle
import winsound
from difflib import SequenceMatcher

import numpy as np
import pandas as pd
import speech_recognition as sr
from load import *
from loguru import logger
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier


def generate_variants(inputs: list, outputs: list, database: dict, command: str = 'counters') -> tuple:
    """
    Retorna as variantes possíveis para os inputs.

    Parâmetros
    ----------
    inputs: list
        Lista com inputs de nomes dos campeões
    outputs: list
        Lista com outputs de nomes dos campeões
    database: dict
        Dicionário com as informações do banco de dados

    Retorna
    -------
    (list, list)
    """

    # Inserindo variantes possíveis
    x = []
    y = []
    if command == 'counters':
        for n, user_input in enumerate(inputs):
            for role in database['roles']:
                new_input = f'counters {user_input} {role}'
                output = f'counters {outputs[n]} {role}'

                x.append(new_input)  # Entrada do usuário
                y.append(output)  # Saída do algoritmo
                x.append(output)  # Entrada ideal
                y.append(output)  # Saída do algoritmo

                for mistake in list(database['mistakes'].keys()):
                    if mistake in new_input:
                        for variant in database['mistakes'][mistake]:
                            x.append(new_input.replace(mistake, variant))
                            y.append(output)
    elif command == 'spells':
        for n, user_input in enumerate(inputs):
            for role in database['roles']:
                new_input = f'{user_input} {role}'
                output = f'spell {outputs[n]} {role}'

                x.append(new_input)  # Entrada do usuário
                y.append(output)  # Saída do algoritmo
                x.append(' '.join(output.split(' ')[1:]))  # Entrada ideal
                y.append(output)  # Saída do algoritmo

                for mistake in list(database['mistakes'].keys()):
                    if mistake in new_input:
                        for variant in database['mistakes'][mistake]:
                            x.append(new_input.replace(mistake, variant))
                            y.append(output)

    return (x, y)


def train_model(max_features: int = 1000, test_size: float = 0.2, export: bool = False) -> tuple:
    """
    Treina o modelo com os dados coletados do banco de dados

    Parâmetros
    ----------
    max_features: int
        Quantidade máxima de tokens a serem utilizados
    test_size: float
        Tamanho do conjunto de teste
    export: bool
        Flag para exportar o modelo

    Retorna
    -------
    (DecisionTreeClassifier, CountVectorizer)
    """

    # Carregando banco de dados
    model_data = pd.read_feather(r'assets\model\model_data.feather')
    x = model_data['input'].to_numpy()
    y = model_data['output'].to_numpy()

    # Vetorização
    vectorizer = CountVectorizer(max_features=max_features)
    x = vectorizer.fit_transform(x).toarray().astype(np.int8)

    # Divisão treino | teste
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=test_size, random_state=10)

    # Treinamento do modelo
    classification_model = DecisionTreeClassifier(random_state=10)
    classification_model.fit(x_train, y_train)

    # Score
    logger.info(f'Score: {classification_model.score(x_test, y_test):.2f}')

    # Exportando modelo
    if export:
        classification_model.fit(x, y)

        backup('assets/model/model.pkl')
        backup('assets/model/vectorizer.pkl')

        pickle.dump(classification_model, open(
            r'assets\model\model.pkl', 'wb'))
        pickle.dump(vectorizer, open(r'assets\model\vectorizer.pkl', 'wb'))
        logger.success('Modelo salvo com sucesso.')

    return (classification_model, vectorizer)


def store_data() -> None:
    """
    Salva os dados recentemente coletados no banco de dados do modelo
    """
    # Formatando dados
    df = pd.DataFrame(columns=['input', 'output'])
    with open(r'assets\texts\input.txt', 'r', encoding='utf-8') as file:
        df['input'] = [command.replace('\n', '')
                       for command in file.readlines()]
    with open(r'assets\texts\output.txt', 'r', encoding='utf-8') as file:
        df['output'] = [command.replace('\n', '')
                        for command in file.readlines()]
    df['input_name'] = df['input'].apply(
        lambda x: ' '.join(x.split(' ')[1:-1]))
    df['output_name'] = df['output'].apply(
        lambda x: ' '.join(x.split(' ')[1:-1]))
    df['score'] = df.apply(lambda x: SequenceMatcher(
        None, x['input_name'], x['output_name']).ratio(), axis=1)

    # Backup dos dados
    backup('assets/model/model_data.feather')

    # Agrupando dados
    model_data = pd.read_feather(r'assets\model\model_data.feather')
    length = len(model_data)
    df = pd.concat([model_data, df], ignore_index=True)

    # Removendo duplicados
    df = df.drop_duplicates()
    length = len(df) - length
    logger.info(
        f'Foram adicionadas {length} novas entradas ao banco de dados do modelo.')

    # Exportando dados
    df = df.reset_index(drop=True)
    df.to_feather(r'assets\model\model_data.feather')


def data_analysis(ignore: list | None, threshold: float = 0.2) -> None:
    """
    Analisa os dados coletados, removendo entradas com pouca semelhança com os nomes esperados
    """

    # Carregando banco de dados
    df = pd.read_feather(r'assets\model\model_data.feather')

    # Filtrando scores baixos
    low_score = df.query(f'score < {threshold} & output_name not in @ignore')
    if len(low_score) == 0:
        logger.info('Nenhuma entrada com scores baixos encontrada.')
        return
    user = input(
        f'Foram encontrados {len(low_score)} entradas com scores baixos. Deseja remove-las? [S/N]\n[Usuário]: ')

    # Removendo entradas com scores baixos
    if user.lower() == 's':
        df = df.drop(low_score.index)
        deleted = low_score['output_name'].tolist()
        deleted = list(set(deleted))
        logger.info(
            f'Os seguintes campeões foram removidos e necessitam ser reinseridos no banco de dados:')
        for champion in deleted:
            logger.info(champion)

        # Todo: Backup

        # Exportando dados
        df = df.reset_index(drop=True)
        df.to_feather(r'assets\model\model_data.feather')

        # Reinserindo dados
        user = input(
            'Deseja coletar os dados faltantes agora? [S/N]\n[Usuário]: ')
        if user.lower() == 's':
            for champion in deleted:
                collect_data_counters(champion, stop=1, repeat=5)
                store_data()


def export_data() -> None:
    """
    Função utilizada para exportar dados para posterior visualização
    """

    # Carregar banco de dados
    model_data = pd.read_feather(r'assets\model\model_data.feather')

    # Exportar dados
    model_data.to_excel(r'assets\model\model_data.xlsx')


def export_txt(x: list, y: list) -> None:
    """
    Função utilizada para exportar dados para posterior visualização e inserção no banco de dados.

    Parâmetros:
    ----------
    x: list
        Lista com as entradas
    y: list
        Lista com as saídas
    
    Retorna:
    -------
    None
    """

    with open(r'assets\texts\input.txt', 'w', encoding='utf-8') as file:
        for n, user_input in enumerate(x):
            if n != len(x) - 1:
                file.write(user_input + '\n')
            else:
                file.write(user_input)

    with open(r'assets\texts\output.txt', 'w', encoding='utf-8') as file:
        for n, output in enumerate(y):
            if n != len(y) - 1:
                file.write(output + '\n')
            else:
                file.write(output)


# ─── Comando "Spell" ──────────────────────────────────────────────────────────


def collect_data_spells(repeat: int = 5) -> None:
    """
    Função utilizada para coletar dados para o modelo (função Spells).
    """
    # Carregando banco de dados
    database = load_data()
    spells = list(database['spells'].keys())

    # Obtendo nomes das spells
    inputs = []
    outputs = []
    r = sr.Recognizer()
    while len(spells) > 0:
        repetition = 0
        spell = spells.pop(0)
        with sr.Microphone() as source:
            while repetition < repeat:
                winsound.PlaySound(
                    'assets\\sounds\\listening.wav', winsound.SND_NOSTOP)
                logger.info(
                    f'[Repetição {repetition+1}/{repeat}]: Diga "{spell}" + top|mid|jungle|adc|support')
                audio = r.listen(source, timeout=6)
                try:
                    user_input = r.recognize_google(
                        audio, language="pt-BR").lower().split(' ')
                    spell_input = user_input[:-1]
                    if user := input(f'[Spell]: {spell_input}\n\nPara confirmar pressione "Enter". Para cancelar, digite algo.\n[Usuário]: ') != '':
                        continue
                    repetition += 1
                    inputs.append(' '.join(spell_input))
                    outputs.append(spell)
                except:
                    logger.error('Nenhum comando reconhecido')

    # Inserindo variantes possíveis
    x, y = generate_variants(inputs, outputs, database, 'spells')

    # Salvando resultados em arquivo txt para posterior visualização
    export_txt(x, y)

    logger.success('Dados coletados e salvos com sucesso!')


# ─── Comando "Counters" ───────────────────────────────────────────────────────


def collect_data_counters(start: int | str, stop: int = 5, repeat: int = 5) -> None:
    """
    Função utilizada para coletar dados para o modelo (função Counters).
    """

    # Carregar banco de dados
    database = load_data()
    champions = database['champions']

    # Converter nome do campeão para id
    if type(start) == str:
        start = champions.index(start)

    # Obtendo nomes dos campeões
    inputs = []
    outputs = []
    iteration = 0
    r = sr.Recognizer()
    while iteration < stop:
        repetition = 0
        with sr.Microphone() as source:
            while repetition < repeat:
                winsound.PlaySound(
                    'assets\\sounds\\listening.wav', winsound.SND_NOSTOP)
                logger.info(
                    f'[Repetição {repetition+1}/{repeat}]: Diga "counters {champions[iteration+start]} top"')
                audio = r.listen(source, timeout=6)
                try:
                    user_input = r.recognize_google(
                        audio, language="pt-BR").lower().split(' ')
                    command = user_input[0]
                    champion = ' '.join(user_input[1:-1])
                    role = user_input[-1]

                    if user := input(f'[Comando]: {command}\n[Campeão]: {champion}\n[Role]: {role}\n\nPara confirmar pressione "Enter". Para cancelar, digite algo.\n[Usuário]: ') != '':
                        continue
                    repetition += 1
                    if champion not in inputs:
                        inputs.append(champion)
                        outputs.append(champions[iteration+start])

                except:
                    logger.error('Nenhum comando reconhecido')
        iteration += 1

    # Inserindo variantes possíveis
    x, y = generate_variants(inputs, outputs, database, 'counters')

    # Salvando resultados em arquivo txt para posterior visualização
    export_txt(x, y)

    logger.success('Dados coletados e salvos com sucesso!')


def insert_data_counters() -> None:
    """
    Função utilizada para inserir dados manualmente no banco de dados do modelo
    """

    # Carregar banco de dados
    database = load_data()
    champions = database['champions']

    inputs = []
    outputs = []
    while True:
        user = input(
            'Insira o nome correto do campeão ou aperte "Enter" para finalizar.\n[Usuário]: ').lower()
        if user == '':
            break
        if user not in champions:
            logger.error(f'Campeão {user} não encontrado')
            continue
        user_input = input(
            f'Insira a variante do nome do campeão.\n[Usuário]: ').lower()

        inputs.append(user_input)
        inputs.append(user)
        outputs.append(user)
        outputs.append(user)

    x, y = generate_variants(inputs, outputs, database, 'counters')

    # Salvando resultados em arquivo txt para posterior visualização
    with open(r'assets\texts\input.txt', 'w', encoding='utf-8') as file:
        for n, user_input in enumerate(x):
            if n != len(x) - 1:
                file.write(user_input + '\n')
            else:
                file.write(user_input)

    with open(r'assets\texts\output.txt', 'w', encoding='utf-8') as file:
        for n, output in enumerate(y):
            if n != len(y) - 1:
                file.write(output + '\n')
            else:
                file.write(output)

    logger.success('Dados coletados e salvos com sucesso!')


if __name__ == '__main__':
    #collect_data_counters(start=95, stop=5, repeat=3)
    #store_data()
    #collect_data_spells(repeat=4)
    #data_analysis(ignore=['jhin'], threshold=0.2)
    train_model(export=True)
