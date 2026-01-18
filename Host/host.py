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
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities

_device = AudioUtilities.GetSpeakers()
_endpoint_volume = _device.EndpointVolume

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
currentScreen = "welcomeScreen"

# Switch Screen Functions
# Switch Screen Functions
def switchScreen(screenName, screen_manager=None):
    manager = screen_manager if screen_manager is not None else root_widget
    if manager is None:
        return
    manager.current = screenName
    global currentScreen
    currentScreen = screenName

    print("Switched to screen: " + screenName)

    if screenName == "settingsScreen":
        toggleSettingsViews(None, "video", manager)
        print("Toggled settings views to video")

# Notification Functions
def displayNotification(message, duration=3):
    if root_widget is None:
        return
    screen = root_widget.get_screen(currentScreen)
    notification_label = screen.ids.notificationLabel
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

# Settings Window Functions
def toggleSettingsViews(_dt, target, screen_manager=None):
    manager = screen_manager if screen_manager is not None else root_widget
    
    if manager is None:
        return
    settingsScreen = manager.get_screen('settingsScreen')

    # Define all settings categories
    categories = ["video", "audio", "gameplay", "network", "support", "accessibility"]

    for category in categories:
        # Update Nav Bar Colors
        try:
            nav_option_id = f"{category}SettingsOption"
            if category == target:
                settingsScreen.ids[nav_option_id].color = (0.749, 0.659, 0.427, 1)
            else:
                settingsScreen.ids[nav_option_id].color = (1, 1, 1, 1)
        except KeyError:
            pass # Handle potential missing IDs gracefully

        # Update Content Visibility and Interactivity
        try:
            content_id = f"{category}Settings"
            widget = settingsScreen.ids[content_id]
            if category == target:
                widget.opacity = 1
                widget.disabled = False
                widget.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
            else:
                widget.opacity = 0
                widget.disabled = True
                widget.pos_hint = {'center_x': 10, 'center_y': 10} # Move off-screen
        except KeyError:
            pass # Handle potential missing IDs gracefully

    if target == "audio":
        getAudioDevices(screen_manager)

def toggleFullscreen(enable):
    Window.fullscreen = enable

def changeMasterVolume(percent):
    _endpoint_volume.SetMasterVolumeLevelScalar(float(percent), None)

def exportLogs():
    print("Exporting logs...")

def checkForUpdates():
    print("Checking for updates...")

def resetSettings():
    print("Resetting settings...")

def getAudioDevices(screen_manager=None):
    try:
        import sounddevice as sd
        allDevices = sd.query_devices()
        outputDevices = []
        defaultName = 'Default Device'
        
        defaultIdx = sd.default.device[1]
        if defaultIdx is not None and defaultIdx >= 0 and defaultIdx < len(allDevices):
            defaultFullInfo = allDevices[defaultIdx]
            defaultName = defaultFullInfo['name']

        wasapiIndex = None
        for i, api in enumerate(sd.query_hostapis()):
            if 'WASAPI' in api['name']:
                wasapiIndex = i
                break
        
        seenNames = set()
        
        if wasapiIndex is not None:
             for d in allDevices:
                if d['hostapi'] == wasapiIndex and d['max_output_channels'] > 0:
                    name = d['name']
                    if name not in seenNames:
                        outputDevices.append(name)
                        seenNames.add(name)
        if not outputDevices:
            for d in allDevices:
                if d['max_output_channels'] > 0:
                    name = d['name']
                    if name not in seenNames:
                        outputDevices.append(name)
                        seenNames.add(name)

        if not outputDevices:
             outputDevices = ['Default Device']

    except Exception as e:
        print(f"Error fetching audio devices: {e}")
        outputDevices = ['Default Device (Error)']
        defaultName = outputDevices[0]

    manager = screen_manager if screen_manager is not None else root_widget
    
    if manager is None:
        return
    settingsScreen = manager.get_screen('settingsScreen')

    settingsScreen.ids.audioOutputDeviceSpinner.values = outputDevices
    match_found = False
    if defaultName in outputDevices:
        settingsScreen.ids.audioOutputDeviceSpinner.text = defaultName
        match_found = True
    else:
        for option in outputDevices:
            if option.startswith(defaultName) or defaultName.startswith(option):
                settingsScreen.ids.audioOutputDeviceSpinner.text = option
                match_found = True
                break
    
    if not match_found and output_devices:
        settingsScreen.ids.audioOutputDeviceSpinner.text = output_devices[0]

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