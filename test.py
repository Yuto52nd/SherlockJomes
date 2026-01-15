from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout


def build_app():
    # Create screen manager
    sm = ScreenManager()
    
    # First screen
    
    screen1 = Screen(name='screen1')
    layout1 = BoxLayout(orientation='vertical')
    layout1.add_widget(Label(text='This is Screen 1'))
    btn1 = Button(text='Go to Screen 2')
    btn1.bind(on_press=lambda x: setattr(sm, 'current', 'screen2'))
    layout1.add_widget(btn1)
    screen1.add_widget(layout1)
    
    # Second screen
    screen2 = Screen(name='screen2')
    layout2 = BoxLayout(orientation='vertical')
    layout2.add_widget(Label(text='This is Screen 2'))
    btn2 = Button(text='Go to Screen 3')
    btn2.bind(on_press=lambda x: setattr(sm, 'current', 'screen3'))
    layout2.add_widget(btn2)
    screen2.add_widget(layout2)
    
    # Third screen
    screen3 = Screen(name='screen3')
    layout3 = BoxLayout(orientation='vertical')
    layout3.add_widget(Label(text='This is Screen 3'))
    btn3 = Button(text='Back to Screen 1')
    btn3.bind(on_press=lambda x: setattr(sm, 'current', 'screen1'))
    layout3.add_widget(btn3)
    screen3.add_widget(layout3)
    
    # Add screens to manager
    sm.add_widget(screen1)
    sm.add_widget(screen2)
    sm.add_widget(screen3)
    
    return sm


if __name__ == '__main__':
    app = App()
    app.build = build_app
    app.run()
