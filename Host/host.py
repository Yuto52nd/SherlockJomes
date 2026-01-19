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
import sqlite3
import json
import os

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
            navOptionId = f"{category}SettingsOption"
            if category == target:
                settingsScreen.ids[navOptionId].color = (0.749, 0.659, 0.427, 1)
            else:
                settingsScreen.ids[navOptionId].color = (1, 1, 1, 1)
        except KeyError:
            pass # Handle potential missing IDs gracefully

        # Update Content Visibility and Interactivity
        try:
            contentId = f"{category}Settings"
            widget = settingsScreen.ids[contentId]
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

    # Load and apply settings for the target category
    if target == "video":
        fullscreen = grabSettings('video')
        print(f"Loading video settings: fullscreen={fullscreen}")
        try:
            videoWidget = settingsScreen.ids.get('videoSettings')
            if videoWidget:
                print(f"Found video widget with {len(videoWidget.children)} children")
                # The toggle is nested: BoxLayout -> inner BoxLayout -> ToggleButton
                toggleBox = videoWidget.children[-2]  # BoxLayout containing the toggle
                innerBox = toggleBox.children[0]  # Inner BoxLayout with padding
                toggle = innerBox.children[0]  # ToggleButton
                print(f"Found toggle button, current state: {toggle.state}")
                toggle.state = 'down' if fullscreen else 'normal'
                print(f"Set fullscreen toggle to: {toggle.state} (fullscreen={fullscreen})")
            else:
                print("Could not find videoSettings widget")
        except (KeyError, IndexError, AttributeError) as e:
            print(f"Error setting video settings: {e}")
            import traceback
            traceback.print_exc()
    
    elif target == "audio":
        getAudioDevices(screen_manager)
        masterVolume, musicVolume, sfxVolume, playerJoinLeaveSounds, outputDevice = grabSettings('audio')
        try:
            # Set sliders
            settingsScreen.ids.get('master_slider').value = masterVolume / 100.0
            settingsScreen.ids.get('music_slider').value = musicVolume / 100.0
            settingsScreen.ids.get('sfx_slider').value = sfxVolume / 100.0
            
            # Set output device spinner
            if outputDevice:
                spinner = settingsScreen.ids.get('audioOutputDeviceSpinner')
                if spinner and outputDevice in spinner.values:
                    spinner.text = outputDevice
            
            # Set player join/leave sounds toggle (we'll need to add ID)
            audioWidget = settingsScreen.ids.get('audioSettings')
            if audioWidget:
                # Find the toggle button for player join/leave sounds
                toggle = audioWidget.children[-4].children[0]
                toggle.state = 'down' if playerJoinLeaveSounds else 'normal'
        except (KeyError, IndexError, AttributeError) as e:
            print(f"Error setting audio settings: {e}")
    
    elif target == "gameplay":
        maxPlayers, autostartWhenFull, autoKickWhenInactive, lockRoomOnStart = grabSettings('gameplay')
        try:
            gameplayWidget = settingsScreen.ids.get('gameplaySettings')
            if gameplayWidget:
                # Set max players slider
                slider = gameplayWidget.children[-2]
                if hasattr(slider, 'children'):
                    slider.children[0].value = maxPlayers
                
                # Set toggles
                autostartToggle = gameplayWidget.children[-3].children[0]
                autostartToggle.state = 'down' if autostartWhenFull else 'normal'
                
                autokickToggle = gameplayWidget.children[-4].children[0]
                autokickToggle.state = 'down' if autoKickWhenInactive else 'normal'
                
                lockroomToggle = gameplayWidget.children[-5].children[0]
                lockroomToggle.state = 'down' if lockRoomOnStart else 'normal'
        except (KeyError, IndexError, AttributeError) as e:
            print(f"Error setting gameplay settings: {e}")
    
    elif target == "network":
        hostIPOverride, protocolMode, adminPassword = grabSettings('network')
        try:
            networkWidget = settingsScreen.ids.get('networkSettings')
            if networkWidget:
                # Set host IP input
                hostInput = networkWidget.children[-2].children[0]
                if hasattr(hostInput, 'text'):
                    hostInput.text = hostIPOverride
                
                protocolToggle = networkWidget.children[-3].children[0]
                protocolToggle.state = 'down' if protocolMode == 'HTTPS' else 'normal'
                
                passwordInput = networkWidget.children[-4].children[0]
                if hasattr(passwordInput, 'text'):
                    passwordInput.text = adminPassword
        except (KeyError, IndexError, AttributeError) as e:
            print(f"Error setting network settings: {e}")
    
    elif target == "accessibility":
        font, subtitles, visualSoundIndicators = grabSettings('accessibility')
        print(f"Loading accessibility settings: font={font}, subtitles={subtitles}, visualSoundIndicators={visualSoundIndicators}")
        try:
            accessibilityWidget = settingsScreen.ids.get('accessibilitySettings')
            if accessibilityWidget:
                fontBox = accessibilityWidget.children[-2]
                fontSpinner = fontBox.children[0]
                if hasattr(fontSpinner, 'text') and font:
                    fontSpinner.text = font
                
                subtitlesBox = accessibilityWidget.children[-3]
                subtitlesToggleBox = subtitlesBox.children[0]
                subtitlesToggle = subtitlesToggleBox.children[0]
                subtitlesToggle.state = 'down' if subtitles else 'normal'
                print(f"Set subtitles to: {subtitles} (state: {subtitlesToggle.state})")
                
                visualBox = accessibilityWidget.children[-4]
                visualToggleBox = visualBox.children[0]
                visualToggle = visualToggleBox.children[0]
                visualToggle.state = 'down' if visualSoundIndicators else 'normal'
                print(f"Set visual sound indicators to: {visualSoundIndicators} (state: {visualToggle.state})")
        except (KeyError, IndexError, AttributeError) as e:
            print(f"Error setting accessibility settings: {e}")

