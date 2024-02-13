from kivy.config import Config

# Set the default window size (width x height)
Config.set('graphics', 'width', '1024')
Config.set('graphics', 'height', '600')

import os
import requests
import cv2
import numpy as np
from kivy.animation import Animation
from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.clock import Clock
from spotipy.oauth2 import SpotifyOAuth
import spotipy

# Spotify API Credentials
SPOTIPY_CLIENT_ID = None
SPOTIPY_CLIENT_SECRET = None # Oops didn't mean to leave that in
SPOTIPY_REDIRECT_URI = 'http://localhost/'
SCOPE = 'user-read-playback-state,user-modify-playback-state,user-library-read,user-library-modify'

class IconButton(ButtonBehavior, Image):
    pass

class SpotifyController(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 75
        self.spacing = 50
        self.repeat_state = 'off'
        self.current_track_liked = False
        with self.canvas.before:
                self.bg_color = Color(rgba=(0, 0, 0, 1))  # White background initially
                self.rect = Rectangle(size=Window.size, pos=self.pos)

        # Initialize Spotify client
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                                            client_secret=SPOTIPY_CLIENT_SECRET,
                                                            redirect_uri=SPOTIPY_REDIRECT_URI,
                                                            scope=SCOPE))
        # Make sure the rectangle covers the whole window and moves with it
        def update_rect(instance, value):
            instance.rect.pos = instance.pos
            instance.rect.size = Window.size

        self.bind(pos=update_rect, size=update_rect)
        # Track Info Layout
        self.track_info_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.3))
        self.add_widget(self.track_info_layout)

        # Album Art
        self.album_art = AsyncImage(source='')
        self.track_info_layout.add_widget(self.album_art)

        # Track Details (Artist & Title)
        self.track_details = BoxLayout(orientation='vertical')
        self.track_info_layout.add_widget(self.track_details)

        self.artist_label = Label(text_size = (750, 505), halign = 'left', valign = 'bottom', font_size='20sp')
        self.track_details.add_widget(self.artist_label)

        self.title_label = Label(text_size = (750, 50), halign = 'left', valign = 'bottom',font_size='24sp', bold=True)
        self.track_details.add_widget(self.title_label)

        # Control Buttons using PNG Icons
        self.controls_layout = BoxLayout(size_hint=(1, 0.2), spacing=65)
        self.add_widget(self.controls_layout)

        # Previous Track Button
        self.prev_track_button = IconButton(source=self.get_icon_path('previous'))
        self.prev_track_button.bind(on_press=self.prev_track)
        self.controls_layout.add_widget(self.prev_track_button)

        # Play/Pause Button
        self.play_pause_button = IconButton(source=self.get_icon_path('pause'))
        self.play_pause_button.bind(on_press=self.toggle_playback)
        self.controls_layout.add_widget(self.play_pause_button)

        # Next Track Button
        self.next_track_button = IconButton(source=self.get_icon_path('next'))
        self.next_track_button.bind(on_press=self.next_track)
        self.controls_layout.add_widget(self.next_track_button)

        # Like Button
        self.like_button = IconButton(source=self.get_icon_path('like'))
        self.like_button.bind(on_press=self.toggle_like)
        self.controls_layout.add_widget(self.like_button)

        # Repeat Button
        self.repeat_button = IconButton(source=self.get_icon_path('arrow-to-end'))
        self.repeat_button.bind(on_press=self.cycle_repeat_state)
        self.controls_layout.add_widget(self.repeat_button)

        # Shuffle Button
        self.shuffle_button = IconButton(source=self.get_icon_path('shuffle'))
        self.shuffle_button.bind(on_press=self.toggle_shuffle)
        self.controls_layout.add_widget(self.shuffle_button)

        # Periodic Update Function
        Clock.schedule_interval(self.update_track_info, 1)
        self.fetch_current_playback_state()
    
    def fetch_current_playback_state(self):
        # Fetch the current playback state from Spotify
        playback_info = self.sp.current_playback()

        if playback_info:
            # Set shuffle state
            self.is_shuffle = playback_info['shuffle_state']
            self.update_shuffle_button_icon()  # Assume you have this method implemented

            # Set repeat state
            self.repeat_state = playback_info['repeat_state']
            self.update_repeat_button_icon()  # Assume you have this method implemented

            # Set play/pause state
            self.is_playing = playback_info['is_playing']
            self.update_play_pause_button_icon()  # Assume you have this method implemented

    def update_shuffle_button_icon(self):
        # Update shuffle button icon based on current state
        if self.is_shuffle:
            self.shuffle_button.source = self.get_icon_path('shuffle')
        else:
            self.shuffle_button.source = self.get_icon_path('no_shuffle')

    def update_repeat_button_icon(self):
        # Update repeat button icon based on current state
        if self.repeat_state == 'off':
            self.repeat_button.source = self.get_icon_path('arrow-to-end')
        elif self.repeat_state == 'context':
            self.repeat_button.source = self.get_icon_path('arrows-repeat-all')
        elif self.repeat_state == 'track':
            self.repeat_button.source = self.get_icon_path('arrows-repeat-1')

    def update_play_pause_button_icon(self):
        # Update play/pause button icon based on current state
        if self.is_playing:
            self.play_pause_button.source = self.get_icon_path('pause')
        else:
            self.play_pause_button.source = self.get_icon_path('play.')
    
    def get_icon_path(self, icon_name):
        return os.path.join('ICONS', 'PNG', f'{icon_name}.png')

    def toggle_playback(self, instance):
        # Toggle playback code here
        playback = self.sp.current_playback()
        if playback and playback['is_playing']:
            self.sp.pause_playback()
            self.play_pause_button.source = self.get_icon_path("play")
        else:
            self.sp.start_playback()
            self.play_pause_button.source = self.get_icon_path("pause")

    def next_track(self, instance):
        self.sp.next_track()

    def prev_track(self, instance):
        self.sp.previous_track()

    def toggle_like(self, instance):
        # This method would require the use of the Spotify Web API to check if the current track is liked and to like/unlike it.
        # Spotify Web API doesn't provide a direct 'like' endpoint; you would need to manage this through your application logic.
        pass
    
    def toggle_shuffle(self, instance):
            # Check the current shuffle state
            current_playback = self.sp.current_playback()
            if current_playback is not None:
                current_shuffle_state = current_playback['shuffle_state']
                # Toggle the shuffle state
                new_shuffle_state = not current_shuffle_state

                # Make the API call to toggle shuffle
                self.sp.shuffle(new_shuffle_state)

                # Update the button icon based on the new state
                if new_shuffle_state:
                    self.shuffle_button.source = self.get_icon_path('shuffle')  # Change to your shuffled icon
                else:
                    self.shuffle_button.source = self.get_icon_path('no_shuffle')  # Change to your unshuffled icon

    def update_track_info(self, dt):
        # Existing code to update the track info...
        track = self.sp.current_user_playing_track()
        if track:
            self.current_track_id = track['item']['id']
            self.is_playing = track['is_playing']
            track = self.sp.current_user_playing_track()
            self.album_art.source = track['item']['album']['images'][0]['url']
            self.artist_label.text = track['item']['artists'][0]['name']
            self.title_label.text = track['item']['name']

            # Download the album cover art
            album_art_url = track['item']['album']['images'][0]['url']
            album_art_path = self.download_album_art(album_art_url)

            # Update the background color to the average color of the album art
            if album_art_path:
                self.animate_background_color(album_art_path, duration=0.5)  # Specify the duration for the animation
            self.check_if_song_is_liked(self.current_track_id)

    def download_album_art(self, url):
        # Download the image and save it locally
        response = requests.get(url)
        if response.status_code == 200:
            album_art_path = 'album_art.jpg'  # You may want to manage file names to avoid collisions
            with open(album_art_path, 'wb') as f:
                f.write(response.content)
            return album_art_path
        return None

    def get_average_color(self, img_path):
        # Calculate the average color of an image
        img = cv2.imread(img_path)
        avg_color_per_row = np.median(img, axis=0)
        avg_color = np.median(avg_color_per_row, axis=0)
        return avg_color.astype(int)

    def animate_background_color(self, img_path, duration):
        # Animate the background color change to the average color of the album art
        avg_color = self.get_average_color(img_path)
        # Convert color from BGR to RGB and normalize to 0-1 range
        min_val = 64
        max_val = 195
        avg_color = np.clip(avg_color, min_val, max_val)

        avg_color = avg_color[::-1] / 255.0
        # Add the alpha value to the color
        avg_color_with_alpha = (*avg_color, 1)
        # Animate the Color's rgba property
        animation = Animation(rgba=avg_color_with_alpha, duration=duration, transition='linear')
        animation.start(self.bg_color)
    
    def cycle_repeat_state(self, instance):
        # Cycle through the repeat states
        if self.repeat_state == 'off':
            self.repeat_state = 'context'
            new_icon = 'arrows-repeat-all'  # Icon for 'context' state
        elif self.repeat_state == 'context':
            self.repeat_state = 'track'
            new_icon = 'arrows-repeat-1'  # Icon for 'track' state
        else:
            self.repeat_state = 'off'
            new_icon = 'arrow-to-end'  # Icon for 'off' state

        # Update the repeat state on Spotify
        self.sp.repeat(self.repeat_state)

        # Update the repeat button icon to reflect the current state
        self.repeat_button.source = self.get_icon_path(new_icon)

    def check_if_song_is_liked(self, track_id):
        # Check if the song is in the user's liked songs
        results = self.sp.current_user_saved_tracks_contains([track_id])
        if results[0]:  # If the first (and only) track is liked
            self.like_button.source = self.get_icon_path('liked')  # Path to your liked icon
        else:
            self.like_button.source = self.get_icon_path('like')  # Path to your like icon

    def toggle_like(self, instance):
        # Toggle the like status of the current song
        liked = self.sp.current_user_saved_tracks_contains([self.current_track_id])[0]
        if liked:
            self.sp.current_user_saved_tracks_delete([self.current_track_id])
            self.like_button.source = self.get_icon_path('like')
        else:
            self.sp.current_user_saved_tracks_add([self.current_track_id])
            self.like_button.source = self.get_icon_path('liked') 
        self.check_if_song_is_liked(self.current_track_id)

class SpotifyApp(App):
    def build(self):
        return SpotifyController()

if __name__ == '__main__':
    SpotifyApp().run()
