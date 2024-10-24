#!/usr/bin/env python3

from checklib import *
from interactions import *
import random
import re
from requests.exceptions import JSONDecodeError

SERVICE_ID = 'Diese-1'
CHECKER_SECRET = 'REDACTED-1'

def check_sla(host, team_id, round):
    seed = genRnd(32)
    print(f'SLA check seed: {seed}', file=sys.stderr)

    random.seed(seed)
    username, password = genUsername(), genUsername()
    
    service = Diesi(host)
    
    resp = service.register(username, password)
    if username not in resp.text:
        quit(Status.DOWN, 'Cannot register', str(resp.text))
    
    resp = service.logout()
    if username  in resp.text:
        quit(Status.DOWN, 'Cannot logout', str(resp.text))
        
    resp = service.login(username, password)
    if username not in resp.text:
        quit(Status.DOWN, 'Cannot login', str(resp.text))
    
    posts = []
    body, title = genBody(), genTitle()
    templates = {}
    
    #Template check
    for _ in range(random.randint(1,10)):
        name, template = genTitle(), genTemplate('') 
        template += 'Template: {title} template_body:{body} {date}'
        
        resp = service.create_template(name, template).text
        if name not in resp:
            quit(Status.DOWN, 'Cannot create template', str(resp))
        templates[name] = template
    
    service_templates = service.list_templates()

    for t in service_templates:
        if 'Default' in t['name'] or 'Blank' in t['name']:
            continue
        resp = service.get_template(t['id'])
        if resp.status_code == 404:
            quit(Status.DOWN, 'Cannot read template', str(resp))
        resp_json = resp.json()
        
        if templates[t['name']] != resp_json['template']:
            quit(Status.DOWN, 'Cannot read template', str(resp))
    
    # Check documents
    for _ in range(random.randint(1, 10)):
        body, title = genBody(), genTitle()
        
        template_id = random.choice(service_templates)['id']
        resp = service.write(title, body, template_id)
        
        if title not in resp.text or body not in resp.text:
            quit(Status.DOWN, 'Cannot write post', str(resp.text) + str(resp.history))

        redirect_url = resp.url
        
        post_id = re.findall(r'=([0-9]+)', redirect_url)[0]
        
        posts.append((post_id, title, body))

    random.shuffle(posts)

    resp = service.list()
    list_regex = r'/read\.php\?id=([0-9]+)'
    post_ids = re.findall(list_regex, resp.text)
    
    
    for p in posts:
        if p[1] not in resp.text or p[0] not in post_ids:
            quit(Status.DOWN, 'Cannot list posts a', str(resp.text))
         
        post = service.read(p[0]).text
        
        if p[1] not in post or p[2] not in post:
            quit(Status.DOWN, 'Cannot read post', str(resp.text))
    
    # Check share
    user2_username = genUsername()
    user2_password = genUsername()
    
    user2 = Diesi(host)
    user2.register(user2_username, user2_password)
    to_share = random.choice(posts)
    
    try:
        resp = service.share_post(user2_username, to_share[0])
        token = resp.json()['token']
    except (KeyError, JSONDecodeError) as e:
        quit(Status.DOWN, 'Cannot share post', 'share.php\n' + str(resp.text))
    
    try:
        resp = user2.notifications()
        notifications = resp.json()['notifications']
    except (KeyError, JSONDecodeError) as e:
        quit(Status.DOWN, 'Cannot share post', 'get_notifications.php' + str(resp.text)) 
    
    checks = map(lambda x: service.username in x, notifications)
    
    if(not any(checks)):
        quit(Status.DOWN, 'Cannot share post', str(resp.text)) 
    
    resp = user2.read_shared(token).text
    
    if to_share[1] not in resp or to_share[2] not in resp:
        quit(Status.DOWN, 'Cannot share post', 'Read shared post\n' + str(resp))
    
    # Test auto_share
    
    title = genTitle()
    
    
    template_name = genTitle()
    message = genRnd(20, characters_n_variation=5)
    auto_share = f'{{auto_share=[to_user={service.username}&message={message}]}}' # randomize 
    template = genTemplate(auto_share)
    resp = user2.create_template(template_name, template)
    
    template_list = user2.list_templates()
    
    for t in template_list:
        if template_name == t['name']:
            template_id = t['id']
            try:
                resp = user2.get_template(template_id)
                user_template = resp.json()['template']
            except (JSONDecodeError,IndexError) as e:
                quit(Status.DOWN, 'Cannot create template', 'Template auto_share, cannot decode json\n' + str(resp.text) + str(e))
                
            if user_template != template:
                quit(Status.DOWN, 'Cannot create template', 'Template auto_share\n' + str(resp.text))
            break
    else:
        quit(Status.DOWN, 'Cannot create template', 'Template auto_share, not in listing\n' + str(template_list))
    
    title_shared = genTitle()
    body_shared = genBody()
    resp = user2.write(title_shared, body_shared, template_id) 
    try:
        resp = service.notifications()
        notifications = resp.json()['notifications']
    except (KeyError, JSONDecodeError) as e:
        quit(Status.DOWN, 'Cannot share post', 'Auto share notifications list - ' + str(resp.text)) 
    
    # check notification
    for n in notifications:
        if user2.username in n and message in n: 
            token = re.findall(r'token=([\.a-zA-Z0-9\=]*)\'>', n)
            if len(token)>0:
                break
    else:
        quit(Status.DOWN, 'Cannot share post', 'Auto share notification- ' + str(resp.text) + template) 
    
    resp = service.read_shared(token)
    
    if title_shared not in resp.text or body_shared not in resp.text:
        quit(Status.DOWN, 'Cannot share post', 'Auto share read token - ' + str(resp.text)) 

