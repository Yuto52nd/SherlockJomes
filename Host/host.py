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

    # Settings Nav Bar Content
    if target == "video":
        settingsScreen.ids.videoSettingsOption.color = (0.749, 0.659, 0.427, 1)
        settingsScreen.ids.audioSettingsOption.color = (1, 1, 1, 1)
        settingsScreen.ids.gameplaySettingsOption.color = (1, 1, 1, 1)
        settingsScreen.ids.networkSettingsOption.color = (1, 1, 1, 1)
        settingsScreen.ids.supportSettingsOption.color = (1, 1, 1, 1)
        settingsScreen.ids.accessibilitySettingsOption.color = (1, 1, 1, 1)
    elif target == "audio":
        settingsScreen.ids.videoSettingsOption.color = (1, 1, 1, 1)
        settingsScreen.ids.audioSettingsOption.color = (0.749, 0.659, 0.427, 1)
        settingsScreen.ids.gameplaySettingsOption.color = (1, 1, 1, 1)
        settingsScreen.ids.networkSettingsOption.color = (1, 1, 1, 1)
        settingsScreen.ids.supportSettingsOption.color = (1, 1, 1, 1)
        settingsScreen.ids.accessibilitySettingsOption.color = (1, 1, 1, 1)
    elif target == "gameplay":
        settingsScreen.ids.videoSettingsOption.color = (1, 1, 1, 1)
        settingsScreen.ids.audioSettingsOption.color = (1, 1, 1, 1)
        settingsScreen.ids.gameplaySettingsOption.color = (0.749, 0.659, 0.427, 1)
        settingsScreen.ids.networkSettingsOption.color = (1, 1, 1, 1)
        settingsScreen.ids.supportSettingsOption.color = (1, 1, 1, 1)
        settingsScreen.ids.accessibilitySettingsOption.color = (1, 1, 1, 1)
    elif target == "network":
        settingsScreen.ids.videoSettingsOption.color = (1, 1, 1, 1)
        settingsScreen.ids.audioSettingsOption.color = (1, 1, 1, 1)
        settingsScreen.ids.gameplaySettingsOption.color = (1, 1, 1, 1)
        settingsScreen.ids.networkSettingsOption.color = (0.749, 0.659, 0.427, 1)
        settingsScreen.ids.supportSettingsOption.color = (1, 1, 1, 1)
        settingsScreen.ids.accessibilitySettingsOption.color = (1, 1, 1, 1)
    elif target == "support":
        settingsScreen.ids.videoSettingsOption.color = (1, 1, 1, 1)
        settingsScreen.ids.audioSettingsOption.color = (1, 1, 1, 1)
        settingsScreen.ids.gameplaySettingsOption.color = (1, 1, 1, 1)
        settingsScreen.ids.networkSettingsOption.color = (1, 1, 1, 1)
        settingsScreen.ids.supportSettingsOption.color = (0.749, 0.659, 0.427, 1)
        settingsScreen.ids.accessibilitySettingsOption.color = (1, 1, 1, 1)
    elif target == "accessibility":
        settingsScreen.ids.videoSettingsOption.color = (1, 1, 1, 1)
        settingsScreen.ids.audioSettingsOption.color = (1, 1, 1, 1)
        settingsScreen.ids.gameplaySettingsOption.color = (1, 1, 1, 1)
        settingsScreen.ids.networkSettingsOption.color = (1, 1, 1, 1)
        settingsScreen.ids.supportSettingsOption.color = (1, 1, 1, 1)
        settingsScreen.ids.accessibilitySettingsOption.color = (0.749, 0.659, 0.427, 1)
    
    # Settings View Content
    if target == "video":
        settingsScreen.ids.videoSettings.opacity = 1
        settingsScreen.ids.audioSettings.opacity = 0
        settingsScreen.ids.gameplaySettingsLabel.opacity = 0
        settingsScreen.ids.networkSettingsLabel.opacity = 0
        settingsScreen.ids.supportSettingsLabel.opacity = 0
        settingsScreen.ids.accessibilitySettingsLabel.opacity = 0
    elif target == "audio":
        settingsScreen.ids.videoSettings.opacity = 0
        settingsScreen.ids.audioSettings.opacity = 1
        settingsScreen.ids.gameplaySettingsLabel.opacity = 0
        settingsScreen.ids.networkSettingsLabel.opacity = 0
        settingsScreen.ids.supportSettingsLabel.opacity = 0
        settingsScreen.ids.accessibilitySettingsLabel.opacity = 0
    elif target == "gameplay":
        settingsScreen.ids.videoSettings.opacity = 0
        settingsScreen.ids.audioSettings.opacity = 0
        settingsScreen.ids.gameplaySettingsLabel.opacity = 1
        settingsScreen.ids.networkSettingsLabel.opacity = 0
        settingsScreen.ids.supportSettingsLabel.opacity = 0
        settingsScreen.ids.accessibilitySettingsLabel.opacity = 0
    elif target == "network":
        settingsScreen.ids.videoSettings.opacity = 0
        settingsScreen.ids.audioSettings.opacity = 0
        settingsScreen.ids.gameplaySettingsLabel.opacity = 0
        settingsScreen.ids.networkSettingsLabel.opacity = 1
        settingsScreen.ids.supportSettingsLabel.opacity = 0
        settingsScreen.ids.accessibilitySettingsLabel.opacity = 0
    elif target == "support":
        settingsScreen.ids.videoSettings.opacity = 0
        settingsScreen.ids.audioSettings.opacity = 0
        settingsScreen.ids.gameplaySettingsLabel.opacity = 0
        settingsScreen.ids.networkSettingsLabel.opacity = 0
        settingsScreen.ids.supportSettingsLabel.opacity = 1
        settingsScreen.ids.accessibilitySettingsLabel.opacity = 0
    elif target == "accessibility":
        settingsScreen.ids.videoSettings.opacity = 0
        settingsScreen.ids.audioSettings.opacity = 0
        settingsScreen.ids.gameplaySettingsLabel.opacity = 0
        settingsScreen.ids.networkSettingsLabel.opacity = 0
        settingsScreen.ids.supportSettingsLabel.opacity = 0
        settingsScreen.ids.accessibilitySettingsLabel.opacity = 1

    if target == "audio":
        getAudioDevices(screen_manager)

def toggleFullscreen(enable):
    Window.fullscreen = enable

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