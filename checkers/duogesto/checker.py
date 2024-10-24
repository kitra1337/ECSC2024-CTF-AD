#!/usr/bin/env python3

from checklib import *
from utils import *
import traceback

PORT = 4960


def register(ip, session, username, password):
    r = session.post(
        f"http://{ip}:{PORT}/api/register", json={"name": username, "password": password}
    )
    return r


def login(ip, session, username, password):
    r = session.post(
        f"http://{ip}:{PORT}/api/login", json={"name": username, "password": password}
    )
    return r


def logout(ip, session):
    r = session.get(f"http://{ip}:{PORT}/api/logout")


def create_impossible_challenge(ip, session, flag):
    filename = random_string(min_length=10, max_length=20) + ".svg"
    text = random_string(min_length=10, max_length=20)
    ans1 = random_string(min_length=10, max_length=20)
    ans2 = random_string(min_length=10, max_length=20)
    ans3 = random_string(min_length=10, max_length=20)

    r = session.post(
        f"http://{ip}:{PORT}/api/upload",
        json={
            "url": "https://ecsc2024.it/_next/static/media/ecsc2024.f58d72ba.svg",
            "filename": filename,
        },
    )
    r = session.post(
        f"http://{ip}:{PORT}/api/createchallenge",
        json={
            "text": text,
            "image": filename,
            "answers": {
                1: {"answer": ans1, "correct": False},
                2: {"answer": ans2, "correct": False},
                3: {"answer": ans3, "correct": False},
            },
            "prize": flag,
        },
    )


def create_random_challenge(ip, session):
    filename = random_string(min_length=10, max_length=20) + ".svg"
    text = random_string(min_length=10, max_length=20)
    ans1 = random_string(min_length=10, max_length=20)
    ans2 = random_string(min_length=10, max_length=20)
    ans3 = random_string(min_length=10, max_length=20)
    correct = random.randint(1, 3)
    prize = random_string(min_length=10, max_length=20)

    chall = {
        "text": text,
        "image": filename,
        "answers": {
            1: {"answer": ans1, "correct": correct == 1},
            2: {"answer": ans2, "correct": correct == 2},
            3: {"answer": ans3, "correct": correct == 3},
        },
        "prize": prize,
    }

    r = session.post(
        f"http://{ip}:{PORT}/api/upload",
        json={
            "url": "https://ecsc2024.it/_next/static/media/ecsc2024.f58d72ba.svg",
            "filename": filename,
        },
    )
    r = session.post(f"http://{ip}:{PORT}/api/createchallenge", json=chall)
    return chall


def get_challenges(ip, session, user):
    r = session.get(f"http://{ip}:{PORT}/api/challenges/{user}")
    return sorted(r.json()["challenges"], key=lambda c: c["_id"])


def get_question(ip, session, id):
    r = session.get(f"http://{ip}:{PORT}/api/question/{id}")
    return r.json()


def add_friend(ip, session, user):
    r = session.post(f"http://{ip}:{PORT}/api/friends", json={"name": user})
    return r.json()


def get_friends(ip, session):
    r = session.get(f"http://{ip}:{PORT}/api/friends")
    return r.json()


def check_register(ip):
    session = requests.Session()
    session.headers.update({"User-Agent": "checker"})

    username = random_string(min_length=10, max_length=20, allowed_chars='0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"$\'()*+,-.:;<=>@[\\]^_`{|}~')
    password = random_string(min_length=10, max_length=20)

    r = register(ip, session, username, password)

    return r.status_code == 200, r.text


def check_login(ip):
    session = requests.Session()
    session.headers.update({"User-Agent": "checker"})

    username = random_string(min_length=10, max_length=20, allowed_chars='0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"$\'()*+,-.:;<=>@[\\]^_`{|}~')
    password = random_string(min_length=10, max_length=20)

    register(ip, session, username, password)
    logout(ip, session)

    session = requests.Session()
    session.headers.update({"User-Agent": "checker"})
    r = login(ip, session, username, password)

    return r.status_code == 200, r.text


