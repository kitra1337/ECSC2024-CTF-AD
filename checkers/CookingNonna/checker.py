#!/usr/bin/env python3

import logging
import random
import traceback

logging.disable()

from checklib import *
from client import *
from flows import *

SERVICE_NAME = 'CookingNonna'
PORT = 2222


def check_sla(host):

    client = Client(host, PORT)
    client.connect()
    username, password = get_user_data()
    client.signup(username, password)
    client.login(username, password)

    for _ in range(random.randint(1, 3)):
        client.create_vault(get_random_length_string(MAX_VAULT_NAME_LEN))
        client.back()

    vaults = client.list_vaults()
    random.shuffle(vaults)

    vault_map = {}
    for el in vaults:
        client.enter_vault(el["id"])
        for _ in range(random.randint(1, 3)):
            client.create_recipe(get_random_length_string(MAX_RECIPE_NAME_LEN), get_random_length_string(MAX_AUTHOR_NAME_LEN), get_random_length_string(MAX_DESCRIPTION_LEN))
        vault_map[el["id"]] = client.list_recipes()
        client.back()

    if not open_close(host, PORT, username, password, vault_map):
        quit(Status.DOWN, 'Failed to open close', 'Failed to open close')

    if not edit_recipe(host, PORT, username, password, vault_map):
       quit(Status.DOWN, 'Failed to edit recipe', 'Failed to edit recipe')
    
    

def put_flag(host, flag):
    username, password = get_user_data(flag)

    client = Client(host, PORT)
    client.connect()
    client.signup(username, password, warning_ok=False)
    client.login(username, password)

    client.create_vault("flag")
    client.back()
    client.list_open_vaults()

    vault_id = client.list_vaults()[0]["id"]
    client.enter_vault(vault_id)
    client.create_recipe("flag", username, flag, locked=True)

    recipe_id = client.list_recipes()[0]["id"]
    
    flag_id = {
        "username": username,
        "vault": vault_id,
        "recipe": recipe_id
    }

    try:
        with open(f'data/{username}', 'w') as f:
            f.write(vault_id + '\n')
            f.write(recipe_id + '\n')
    except Exception as e:
        quit(Status.ERROR, 'Failed to save flag info', str(e))

    try:
        post_flag_id(SERVICE_NAME, team_id, flag_id)
    except Exception as e:
        quit(Status.ERROR, 'Failed to post flag id', str(e))

def get_flag(host, flag):
    username, password = get_user_data(flag)

    with open(f'data/{username}', 'r') as f:
        vault_id = f.readline().strip()
        recipe_id = f.readline().strip()

    client = Client(host, PORT)
    client.connect()
    client.login(username, password)

    client.open_vault(vault_id)
    client.open_recipe(recipe_id)
    recipe = client.show_recipe()["description"]
    if recipe != flag:
        quit(Status.DOWN, 'Retrieved flag does not match', f'Got: {recipe}')    
    pass

if __name__ == '__main__':

    if 'LOCALHOST_RULEZ' in os.environ:
        action = os.environ.get('ACTION')
        team_id = '0'
        host = '127.0.0.1'
        flag = os.environ.get('FLAG', "ABCDEFGHIJKLMNOPQRSTUVWXYZ01234=")
    else:
        data = get_data()
        action = data['action']
        team_id = data['teamId']
        host = '10.60.' + team_id + '.1'
        flag = data['flag']

    if action == Action.CHECK_SLA.name:
        try:
            check_sla(host)
        except Exception as e:
            quit(Status.DOWN, 'Cannot check SLA', traceback.format_exc())
    elif action == Action.PUT_FLAG.name:
        try:
            put_flag(host, flag)
        except Exception as e:
            quit(Status.DOWN, "Cannot put flag", traceback.format_exc())
    elif action == Action.GET_FLAG.name:
        try:
            get_flag(host, flag)
        except Exception as e:
            quit(Status.DOWN, "Cannot get flag", traceback.format_exc())
    else:
        quit(Status.ERROR, 'System error', 'Unknown action: ' + action)

    quit(Status.OK, 'OK')
