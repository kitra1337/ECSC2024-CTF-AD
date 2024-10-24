from client import *

SIGNUP_PROBABILITY = 0.75
FORCE_DISCARD_PROBABILITY = 0.5
def edit_recipe(host, port, username, password, vault_map):

    signup = random.random() < SIGNUP_PROBABILITY

    client = Client(host, port)
    client.connect()
    if signup:
        new_username, new_password = get_user_data()
        username = new_username
        password = new_password
        client.signup(new_username, new_password)
        client.login(new_username, new_password)
        client.create_vault(get_random_length_string(MAX_VAULT_NAME_LEN))
        client.create_recipe(get_random_length_string(MAX_RECIPE_NAME_LEN), get_random_length_string(MAX_AUTHOR_NAME_LEN), get_random_length_string(MAX_DESCRIPTION_LEN))
        recipe_id = client.list_open_recipes()[0]["id"]
        client.back()
        vault_id = client.list_open_vaults()[0]["id"]
        client.enter_vault(vault_id)
        client.select_recipe(recipe_id)
    else:
        client.login(username, password)
        vault_id = client.list_vaults()[0]["id"]
        client.open_vault(vault_id)
        recipe_id = client.list_recipes()[0]["id"]
        client.open_recipe(recipe_id)
        res = client.show_recipe()
        recipes = vault_map[vault_id]
        found = False
        for recipe in recipes:
            if recipe["id"] == recipe_id:
                if recipe["name"] != res["name"]:
                    raise Exception("Recipe data mismatch in edit_recipe")
                found = True
                break
        
        if not found:
            raise Exception("Recipe not found in edit_recipe")
    
    new_name = get_random_length_string(MAX_RECIPE_NAME_LEN)
    new_author = get_random_length_string(MAX_AUTHOR_NAME_LEN)
    new_description = get_random_length_string(MAX_DESCRIPTION_LEN)

    client.edit_recipe(new_name, new_author, new_description)
    if random.random() < FORCE_DISCARD_PROBABILITY:
        client.close_recipe(save=True)
    else:
        client.save_recipe()

    client.back()
    client.logout()
    client.login(username, password)
    
    client.open_vault(vault_id)
    client.open_recipe(recipe_id)
    res = client.show_recipe()
    if res["name"] != new_name or res["author"] != new_author or res["description"] != new_description:
        return False
    return True
    
def open_close(host, port, username, password, vault_map):
    client = Client(host, port)
    client.connect()
    client.login(username, password)
    for vault_id, recipes in vault_map.items():
        client.open_vault(vault_id)
        for recipe in recipes:
            client.open_recipe(recipe["id"])
            res = client.show_recipe()
            if res["name"] != recipe["name"]:
                return False
        client.back()
    return True


