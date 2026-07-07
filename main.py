"""
SpeedyTest - A polished speed testing application
Similar to Ookla's Speedtest but with a modern KivyMD interface
Android-compatible version
"""

import threading
import json
import os
from datetime import datetime
from collections import deque

from kivy.core.window import Window
from kivy.clock import Clock, mainthread
from kivy.metrics import dp
from kivy.uix.popup import Popup

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
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.divider import MDDivider
from kivymd.uix.spinner import MDSpinner
from kivy.uix.image import Image

try:
    import speedtest
except ImportError:
    speedtest = None

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
        self.load_history()
        
    def load_history(self):
        """Load history from file"""
        try:
            history_file = self.get_history_path()
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    saved_history = json.load(f)
                    self.history = deque(saved_history, maxlen=10)
        except Exception as e:
            print(f"Error loading history: {e}")
    
    def save_history(self):
        """Save history to file"""
        try:
            history_file = self.get_history_path()
            os.makedirs(os.path.dirname(history_file), exist_ok=True)
            with open(history_file, 'w') as f:
                json.dump(list(self.history), f)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    @staticmethod
    def get_history_path():
        """Get path for history file"""
        app_dir = os.path.expanduser('~/.speedytest')
        return os.path.join(app_dir, 'history.json')
        
    def get_best_server(self, callback=None):
        """Find the best server"""
        try:
            if speedtest is None:
                raise Exception("speedtest module not installed")
            
            self.status_message = "Finding best server..."
            if callback:
                callback(self.status_message, 10)
            
            self.speedtest = speedtest.Speedtest()
            self.speedtest.get_servers()
            self.speedtest.get_best_server()
            
            self.status_message = "Server found!"
            if callback:
                callback(self.status_message, 20)
                
        except Exception as e:
            self.status_message = f"Error: {str(e)}"
            print(f"Server error: {e}")
            if callback:
                callback(self.status_message, 0)
    
    def test_download(self, callback=None):
        """Test download speed"""
        try:
            self.status_message = "Testing download speed..."
            if callback:
                callback(self.status_message, 30)
            
            self.speedtest.download()
            self.results['download'] = self.speedtest.results.download / 1_000_000  # Convert to Mbps
            
            if callback:
                callback(self.status_message, 60)
            
        except Exception as e:
            self.status_message = f"Download error: {str(e)}"
            print(f"Download error: {e}")
    
    def test_upload(self, callback=None):
        """Test upload speed"""
        try:
            self.status_message = "Testing upload speed..."
            if callback:
                callback(self.status_message, 60)
            
            self.speedtest.upload()
            self.results['upload'] = self.speedtest.results.upload / 1_000_000  # Convert to Mbps
            
            if callback:
                callback(self.status_message, 90)
            
        except Exception as e:
            self.status_message = f"Upload error: {str(e)}"
            print(f"Upload error: {e}")
    
    def get_ping(self):
        """Get ping value"""
        try:
            self.results['ping'] = self.speedtest.results.ping
        except Exception as e:
            self.status_message = f"Ping error: {str(e)}"
            print(f"Ping error: {e}")
    
    def run_full_test(self, callback=None):
        """Run complete speed test"""
        self.is_testing = True
        self.current_progress = 0
        
        try:
            if speedtest is None:
                self.status_message = "speedtest-cli not installed"
                if callback:
                    callback(self.status_message, 0)
                self.is_testing = False
                return False
            
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
            try:
                server_info = self.speedtest.get_best_server()
                self.results['server'] = server_info.get('sponsor', 'Unknown')
            except:
                self.results['server'] = 'Unknown'
            
            self.results['isp'] = self.speedtest.results.isp
            self.results['ip'] = self.speedtest.results.ip
            
            # Save to history
            self.history.append(self.results.copy())
            self.save_history()
            
            self.status_message = "Test complete!"
            self.current_progress = 100
            if callback:
                callback(self.status_message, 100)
            
            self.is_testing = False
            return True
            
        except Exception as e:
            self.status_message = f"Test failed: {str(e)}"
            print(f"Test error: {e}")
            if callback:
                callback(self.status_message, 0)
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
        self.md_bg_color = (1, 1, 1, 1)
        
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
        self.value_label = MDLabel(
            text=str(value),
            font_style='H3',
            theme_text_color='Primary',
            bold=True,
            size_hint_y=None,
            height=dp(50)
        )
        self.add_widget(self.value_label)
        
        # Unit
        unit_label = MDLabel(
            text=unit,
            font_style='Body2',
            theme_text_color='Hint',
            size_hint_y=None,
            height=dp(20)
        )
        self.add_widget(unit_label)
    
    def update_value(self, value):
        """Update the value label"""
        self.value_label.text = str(value)


