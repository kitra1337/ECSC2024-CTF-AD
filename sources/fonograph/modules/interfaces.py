#!/usr/bin/env python3

from .client import *
from .gui_utils import *
import io
import requests
from mutagen.mp3 import MP3
from pygame import mixer
from pygame_gui.core import ObjectID

textline = lambda *args, **kwargs: pygame_gui.elements.ui_text_entry_line.UITextEntryLine(*args, **kwargs)
button = lambda *args, **kwargs: pygame_gui.elements.UIButton(*args, **kwargs)
label = lambda *args, **kwargs: pygame_gui.elements.UILabel(*args, **kwargs)
image = lambda *args, **kwargs: pygame_gui.elements.ui_image.UIImage(*args, **kwargs)
selectionlist = lambda *args, **kwargs: pygame_gui.elements.UISelectionList(*args, **kwargs)
textarea = lambda *args, **kwargs: pygame_gui.elements.UITextEntryBox(*args, **kwargs)
feedback_message = lambda *args, **kwargs: pygame_gui.elements.UITextBox(relative_rect=pygame.Rect((20, HEIGHT-100), (530, 90)), *args, object_id=ObjectID('@feedback_message', ''), **kwargs)

mixer.init()

def center(s, n):
    if len(s) > n:
        return s
    pad = (n - len(s))//2
    return ' '*pad + s + ' '*(n - len(s) - pad)