def check_change_propic(ip):
    return True, ""


def check_take_quiz(ip):
    session = requests.Session()
    session.headers.update({"User-Agent": "checker"})

    username = random_string(min_length=10, max_length=20, allowed_chars='0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"$\'()*+,-.:;<=>@[\\]^_`{|}~')
    password = random_string(min_length=10, max_length=20)

    register(ip, session, username, password)

    for i in range(5):
        question = get_question(ip, session, i + 1)
        r = session.post(
            f"http://{ip}:{PORT}/api/answer", json={"answer": question["answers"][0]}
        )

    return (
        r.status_code == 200 and "Congratulations! You completed the quiz!" in r.text
    ), r.text


def check_create_challenge(ip):
    session = requests.Session()
    session.headers.update({"User-Agent": "checker"})

    username = random_string(min_length=10, max_length=20, allowed_chars='0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"$\'()*+,-.:;<=>@[\\]^_`{|}~')
    password = random_string(min_length=10, max_length=20)

    register(ip, session, username, password)
    chall = create_random_challenge(ip, session)
    challenges = get_challenges(ip, session, username)
    question = get_question(ip, session, challenges[0]["_id"])

    correct = True
    if chall["image"] not in question["image"]:
        correct = False
    if chall["text"] != question["question"]:
        correct = False
    if [
        chall["answers"][1]["answer"],
        chall["answers"][2]["answer"],
        chall["answers"][3]["answer"],
    ] != question["answers"]:
        correct = False
    if username != question["author"]:
        correct = False
    if chall["prize"] != question["prize"]:
        correct = False

    return correct, str(chall)


def check_win_challenge(ip):
    session = requests.Session()
    session.headers.update({"User-Agent": "checker"})

    username = random_string(min_length=10, max_length=20, allowed_chars='0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"$\'()*+,-.:;<=>@[\\]^_`{|}~')
    password = random_string(min_length=10, max_length=20)

    register(ip, session, username, password)
    chall = create_random_challenge(ip, session)
    correct = chall["answers"][
        list(filter(lambda k: chall["answers"][k]["correct"], chall["answers"]))[0]
    ]["answer"]

    author = username

    session = requests.Session()
    session.headers.update({"User-Agent": "checker"})

    username = random_string(min_length=10, max_length=20, allowed_chars='0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"$\'()*+,-.:;<=>@[\\]^_`{|}~')
    password = random_string(min_length=10, max_length=20)

    register(ip, session, username, password)

    # TODO: remove
    logout(ip, session)
    login(ip, session, username, password)

    id = get_challenges(ip, session, author)[0]["_id"]
    get_question(ip, session, id)

    r = session.post(f"http://{ip}:{PORT}/api/answer", json={"answer": correct})
    ans = r.json()

    if not ans["correct"] or ans["message"] != chall["prize"]:
        return False, f"{ans}"

    return True, ""


def check_lose_challenge(ip):
    session = requests.Session()
    session.headers.update({"User-Agent": "checker"})

    username = random_string(min_length=10, max_length=20, allowed_chars='0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"$\'()*+,-.:;<=>@[\\]^_`{|}~')
    password = random_string(min_length=10, max_length=20)

    register(ip, session, username, password)
    chall = create_random_challenge(ip, session)
    wrong = chall["answers"][
        list(filter(lambda k: not chall["answers"][k]["correct"], chall["answers"]))[0]
    ]["answer"]

    author = username

    session = requests.Session()
    session.headers.update({"User-Agent": "checker"})

    username = random_string(min_length=10, max_length=20, allowed_chars='0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"$\'()*+,-.:;<=>@[\\]^_`{|}~')
    password = random_string(min_length=10, max_length=20)

    register(ip, session, username, password)

    # TODO: remove
    logout(ip, session)
    login(ip, session, username, password)

    id = get_challenges(ip, session, author)[0]["_id"]
    get_question(ip, session, id)

    r = session.post(f"http://{ip}:{PORT}/api/answer", json={"answer": wrong})
    ans = r.json()

    if ans["correct"]:
        return False, f"{ans}"

    return True, ""


