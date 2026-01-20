from kivy.base import runTouchApp
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.label import Label
from kivy.properties import BooleanProperty, StringProperty, NumericProperty, ListProperty, ObjectProperty
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, RoundedRectangle, Rectangle, PushMatrix, PopMatrix, Rotate
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.textinput import TextInput
from kivy.core.text import LabelBase, DEFAULT_FONT
import threading
import requests
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities
import sqlite3
import json
import os
import shutil
from datetime import datetime

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

    if screenName == "settingsScreen":
        toggleSettingsViews(None, "video", manager)
    elif screenName == "gameScreen":
        initializeGameMap(manager)

# Notification Functions
def displayNotification(message, duration=3):
    global root_widget
    
    # Try to get root widget if not set
    if root_widget is None:
        # Try to get from Window's children
        if Window.children:
            root_widget = Window.children[0]
        else:
            log("Cannot display notification: No root widget available")
            return
    
    try:
        screen = root_widget.get_screen(currentScreen)
        notificationLabel = screen.ids.notificationLabel
        notificationLabel.text = message
        notificationLabel.opacity = 0
        
        # Update size based on text
        notificationLabel.texture_update()
        notificationLabel.size = (max(notificationLabel.texture_size[0] + 40, 200), 50)
        
        # Fade in animation
        anim = Animation(opacity=1, duration=0.3)
        anim.start(notificationLabel)

        def hideNotification(dt):
            anim = Animation(opacity=0, duration=0.5)
            anim.start(notificationLabel)

        Clock.schedule_once(hideNotification, duration)
    except Exception as e:
        log(f"Error displaying notification: {e}")

# Welcome Window Functions
def toggleWelcomeButtons(_dt, enable=True):
    if root_widget is None:
        return
    welcomeScreen = root_widget.get_screen('welcomeScreen')
    createButton = welcomeScreen.ids.createGameButton
    
    createButton.disabled = not enable

