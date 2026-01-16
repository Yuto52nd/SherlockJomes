from kivy.base import runTouchApp
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.label import Label
from kivy.properties import BooleanProperty, StringProperty, NumericProperty, ListProperty, ObjectProperty
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, RoundedRectangle
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.textinput import TextInput
import threading
import requests

# Global reference to root widget
root_widget = None

# Notification Functions
def showNotification(message, duration=3):
    if root_widget is None:
        return
    welcome_screen = root_widget.get_screen('welcomeScreen')
    notification_label = welcome_screen.ids.notificationLabel
    notification_label.text = message
    notification_label.opacity = 1

    def hideNotification(dt):
        anim = Animation(opacity=0, duration=0.5)
        anim.start(notification_label)

    Clock.schedule_once(hideNotification, duration)

# Welcome Window Functions
def disableButtons(_dt):
    if root_widget is None:
        return
    welcome_screen = root_widget.get_screen('welcomeScreen')
    create_button = welcome_screen.ids.createGameButton
    customise_button = welcome_screen.ids.customiseButton
    
    create_button.disabled = True
    customise_button.disabled = True

# Utility Functions
def checkServerStatus():
    try:
        response = requests.get('http://localhost:5000/ping')
        if response.status_code == 200 and response.json().get("message") == "pong":
            return True
    except requests.ConnectionError:
        return False
    return False

def runner():
    # This checks that the server is online
    while checkServerStatus() is False:
        pass
    try:
        response = requests.get('http://localhost:5000/ping')
        if response.status_code == 200 and response.json().get("message") == "pong":
            print("Server is alive:", response.json())
            #if this server is online then everything continues
    except requests.ConnectionError:
        Clock.schedule_once(disableButtons)
        Clock.schedule_once(lambda dt: showNotification("Unable to reach the server", duration=5))
        #if server is not online then buttons will be disabled and the user will be notified

if __name__ == '__main__':
    # Start background thread
    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    
    # Run GUI in main thread
    root_widget = Builder.load_file('221BBakerStreet.kv')
    runTouchApp(root_widget)