class HomeScreen(MDScreen):
    """Main home screen with test button and display"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.engine = SpeedtestEngine()
        self.test_thread = None
        
        main_layout = MDBoxLayout(
            orientation='vertical',
            padding=dp(15),
            spacing=dp(10),
            md_bg_color=(0.95, 0.95, 0.95, 1)
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
            size_hint_y=None
        )
        scroll_content.bind(minimum_height=scroll_content.setter('height'))
        
        self.download_card = ResultsCard(
            title="DOWNLOAD",
            value="--",
            unit="Mbps"
        )
        scroll_content.add_widget(self.download_card)
        
        self.upload_card = ResultsCard(
            title="UPLOAD",
            value="--",
            unit="Mbps"
        )
        scroll_content.add_widget(self.upload_card)
        
        self.ping_card = ResultsCard(
            title="PING",
            value="--",
            unit="ms"
        )
        scroll_content.add_widget(self.ping_card)
        
        self.server_card = ResultsCard(
            title="SERVER",
            value="--",
            unit=""
        )
        scroll_content.add_widget(self.server_card)
        
        scroll.add_widget(scroll_content)
        main_layout.add_widget(scroll)
        
        # Status and progress
        status_box = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(60),
            spacing=dp(5)
        )
        
        self.status_label = MDLabel(
            text="Ready to test",
            font_style='Body2',
            theme_text_color='Hint',
            size_hint_y=None,
            height=dp(25)
        )
        status_box.add_widget(self.status_label)
        
        self.progress_bar = MDProgressBar(
            size_hint_y=None,
            height=dp(4),
            value=0
        )
        status_box.add_widget(self.progress_bar)
        
        main_layout.add_widget(status_box)
        
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
        
        if speedtest is None:
            self.status_label.text = "Error: speedtest-cli not installed"
            return
        
        self.test_button.disabled = True
        self.status_label.text = "Initializing test..."
        self.progress_bar.value = 0
        
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
            self.download_card.update_value(f"{self.engine.results['download']:.2f}")
        if self.engine.results['upload']:
            self.upload_card.update_value(f"{self.engine.results['upload']:.2f}")
        if self.engine.results['ping']:
            self.ping_card.update_value(f"{self.engine.results['ping']:.1f}")
        if self.engine.results['server']:
            self.server_card.update_value(self.engine.results['server'][:20])
    
    def _test_complete(self):
        """Called when test is complete"""
        self.test_button.disabled = False
        if self.engine.results['download']:
            self.status_label.text = "✓ Test completed!"
        else:
            self.status_label.text = "✗ Test failed!"
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
        
        main_layout = MDBoxLayout(
            orientation='vertical',
            padding=dp(15),
            spacing=dp(10),
            md_bg_color=(0.95, 0.95, 0.95, 1)
        )
        
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
            if result.get('download') and result.get('upload'):
                text = (f"Test {len(list(history)) - i + 1}: "
                       f"↓ {result['download']:.1f}Mbps | "
                       f"↑ {result['upload']:.1f}Mbps")
                item = OneLineListItem(text=text)
                self.history_list.add_widget(item)
                
                if i < len(list(history)):
                    self.history_list.add_widget(MDDivider())
    
    def go_back(self, instance):
        """Return to home screen"""
        self.manager.current = 'home'


class SettingsScreen(MDScreen):
    """Screen for application settings"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        main_layout = MDBoxLayout(
            orientation='vertical',
            padding=dp(15),
            spacing=dp(10),
            md_bg_color=(0.95, 0.95, 0.95, 1)
        )
        
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
            radius=[dp(15)],
            md_bg_color=(1, 1, 1, 1)
        )
        
        info_label = MDLabel(
            text="SpeedyTest v1.0\n\nA polished speed testing application using KivyMD.\n\nPowered by speedtest-cli\n\nInstall speedtest-cli:\npip install speedtest-cli",
            font_style='Body2',
            theme_text_color='Hint',
            size_hint_y=None,
            height=dp(200)
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
        self.title = "SpeedyTest"
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