# Game Screen Functions
def initializeGameMap(screen_manager=None, mapName='original.json'):
    manager = screen_manager if screen_manager is not None else root_widget
    if manager is None:
        return
    
    gameScreen = manager.get_screen('gameScreen')
    mapGrid = gameScreen.ids.mapGrid
    
    if len(mapGrid.children) > 0:
        return
    
    colorMap = {
        0: (0.918, 0.796, 0.322, 1),    # Yellow
        1: (0.8, 0.2, 0.2, 1),          # Red
        2: (0.2, 0.4, 0.8, 1),          # Blue
        3: (0.2, 0.7, 0.3, 1),          # Green
        4: (0.6, 0.3, 0.8, 1),          # Purple
        5: (1.0, 0.5, 0.0, 1),          # Orange
        6: (0.0, 0.8, 0.8, 1),          # Cyan
        7: (0.9, 0.4, 0.6, 1),          # Pink
        8: (0.5, 0.3, 0.1, 1),          # Brown
        9: (0.4, 0.4, 0.4, 1),          # Dark Gray
        10: (0.2, 0.6, 0.4, 1),         # Teal
        11: (0.7, 0.0, 0.3, 1),         # Maroon
        12: (0.0, 0.2, 0.5, 1),         # Navy
        13: (0.5, 0.7, 0.2, 1),         # Lime
        14: (0.8, 0.6, 0.2, 1),         # Gold
        15: (0.3, 0.0, 0.5, 1),         # Indigo
        16 : (0.1, 0.1, 0.1, 1),         # Black
    }
    
    try:
        mapPath = os.path.join(os.path.dirname(__file__), 'Maps', mapName)
        log(f"Attempting to load map from: {mapPath}")
        with open(mapPath, 'r') as f:
            mapDataRaw = json.load(f)
        
        # Extract grid and image mappings
        if isinstance(mapDataRaw, dict) and 'grid' in mapDataRaw:
            mapData = mapDataRaw['grid']
            imageMappings = mapDataRaw.get('images', {})
        else:
            mapData = mapDataRaw
            imageMappings = {}
            
        log(f"Loaded map: {mapName}")
        log(f"Map data type: {type(mapData)}, Length: {len(mapData) if isinstance(mapData, list) else 'N/A'}")
        if isinstance(mapData, list) and len(mapData) > 0:
            log(f"First row sample: {mapData[0][:5] if isinstance(mapData[0], list) else mapData[0]}")
        if imageMappings:
            log(f"Image mappings: {imageMappings}")
    except Exception as e:
        log(f"Error loading map {mapName}: {e}")
        mapData = [[0 for _ in range(24)] for _ in range(24)]
        imageMappings = {}
    
    if imageMappings:
        for tileValueStr, imagePath in imageMappings.items():
            tileValue = int(tileValueStr)
            fullImagePath = os.path.join(os.path.dirname(__file__), imagePath)
            
            if os.path.exists(fullImagePath):
                visited = [[False for _ in range(24)] for _ in range(24)]
                blocks = []
                
                # Special handling for tile 16 (lampposts) - find linear blocks only
                if tileValue == 16:
                    for row in range(24):
                        for col in range(24):
                            try:
                                if mapData[row][col] == tileValue and not visited[row][col]:
                                    # Check if this starts a horizontal or vertical line
                                    block = [(row, col)]
                                    visited[row][col] = True
                                    
                                    # Try horizontal extension
                                    horizontalBlock = block.copy()
                                    c = col + 1
                                    while c < 24 and mapData[row][c] == tileValue:
                                        horizontalBlock.append((row, c))
                                        visited[row][c] = True
                                        c += 1
                                    
                                    # Try vertical extension
                                    verticalBlock = [(row, col)]
                                    r = row + 1
                                    while r < 24 and mapData[r][col] == tileValue:
                                        verticalBlock.append((r, col))
                                        r += 1
                                    
                                    # Use whichever extension is longer
                                    if len(horizontalBlock) > len(verticalBlock):
                                        blocks.append(horizontalBlock)
                                    else:
                                        # Mark vertical cells as visited
                                        for vr, vc in verticalBlock:
                                            visited[vr][vc] = True
                                        blocks.append(verticalBlock)
                            except (IndexError, KeyError, TypeError):
                                pass
                else:
                    # For non-lamppost tiles, use standard flood fill
                    for row in range(24):
                        for col in range(24):
                            try:
                                if mapData[row][col] == tileValue and not visited[row][col]:
                                    block = []
                                    queue = [(row, col)]
                                    visited[row][col] = True
                                    
                                    while queue:
                                        r, c = queue.pop(0)
                                        block.append((r, c))
                                        
                                        # Check 4 adjacent cells (up, down, left, right)
                                        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                                            nr, nc = r + dr, c + dc
                                            if (0 <= nr < 24 and 0 <= nc < 24 and 
                                                not visited[nr][nc] and 
                                                mapData[nr][nc] == tileValue):
                                                visited[nr][nc] = True
                                                queue.append((nr, nc))
                                    
                                    blocks.append(block)
                            except (IndexError, KeyError, TypeError):
                                pass
                
                # Process each block separately
                for blockIdx, block in enumerate(blocks):
                    minRow = min(r for r, c in block)
                    maxRow = max(r for r, c in block)
                    minCol = min(c for r, c in block)
                    maxCol = max(c for r, c in block)
                    
                    # Determine orientation: horizontal if width > height, vertical otherwise
                    width = maxCol - minCol + 1
                    height = maxRow - minRow + 1
                    isHorizontal = width > height
                    
                    # Only rotate if it's tile 16 (lamppost) and horizontal
                    shouldRotate = (tileValue == 16 and isHorizontal)
                    
                    # Add image to canvas.before of mapGrid with rotation if needed
                    if shouldRotate:
                        with mapGrid.canvas.before:
                            Color(1, 1, 1, 1)
                            PushMatrix()
                            rotateInstr = Rotate(angle=90, origin=(0, 0))
                            imageRect = Rectangle(source=fullImagePath)
                            PopMatrix()
                        
                        def updateImagePos(instance, value, rect=imageRect, rot=rotateInstr,
                                          mr=minRow, Mr=maxRow, mc=minCol, Mc=maxCol):
                            gridWidth = instance.width
                            gridHeight = instance.height
                            squareSize = min(gridWidth / 24, gridHeight / 24)
                            
                            x = instance.x + mc * squareSize
                            y = instance.y + (23 - Mr) * squareSize
                            width = (Mc - mc + 1) * squareSize
                            height = (Mr - mr + 1) * squareSize
                            
                            # Calculate center for rotation
                            centerX = x + width / 2
                            centerY = y + height / 2
                            
                            # Set rotation
                            rot.angle = 90
                            rot.origin = (centerX, centerY)
                            
                            # Position: shift to account for rotation around center
                            # When rotated 90°, the width becomes height and vice versa
                            rect.pos = (centerX - height/2, centerY - width/2)
                            rect.size = (height, width)
                        
                        log(f"Added HORIZONTAL lamppost block {blockIdx+1} at rows {minRow}-{maxRow}, cols {minCol}-{maxCol} (w={width}, h={height})")
                    else:
                        with mapGrid.canvas.before:
                            Color(1, 1, 1, 1)
                            imageRect = Rectangle(source=fullImagePath)
                        
                        def updateImagePos(instance, value, rect=imageRect, 
                                          mr=minRow, Mr=maxRow, mc=minCol, Mc=maxCol):
                            gridWidth = instance.width
                            gridHeight = instance.height
                            squareSize = min(gridWidth / 24, gridHeight / 24)
                            
                            x = instance.x + mc * squareSize
                            y = instance.y + (23 - Mr) * squareSize
                            width = (Mc - mc + 1) * squareSize
                            height = (Mr - mr + 1) * squareSize
                            
                            rect.pos = (x, y)
                            rect.size = (width, height)
                        
                        log(f"Added {'horizontal' if isHorizontal else 'vertical'} image {imagePath} for tile value {tileValue} block {blockIdx+1} at rows {minRow}-{maxRow}, cols {minCol}-{maxCol}")
                    
                    mapGrid.bind(pos=updateImagePos, size=updateImagePos)
                    Clock.schedule_once(lambda dt: updateImagePos(mapGrid, None), 0.1)
                    
                    log(f"Added {'horizontal' if isHorizontal else 'vertical'} image {imagePath} for tile value {tileValue} block {blockIdx+1} at rows {minRow}-{maxRow}, cols {minCol}-{maxCol}")
            else:
                log(f"Image not found: {fullImagePath}")
    
    colorCount = {}
    for row in range(24):
        for col in range(24):
            try:
                tileValue = mapData[row][col]
            except (IndexError, KeyError, TypeError):
                tileValue = 0
            
            colorCount[tileValue] = colorCount.get(tileValue, 0) + 1
            
            # Make tiles with images transparent, others use their color
            if str(tileValue) in imageMappings:
                squareColor = (0, 0, 0, 0)  # Transparent
            else:
                squareColor = colorMap.get(tileValue, (0.8, 0.2, 0.2, 1))  # Default to red
            
            square = Button(
                background_normal='',
                background_color=squareColor,
                border=(1, 1, 1, 1)
            )
            
            # Only add border for yellow squares (value 0)
            if tileValue == 0:
                from kivy.graphics import Line
                with square.canvas.after:
                    Color(0.3, 0.3, 0.3, 1)
                    square.border_line = Line(rectangle=(square.x, square.y, square.width, square.height), width=1.5)
                
                def updateRect(instance, value):
                    instance.border_line.rectangle = (instance.x, instance.y, instance.width, instance.height)
                
                square.bind(pos=updateRect, size=updateRect)
            
            mapGrid.add_widget(square)
    
    log(f"Initialized {24*24} map squares from {mapName}")
    log(f"Color distribution: {colorCount}")

