import json

import requests as re
from bs4 import BeautifulSoup
from load import backup
from loguru import logger


def gather_duos(patch: str) -> None:
    """
    Obtém os dados de duos do patch

    Parâmetros:
    ----------
    patch: str
        Identificação do patch
    
    Retorna:
    -------
    None
    """

    url = f'https://stats2.u.gg/lol/1.5/duos/br1/{patch}/ranked_solo_5x5/platinum_plus/1.5.0.json'
    r = re.get(url).json()[0]

    adc_supp = r['adc_supp']
    mid_jungle = r['mid_jungle']
    top_jungle = r['top_jungle']
    duos_combination = [adc_supp, mid_jungle, top_jungle]
    duos = {'adc_supp': {},
            'mid_jungle': {},
            'top_jungle': {}}

    # Banco de dados de campeões
    with open(f'assets/draft/champions.json', 'r') as file:
        champions = json.load(file)

    for n, combination in enumerate(duos_combination):
        for duo in combination:
            # Primeiro campeão
            id_1 = champions[str(duo[0])]
            win_1 = duo[2]/duo[3]

            # Segundo campeão
            id_2 = champions[str(duo[4])]
            win_2 = duo[6]/duo[7]

            # Duo
            win_3 = duo[8]/duo[9]
            score = (win_1 + win_2 + win_3 - 1.5) * 100

            if n == 0:
                key = 'adc_supp'
            elif n == 1:
                key = 'mid_jungle'
            else:
                key = 'top_jungle'
            duos[key][f'{id_1} & {id_2}'] = score

    backup(f'assets/draft/duos.json')

    with open(f'assets/draft/duos.json', 'w') as file:
        json.dump(duos, file, indent=1)
    logger.info(f'Dados do patch {patch.replace("_",".")} salvos com sucesso!')


def gather_champions(patch: str) -> None:
    """
    Obtém os dados de campeões do patch
    
    Parâmetros:
    ----------
    patch: str
        Identificação do patch
    
    Retorna:
    -------
    None
    """

    url = f'https://static.bigbrain.gg/assets/lol/riot_static/{patch}/data/en_US/champion.json'
    r = re.get(url).json()['data']

    backup(f'assets/draft/champions.json')

    champions = {}
    for champion in r:
        champions[r[champion]['key']] = r[champion]['id']

    with open(f'assets/draft/champions.json', 'w') as file:
        json.dump(champions, file, indent=2)
    logger.info(f'Dados de campeões do patch {patch} salvos com sucesso!')


def draft(command: str) -> None:
    """
    Obtém duos que são counters de determinado campeão em determinada role.
    
    Parâmetros:
    ----------
    command: str
        Comando do usuário
    
    Retorna:
    -------
    None
    """

    # Interpretando comando
    _, role = command.split(' ')

    # Banco de dados de duos
    with open(f'assets/draft/duos.json', 'r') as file:
        duos = json.load(file)

    counters_dict = counters(command)

    # Formatando
    role = role.replace('support', 'supp')

    # Opções de draft
    draft_options = {}
    for roles in duos:
        if role in roles:
            duos_role = duos[roles]
            for counter in counters_dict:
                for duo in duos_role:
                    if counter in duo:
                        draft_options[f'{duo} - {roles}'] = counters_dict[counter] + \
                            duos_role[duo]

    # Ordenando pelo score
    draft_options = {k: v for k, v in sorted(
        draft_options.items(), key=lambda item: item[1], reverse=True)}

    # Mostrando os 10 primeiros resultados
    for i, option in enumerate(draft_options):
        if i == 10:
            break
        print(f'[{i+1}º] {option}: {round(draft_options[option],2)}')


def counters(command: str, display: bool = False) -> dict:
    """
    Obtém lista de counters de um determinado campeão, em uma determinada role.
    
    Parâmetros:
    ------------
    command: str
        Comando a ser interpretado.
    display: bool
        Se True, mostra os 10 primeiros resultados.
        Se False, não mostra os 10 primeiros resultados.
    
    Retorno:
    --------
    dict:
        Dicionário de counters de um determinado campeão, em uma determinada role.
    """

    # Interpretando comando
    champion, role = command.split(' ')

    # Web Scrapping
    r = re.get(
        f'https://u.gg/lol/champions/{champion}/counter?role={role}?region=br1')
    soup = BeautifulSoup(r.text, 'html.parser')
    response = soup.find('script', {'id': 'reactn-preloaded-state'}).text
    del soup  # Limpando memória

    # Formatando
    role = role.replace('support', 'supp')

    # Selecionando dados
    start = response.index(f'platinum_plus_{role}')
    start = response.index('counters', start) + 11
    end = response.index(']', start)
    response = response[start+1:end -
                        1].replace('},{', ' ').replace('"', '').split(' ')

    # Banco de dados de campeões
    with open(f'assets/draft/champions.json', 'r') as file:
        champions = json.load(file)

    # Confrontos
    counters = {}
    for matchup in response:
        matchup = matchup.split(',')
        counters[champions[matchup[0].split(':')[1]]] = float(
            matchup[-1].split(':')[1]) - 50
    del response  # Limpando memória

    # Ordenando pelo score
    counters = {k: v for k, v in sorted(
        counters.items(), key=lambda item: item[1], reverse=True)}

    if display:
        for i, option in enumerate(counters):
            if i == 10:
                break
            print(f'[{i+1}º] {option}: {round(counters[option],2) + 50}%')

    return counters


if __name__ == '__main__':
    gather_champions('13.7.1')
    gather_duos('13_7')