def check_set_friends(ip):
    session1 = requests.Session()
    session1.headers.update({"User-Agent": "checker"})

    username = random_string(min_length=10, max_length=20, allowed_chars='0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"$\'()*+,-.:;<=>@[\\]^_`{|}~')
    password = random_string(min_length=10, max_length=20)

    register(ip, session1, username, password)

    friend = username

    session2 = requests.Session()
    session2.headers.update({"User-Agent": "checker"})

    username = random_string(min_length=10, max_length=20, allowed_chars='0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"$\'()*+,-.:;<=>@[\\]^_`{|}~')
    password = random_string(min_length=10, max_length=20)

    register(ip, session2, username, password)

    add_friend(ip, session2, friend)
    friends = get_friends(ip, session1)

    return username in friends["friends"], f"{friends}"


def check_friend_prize(ip):
    session1 = requests.Session()
    session1.headers.update({"User-Agent": "checker"})

    username1 = random_string(min_length=10, max_length=20, allowed_chars='0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"$\'()*+,-.:;<=>@[\\]^_`{|}~')
    password1 = random_string(min_length=10, max_length=20)

    register(ip, session1, username1, password1)

    friend = username1

    session2 = requests.Session()
    session2.headers.update({"User-Agent": "checker"})

    username2 = random_string(min_length=10, max_length=20, allowed_chars='0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"$\'()*+,-.:;<=>@[\\]^_`{|}~')
    password2 = random_string(min_length=10, max_length=20)

    register(ip, session2, username2, password2)

    chall1 = create_random_challenge(ip, session2)

    add_friend(ip, session2, friend)

    # TODO: remove
    logout(ip, session1)
    login(ip, session1, username1, password1)

    id = get_challenges(ip, session1, username2)[0]["_id"]
    chall2 = get_question(ip, session1, id)

    return chall1["prize"] == chall2["prize"], f"{chall1 = }\n{chall2 = }"