# Settings Window Functions
def toggleSettingsViews(_dt, target, screen_manager=None):
    manager = screen_manager if screen_manager is not None else root_widget
    
    if manager is None:
        return
    settingsScreen = manager.get_screen('settingsScreen')

    categories = ["video", "audio", "gameplay", "network", "support", "accessibility"]

    for category in categories:
        try:
            navOptionId = f"{category}SettingsOption"
            if category == target:
                settingsScreen.ids[navOptionId].color = (0.749, 0.659, 0.427, 1)
            else:
                settingsScreen.ids[navOptionId].color = (1, 1, 1, 1)
        except KeyError:
            pass

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
                widget.pos_hint = {'center_x': 10, 'center_y': 10}
        except KeyError:
            pass

    
    if target == "video":
        fullscreen = grabSettings('video')
        try:
            videoWidget = settingsScreen.ids.get('videoSettings')
            if videoWidget:
                toggleBox = videoWidget.children[-2]
                innerBox = toggleBox.children[0]
                toggle = innerBox.children[0]
                toggle.state = 'down' if fullscreen else 'normal'
            else:
                pass
        except (KeyError, IndexError, AttributeError) as e:
            pass
    
    elif target == "audio":
        getAudioDevices(screen_manager)
        masterVolume, musicVolume, sfxVolume, playerJoinLeaveSounds, outputDevice = grabSettings('audio')
        try:
            # Set sliders
            settingsScreen.ids.get('master_slider').value = masterVolume / 100.0
            settingsScreen.ids.get('music_slider').value = musicVolume / 100.0
            settingsScreen.ids.get('sfx_slider').value = sfxVolume / 100.0
            
            if outputDevice:
                spinner = settingsScreen.ids.get('audioOutputDeviceSpinner')
                if spinner and outputDevice in spinner.values:
                    spinner.text = outputDevice
            
            audioWidget = settingsScreen.ids.get('audioSettings')
            if audioWidget:
                toggle = audioWidget.children[-4].children[0]
                toggle.state = 'down' if playerJoinLeaveSounds else 'normal'
        except (KeyError, IndexError, AttributeError) as e:
            pass

    elif target == "gameplay":
        maxPlayers, autostartWhenFull, autoKickWhenInactive, lockRoomOnStart = grabSettings('gameplay')
        try:
            gameplayWidget = settingsScreen.ids.get('gameplaySettings')
            if gameplayWidget:
                slider = gameplayWidget.children[-2]
                if hasattr(slider, 'children'):
                    slider.children[0].value = maxPlayers
                
                autostartToggle = gameplayWidget.children[-3].children[0]
                autostartToggle.state = 'down' if autostartWhenFull else 'normal'
                
                autokickToggle = gameplayWidget.children[-4].children[0]
                autokickToggle.state = 'down' if autoKickWhenInactive else 'normal'
                
                lockroomToggle = gameplayWidget.children[-5].children[0]
                lockroomToggle.state = 'down' if lockRoomOnStart else 'normal'
        except (KeyError, IndexError, AttributeError) as e:
            pass

    elif target == "network":
        hostIPOverride, protocolMode, adminPassword = grabSettings('network')
        try:
            networkWidget = settingsScreen.ids.get('networkSettings')
            if networkWidget:
                hostInput = networkWidget.children[-2].children[0]
                if hasattr(hostInput, 'text'):
                    hostInput.text = hostIPOverride
                
                protocolToggle = networkWidget.children[-3].children[0]
                protocolToggle.state = 'down' if protocolMode == 'HTTPS' else 'normal'
                
                passwordInput = networkWidget.children[-4].children[0]
                if hasattr(passwordInput, 'text'):
                    passwordInput.text = adminPassword
        except (KeyError, IndexError, AttributeError) as e:
            pass

    elif target == "accessibility":
        font, subtitles, visualSoundIndicators = grabSettings('accessibility')
        try:
            # Populate font spinner with available fonts
            availableFonts = findAvailableFonts()
            fontSpinner = settingsScreen.ids.get('font_spinner')
            if fontSpinner and availableFonts:
                fontSpinner.values = availableFonts
                if font and font in availableFonts:
                    fontSpinner.text = font
                elif availableFonts:
                    fontSpinner.text = availableFonts[0]
            
            accessibilityWidget = settingsScreen.ids.get('accessibilitySettings')
            if accessibilityWidget:
                subtitlesBox = accessibilityWidget.children[-3]
                subtitlesToggleBox = subtitlesBox.children[0]
                subtitlesToggle = subtitlesToggleBox.children[0]
                subtitlesToggle.state = 'down' if subtitles else 'normal'
                
                visualBox = accessibilityWidget.children[-4]
                visualToggleBox = visualBox.children[0]
                visualToggle = visualToggleBox.children[0]
                visualToggle.state = 'down' if visualSoundIndicators else 'normal'
        except (KeyError, IndexError, AttributeError) as e:
            pass

