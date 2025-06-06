import os
import random
import string
os.environ["PWNLIB_NOTERM"] = "True"
from pwn import remote, context
from enum import Enum
from hashlib import sha256
import json

context.timeout = 5

ALPHABET = string.ascii_letters + string.digits

MENU_STRIP = b"=============================="
MAX_USERNAME_LEN = 32
MAX_PASSWORD_LEN = 32
MAX_VAULT_NAME_LEN = 64
MAX_RECIPE_NAME_LEN = 64
MAX_AUTHOR_NAME_LEN = 64
MAX_DESCRIPTION_LEN = 256
ID_LEN = 31

def get_random_string(length):
    return "".join(random.choices(ALPHABET, k=length))

def get_random_length_string(max_length):
    length = int(random.uniform(0.75, 1.0) * max_length)
    return get_random_string(length)

def get_user_data(flag=None):
    random.seed(flag or os.urandom(16))
    username = get_random_length_string(MAX_USERNAME_LEN)
    password = get_random_length_string(MAX_PASSWORD_LEN)
    return username, password

AuthOperations = Enum("AuthOperation", ["SIGNUP", "LOGIN", "EXIT"])

VaultOperations = Enum(
    "VaultOperation",
    ["LIST", "CREATE", "OPEN", "CLOSE", "LIST_OPEN", "ENTER", "LOGOUT"],
)

RecipeOperations = Enum(
    "RecipeOperation",
    [
        "LIST",
        "CREATE",
        "OPEN",
        "CLOSE",
        "SAVE",
        "DISCARD",
        "LIST_OPEN",
        "SELECT",
        "SHOW",
        "EDIT",
        "BACK",
    ],
)

p = 18446744073709551653 # next_prime(next_prime(2**64))
ROUNDS = 16

def F(x, t):
    return (pow(x, 5, p) + t*pow(x, 3, p) + 11068046444225730992*pow(t, 2, p)*x) % p

def decrypt(ct, username, key):
    ct = bytes.fromhex(ct)
    blocks = [ct[i:i+32] for i in range(0, len(ct), 32)]
    k = int(sha256(key).digest().hex()[:16], 16)
    c = [sha256(username).digest()]
    pts = []

    for _ in range(2*ROUNDS-1):
        c.append(sha256(c[-1]).digest())

    for x in blocks:
        state = [int.from_bytes(x[i:i+8], "big") for i in range(0,len(x),8)]
        for i in range(ROUNDS):
            state = state[3:] + state[:3]
            state[1] -= F(state[0] + k + int(c[::-1][2*i+1].hex(), 16), 2*(ROUNDS-i))
            state[1] %= p
            state[3] -= F(state[2] + k + int(c[::-1][2*i].hex(), 16), 2*(ROUNDS-i)+1)
            state[3] %= p
        # print(state)
        pts.append(b"".join([int.to_bytes(s, 8, "big") for s in state]))
    return b"".join(pts)