def check_upload(ip):
 

    url_list = [
        "https://filebin.net/static/img/favicon.png",
        "https://www.w3.org/assets/logos/w3c/w3c-no-bars.svg",
        "https://static.npmjs.com/attachments/ck3uwed1cmso79y74pjugy10f-gak-2x.png",
        "https://www.example.com/",
        "https://az15297.vo.msecnd.net/images/acquisition-generic-image.png",
        "https://res.cloudinary.com/dbulfrlrz/image/upload/v1703162849/static/logos/icons/vpn_f9embt.svg",
        "https://book.hacktricks.xyz/robots.txt",
        "https://proton.me/robots.txt",
        "https://cdn.sstatic.net/Img/favicons-sprite16.png"
        "https://instagram.com/robots.txt",
        "https://www.facebook.com/robots.txt",
        "https://github.blog/wp-content/uploads/2021/02/npm-github.png?w=100",
        "https://github.blog/wp-content/uploads/2019/09/security-1200-630.png?w=100",
        "https://www.mozilla.org/media/img/home/2018/newsletter-graphic-high-res.dfdd8a0a8b68.png",
        "https://twitter.com/robots.txt",
        "https://www.linkedin.com/robots.txt",
        "https://www.pinterest.com/favicon.ico",
        "https://www.tiktok.com/robots.txt",
        "https://it.quora.com/favicon.ico",
        "https://ngrok.com/robots.txt",
        "https://www.cloudflare.com/favicon.ico",
        "https://gitlab.com/assets/favicon-72a2cad5025aa931d6ea56c3201d1f18e68a8cd39788c7c80d5b2b82aa5143ef.png",
        "https://developer.mozilla.org/en-US/blog/mdn-scrimba-back2school/featured.png",
        "https://portswigger.net/burp/images/bsp-burp-illy.png",
        "https://duckduckgo.com/_next/static/media/opera-lg.237c4418.png",
        "https://www.mozilla.org/media/protocol/img/logos/mozilla/logo-word-hor.e20791bb4dd4.svg",
        "https://duckduckgo.com/_next/static/media/play-store.e5d5ed36.png",
        "https://www.w3.org/2008/site/images/logo-w3c-mobile-lg",
        "https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_92x30dp.png",
        "https://github.com/favicon.ico",
        "https://cyberchallenge.it/assets/icons/Logo.svg",
        "https://pastebin.com/themes/pastebin/img/guest.webp",
        "https://cdn.webhook.site/icon.png",
        "https://static.xx.fbcdn.net/rsrc.php/y1/r/4lCu2zih0ca.svg",
        "https://www.instagram.com/static/images/web/mobile_nav_type_logo.png/735145cfe0a4.png",
        "https://www.youtube.com/favicon.ico",
        "https://httpbin.org/static/favicon.ico",
        "https://djeqr6to3dedg.cloudfront.net/repo-logos/library/alpine/live/logo-1720462146426.png",
        "https://www.python.org/static/opengraph-icon-200x200.png",
        "https://www.rust-lang.org/static/images/rust-logo-blk.svg",
        "https://www.ruby-lang.org/images/header-ruby-logo.png",
        "https://www.php.net/images/logos/php-logo.svg",
        "https://www.apple.com/favicon.ico",
        "https://wetransfer.com/robots.txt",
        "https://avatars.githubusercontent.com/u/91921128?s=200&v=4",
        "https://ecsc2024.it/_next/image?url=%2F_next%2Fstatic%2Fmedia%2Fbg-04.5fddd844.png&w=640&q=75",
        "https://ecsc2024.it/_next/image?url=%2F_next%2Fstatic%2Fmedia%2Fmarriott.5e336fba.jpg&w=256&q=75",
        "https://ecsc2024.it/_next/image?url=%2F_next%2Fstatic%2Fmedia%2Fogr-4.c6942fb6.jpg&w=256&q=75",
        "https://ecsc2024.it/_next/image?url=%2F_next%2Fstatic%2Fmedia%2Fturin-2.8c7ebb46.jpg&w=256&q=75",
        "https://ecsc2024.it/_next/image?url=%2F_next%2Fstatic%2Fmedia%2Fturin-1.40180fca.jpg&w=256&q=75",
        "https://ecsc2024.it/_next/image?url=%2F_next%2Fstatic%2Fmedia%2Fbg-05.3adce735.png&w=640&q=75",
        "https://ecsc2024.it/_next/image?url=%2F_next%2Fstatic%2Fmedia%2Fcybersecnatlab.5869af1e.png&w=1920&q=75",
        "https://ecsc2024.it/_next/image?url=%2F_next%2Fstatic%2Fmedia%2Facn.e12205b6.png&w=1920&q=75",
        "https://ecsc2024.it/writeups/arxelerated/1_QEMU_cat.png",
        "https://github.githubassets.com/assets/illu-copilot-editor-6474457a5b19.png",
        "https://github.githubassets.com/assets/illu-code-scanning-fc9dfb212aa3.png?width=644&format=webpll",
        "https://cyberchallenge.it/assets/icons/Logo.svg",
        "https://cyberchallenge.it/assets/icons/FAQ.svg",
        "https://cyberchallenge.it/assets/icons/Program.svg",
        "https://cyberchallenge.it/assets/icons/Sponsor.svg",
        "https://cyberchallenge.it/assets/icons/Testimonials.svg",
        "https://cyberchallenge.it/assets/icons/TeamItaly.svg",
        "https://cyberchallenge.it/assets/icons/Contact.svg",
        "https://cyberchallenge.it/assets/icons/Students.svg",
        "https://cyberchallenge.it/assets/icons/HighSchools.svg",
        "https://cyberchallenge.it/assets/icons/University.svg",
        "https://cyberchallenge.it/assets/icons/Sponsor.svg",
        "https://cyberchallenge.it/assets/icons/University.svg",
        "https://cyberchallenge.it/assets/icons/Internship.svg",
        "https://cyberchallenge.it/assets/icons/Lavoro.svg",
        "https://cyberchallenge.it/assets/icons/University.svg",
        "https://cyberchallenge.it/assets/icons/News.svg",
        "https://cyberchallenge.it/assets/icons/PressRelease.svg",
        "https://cyberchallenge.it/assets/icons/PressKit.svg",
        "https://cyberchallenge.it/assets/icons/HallFame.svg",
        "https://cyberchallenge.it/assets/icons/Photo.svg",
        "https://cyberchallenge.it/assets/icons/PublicStats.svg",
        "https://cyberchallenge.it/assets/icons/CTF.svg",
        "https://cyberchallenge.it/assets/icons/OpenCC-IT.svg",
        "https://cyberchallenge.it/assets/icons/Mail.svg",
        "https://cyberchallenge.it/assets/icons/X.svg",
        "https://cyberchallenge.it/assets/icons/FB.svg",
        "https://cyberchallenge.it/assets/icons/Linkedin.svg",
        "https://cyberchallenge.it/assets/icons/Instagram.svg",
        "https://cyberchallenge.it/_next/image?url=%2Fassets%2Fimgs%2Fbackground%2F7.webp&w=3840&q=75",
        "https://cyberchallenge.it/assets/icons/University.svg",
        "https://cyberchallenge.it/media/public/venue/logo/aeronautica.png",
        "https://cyberchallenge.it/media/public/venue/logo/unibo.png",
        "https://cyberchallenge.it/media/public/venue/logo/c3t.png",
        "https://cyberchallenge.it/media/public/venue/logo/esercito.png",
        "https://cyberchallenge.it/media/public/venue/logo/unibz.png",
        "https://cyberchallenge.it/media/public/venue/logo/poliba.png",
        "https://cyberchallenge.it/media/public/venue/logo/polimi.png",
        "https://cyberchallenge.it/media/public/venue/logo/polito.png",
        "https://cyberchallenge.it/media/public/venue/logo/unirm1.png",
        "https://cyberchallenge.it/media/public/venue/logo/unive.png",
        "https://cyberchallenge.it/media/public/venue/logo/unicampus.png",
        "https://cyberchallenge.it/media/public/venue/logo/unicampania.png",
        "https://cyberchallenge.it/media/public/venue/logo/univaq.png",
        "https://cyberchallenge.it/media/public/venue/logo/uninsubria.png",
        "https://cyberchallenge.it/media/public/venue/logo/uniba.png",
        "https://cyberchallenge.it/media/public/venue/logo/unibs.png",
        "https://cyberchallenge.it/media/public/venue/logo/unica.png",
        "https://cyberchallenge.it/media/public/venue/logo/unicam.png",
        "https://cyberchallenge.it/media/public/venue/logo/unict.png",
        "https://cyberchallenge.it/media/public/venue/logo/unife.png",
        "https://cyberchallenge.it/media/public/venue/logo/unige.png",
        "https://cyberchallenge.it/media/public/venue/logo/unime.png",
        "https://cyberchallenge.it/media/public/venue/logo/unimi.png",
        "https://cyberchallenge.it/media/public/venue/logo/unimib.png",
        "https://cyberchallenge.it/media/public/venue/logo/unipd.png",
        "https://cyberchallenge.it/media/public/venue/logo/unipa.png",
        "https://cyberchallenge.it/media/public/venue/logo/unipr.png",
        "https://cyberchallenge.it/media/public/venue/logo/unipg.png",
        "https://cyberchallenge.it/media/public/venue/logo/unirm2.png",
        "https://cyberchallenge.it/media/public/venue/logo/unisa.png",
        "https://cyberchallenge.it/media/public/venue/logo/unitn.png",
        "https://cyberchallenge.it/media/public/venue/logo/uniud.png",
        "https://cyberchallenge.it/media/public/venue/logo/univr.png",
        "https://cyberchallenge.it/media/public/venue/logo/unich.png",
        "https://cyberchallenge.it/media/public/venue/logo/unirm3.png",
        "https://cyberchallenge.it/media/public/venue/logo/unical.png",
        "https://cyberchallenge.it/media/public/venue/logo/unisalento.png",
        "https://cyberchallenge.it/media/public/venue/logo/unimore.png",
        "https://cyberchallenge.it/media/public/venue/logo/napoli.png",
        "https://cyberchallenge.it/media/public/venue/logo/unipi.png",
        "https://cyberchallenge.it/media/public/venue/logo/unito.png",
        "https://cyberchallenge.it/media/public/venue/logo/unirc.png",
        "https://cyberchallenge.it/media/public/venue/logo/univpm.png",
        "https://cyberchallenge.it/assets/icons/Logo.svg",
        "https://cyberchallenge.it/assets/loghi/logo-lab.svg",
        "https://cyberchallenge.it/assets/icons/Mail.svg",
        "https://cyberchallenge.it/assets/icons/X.svg",
        "https://cyberchallenge.it/assets/icons/FB.svg",
        "https://cyberchallenge.it/assets/icons/Linkedin.svg",
        "https://cyberchallenge.it/assets/icons/Instagram.svg",
    ]


    user = UserChallenge(ip)
    user.register()

    url = random.choice(url_list)
    
    try:
        filename = random_string(1,10)
        user.upload_file(url, filename)

        cid = user.create_challenge(
            {
                "text": random_string(1,20),
                "image": filename,
                "answers": {
                    1: {
                        "answer": random_string(),
                        "correct": random.random() > 0.3,
                    },
                    2: {
                        "answer": random_string(),
                        "correct": random.random() > 0.3,
                    },
                    3: {
                        "answer": random_string(),
                        "correct": random.random() > 0.3,
                    },
                },
                "prize": random_string(),
            }
        )
        res = user.get_qimage(cid)

        r = requests.get(url, timeout=3)

        if r.content != res:

            user = UserChallenge(ip)
            user.register()

            url = random.choice(url_list)
            
            filename = random_string(1,10)
            user.upload_file(url, filename)

            cid = user.create_challenge(
                {
                    "text": random_string(1,20),
                    "image": filename,
                    "answers": {
                        1: {
                            "answer": random_string(),
                            "correct": random.random() > 0.3,
                        },
                        2: {
                            "answer": random_string(),
                            "correct": random.random() > 0.3,
                        },
                        3: {
                            "answer": random_string(),
                            "correct": random.random() > 0.3,
                        },
                    },
                    "prize": random_string(),
                }
            )
            res = user.get_qimage(cid)

            r = requests.get(url, timeout=3)

            if r.content != res:
                return False, f"{url}\n{r.content}\n{len(res)}"
    
    except CheckException as e:
        d = e.debug + f'\n{url}'
        return False, d
        
    return True, ""