def adjustVolume(target, percent):
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
    
    try:
        if os.path.exists(settingsPath):
            with open(settingsPath, 'r') as f:
                settings = json.load(f)
    except Exception as e:
        pass
    settings[target] = value
    
    try:
        with open(settingsPath, 'w') as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        pass

def saveSettings(settingsDict):
    settingsPath = os.path.join(os.path.dirname(__file__), 'settings.json')
    try:
        with open(settingsPath, 'w') as f:
            json.dump(settingsDict, f, indent=2)
        return True
    except Exception as e:
        pass
        return False

def exportLogs():
    log("Exporting logs...")
    try:
        logFile = os.path.join(os.path.dirname(__file__), 'host_log.txt')
        
        if not os.path.exists(logFile):
            displayNotification("No log file found to export", duration=3)
            log("Export failed: No log file found")
            return
        
        # Get user's Downloads folder
        downloadsFolder = os.path.join(os.path.expanduser('~'), 'Downloads')
        
        # Create a timestamped filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        destination = os.path.join(downloadsFolder, f'host_log_{timestamp}.txt')
        
        # Copy the file
        shutil.copy2(logFile, destination)
        
        log(f"Logs exported successfully to {destination}")
        displayNotification("Logs exported to Downloads", duration=3)
        
    except Exception as e:
        log(f"Error exporting logs: {e}")
        displayNotification("Failed to export logs", duration=3)
    