class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.io: remote = None

        self.logged_in = False
        self.vault_open = False
        self.recipe_open = False

    def must_be_logged_in(self):
        if not self.logged_in:
            raise ValueError("Must be logged in")

    def must_not_be_logged_in(self):
        self.must_not_be_vault_open()
        if self.logged_in:
            raise ValueError("Must not be logged in")

    def must_be_vault_open(self):
        self.must_be_logged_in()
        if not self.vault_open:
            raise ValueError("Must have a vault open")

    def must_not_be_vault_open(self):
        self.must_not_be_recipe_open()
        if self.vault_open:
            raise ValueError("Must not have a vault open")

    def must_be_recipe_open(self):
        self.must_be_vault_open()
        if not self.recipe_open:
            raise ValueError("Must have a recipe open")

    def must_not_be_recipe_open(self):
        if self.recipe_open:
            raise ValueError("Must not have a recipe open")

    def must_be_auth_menu(self):
        self.must_not_be_logged_in()

    def must_be_vault_menu(self):
        self.must_be_logged_in()
        self.must_not_be_vault_open()

    def must_be_recipe_menu(self):
        self.must_be_vault_open()

    def connect(self):
        self.io = remote(self.host, self.port)

    def _get_list(self):
        output = self.io.recvuntil(MENU_STRIP, drop=True).decode().split("[ID]: ")[1:]
        result = []
        for entry in output:
            id_name_split = entry.split("[Name]: ")
            entry_id = id_name_split[0].strip()
            entry_name = id_name_split[1].split("\n")[0].strip()
            result.append({
                "id": entry_id,
                "name": entry_name
            })
        return result
    
    def send_choice(self, operation):
        self.io.sendlineafter(b"[Enter choice]> ", f"{operation.value}".encode())
        self.io.recvline()

    def get_result(self):
        return self.io.recvline().decode().rstrip()
    
    def expect_success(self, warning_ok=False):
        res = self.get_result()
        if not res.startswith("[+]"):
            if warning_ok and res.startswith("[!]"):
                return
            raise ValueError(res)

    def expect_warning(self):
        res = self.get_result()
        if not res.startswith("[!]"):
            raise ValueError(f"Expected warning, got: {res}")

    def signup(self, username, password, warning_ok=True):
        self.must_be_auth_menu()

        if len(username) > MAX_USERNAME_LEN:
            raise ValueError("Username too long")
        if len(password) > MAX_PASSWORD_LEN:
            raise ValueError("Password too long")

        if isinstance(username, str):
            username = username.encode()
        if isinstance(password, str):
            password = password.encode()

        self.send_choice(AuthOperations.SIGNUP)
        self.io.sendlineafter(b"[Enter username]> ", username)
        self.io.sendlineafter(b"[Enter password]> ", password)
        self.expect_success(warning_ok=warning_ok)

    def login(self, username, password, should_fail=False):
        self.must_be_auth_menu()

        if len(username) > MAX_USERNAME_LEN:
            raise ValueError("Username too long")
        if len(password) > MAX_PASSWORD_LEN:
            raise ValueError("Password too long")

        if isinstance(username, str):
            username = username.encode()
        if isinstance(password, str):
            password = password.encode()

        self.send_choice(AuthOperations.LOGIN)
        self.io.sendlineafter(b"[Enter username]> ", username)
        self.io.recvline()
        challenge = self.io.recvline(False).decode()
        dec = decrypt(challenge, username, password)
        dec = dec[:-dec[-1]]

        if not should_fail:
            dec_json = json.loads(dec)
            self.io.sendlineafter(b"]> ", dec_json["nonce"].encode())
            self.expect_success()
            self.logged_in = True
        else:
            self.io.sendlineafter(b"]> ", b"ciao")
            self.expect_warning()

    # VAULT OPERATIONS
    def list_vaults(self):
        self.must_be_vault_menu()

        self.send_choice(VaultOperations.LIST)
        res = self.get_result()
        if res.startswith("[*] No vaults found"):
            return []
        if not res.startswith("[+] Vaults:"):
            raise ValueError(res)
        return self._get_list()
    
    def create_vault(self, name):
        self.must_be_vault_menu()

        if len(name) > MAX_VAULT_NAME_LEN:
            raise ValueError("Vault name too long")

        if isinstance(name, str):
            name = name.encode()

        self.send_choice(VaultOperations.CREATE)
        self.io.sendlineafter(b"[Enter vault name]> ", name)

        self.expect_success()
        self.vault_open = True

        if len(name) == MAX_VAULT_NAME_LEN:
            # NOTE: Added just for exploit purposes. When sending any value where len(val) == MAX, then the newline is not read, and the newline is therefore sent to the following menu, which results in an invalid choice.
            self.io.recvuntil(b"[!] Invalid choice", timeout=1)

    def open_vault(self, vault_id):
        self.must_be_vault_menu()

        if len(vault_id) != ID_LEN:
            raise ValueError("Invalid vault ID")

        if isinstance(vault_id, str):
            vault_id = vault_id.encode()

        self.send_choice(VaultOperations.OPEN)
        self.io.sendlineafter(b"[Enter vault ID]> ", vault_id)

        self.expect_success()
        self.vault_open = True

    def close_vault(self, vault_id):
        self.must_be_vault_menu()

        if len(vault_id) != ID_LEN:
            raise ValueError("Invalid vault ID")

        if isinstance(vault_id, str):
            vault_id = vault_id.encode()
    
        self.send_choice(VaultOperations.CLOSE)
        self.io.sendlineafter(b"[Enter vault ID]> ", vault_id)
        self.expect_success()
        self.vault_open = False

    def list_open_vaults(self):
        self.must_be_vault_menu()

        self.send_choice(VaultOperations.LIST_OPEN)
        res = self.get_result()
        if res.startswith("[*] No vaults open"):
            return []
        if not res.startswith("[+] Open vaults:"):
            raise ValueError(res)
        return self._get_list()
    
    def enter_vault(self, vault_id):
        self.must_be_vault_menu()

        if len(vault_id) != ID_LEN:
            raise ValueError("Invalid vault ID")

        if isinstance(vault_id, str):
            vault_id = vault_id.encode()

        self.send_choice(VaultOperations.ENTER)
        self.io.sendlineafter(b"[Enter vault ID]> ", vault_id)
        self.expect_success()
        self.vault_open = True

    def logout(self, discard=False):
        self.send_choice(VaultOperations.LOGOUT)
        res = self.io.recvuntil(b"]")
        self.io.unrecv(res)
        res = res.decode()
        if res.startswith("[You have unsaved recipes"):
            self.io.sendlineafter(b"[You have unsaved recipes. Discard them? (y/n)]> ", b"y" if discard else b"n")
            if not discard:
                return
            self.expect_success()
        else:
            self.expect_success()
        self.logged_in = False
        self.vault_open = False

    def list_recipes(self):
        self.must_be_recipe_menu()

        self.send_choice(RecipeOperations.LIST)
        res = self.get_result()
        if res.startswith("[*] No recipes found"):
            return []
        if not res.startswith("[+] Recipes:"):
            raise ValueError(res)
        return self._get_list()
    
    def create_recipe(self, name, author, description, locked=False):
        self.must_be_recipe_menu()

        if len(name) > MAX_RECIPE_NAME_LEN or len(author) > MAX_AUTHOR_NAME_LEN or len(description) > MAX_DESCRIPTION_LEN:
            raise ValueError("Name, author, or description too long")

        if isinstance(name, str):
            name = name.encode()
        if isinstance(author, str):
            author = author.encode()
        if isinstance(description, str):
            description = description.encode()

        self.send_choice(RecipeOperations.CREATE)
        self.io.sendlineafter(b"[Enter recipe name]> ", name)
        self.io.sendlineafter(b"[Enter author name]> ", author)
        self.io.sendlineafter(b"[Enter description]> ", description)
        self.io.sendlineafter(b"[Lock recipe? (y/n)]> ", b"y" if locked else b"n")
        self.expect_success()
        self.recipe_open = True

    def open_recipe(self, recipe_id):
        self.must_be_recipe_menu()

        if len(recipe_id) != ID_LEN:
            raise ValueError("Invalid recipe ID")

        if isinstance(recipe_id, str):
            recipe_id = recipe_id.encode()

        self.send_choice(RecipeOperations.OPEN)
        self.io.sendlineafter(b"[Enter recipe ID]> ", recipe_id)
        self.expect_success()
        self.recipe_open = True

    def close_recipe(self, save=False):
        self.must_be_recipe_menu()
        self.must_be_recipe_open()

        self.send_choice(RecipeOperations.CLOSE)
        res = self.io.recvuntil(b"]")
        self.io.unrecv(res)
        res = res.decode()
        if res.startswith("[Save"):
            self.io.sendlineafter(b"[Save recipe before closing? (y/n)]> ", b"y" if save else b"n")
            self.expect_success()
            if save:
                self.expect_success()
        else:
            self.expect_success()

        self.recipe_open = False

    def save_recipe(self):
        self.must_be_recipe_menu()
        self.must_be_recipe_open()

        self.send_choice(RecipeOperations.SAVE)
        self.expect_success()

    def discard_recipe(self):
        self.must_be_recipe_menu()
        self.must_be_recipe_open()

        self.send_choice(RecipeOperations.DISCARD)
        self.expect_success()

        self.recipe_open = False

    def list_open_recipes(self):
        self.must_be_recipe_menu()

        self.send_choice(RecipeOperations.LIST_OPEN)
        res = self.get_result()
        if res.startswith("[*] No recipes open"):
            return []
        if not res.startswith("[+] Open recipes:"):
            raise ValueError(res)
        return self._get_list()
    
    def select_recipe(self, recipe_id):
        self.must_be_recipe_menu()

        if len(recipe_id) != ID_LEN:
            raise ValueError(f"Invalid recipe ID: {recipe_id}")

        if isinstance(recipe_id, str):
            recipe_id = recipe_id.encode()

        self.send_choice(RecipeOperations.SELECT)
        self.io.sendlineafter(b"[Enter recipe ID]> ", recipe_id)
        self.expect_success()
        self.recipe_open = True

    def show_recipe(self):
        self.must_be_recipe_menu()
        self.must_be_recipe_open()

        self.send_choice(RecipeOperations.SHOW)
        res = self.get_result()
        if not res.startswith("[+] Recipe:"):
            raise ValueError(res)

        res = self.io.recvuntil(MENU_STRIP, drop=True).decode()
        id, name, author, description = list(map(lambda x: x.split("\n")[0], res.split(": ")[1:]))

        return {
            "id": id,
            "name": name,
            "author": author,
            "description": description
        }
    
    def edit_recipe(self, name, author, description):
        self.must_be_recipe_menu()
        self.must_be_recipe_open()

        if len(name) > MAX_RECIPE_NAME_LEN or len(author) > MAX_AUTHOR_NAME_LEN or len(description) > MAX_DESCRIPTION_LEN:
            raise ValueError("Name, author, or description too long")

        if isinstance(name, str):
            name = name.encode()
        if isinstance(author, str):
            author = author.encode()
        if isinstance(description, str):
            description = description.encode()

        self.send_choice(RecipeOperations.EDIT)
        self.io.sendlineafter(b"[Enter recipe name]> ", name)
        self.io.sendlineafter(b"[Enter author name]> ", author)
        self.io.sendlineafter(b"[Enter description]> ", description)
        self.expect_success()

    def back(self):
        self.send_choice(RecipeOperations.BACK)
        self.recipe_open = False
        self.vault_open = False