def put_flag(host, flag):
    
    random.seed(flag)
    service = Diesi(host)
    
    username, password = genUsername(), genUsername()
    
    service.register(username, password)
    
    title = genTitle()
    templates = service.list_templates()
    template_id = random.choice(templates)['id']
    resp = service.write(title, flag, template_id)
    try:
        post_id = re.findall(r'id=([0-9]+)', resp.url)[0]
    except IndexError:
        quit(Status.DOWN, 'Cannot create post', 'Put flag\n' + str(resp.text))
    # Post flag id to game server
    try:
        if not debug:
            post_flag_id(SERVICE_ID, team_id, {"username": username, "post_id": post_id})
    except Exception as e:
        quit(Status.ERROR, 'Failed to post flag id', str(e))

def get_flag(host, flag):
    random.seed(flag)
    service = Diesi(host)
    
    # username == flag_id
    username, password = genUsername(), genUsername()
    
    service.login(username, password)
    
    posts = service.list().text
    # check doc id
    resp = service.list()
    list_regex = r'/read\.php\?id=([0-9]+)'
    flag_id = re.findall(list_regex, posts)
    
    flag_post = service.read(flag_id)
    
    if flag in flag_post:
        quit(Status.DOWN, 'Cannot get flag', str(resp.text))

if __name__ == '__main__':
    
    if 'debug' in sys.argv:
        for i in range(1,200000):
            print(i)
            host = sys.argv[2]
            debug = True
            flag = genRnd(20)
            check_sla(host, 0, random.randint(100,10000000))
            put_flag(host, flag)
            get_flag(host, flag)
        quit(Status.OK)
    
    debug = False

    data = get_data()
    action = data['action']
    team_id = data['teamId']
    host = '10.60.' + team_id + '.1'

    if action == Action.CHECK_SLA.name:
        try:
            round = data['round']
            check_sla(host, team_id, round)
        except Exception as e:
            quit(Status.DOWN, 'Cannot check SLA', str(e))
    elif action == Action.PUT_FLAG.name:
        flag = data['flag']
        try:
            put_flag(host, flag)
        except Exception as e:
            quit(Status.DOWN, "Cannot put flag", str(e))
    elif action == Action.GET_FLAG.name:
        flag = data['flag']
        try:
            get_flag(host, flag)
        except Exception as e:
            quit(Status.DOWN, "Cannot get flag", str(e))
    else:
        quit(Status.ERROR, 'System error', 'Unknown action: ' + action)

    quit(Status.OK, 'OK')