def checkForUpdates():
    log("Checking for updates...")
    displayNotification("No updates available", duration=3)

def resetSettings():
    log("Resetting settings...")
    setSetting('fullscreen', False)
    setSetting('masterVolume', 80)
    setSetting('musicVolume', 50)
    setSetting('sfxVolume', 40)
    setSetting('playerJoinLeaveSounds', True)
    setSetting('outputDevice', 'Default Device')
    setSetting('maxPlayers', 8)
    setSetting('autostartWhenFull', True)
    setSetting('autoKickWhenInactive', False)
    setSetting('lockRoomOnStart', False)
    setSetting('hostIPOverride', '')
    setSetting('protocolMode', 'HTTPS')
    setSetting('adminPassword', '')
    setSetting('font', 'Century')
    setSetting('subtitles', True)
    setSetting('visualSoundIndicators', True)
    displayNotification("Settings have been reset to default\nPlease restart the application for changes to take effect.", duration=3)

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
    
    if not match_found and outputDevices:
        settingsScreen.ids.audioOutputDeviceSpinner.text = outputDevices[0]

def findAvailableFonts():
    availableFonts = []
    
    if os.name == 'nt':  # Windows
        fontsDir = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
        
        try:
            # Get all font files (.ttf and .otf)
            for filename in os.listdir(fontsDir):
                if filename.lower().endswith(('.ttf', '.otf')):
                    # Remove the file extension to get the font name
                    fontName = os.path.splitext(filename)[0]
                    # Clean up common suffixes (Regular, Bold, Italic, etc.)
                    fontName = fontName.replace('-Regular', '').replace('Regular', '')
                    fontName = fontName.replace('-Bold', '').replace('Bold', '')
                    fontName = fontName.replace('-Italic', '').replace('Italic', '')
                    fontName = fontName.replace('-Light', '').replace('Light', '')
                    fontName = fontName.replace('-Medium', '').replace('Medium', '')
                    fontName = fontName.strip()
                    
                    if fontName and fontName not in availableFonts:
                        availableFonts.append(fontName)
            
            # Sort alphabetically for easier selection
            availableFonts.sort()
        except Exception as e:
            log(f"Error scanning fonts directory: {e}")
            availableFonts = ['Arial', 'Calibri', 'Courier New']  # Fallback
    else:
        # Non-Windows fallback
        availableFonts = ['Arial', 'Helvetica', 'Times New Roman', 'Courier']
    
    return availableFonts if availableFonts else ['Default']

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
    conn = sqlite3.connect('221BBakerStreet.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA integrity_check")
    result = cursor.fetchone()
    if result[0] == 'ok':
        pass
    else:
        pass
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

def log(message):
    file = os.path.join(os.path.dirname(__file__), 'host_log.txt')
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(file, 'a') as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        pass

def runner():
    # Set global font
    font = grabSettings('accessibility')[0]
    if font:
        # Check if it's a valid font file path
        if os.path.isfile(font):
            try:
                LabelBase.register(DEFAULT_FONT, fn_regular=font)
                log(f"Font '{font}' loaded successfully")
            except Exception as e:
                log(f"Error loading font file '{font}': {e}")
        else:
            # Try to find font in Windows Fonts directory
            font_path = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', f'{font}.ttf')
            if os.path.isfile(font_path):
                try:
                    LabelBase.register(DEFAULT_FONT, fn_regular=font_path)
                    log(f"Font '{font}' loaded from system fonts")
                except Exception as e:
                    log(f"Error loading system font '{font}': {e}")
            else:
                log(f"Font '{font}' not found, using default font")
    
    # Check if fullscreen is set
    fullscreen = grabSettings('video')
    if fullscreen:
        toggleFullscreen(enable=True)
        log("Fullscreen mode enabled on startup")
    # This checks that the server is online
    checkServerStatus()

if __name__ == '__main__':
    # Start background thread
    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    
    # Run GUI in main thread
    root_widget = Builder.load_file('221BBakerStreet.kv')
    runTouchApp(root_widget)