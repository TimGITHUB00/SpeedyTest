"""
SpeedyTest - A polished speed testing application
Similar to Ookla's Speedtest but with a modern KivyMD interface
"""

import threading
import time
from datetime import datetime
from collections import deque

from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
from kivy.clock import Clock, mainthread
from kivy.metrics import dp

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.divider import MDDivider
from kivymd.uix.textfield import MDTextField
from kivymd.theme_manager import ThemeManager

import speedtest as st
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import io


Window.size = (400, 800)


class SpeedtestEngine:
    """Handles all speedtest operations"""
    
    def __init__(self):
        self.speedtest = None
        self.is_testing = False
        self.results = {
            'download': None,
            'upload': None,
            'ping': None,
            'server': None,
            'timestamp': None,
            'isp': None,
            'ip': None
        }
        self.history = deque(maxlen=10)
        self.current_progress = 0
        self.status_message = ""
        
    def get_best_server(self, callback=None):
        """Find the best server"""
        try:
            self.status_message = "Finding best server..."
            if callback:
                callback(self.status_message, 10)
            
            self.speedtest = st.Speedtest()
            self.speedtest.get_servers()
            self.speedtest.get_best_server()
            
            self.status_message = "Server found!"
            if callback:
                callback(self.status_message, 20)
                
        except Exception as e:
            self.status_message = f"Error: {str(e)}"
            if callback:
                callback(self.status_message, 0)
    
    def test_download(self, callback=None):
        """Test download speed"""
        try:
            self.status_message = "Testing download speed..."
            if callback:
                callback(self.status_message, 30)
            
            self.speedtest.download(callback=lambda speed: self._update_progress(speed, callback, 30, 60))
            self.results['download'] = self.speedtest.results.download / 1_000_000  # Convert to Mbps
            
        except Exception as e:
            self.status_message = f"Download error: {str(e)}"
    
    def test_upload(self, callback=None):
        """Test upload speed"""
        try:
            self.status_message = "Testing upload speed..."
            if callback:
                callback(self.status_message, 60)
            
            self.speedtest.upload(callback=lambda speed: self._update_progress(speed, callback, 60, 90))
            self.results['upload'] = self.speedtest.results.upload / 1_000_000  # Convert to Mbps
            
        except Exception as e:
            self.status_message = f"Upload error: {str(e)}"
    
    def get_ping(self):
        """Get ping value"""
        try:
            self.results['ping'] = self.speedtest.results.ping
        except Exception as e:
            self.status_message = f"Ping error: {str(e)}"
    
    def _update_progress(self, speed, callback, start, end):
        """Update progress during speed tests"""
        if callback:
            progress = start + (end - start) * 0.5
            self.current_progress = int(progress)
            callback(self.status_message, self.current_progress)
    
    def run_full_test(self, callback=None):
        """Run complete speed test"""
        self.is_testing = True
        self.current_progress = 0
        
        try:
            # Get best server
            self.get_best_server(callback)
            
            # Get ping
            self.get_ping()
            
            # Test download
            self.test_download(callback)
            
            # Test upload
            self.test_upload(callback)
            
            # Store results
            self.results['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.results['server'] = self.speedtest.get_best_server()['sponsor']
            self.results['isp'] = self.speedtest.results.isp
            self.results['ip'] = self.speedtest.results.ip
            
            # Save to history
            self.history.append(self.results.copy())
            
            self.status_message = "Test complete!"
            self.current_progress = 100
            if callback:
                callback(self.status_message, 100)
            
            self.is_testing = False
            return True
            
        except Exception as e:
            self.status_message = f"Test failed: {str(e)}"
            self.is_testing = False
            return False


class ResultsCard(MDCard):
    """Custom card for displaying speed test results"""
    
    def __init__(self, title, value, unit, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(15)
        self.spacing = dp(10)
        self.size_hint_y = None
        self.height = dp(120)
        self.radius = [dp(15)]
        self.elevation = 2
        
        # Title
        title_label = MDLabel(
            text=title,
            font_style='Caption',
            theme_text_color='Hint',
            size_hint_y=None,
            height=dp(20)
        )
        self.add_widget(title_label)
        
        # Value
        value_label = MDLabel(
            text=f"{value}",
            font_style='H3',
            theme_text_color='Primary',
            bold=True,
            size_hint_y=None,
            height=dp(50)
        )
        self.add_widget(value_label)
        
        # Unit
        unit_label = MDLabel(
            text=unit,
            font_style='Body2',
            theme_text_color='Hint',
            size_hint_y=None,
            height=dp(20)
        )
        self.add_widget(unit_label)


class HomeScreen(MDScreen):
    """Main home screen with test button and display"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.engine = SpeedtestEngine()
        self.test_thread = None
        
        main_layout = MDBoxLayout(
            orientation='vertical',
            padding=dp(15),
            spacing=dp(10)
        )
        
        # Header
        header = MDLabel(
            text="SpeedyTest",
            font_style='H3',
            theme_text_color='Primary',
            bold=True,
            size_hint_y=None,
            height=dp(50)
        )
        main_layout.add_widget(header)
        
        # Scroll view for results
        scroll = MDScrollView()
        scroll_content = MDGridLayout(
            cols=2,
            spacing=dp(10),
            padding=dp(0),
            size_hint_y=None,
            height=dp(500)
        )
        scroll_content.bind(minimum_height=scroll_content.setter('height'))
        
        self.download_card = ResultsCard(
            title="DOWNLOAD",
            value="-- ",
            unit="Mbps"
        )
        scroll_content.add_widget(self.download_card)
        
        self.upload_card = ResultsCard(
            title="UPLOAD",
            value="-- ",
            unit="Mbps"
        )
        scroll_content.add_widget(self.upload_card)
        
        self.ping_card = ResultsCard(
            title="PING",
            value="-- ",
            unit="ms"
        )
        scroll_content.add_widget(self.ping_card)
        
        self.jitter_card = ResultsCard(
            title="JITTER",
            value="-- ",
            unit="ms"
        )
        scroll_content.add_widget(self.jitter_card)
        
        scroll.add_widget(scroll_content)
        main_layout.add_widget(scroll)
        
        # Status and progress
        self.status_label = MDLabel(
            text="Ready to test",
            font_style='Body2',
            theme_text_color='Hint',
            size_hint_y=None,
            height=dp(30)
        )
        main_layout.add_widget(self.status_label)
        
        self.progress_bar = MDProgressBar(
            size_hint_y=None,
            height=dp(4)
        )
        main_layout.add_widget(self.progress_bar)
        
        # Buttons
        button_layout = MDBoxLayout(
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10)
        )
        
        self.test_button = MDRaisedButton(
            text="START TEST",
            size_hint_x=0.5
        )
        self.test_button.bind(on_press=self.start_test)
        button_layout.add_widget(self.test_button)
        
        history_button = MDFlatButton(
            text="HISTORY",
            size_hint_x=0.5
        )
        history_button.bind(on_press=self.show_history)
        button_layout.add_widget(history_button)
        
        main_layout.add_widget(button_layout)
        
        self.add_widget(main_layout)
    
    def start_test(self, instance):
        """Start the speed test"""
        if self.engine.is_testing:
            return
        
        self.test_button.disabled = True
        self.test_thread = threading.Thread(target=self._run_test_thread, daemon=True)
        self.test_thread.start()
    
    def _run_test_thread(self):
        """Run test in background thread"""
        self.engine.run_full_test(callback=self._update_ui)
        Clock.schedule_once(lambda dt: self._test_complete(), 0)
    
    @mainthread
    def _update_ui(self, status, progress):
        """Update UI from background thread"""
        self.status_label.text = status
        self.progress_bar.value = progress
        
        # Update cards with current results
        if self.engine.results['download']:
            self.download_card.children[1].text = f"{self.engine.results['download']:.2f}"
        if self.engine.results['upload']:
            self.upload_card.children[1].text = f"{self.engine.results['upload']:.2f}"
        if self.engine.results['ping']:
            self.ping_card.children[1].text = f"{self.engine.results['ping']:.1f}"
    
    def _test_complete(self):
        """Called when test is complete"""
        self.test_button.disabled = False
        self.status_label.text = "Test completed!"
        self.progress_bar.value = 100
    
    def show_history(self, instance):
        """Show test history"""
        history_screen = self.manager.get_screen('history')
        history_screen.load_history(self.engine.history)
        self.manager.current = 'history'


class HistoryScreen(MDScreen):
    """Screen showing test history"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        main_layout = MDBoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        
        # Header
        header = MDLabel(
            text="Test History",
            font_style='H4',
            theme_text_color='Primary',
            bold=True,
            size_hint_y=None,
            height=dp(40)
        )
        main_layout.add_widget(header)
        
        # Scroll view for history
        scroll = MDScrollView()
        self.history_list = MDList()
        scroll.add_widget(self.history_list)
        main_layout.add_widget(scroll)
        
        # Back button
        back_button = MDFlatButton(
            text="← BACK",
            size_hint_y=None,
            height=dp(45)
        )
        back_button.bind(on_press=self.go_back)
        main_layout.add_widget(back_button)
        
        self.add_widget(main_layout)
    
    def load_history(self, history):
        """Load test history into list"""
        self.history_list.clear_widgets()
        
        if not history:
            self.history_list.add_widget(
                OneLineListItem(text="No test history yet")
            )
            return
        
        for i, result in enumerate(reversed(list(history)), 1):
            text = (f"Test {len(list(history)) - i + 1}: "
                   f"↓ {result['download']:.1f} Mbps | "
                   f"↑ {result['upload']:.1f} Mbps | "
                   f"Ping {result['ping']:.1f} ms")
            item = OneLineListItem(text=text)
            self.history_list.add_widget(item)
            
            if i < len(history):
                self.history_list.add_widget(MDDivider())
    
    def go_back(self, instance):
        """Return to home screen"""
        self.manager.current = 'home'


class SettingsScreen(MDScreen):
    """Screen for application settings"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        main_layout = MDBoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        
        # Header
        header = MDLabel(
            text="Settings",
            font_style='H4',
            theme_text_color='Primary',
            bold=True,
            size_hint_y=None,
            height=dp(40)
        )
        main_layout.add_widget(header)
        
        # Settings content
        settings_card = MDCard(
            orientation='vertical',
            padding=dp(15),
            spacing=dp(15),
            size_hint_y=None,
            height=dp(300),
            radius=[dp(15)]
        )
        
        # Theme selection
        theme_label = MDLabel(
            text="Theme",
            font_style='Body1',
            size_hint_y=None,
            height=dp(30)
        )
        settings_card.add_widget(theme_label)
        
        info_label = MDLabel(
            text="SpeedyTest v1.0\n\nA polished speed testing application using KivyMD.\n\nPowered by speedtest-cli",
            font_style='Body2',
            theme_text_color='Hint',
            size_hint_y=None,
            height=dp(150)
        )
        settings_card.add_widget(info_label)
        
        main_layout.add_widget(settings_card)
        
        # Back button
        back_button = MDFlatButton(
            text="← BACK",
            size_hint_y=None,
            height=dp(45)
        )
        back_button.bind(on_press=self.go_back)
        main_layout.add_widget(back_button)
        
        self.add_widget(main_layout)
    
    def go_back(self, instance):
        """Return to home screen"""
        self.manager.current = 'home'


class SpeedyTestApp(MDApp):
    """Main application class"""
    
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.primary_hue = "600"
        self.theme_cls.theme_style = "Light"
        
        screen_manager = MDScreenManager()
        
        # Add screens
        screen_manager.add_widget(HomeScreen(name='home'))
        screen_manager.add_widget(HistoryScreen(name='history'))
        screen_manager.add_widget(SettingsScreen(name='settings'))
        
        return screen_manager


if __name__ == '__main__':
    app = SpeedyTestApp()
    app.run()
