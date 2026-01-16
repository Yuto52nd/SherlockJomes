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

# Classes
class HoverButton(Button):
    def __init__(self, **kwargs):
        super(HoverButton, self).__init__(**kwargs)
        Window.bind(mouse_pos=self.on_mouse_pos)
        self.register_event_type('on_enter')
        self.register_event_type('on_leave')
        self._is_hovering = False
    
    def on_mouse_pos(self, *args):
        if not self.get_root_window():
            return
        pos = args[1]
        if self.collide_point(*self.to_widget(*pos)):
            if not self._is_hovering:
                self._is_hovering = True
                self.dispatch('on_enter')
        else:
            if self._is_hovering:
                self._is_hovering = False
                self.dispatch('on_leave')
    
    def on_enter(self):
        pass
    
    def on_leave(self):
        pass

#Global Variables
serverStatus = False

# Notification Functions
def displayNotification(message, duration=3):
    if root_widget is None:
        return
    welcome_screen = root_widget.get_screen('welcomeScreen')
    notification_label = welcome_screen.ids.notificationLabel
    notification_label.text = message
    notification_label.opacity = 0
    
    # Fade in animation
    anim = Animation(opacity=1, duration=0.3)
    anim.start(notification_label)

    def hideNotification(dt):
        anim = Animation(opacity=0, duration=0.5)
        anim.start(notification_label)

    Clock.schedule_once(hideNotification, duration)

# Welcome Window Functions
def toggleWelcomeButtons(_dt, enable=True):
    if root_widget is None:
        return
    welcomeScreen = root_widget.get_screen('welcomeScreen')
    createButton = welcomeScreen.ids.createGameButton
    
    createButton.disabled = not enable

# Utility Functions
def checkServerStatus():
    global serverStatus
    try:
        response = requests.get('http://localhost:5000/ping')
        if response.status_code == 200 and response.json().get("message") == "pong":
            Clock.schedule_once(lambda dt: toggleWelcomeButtons(dt, enable=True))
            if not serverStatus:
                displayNotification("Server is online", duration=3)
            serverStatus = True
            return True
    except requests.ConnectionError:
        Clock.schedule_once(lambda dt: toggleWelcomeButtons(dt, enable=False))
        Clock.schedule_once(lambda dt: displayNotification("Unable to reach the server", duration=5))
        Clock.schedule_once(lambda dt: checkServerStatus(), 60)
        serverStatus = False
        return False
    return False

def runner():
    # This checks that the server is online
    checkServerStatus()

if __name__ == '__main__':
    # Start background thread
    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    
    # Run GUI in main thread
    root_widget = Builder.load_file('221BBakerStreet.kv')
    runTouchApp(root_widget)