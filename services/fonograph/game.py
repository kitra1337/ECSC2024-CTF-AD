#!/usr/bin/env python3
import sys
sys.path.insert(0,'')

from modules.interfaces import *
from enum import Enum

pygame.init()
pygame.display.set_caption('fonograph')
clock = pygame.time.Clock()
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))

Status = Enum('Status', ['LOGGED_OUT', 'SHOW_PLAYLISTS', 'ADD_PLAYLIST', 'SHOW_PLAYLIST_SONGS', 'PLAY_SONG', 'VIEW_SHARED_PLAYLIST'])

logged_out_interface = LoggedOutInterface(SCREEN)

show_playlists_interface = ShowPlaylistsInterface(SCREEN)
add_playlist_interface = AddPlaylistInterface(SCREEN)
show_playlist_songs_interface = ShowPlaylistSongsInterface(SCREEN)
play_song_interface = PlaySongInterface(SCREEN)
view_shared_playlist_interface = ViewSharedPlaylistInterface(SCREEN)

loggedin_interfaces = [show_playlists_interface, add_playlist_interface, show_playlist_songs_interface, play_song_interface, view_shared_playlist_interface]

all_interfaces = [logged_out_interface] + loggedin_interfaces

async def main():
    status = Status.LOGGED_OUT
    old_status = None
    old_interface = None
    is_running = True

    while is_running:
        time_delta = clock.tick(FPS)/1000.0

        if status != old_status:
            if status == Status.LOGGED_OUT:
                for interface_ in all_interfaces:
                    interface_.reset_client()
                interface = logged_out_interface

            elif status == Status.SHOW_PLAYLISTS:
                for interface_ in loggedin_interfaces:
                    interface_.set_client(logged_out_interface.client)
                interface = show_playlists_interface
                await interface.get_all_playlists()

            elif status == Status.ADD_PLAYLIST:
                interface = add_playlist_interface
                await interface.get_songs()
                await interface.get_pictures()
            
            elif status == Status.SHOW_PLAYLIST_SONGS:
                interface = show_playlist_songs_interface
                
            elif status == Status.PLAY_SONG:
                interface = play_song_interface
            
            elif status == Status.VIEW_SHARED_PLAYLIST:
                interface = view_shared_playlist_interface
        
            if old_interface:
                interface.set_feedback_message(old_interface.feedback_message)
        
        old_status = status
        old_interface = interface

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False

            result = await interface.handle(event)
            if result["status"] == 'logged out':
                status = Status.LOGGED_OUT
            elif result["status"] == 'logged in':
                status = Status.SHOW_PLAYLISTS
            elif result["status"] == 'view playlist':
                status = Status.SHOW_PLAYLIST_SONGS
                client_logger.info(f'{result = }')
                if 'from' not in result:
                    show_playlist_songs_interface.set_playlist(result)
            elif result["status"] == 'add playlist':
                status = Status.ADD_PLAYLIST
            elif result["status"] == 'play song':
                client_logger.info(f'{result = }')
                status = Status.PLAY_SONG
                play_song_interface.set_song(result['song'])
            elif result["status"] == 'view shared playlist':
                status = Status.VIEW_SHARED_PLAYLIST
            interface.manager.process_events(event)

        interface.manager.update(time_delta)
        interface.render()
        pygame.display.update()

if __name__ == '__main__':
    asyncio.run(main())
