import string
import random
import requests
import io
import re


def genRnd(characters_n, population=string.ascii_letters+ string.digits, characters_n_variation=0):
    assert characters_n > characters_n_variation
    
    v = characters_n + random.randint(-characters_n_variation, characters_n_variation)

    s = random.choices(population, k=v)
    
    return ''.join(s)

def genUsername():
    alphabet = string.digits + string.ascii_letters + '[]<>{.;!"\'$=/\\#@'
    return genRnd(16, alphabet, 8)

def genTitle():
    return genText(random.randint(1, 4))

def genBody():
    return genText(random.randint(2, 16))

def genText(words):
    alphabet = string.digits + string.ascii_letters + '[]<>{}.;!"\'$=/\\#@'
    return ' '.join([genRnd(12, alphabet, 8) for _ in range(words)])

def genTemplate(auto_share):
    alphabet = string.digits + string.ascii_letters + '[]<>{}.;!"\'$=/\\#@'
    
    words = [genRnd(16, alphabet, 8) for _ in range(random.randint(2, 12))]
    words.extend(['{author}', '{date}', '{title}', '{body}', auto_share])
    
    random.shuffle(words)
    return ' '.join(words)
    
class Diesi:
    def __init__(self, host):
        self.base = f'http://{host}'
        self.sess = requests.Session()
        self.sess.headers.update({'User-Agent': 'checker'})

    def login(self, username, password):
        URL = self.base + '/login.php'
        
        data = {
            'username': username,
            'password': password
        }
        
        return self.sess.post(URL, data=data)
    
    
    def register(self, username, password):
        URL = self.base + '/register.php'
        self.username = username
        self.password = password

        data = {
            'username': username,
            'password': password
        }
        
        return self.sess.post(URL, data=data)
    
    def logout(self):
        URL = self.base + '/logout.php'
        
        return self.sess.get(URL)
    
    def write(self, title, body, template_id):
        URL = self.base + '/write.php'
        
        data = {
            'title': title,
            'body': body,
            'template': template_id
        }
        
        return self.sess.post(URL, data = data)
    
    def list(self):
        URL = self.base + '/list.php'
        
        return self.sess.get(URL)
    
    def read(self, id):
        URL = self.base + '/read.php'
        data = {
            'id' : id
        }
        return self.sess.get(URL, params=data)
    
    def create_template(self, name, template):
        URL = self.base + '/create_template.php'
        data = {
            'name': name,
            'template': template
        }
        
        return self.sess.post(URL, data=data)
    
    def get_template(self, id):
        URL = self.base + '/get_template.php'
        
        return self.sess.get(URL, params={'id': id})
    
    def list_templates(self):
        URL = self.base + '/write.php'
        
        resp = self.sess.get(URL).text
        
        parsed = re.findall(r'<option value="([0-9]+)">(.+?)</option>', resp)
        templates = []
        
        for t in parsed:
            templates.append({
                'id': t[0],
                'name': t[1]
            })
        
        return templates
        
    
    def hsm_import_key(self, key:bytes):
        URL = self.base + '/settings.php'
        key_f = io.BytesIO(key)
    
        files = {
            'key': key_f
        }
        
        return self.sess.post(URL, files=files)
    
    def hsm_import_item(self, item:bytes):
        URL = self.base + '/write_secret.php'
        
        item_f = io.BytesIO(item)
        
        files = {
            'document': item_f
        }
        
        return self.sess.post(URL,  files=files)
    
    def hsm_get_item(self, item_id:bytes, share_token:str):
        URL = self.base + '/read_secret.php'
        
        files = {
            'share_token': io.StringIO(share_token)
        }
        
        data = {
            'item_id': item_id,
        }
        
        return self.sess.post(URL, data=data, files=files)
    
    def share_post(self, to, post_id):
        URL = self.base + '/share.php'
        
        return self.sess.post(URL, data={'to': to, 'document': post_id})
    
    def notifications(self):
        URL = self.base + '/notifications.php'
        
        return self.sess.get(URL)
    
    def read_shared(self, token):
        URL = self.base + '/read.php'
        
        return self.sess.get(URL, params={'token': token})
        