def adjustVolume(target, percent):
    # Convert slider value (0.0-1.0) to integer (0-100)
    volumeValue = int(percent * 100)
    
    if target == "master":
        setSetting('masterVolume', volumeValue)
        _endpoint_volume.SetMasterVolumeLevelScalar(float(percent), None)
    elif target == "music":
        setSetting('musicVolume', volumeValue)
    elif target == "sfx":
        setSetting('sfxVolume', volumeValue)

def setSetting(target, value):
    settingsPath = os.path.join(os.path.dirname(__file__), 'settings.json')
    settings = {}
    
    # Load existing settings
    try:
        if os.path.exists(settingsPath):
            with open(settingsPath, 'r') as f:
                settings = json.load(f)
    except Exception as e:
        print(f"Error loading settings in setSetting: {e}")
    
    # Update the target setting
    settings[target] = value
    
    # Save back to file
    try:
        with open(settingsPath, 'w') as f:
            json.dump(settings, f, indent=2)
        print(f"Setting '{target}' updated to: {value}")
    except Exception as e:
        print(f"Error saving settings: {e}")

def saveSettings(settingsDict):
    settingsPath = os.path.join(os.path.dirname(__file__), 'settings.json')
    try:
        with open(settingsPath, 'w') as f:
            json.dump(settingsDict, f, indent=2)
        print("Settings saved successfully")
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False

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

def checkDatabaseIntegrity():
    print("Checking database integrity...")
    conn = sqlite3.connect('221BBakerStreet.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA integrity_check")
    result = cursor.fetchone()
    if result[0] == 'ok':
        print("Database integrity check passed.")
    else:
        print("Database integrity check failed.")
    conn.close()

def toggleFullscreen(enable):
    """Toggle fullscreen mode using desktop resolution"""
    if enable:
        Window.fullscreen = 'auto'  # Use desktop resolution
    else:
        Window.fullscreen = False  # Windowed mode

def grabSettings(section):
    settingsPath = os.path.join(os.path.dirname(__file__), 'settings.json')
    
    with open(settingsPath, 'r') as f:
        settings = json.load(f)
    
    if section == 'video':
        return settings['fullscreen']
    elif section == 'audio':
        return settings['masterVolume'], settings['musicVolume'], settings['sfxVolume'], settings['playerJoinLeaveSounds'], settings['outputDevice']
    elif section == 'gameplay':
        return settings['maxPlayers'], settings['autostartWhenFull'], settings['autoKickWhenInactive'], settings['lockRoomOnStart']
    elif section == 'network':
        return settings['hostIPOverride'], settings['protocolMode'], settings['adminPassword']
    elif section == 'accessibility':
        return settings['font'], settings['subtitles'], settings['visualSoundIndicators']
    else:
        return settings

def runner():
    # Check if fullscreen is set
    fullscreen = grabSettings('video')
    if fullscreen:
        toggleFullscreen(enable=True)
    # This checks that the server is online
    checkServerStatus()

if __name__ == '__main__':
    # Start background thread
    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    
    # Run GUI in main thread
    root_widget = Builder.load_file('221BBakerStreet.kv')
    runTouchApp(root_widget)