def test():
    HOST = os.environ.get("HOST", "localhost")
    PORT = int(os.environ.get("PORT", 1337))

    user_1_username = get_random_length_string(MAX_USERNAME_LEN)
    user_1_password = get_random_length_string(MAX_PASSWORD_LEN)

    client = Client(HOST, PORT)
    client.connect()

    client.signup(user_1_username, user_1_password)
    client.login(user_1_username, user_1_password)

    vault_1_name = get_random_length_string(MAX_VAULT_NAME_LEN)
    client.create_vault(vault_1_name)

    recipe_1_name = get_random_length_string(MAX_RECIPE_NAME_LEN)
    recipe_1_author = get_random_length_string(MAX_AUTHOR_NAME_LEN)
    recipe_1_description = get_random_length_string(MAX_DESCRIPTION_LEN)
    client.create_recipe(recipe_1_name, recipe_1_author, recipe_1_description)

    recipe_1 = client.show_recipe()
    assert recipe_1["name"] == recipe_1_name
    assert recipe_1["author"] == recipe_1_author
    assert recipe_1["description"] == recipe_1_description

    recipe_2_name = get_random_length_string(MAX_RECIPE_NAME_LEN)
    recipe_2_author = get_random_length_string(MAX_AUTHOR_NAME_LEN)
    recipe_2_description = get_random_length_string(MAX_DESCRIPTION_LEN)

    client.create_recipe(recipe_2_name, recipe_2_author, recipe_2_description)
    recipe_2 = client.show_recipe()
    assert recipe_2["name"] == recipe_2_name
    assert recipe_2["author"] == recipe_2_author
    assert recipe_2["description"] == recipe_2_description

    list_result = client.list_recipes()
    assert len(list_result) == 2 # Order is not guaranteed

    list_open_result = client.list_open_recipes() # Order is guaranteed
    assert list_open_result[0]["id"] == recipe_1["id"]
    assert list_open_result[0]["name"] == recipe_1_name
    assert list_open_result[1]["id"] == recipe_2["id"]
    assert list_open_result[1]["name"] == recipe_2_name

    current_recipe = client.show_recipe()
    assert current_recipe["id"] == recipe_2["id"]

    client.select_recipe(recipe_1["id"])
    current_recipe = client.show_recipe()
    assert current_recipe["id"] == recipe_1["id"]

    recipe_1_name = get_random_length_string(MAX_RECIPE_NAME_LEN)
    recipe_1_author = get_random_length_string(MAX_AUTHOR_NAME_LEN)
    recipe_1_description = get_random_length_string(MAX_DESCRIPTION_LEN)

    client.edit_recipe(recipe_1_name, recipe_1_author, recipe_1_description)

    recipe_1 = client.show_recipe()
    assert recipe_1["name"] == recipe_1_name
    assert recipe_1["author"] == recipe_1_author
    assert recipe_1["description"] == recipe_1_description

    client.save_recipe()

    client.back()

    vault_2_name = get_random_length_string(MAX_VAULT_NAME_LEN)
    client.create_vault(vault_2_name)

    recipe_3_name = get_random_length_string(MAX_RECIPE_NAME_LEN)
    recipe_3_author = get_random_length_string(MAX_AUTHOR_NAME_LEN)
    recipe_3_description = get_random_length_string(MAX_DESCRIPTION_LEN)

    client.create_recipe(recipe_3_name, recipe_3_author, recipe_3_description)
    recipe_3 = client.show_recipe()
    assert recipe_3["name"] == recipe_3_name
    assert recipe_3["author"] == recipe_3_author
    assert recipe_3["description"] == recipe_3_description

    list_result = client.list_recipes()
    assert len(list_result) == 1
    assert list_result[0]["id"] == recipe_3["id"]

    recipe_3_name_discard = get_random_length_string(MAX_RECIPE_NAME_LEN)
    recipe_3_author_discard = get_random_length_string(MAX_AUTHOR_NAME_LEN)
    recipe_3_description_discard = get_random_length_string(MAX_DESCRIPTION_LEN)

    client.edit_recipe(recipe_3_name_discard, recipe_3_author_discard, recipe_3_description_discard)
    recipe_3_discard = client.show_recipe()
    assert recipe_3_discard["name"] == recipe_3_name_discard
    assert recipe_3_discard["author"] == recipe_3_author_discard
    assert recipe_3_discard["description"] == recipe_3_description_discard

    client.close_recipe(save=False)

    list_result = client.list_recipes()
    assert len(list_result) == 1

    list_result = client.list_open_recipes()
    assert len(list_result) == 0

    client.open_recipe(recipe_3["id"])
    recipe_3 = client.show_recipe()
    assert recipe_3["name"] == recipe_3_name
    assert recipe_3["author"] == recipe_3_author
    assert recipe_3["description"] == recipe_3_description

    recipe_3_name_save = get_random_length_string(MAX_RECIPE_NAME_LEN)
    recipe_3_author_save = get_random_length_string(MAX_AUTHOR_NAME_LEN)
    recipe_3_description_save = get_random_length_string(MAX_DESCRIPTION_LEN)

    client.edit_recipe(recipe_3_name_save, recipe_3_author_save, recipe_3_description_save)
    recipe_3_save = client.show_recipe()
    assert recipe_3_save["name"] == recipe_3_name_save
    assert recipe_3_save["author"] == recipe_3_author_save
    assert recipe_3_save["description"] == recipe_3_description_save

    client.close_recipe(save=True)

    list_result = client.list_recipes()
    assert len(list_result) == 1

    list_result = client.list_open_recipes()
    assert len(list_result) == 0

    client.open_recipe(recipe_3["id"])
    recipe_3 = client.show_recipe()
    assert recipe_3["name"] == recipe_3_name_save
    assert recipe_3["author"] == recipe_3_author_save
    assert recipe_3["description"] == recipe_3_description_save

    recipe_3_name_discard = get_random_length_string(MAX_RECIPE_NAME_LEN)
    recipe_3_author_discard = get_random_length_string(MAX_AUTHOR_NAME_LEN)
    recipe_3_description_discard = get_random_length_string(MAX_DESCRIPTION_LEN)

    client.edit_recipe(recipe_3_name_discard, recipe_3_author_discard, recipe_3_description_discard)
    recipe_3_discard = client.show_recipe()
    assert recipe_3_discard["name"] == recipe_3_name_discard
    assert recipe_3_discard["author"] == recipe_3_author_discard
    assert recipe_3_discard["description"] == recipe_3_description_discard

    client.discard_recipe()

    list_result = client.list_recipes()
    assert len(list_result) == 1

    list_result = client.list_open_recipes()
    assert len(list_result) == 0

    client.open_recipe(recipe_3["id"])
    recipe_3 = client.show_recipe()
    assert recipe_3["name"] == recipe_3_name_save
    assert recipe_3["author"] == recipe_3_author_save
    assert recipe_3["description"] == recipe_3_description_save

    client.back()

    vaults = client.list_open_vaults()
    vault_1 = vaults[0]
    assert vault_1["name"] == vault_1_name
    vault_2 = vaults[1]
    assert vault_2["name"] == vault_2_name

    client.logout(True)

    client.login(user_1_username, user_1_password)

    list_result = client.list_vaults()
    assert len(list_result) == 2

    list_result = client.list_open_vaults()
    assert len(list_result) == 0

    client.open_vault(vault_1["id"])
    client.back()

    list_result = client.list_open_vaults()
    assert len(list_result) == 1
    assert list_result[0]["id"] == vault_1["id"]

    client.enter_vault(vault_1["id"])

    list_result = client.list_recipes()
    assert len(list_result) == 2

    list_result = client.list_open_recipes()
    assert len(list_result) == 0

    client.open_recipe(recipe_1["id"])
    recipe_1_shown = client.show_recipe()
    assert recipe_1_shown["name"] == recipe_1["name"]
    assert recipe_1_shown["author"] == recipe_1["author"]
    assert recipe_1_shown["description"] == recipe_1["description"]

    client.open_recipe(recipe_2["id"])
    recipe_2_shown = client.show_recipe()
    assert recipe_2_shown["name"] == recipe_2["name"]
    assert recipe_2_shown["author"] == recipe_2["author"]
    assert recipe_2_shown["description"] == recipe_2["description"]

    client.back()

    list_result = client.list_open_vaults()
    assert len(list_result) == 1

    client.open_vault(vault_2["id"])

    list_result = client.list_recipes()
    assert len(list_result) == 1

    list_result = client.list_open_recipes()
    assert len(list_result) == 0

    client.open_recipe(recipe_3["id"])
    recipe_3_shown = client.show_recipe()
    assert recipe_3_shown["name"] == recipe_3["name"]
    assert recipe_3_shown["author"] == recipe_3["author"]
    assert recipe_3_shown["description"] == recipe_3["description"]

if __name__ == "__main__":
    test()