class BaseInterface():
    def __init__(self, screen):
        self.screen = screen
        self.background = pygame.Surface((WIDTH, HEIGHT))
        self.background.fill(pygame.Color(BG_COLOR))
        self.client = None
        self.manager = pygame_gui.UIManager((WIDTH, HEIGHT), theme_path='./assets/themes/theme.json')
        self.feedback_message = ''
        self.feedback_message_box = feedback_message(html_text='', manager=self.manager)
        self.logout_button = button(relative_rect=pygame.Rect((WIDTH - 210, 10), (200, 50)), manager=self.manager, text='Logout')
        self.title = label(relative_rect=pygame.Rect((CENTER - 200, 20), (600, 200)), manager=self.manager, text='fonograph', object_id=ObjectID('@title', ''))
        self.left_logo = image(relative_rect=pygame.Rect((CENTER - 400, 30), (180, 180)), manager=self.manager, image_surface=logo)

    async def handle_logout(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.logout_button:
                try:
                    await self.client.logout()
                except CantConnectException:
                    self.set_feedback_message('can\'t connect')
                else:
                    self.set_feedback_message('logout success')
                    return {'status': 'logged out'}
        return {'status': None}
    
    def set_feedback_message(self, msg=''):
        self.feedback_message = msg
        self.feedback_message_box.kill()
        self.feedback_message_box = feedback_message(html_text=msg, manager=self.manager)
    
    def set_client(self, client):
        self.client = client
    
    def reset_client(self):
        self.client = None
    
    def render(self):
        self.screen.blit(self.background, (0,0))
        self.manager.draw_ui(self.screen)

class LoggedOutInterface(BaseInterface):
    def __init__(self, screen):
        super().__init__(screen)
        self.client = None
        
        self.logout_button.disable()
        self.logout_button.hide()

        self.ip_textbox = textline(relative_rect=pygame.Rect((CENTER-100, 400), (200, 50)), manager=self.manager, initial_text='0.0.0.0')
        self.username_textbox = textline(relative_rect=pygame.Rect((CENTER-100, 460), (200, 50)), manager=self.manager, placeholder_text='username')
        self.password_textbox = textline(relative_rect=pygame.Rect((CENTER-100, 520), (200, 50)), manager=self.manager, placeholder_text='password')
        self.login_button = button(relative_rect=pygame.Rect((CENTER-150, 580), (145, 50)), manager=self.manager, text='Login')
        self.signup_button = button(relative_rect=pygame.Rect((CENTER+5, 580), (145, 50)), manager=self.manager, text='Sign Up')

    
    async def handle(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            ip = self.ip_textbox.get_text()
            username = self.username_textbox.get_text()
            password = self.password_textbox.get_text()
            self.set_client(Client(f'ws://{ip}:5000/api'))
            if event.ui_element == self.login_button:
                try:
                    await self.client.login(username, password)
                except CantConnectException:
                    self.set_feedback_message('can\'t connect')
                except CantLoginException:
                    self.set_feedback_message('login failed')
                else:
                    self.set_feedback_message('login success')
                    return {'status': 'logged in'}
            elif event.ui_element == self.signup_button:
                try:
                    await self.client.register(username, password)
                except CantConnectException:
                    self.set_feedback_message('can\'t connect')
                except CantRegisterException:
                    self.set_feedback_message('signup failed')
                else:
                    self.set_feedback_message('signup_success')
                    return {'status': 'logged in'}
        return {"status": None}

class ShowPlaylistsInterface(BaseInterface):
    def __init__(self, screen):
        super().__init__(screen)
        self.ui_playlists = selectionlist(relative_rect=pygame.Rect((200, 240), (1200, 550)), manager=self.manager, item_list=[])
        self.add_playlist_button = button(relative_rect=pygame.Rect((CENTER-205, 800), (200, 50)), manager=self.manager, text='New playlist')
        self.view_shared_playlist_button = button(relative_rect=pygame.Rect((CENTER+5, 800), (200, 50)), manager=self.manager, text='View shared playlist')

    async def get_all_playlists(self):
        try:
            self.playlists = await self.client.get_all_playlists()
        except CantConnectException:
            self.set_feedback_message('can\'t connect')
        
        self.ui_playlists.set_item_list(self.parse_playlists())

    async def handle(self, event):
        result = await self.handle_logout(event)
        if result['status'] == 'logged out':
            return result
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.add_playlist_button:
                self.set_feedback_message('')
                return {"status": "add playlist"}
            elif event.ui_element == self.view_shared_playlist_button:
                return {"status": "view shared playlist"}
        elif event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if event.ui_element == self.ui_playlists:
                uuid = event.text.split(' | ')[-1].strip()
                self.client.logger.info(f'{uuid = }')
                pic, songs = self.playlist_by_uuid(uuid)
                self.set_feedback_message('')
                return {"status": 'view playlist', 'picture': pic, 'songs': songs}
        return {"status": None}

    def parse_playlists(self):
        result = []
        for pl in self.playlists:
            s = ' | '.join([center(pl[k], 40) for k in ['title', 'description', 'id']])
            result.append(s)
        return result

    def playlist_by_uuid(self, uuid):
        for pl in self.playlists:
            if pl['id'] == uuid:
                return pl['picture'], pl['songs']
        else:
            return None, None

class AddPlaylistInterface(BaseInterface):
    def __init__(self, screen):
        super().__init__(screen)

        self.title_textbox = textline(relative_rect=pygame.Rect((CENTER-300, 240), (600, 50)), manager=self.manager, placeholder_text='Playlist Title')
        self.description_textbox = textarea(relative_rect=pygame.Rect((CENTER-300, 300), (600, 100)), manager=self.manager, placeholder_text='Playlist description')
        self.public_checkbox = button(relative_rect=pygame.Rect((CENTER-250, 440), (200, 50)), manager=self.manager, text='Public playlist (toggle)')
        self.add_button = button(relative_rect=pygame.Rect((CENTER-100, 800), (200, 50)), manager=self.manager, text='Add')
        self.back_button = button(relative_rect=pygame.Rect((10, 10), (100, 50)), manager=self.manager, text='< back')
        self.ui_songs = selectionlist(relative_rect=pygame.Rect((CENTER + 30, 450), (500, 300)), manager=self.manager, item_list=[], allow_multi_select=True)
        self.ui_pictures_select = None
        self.ui_picture_preview = None

    async def get_songs(self):
        try:
            self.songs = await self.client.get_songs()
        except CantConnectException:
            self.set_feedback_message('can\'t connect')
        
        self.ui_songs_rendered = self.parse_songs()
        self.ui_songs.set_item_list(self.ui_songs_rendered)


    async def get_pictures(self):
        try:
            self.pictures = await self.client.get_pictures()
        except CantConnectException:
            self.set_feedback_message('can\'t connect')
        self.ui_pictures_rendered = [
            str(x['id'])
            for x in self.pictures
        ]

        self.ui_pictures_surfaces = {}
        for pic in self.pictures:
            url = pic['url']
            assert url.startswith(EXPECTED_START_URL_PICTURES), f'url mismatch {self.picture_url = }'
            resp = requests.get(url, stream=True)
            pic_ = io.BytesIO(resp.content)
            self.ui_pictures_surfaces[str(pic['id'])] = pygame.image.load(pic_)
        
        if self.ui_pictures_select is None:
            self.ui_pictures_select = selectionlist(relative_rect=pygame.Rect((CENTER - 200, 540), (80, 200)), manager=self.manager, item_list=self.ui_pictures_rendered, allow_multi_select=False, default_selection=self.ui_pictures_rendered[0])
        if self.ui_picture_preview is None:
            self.ui_picture_preview = image(relative_rect=pygame.Rect((CENTER - 420, 540), (200, 200)), manager=self.manager, image_surface=self.ui_pictures_surfaces[self.ui_pictures_rendered[0]])


    async def handle(self, event):
        result = await self.handle_logout(event)
        if result['status'] == 'logged out':
            return result

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.public_checkbox:
                if event.ui_element.is_selected:
                    event.ui_element.unselect()
                else:
                    event.ui_element.select()
            elif event.ui_element == self.add_button:
                title = self.title_textbox.get_text()
                description = self.description_textbox.get_text()

                public = self.public_checkbox.is_selected
                token, pubkey = None, 0
                if not public:
                    token = rng.randrange(q)
                    pubkey = pow(g, token, p)

                songs = self.ui_songs.get_multi_selection()
                songs = [
                    self.ui_songs_rendered.index(x)
                    for x in songs
                ]
                
                try:
                    playlist_id = await self.client.add_playlist(title, description, public, songs, pubkey)
                except CantConnectException:
                    self.set_feedback_message('can\'t connect')
                else:
                    picture = self.ui_pictures_select.get_single_selection()
                    if picture is not None:
                        picture = int(picture)
                        try:
                            await self.client.set_picture(playlist_id, picture)
                        except CantConnectException:
                            self.set_feedback_message('can\'t connect')

                    if not public:
                        self.set_feedback_message(f'playlist added\nid: {playlist_id}\ntoken: {hex(token)[2:].zfill(40)}')
                    else:
                        self.set_feedback_message(f'playlist added')
                    return {'status': 'logged in'}

            elif event.ui_element == self.back_button:
                self.set_feedback_message('')
                return {"status": "logged in"}

        if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if event.ui_element == self.ui_pictures_select:
                selected_surface = self.ui_pictures_surfaces[self.ui_pictures_select.get_single_selection()]
                self.ui_picture_preview.set_image(selected_surface)
                 
        return {'status': None}

    def parse_songs(self):
        duration2str = lambda x: f"{x//60}:{x%60:02}"
        ret = []
        for x in self.songs:
            s = center(x['title'], 40) + ' | '
            s += center(x['author'], 10) + ' | '
            s += center(duration2str(x['duration']), 10)
            ret.append(s)
        return ret

class ShowPlaylistSongsInterface(BaseInterface):
    def __init__(self, screen):
        super().__init__(screen)
        self.ui_songs = selectionlist(relative_rect=pygame.Rect((200, 280), (1200, 550)), manager=self.manager, item_list=[])
        self.back_button = button(relative_rect=pygame.Rect((10, 10), (100, 50)), manager=self.manager, text='< back')
        
        self.ui_image = None
    
    def set_playlist(self, result):
        self.songs = result['songs'][:]
        self.ui_songs.set_item_list(self.parse_songs())

        self.picture_url = result['picture']

        if self.picture_url is None:
            self.ui_songs.set_relative_position(pygame.math.Vector2(200, 240))
            self.ui_songs.set_dimensions(pygame.math.Vector2(1200, 550))
            
            if self.ui_image is not None:
                self.ui_image.kill()
                self.ui_image = None
        else:
            assert self.picture_url.startswith(EXPECTED_START_URL_PICTURES), f'url mismatch {self.picture_url = }'
            resp = requests.get(self.picture_url, stream=True)
            self.picture = io.BytesIO(resp.content)
            self.picture = pygame.image.load(self.picture)

            if self.ui_image is None:
                self.ui_image = image(relative_rect=pygame.Rect((200, 365), (300, 300)), manager=self.manager, image_surface=self.picture)

                self.ui_songs.set_relative_position(pygame.math.Vector2(CENTER - 100, 240))
                self.ui_songs.set_dimensions(pygame.math.Vector2(800, 550))


    async def handle(self, event):
        result = await self.handle_logout(event)
        if result['status'] == 'logged out':
            return result

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.back_button:
                self.set_feedback_message('')
                return {"status": "logged in"}
        elif event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if event.ui_element == self.ui_songs:
                title, author, duration = event.text.split(' | ')
                for song in self.songs:
                    if song['author'] == author.strip() and song['title'] == title.strip():
                        break
                else:
                    self.set_feedback_message('song not found')
                    return {'status': None}
                self.set_feedback_message('')
                return {"status": 'play song', 'song': song}
        return {"status": None}
    
    def parse_songs(self):
        duration2str = lambda x: f"{x//60}:{x%60:02}"
        ret = []
        for x in self.songs:
            s = center(x['title'], 40) + ' | '
            s += center(x['author'], 10) + ' | '
            s += center(duration2str(x['duration']), 10)
            ret.append(s)
        return ret

class PlaySongInterface(BaseInterface):
    def __init__(self, screen):
        super().__init__(screen)
        self.back_button = button(relative_rect=pygame.Rect((10, 10), (100, 50)), manager=self.manager, text='< back')

        self.play_button = button(relative_rect=pygame.Rect((CENTER-160, 600), (150, 100)), manager=self.manager, text='PLAY', object_id=ObjectID('@play_pause', ''))
        self.pause_button = button(relative_rect=pygame.Rect((CENTER+10, 600), (150, 100)), manager=self.manager, text='PAUSE', object_id=ObjectID('@play_pause', ''))

        self.song_title_label = label(relative_rect=pygame.Rect((0, 350), (WIDTH, 150)), manager=self.manager, object_id=ObjectID('','#song_title'), text='')

        self.volume_slider = pygame_gui.elements.ui_horizontal_slider.UIHorizontalSlider(pygame.Rect((CENTER-165, 540), (330, 50)), manager=self.manager, click_increment=5, start_value=20, value_range=(0,100))
        self.volume_icon = image(pygame.Rect((CENTER-225, 540), (50, 50)), manager=self.manager, image_surface=volume_icon)
    
    def set_song(self, song):
        self.song = song
        self.song_url = self.song['download_link']
        assert self.song_url.startswith(EXPECTED_START_URL_MUSIC), f'url mismatch {self.song_url = }'
        self.client.logger.info(f'starting download {self.song_url = }')
        resp = requests.get(self.song_url, stream=True)
        self.client.logger.info(f'song downloaded')
        self.mp3 = io.BytesIO(resp.content)
        mixer.music.load(self.mp3)
        mixer.music.set_volume(0.2)
        self.music_status = None
        self.song_title_label.set_text(self.song['title'].strip())
    
    async def handle(self, event):
        result = await self.handle_logout(event)
        if result['status'] == 'logged out':
            mixer.music.pause()
            return result

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.back_button:
                self.set_feedback_message('')
                mixer.music.pause()
                return {"status": "view playlist", 'from': 'play song'}
            elif event.ui_element == self.play_button:
                if self.music_status == 'paused':
                    mixer.music.unpause()
                else:
                    mixer.music.play()
                return {"status": None}
            elif event.ui_element == self.pause_button:
                mixer.music.pause()
                self.music_status = 'paused'
        
        elif event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
            if event.ui_element == self.volume_slider:
                value = self.volume_slider.get_current_value()
                mixer.music.set_volume(value/100)

        return {"status": None}

class ViewSharedPlaylistInterface(BaseInterface):
    def __init__(self, screen):
        super().__init__(screen)
        self.back_button = button(relative_rect=pygame.Rect((10, 10), (100, 50)), manager=self.manager, text='< back')
        self.playlist_id_input = textline(relative_rect=pygame.Rect((CENTER-455, 400), (450, 70)), manager=self.manager, placeholder_text='Shared playlist id')
        self.token_input = textline(relative_rect=pygame.Rect((CENTER+5, 400), (450, 70)), manager=self.manager, placeholder_text='Token')
        self.submit_button = button(relative_rect=pygame.Rect((CENTER-100, 480), (200, 50)), manager=self.manager, text='Submit')
        self.token_input.set_allowed_characters(list('0123456789abcdef'))

    async def handle(self, event):
        result = await self.handle_logout(event)
        if result['status'] == 'logged out':
            mixer.music.pause()
            return result
        
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.back_button:
                self.set_feedback_message('')
                return {"status": "logged in"}
            elif event.ui_element == self.submit_button:
                playlist_id = self.playlist_id_input.get_text()
                token = int(self.token_input.get_text(), 16)
                result = await self.client.get_shared_playlist(playlist_id, token)
                if result is None:
                    self.set_feedback_message('wrong token')
                    return {'status': 'logged in'}
                else:
                    self.set_feedback_message('ok')
                    result['status'] = 'view playlist'
                    return result
        return {'status': None}