def check_sla(host):
    # Check service functionality

    checks = [
        check_register,
        check_login,
        check_change_propic,
        check_take_quiz,
        check_create_challenge,
        check_win_challenge,
        check_lose_challenge,
        check_set_friends,
        check_friend_prize,
        check_upload,
    ]

    messages = {
        "check_register": "Cannot register",
        "check_login": "Cannot login",
        "check_change_propic": "Cannot change profile picture",
        "check_take_quiz": "Cannot take quiz",
        "check_create_challenge": "Cannot create challenge",
        "check_win_challenge": "Cannot play challenge",
        "check_lose_challenge": "Cannot play challenge",
        "check_set_friends": "Cannot use friends",
        "check_friend_prize": "Cannot use friends",
        "check_upload": "Cannot upload or retrieve file",
    }

    seed = random_string(min_length=10, max_length=20)
    random.seed(seed)

    random.shuffle(checks)
    for u in checks:
        try:
            check, data = u(host)
            if not check:
                quit(Status.DOWN, messages[u.__name__], f"{seed}\n{u}\n{data}")
        except Exception:
            quit(Status.DOWN, messages[u.__name__], f"{seed}\n{u.__name__}\n{traceback.format_exc()}")

    quit(Status.OK, "OK")


def put_flag(host, flag):
    # Generate flag_id for the flag, put the flag inside the service

    random.seed(flag)
    session = requests.Session()
    session.headers.update({"User-Agent": "checker"})

    username = random_string(min_length=10, max_length=20, allowed_chars='0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
    password = random_string(min_length=10, max_length=20)

    flag_id = username

    try:
        r = register(host, session, username, password)
        if "error" in r.json():
            raise Exception("Error on register")
    except:
        quit(Status.DOWN, "Cannot register", f"{flag}\n{traceback.format_exc()}")

    try:
        create_impossible_challenge(host, session, flag)
    except:
        quit(
            Status.DOWN, "Cannot create challenge", f"{flag}\n{traceback.format_exc()}"
        )

    # Post flag id to game server
    try:
        post_flag_id("duogesto", team_id, {"username": flag_id})
    except Exception as e:
        quit(Status.ERROR, "Failed to post flag id", str(e))

    quit(Status.OK, "OK")


def get_flag(host, flag):

    # Generate flag_id for this flag, retrieve the flag from the service

    random.seed(flag)
    session = requests.Session()
    session.headers.update({"User-Agent": "checker"})

    username = random_string(min_length=10, max_length=20, allowed_chars='0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
    password = random_string(min_length=10, max_length=20)

    try:
        login(host, session, username, password)
    except:
        quit(Status.DOWN, "Cannot login", f"{flag}\n{traceback.format_exc()}")

    try:
        challenges = get_challenges(host, session, username)
        id = challenges[0]["_id"]
    except:
        quit(Status.DOWN, "Cannot get challenges", f"{flag}\n{traceback.format_exc()}")

    try:
        question = get_question(host, session, id)
    except:
        quit(Status.DOWN, "Cannot get question", f"{flag}\n{traceback.format_exc()}")

    try:
        if question["prize"] != flag:
            raise Exception(str(question))
    except:
        quit(Status.DOWN, "Cannot get flag", f"{flag}\n{traceback.format_exc()}")

    quit(Status.OK, "OK")


if __name__ == "__main__":

    if len(sys.argv) > 1:
        if sys.argv[1] == "dev":
            check_sla("localhost")
            exit(0)

    data = get_data()
    action = data["action"]
    team_id = data["teamId"]
    host = "10.60." + team_id + ".1"

    if "LOCALHOST" in os.environ:
        host = "127.0.0.1"

    if action == Action.CHECK_SLA.name:
        try:
            check_sla(host)
        except Exception as e:
            quit(Status.DOWN, "Cannot check SLA", f"{traceback.format_exc()}")
    elif action == Action.PUT_FLAG.name:
        flag = data["flag"]
        try:
            put_flag(host, flag)
        except Exception as e:
            quit(Status.DOWN, "Cannot put flag", f"{flag}\n{traceback.format_exc()}")
    elif action == Action.GET_FLAG.name:
        flag = data["flag"]
        try:
            get_flag(host, flag)
        except Exception as e:
            quit(Status.DOWN, "Cannot get flag", f"{flag}\n{traceback.format_exc()}")
    else:
        quit(Status.ERROR, "System error", "Unknown action: " + action)

    quit(Status.OK)
