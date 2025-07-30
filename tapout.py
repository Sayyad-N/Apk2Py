# TapOut by SayyadN and Team
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.animation import Animation
from kivy.clock import Clock

from jnius import autoclass, cast
from android.runnable import run_on_ui_thread
import time

Window.clearcolor = (0.95, 0.95, 1, 1)  # Lavender

# Splash Screen
class SplashScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = FloatLayout()
        self.title = Label(text="[b][color=#6A0DAD]TapOut[/color][/b]", markup=True, font_size='50sp',
                           pos_hint={'center_x': 0.5, 'center_y': 0.5}, opacity=0)
        layout.add_widget(self.title)
        self.add_widget(layout)
        self.animate_logo()
        Clock.schedule_once(self.switch_to_main, 3)

    def animate_logo(self):
        anim = Animation(opacity=1, font_size='60sp', duration=1.5) + Animation(font_size='45sp', duration=1)
        anim.start(self.title)

    def switch_to_main(self, dt):
        self.manager.current = 'main'

# About screen
class AboutScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        title = Label(text='[b]About TapOut[/b]', markup=True, font_size='24sp', color=(0.3, 0.1, 0.4, 1))
        members = Label(
            text='[b]Developed by:[/b]\nمحمد الصياد (SayyadN)\nمعاذ عاطف\nأسامه أشرف\nعمر محمد\nمصطفى الابراشي',
            markup=True, font_size='18sp', color=(0.2, 0.1, 0.3, 1))
        back_btn = Button(text='Back', size_hint=(1, 0.2), background_color=(0.5, 0.2, 0.8, 1), color=(1, 1, 1, 1))
        back_btn.bind(on_press=lambda x: self.manager.current = 'main')
        layout.add_widget(title)
        layout.add_widget(members)
        layout.add_widget(back_btn)
        self.add_widget(layout)

# Study Mode screen
class StudyOverlay(Screen):
    def __init__(self, duration, **kwargs):
        super().__init__(**kwargs)
        self.time_left = duration * 60
        self.label = Label(text='[b]📚 Study Mode Active[/b]', markup=True, font_size='22sp',
                           color=(0.5, 0.2, 0.8, 1))
        layout = BoxLayout(orientation='vertical', padding=50)
        layout.add_widget(self.label)
        self.add_widget(layout)
        Clock.schedule_interval(self.update_timer, 1)

    def update_timer(self, dt):
        if self.time_left > 0:
            self.time_left -= 1
            mins, sec = divmod(self.time_left, 60)
            self.label.text = f"[b]📚 Study Mode Active\n{mins}m {sec}s left[/b]"
        else:
            self.manager.current = 'main'
            return False

# Main screen
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        self.blocked_apps = []
        self.pkg_name = ""
        self.time_left = 0

        self.pkg_in = TextInput(hint_text='Enter app package name', multiline=False)
        self.time_in = TextInput(hint_text='Enter time in minutes', multiline=False, input_filter='int')
        self.start_btn = Button(text="Start Monitoring", background_color=(0.5, 0.2, 0.8, 1), color=(1, 1, 1, 1))
        self.study_btn = Button(text="📚 Start Study Mode", background_color=(0.4, 0.1, 0.6, 1), color=(1, 1, 1, 1))
        self.about_btn = Button(text="About", background_color=(0.4, 0.2, 0.6, 1), color=(1, 1, 1, 1))
        self.status_label = Label(text="Waiting...", color=(0.3, 0.1, 0.4, 1), font_size='16sp')

        self.start_btn.bind(on_press=self.start_monitor)
        self.study_btn.bind(on_press=self.start_study_mode)
        self.about_btn.bind(on_press=lambda x: self.manager.current = 'about')

        layout.add_widget(self.pkg_in)
        layout.add_widget(self.time_in)
        layout.add_widget(self.start_btn)
        layout.add_widget(self.study_btn)
        layout.add_widget(self.about_btn)
        layout.add_widget(self.status_label)

        self.add_widget(layout)
        Clock.schedule_interval(self.foreground_monitor, 1)

    def start_monitor(self, instance):
        try:
            self.pkg_name = self.pkg_in.text.strip()
            self.time_left = int(self.time_in.text.strip()) * 60
            if not self.pkg_name or self.time_left <= 0:
                self.status_label.text = "❌ Please enter valid data"
                return

            self.status_label.text = f"⏳ Monitoring {self.pkg_name}..."
            Clock.schedule_interval(self.update_timer, 1)
        except Exception as e:
            self.status_label.text = f"Error: {e}"

    def start_study_mode(self, instance):
        try:
            duration = int(self.time_in.text.strip())
            self.manager.add_widget(StudyOverlay(name='study', duration=duration))
            self.manager.current = 'study'
        except:
            self.status_label.text = "Please enter time before study mode"

    def update_timer(self, dt):
        if self.time_left > 0:
            self.time_left -= 1
            mins, sec = divmod(self.time_left, 60)
            self.status_label.text = f"{mins}m {sec}s left for {self.pkg_name}"
        else:
            self.status_label.text = f"🚫 Blocking {self.pkg_name}"
            if self.pkg_name not in self.blocked_apps:
                self.blocked_apps.append(self.pkg_name)
            return False

    def foreground_monitor(self, dt):
        current_app = self.get_foreground_app()
        if current_app in self.blocked_apps:
            self.show_block_popup(current_app)

    def get_foreground_app(self):
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Context = autoclass('android.content.Context')
        UsageStatsManager = autoclass('android.app.usage.UsageStatsManager')
        System = autoclass('java.lang.System')

        usage_stats_mgr = cast('android.app.usage.UsageStatsManager',
                               PythonActivity.mActivity.getSystemService(Context.USAGE_STATS_SERVICE))

        end_time = System.currentTimeMillis()
        begin_time = end_time - 10000

        stats = usage_stats_mgr.queryUsageStats(4, begin_time, end_time)
        last_app = None
        last_time = 0

        if stats:
            for usage in stats.toArray():
                if usage.getLastTimeUsed() > last_time:
                    last_time = usage.getLastTimeUsed()
                    last_app = usage.getPackageName()
        return last_app

    @run_on_ui_thread
    def show_block_popup(self, app_name):
        content = BoxLayout(orientation='vertical', padding=20, spacing=10)
        msg = Label(text=f"🚫 {app_name} is blocked!", font_size='18sp', color=(0.4, 0.2, 0.6, 1))
        ok_btn = Button(text='Back to Work', background_color=(0.6, 0.4, 0.8, 1), color=(1, 1, 1, 1))
        content.add_widget(msg)
        content.add_widget(ok_btn)
        popup = Popup(title='Focus Mode', content=content, size_hint=(0.8, 0.4), auto_dismiss=False)
        ok_btn.bind(on_press=popup.dismiss)
        popup.open()

class TapOutApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(SplashScreen(name='splash'))
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(AboutScreen(name='about'))
        return sm

if __name__ == '__main__':
    TapOutApp().run()
