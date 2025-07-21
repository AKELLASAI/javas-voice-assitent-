import sys


import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.core.window import Window
import openai
import google.generativeai as genai
import subprocess
import os
from llama_cpp import Llama
import pyttsx3
# For Wikipedia fallback
import wikipedia

# For speech recognition
import speech_recognition as sr

# For wake word detection
import threading
import queue


# OpenAI API key (user can set their own)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "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")
# Gemini API key (auto)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyCVE2BJQKko0ACPWwWH2HQrPjXEAMYyjvQ")
# Path to local LLM model (Phi-3)
PHI3_MODEL_PATH = r"c:\\Users\\svake\\Downloads\\Phi-3-mini-4k-instruct-q4.gguf"

def launch_windows_app(app_name):
    # Map common app names to their executable
    app_map = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "paint": "mspaint.exe",
        "wordpad": "write.exe",
        "explorer": "explorer.exe",
        "cmd": "cmd.exe",
        "powershell": "powershell.exe",
        "chrome": r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "edge": r"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
        "taskmgr": "taskmgr.exe",
        "control": "control.exe",
        "regedit": "regedit.exe",
        "snippingtool": "snippingtool.exe",
        "word": r"C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE",
        "excel": r"C:\\Program Files\\Microsoft Office\\root\\Office16\\EXCEL.EXE",
        "powerpoint": r"C:\\Program Files\\Microsoft Office\\root\\Office16\\POWERPNT.EXE",
        "onenote": r"C:\\Program Files\\Microsoft Office\\root\\Office16\\ONENOTE.EXE",
    # Add more as needed
    }
    exe = app_map.get(app_name.lower())
    if exe:
        try:
            subprocess.Popen(exe)
            return f"Launched {app_name}."
        except Exception as e:
            return f"Failed to launch {app_name}: {e}"
    else:
        # Try launching as a .exe in PATH or current dir
        try:
            subprocess.Popen(f"{app_name}.exe")
            return f"Tried to launch {app_name}.exe from PATH."
        except Exception as e:
            return f"Unknown application: {app_name} ({e})"

def parse_and_launch(text):
    # Simple intent detection for launching apps
    import re
    match = re.search(r"open (\w+)", text.lower())
    if match:
        app = match.group(1)
        return launch_windows_app(app)
    return None


class JavasChat(BoxLayout):
    def open_tools_popup(self, instance):
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        popup = Popup(title="Tools", content=Label(text="Tools panel coming soon!"), size_hint=(0.5, 0.3))
        popup.open()
    def __init__(self, **kwargs):
        super().__init__(orientation='horizontal', **kwargs)
        self.padding = 10
        self.spacing = 5

        # Sidebar and main layout must be defined at the top so they are always in scope
        from kivy.uix.boxlayout import BoxLayout as KivyBox
        from kivy.uix.button import Button
        import webbrowser
        sidebar = KivyBox(orientation='vertical', size_hint_x=0.16, spacing=6)
        main_layout = KivyBox(orientation='vertical')
        sidebar_buttons = [
            ("Google Meet", "https://meet.google.com/"),
            ("Microsoft Teams", "https://teams.microsoft.com/"),
            ("Google Drive", "https://drive.google.com/"),
            ("OneDrive", "https://onedrive.live.com/"),
            ("PDF Converter", "https://www.ilovepdf.com/pdf_to_word"),
            ("Google Docs", "https://docs.google.com/"),
            ("Google Sheets", "https://sheets.google.com/"),
            ("Google Sites", "https://sites.google.com/"),
            ("Gemini (Google AI)", "https://gemini.google.com/"),
            ("ChatGPT (OpenAI)", "https://chat.openai.com/"),
        ]
        for label, url in sidebar_buttons:
            btn = Button(text=label, size_hint_y=None, height=38, font_size=13)
            btn.bind(on_press=lambda inst, u=url: webbrowser.open(u))
            sidebar.add_widget(btn)
        # Add Tools button for full access
        tools_btn = Button(text="🛠️ Tools", size_hint_y=None, height=38, font_size=13, background_color=(0.2,0.6,1,1))
        tools_btn.bind(on_press=self.open_tools_popup)
        sidebar.add_widget(tools_btn)

        # 3D-like animated face widget
        from kivy.uix.widget import Widget
        from kivy.graphics import Ellipse, Color, Line
        from kivy.uix.video import Video
        from kivy.uix.filechooser import FileChooserIconView
        from kivy.uix.popup import Popup
        self.video_widget = None
        class JavasFace(Widget):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.size_hint_y = 0.25
                self.eye_offset = 0
                self.mouth_open = 0
                with self.canvas:
                    # Face outline
                    Color(0.1, 0.1, 0.1, 1)
                    self.face = Ellipse(pos=self.pos, size=(180, 180))
                    # Eyes
                    Color(0.9, 0.9, 0.2, 1)
                    self.left_eye = Ellipse(pos=(self.x+45, self.y+120), size=(20, 20))
                    self.right_eye = Ellipse(pos=(self.x+115, self.y+120), size=(20, 20))
                    # Mouth
                    Color(0.8, 0.8, 0.1, 1)
                    self.mouth = Line(points=[self.x+60, self.y+70, self.x+90, self.y+60, self.x+120, self.y+70], width=3)
                self.bind(pos=self.update_face, size=self.update_face)
            def update_face(self, *args):
                # Update face position and animate eyes/mouth
                self.face.pos = (self.x, self.y)
                self.face.size = (180, 180)
                self.left_eye.pos = (self.x+45+self.eye_offset, self.y+120)
                self.right_eye.pos = (self.x+115-self.eye_offset, self.y+120)
                # Animate mouth open/close
                y = self.y+60-self.mouth_open
                self.mouth.points = [self.x+60, y+10, self.x+90, y, self.x+120, y+10]
            def animate(self, thinking=False, speaking=False):
                # Animate eyes and mouth for thinking/speaking
                import random
                if thinking:
                    self.eye_offset = random.randint(-3, 3)
                    self.mouth_open = random.randint(0, 5)
                elif speaking:
                    self.eye_offset = 0
                    self.mouth_open = random.randint(5, 15)
                else:
                    self.eye_offset = 0
                    self.mouth_open = 0
                self.update_face()
        # Video widget placeholder removed; only add face widget
        self.face_widget = JavasFace()
        main_layout.add_widget(self.face_widget)
        # Loading indicator (must be created after face)
        self.loading = Label(text="", size_hint_y=0.05, color=(0.5,0.5,0.5,1))
        main_layout.add_widget(self.loading)

        # Local LLM (Iron Man) chatbox
        from kivy.graphics import Color, Line, Rectangle
        self.local_llm_chat_box = KivyBox(size_hint=(1, 0.25), padding=2, orientation='vertical')
        with self.local_llm_chat_box.canvas.before:
            Color(0.1, 0.1, 0.1, 0.8)
            self._llm_bg = Rectangle(pos=self.local_llm_chat_box.pos, size=self.local_llm_chat_box.size)
            Color(0.8, 0.2, 0.2, 1)  # Red border for Iron Man
            self._llm_border = Line(rectangle=(self.local_llm_chat_box.x, self.local_llm_chat_box.y, self.local_llm_chat_box.width, self.local_llm_chat_box.height), width=2)
        def update_llm_box_bg(*args):
            self._llm_bg.pos = self.local_llm_chat_box.pos
            self._llm_bg.size = self.local_llm_chat_box.size
            self._llm_border.rectangle = (self.local_llm_chat_box.x, self.local_llm_chat_box.y, self.local_llm_chat_box.width, self.local_llm_chat_box.height)
        self.local_llm_chat_box.bind(pos=update_llm_box_bg, size=update_llm_box_bg)
        self.local_llm_chat_log = Label(size_hint_x=1, size_hint_y=None, text="[b][color=FF4500]Iron Man LLM Chat[/color][/b]", halign="left", valign="top", markup=True)
        self.local_llm_chat_log.bind(texture_size=self._update_llm_text_size)
        self.local_llm_chat_log.text_size = (Window.width - 40, None)
        self.local_llm_chat_log.height = self.local_llm_chat_log.texture_size[1]
        self.local_llm_chat_box.add_widget(self.local_llm_chat_log)
        main_layout.add_widget(self.local_llm_chat_box)

        # Chat area with border effect
        from kivy.uix.scrollview import ScrollView
        chat_box = KivyBox(size_hint=(1, 0.8), padding=2)
        from kivy.graphics import Color, Line, Rectangle
        with chat_box.canvas.before:
            Color(0.2, 0.2, 0.2, 0.8)  # Background color
            self._chat_bg = Rectangle(pos=chat_box.pos, size=chat_box.size)
            Color(1, 0.84, 0, 1)  # Gold border
            self._chat_border = Line(rectangle=(chat_box.x, chat_box.y, chat_box.width, chat_box.height), width=2)
        def update_box_bg(*args):
            self._chat_bg.pos = chat_box.pos
            self._chat_bg.size = chat_box.size
            self._chat_border.rectangle = (chat_box.x, chat_box.y, chat_box.width, chat_box.height)
        chat_box.bind(pos=update_box_bg, size=update_box_bg)
        self.scroll = ScrollView(size_hint=(1, 1))
        self.chat_log = Label(size_hint_x=1, size_hint_y=None, text="Javas LLM Assistant\n", halign="left", valign="top", markup=True)
        self.chat_log.bind(texture_size=self._update_text_size)
        self.chat_log.text_size = (Window.width - 40, None)
        self.chat_log.height = self.chat_log.texture_size[1]
        self.scroll.add_widget(self.chat_log)
        chat_box.add_widget(self.scroll)
        main_layout.add_widget(chat_box)

        # Model selector
        from kivy.uix.spinner import Spinner
        self.model_spinner = Spinner(
            text='OpenAI',
            values=('OpenAI', 'Gemini', 'Local LLM'),
            size_hint_y=0.07,
            size_hint_x=0.3
        )
        main_layout.add_widget(self.model_spinner)
        self.local_llm = None
        # Setup TTS engine for Iron Man-like voice
        import pyttsx3
        self.tts_engine = pyttsx3.init()
        voices = self.tts_engine.getProperty('voices')
        for v in voices:
            if 'male' in v.name.lower() or 'baritone' in v.name.lower() or 'david' in v.name.lower():
                self.tts_engine.setProperty('voice', v.id)
                break
        self.tts_engine.setProperty('rate', 150)
        self.tts_engine.setProperty('volume', 1.0)

        # Settings panel
        self.settings_btn = Button(text="⚙️ Settings", size_hint_y=0.07, size_hint_x=0.3)
        # (All duplicate/over-indented widget additions removed)
        self.settings_btn.bind(on_press=self.open_settings)
        main_layout.add_widget(self.settings_btn)

        # Emotion selector
        from kivy.uix.spinner import Spinner
        self.emotion_spinner = Spinner(
            text='neutral',
            values=('neutral', 'happy', 'sad'),
            size_hint_y=0.07,
            size_hint_x=0.3
        )
        main_layout.add_widget(self.emotion_spinner)
        self.current_emotion = 'neutral'
        def on_emotion_select(spinner, text):
            self.current_emotion = text
        self.emotion_spinner.bind(text=on_emotion_select)

        # Wake word detection (automatic, no button)
        import queue
        self.wake_word_active = True
        self.wake_word_thread = None
        self.wake_word_queue = queue.Queue()
        # Start wake word listener automatically
        self.loading.text = "Wake word listening... Say 'Hey Javas'"
        self.wake_word_thread = threading.Thread(target=self.wake_word_listener, daemon=True)
        self.wake_word_thread.start()

        # Always Listening mode
        self.always_listen = False
        self.always_listen_btn = Button(text="👂 Always Listening: OFF", size_hint_y=0.07, size_hint_x=1)
        self.always_listen_btn.bind(on_press=self.toggle_always_listen)
        main_layout.add_widget(self.always_listen_btn)

        # Add the sidebar and main layout to the root (only once, at correct scope)
        self.add_widget(sidebar)
        self.add_widget(main_layout)

        # --- Chatbox (user input area) ---
        from kivy.uix.boxlayout import BoxLayout as KivyBox
        chatbox_layout = KivyBox(orientation='horizontal', size_hint_y=0.09, spacing=6, padding=[0, 4, 0, 0])
        self.input_box = TextInput(hint_text="Type your message...", multiline=False, size_hint_x=0.65, font_size=16)
        self.send_btn = Button(text="Send", size_hint_x=0.15, font_size=15)
        self.send_btn.bind(on_press=self.send_message)
        self.listen_btn = Button(text="🎤", size_hint_x=0.10, font_size=18)
        self.listen_btn.bind(on_press=self.listen_to_user)
        self.clear_btn = Button(text="🗑️", size_hint_x=0.10, font_size=18)
        self.clear_btn.bind(on_press=self.clear_chat_history)
        chatbox_layout.add_widget(self.input_box)
        chatbox_layout.add_widget(self.send_btn)
        chatbox_layout.add_widget(self.listen_btn)
        chatbox_layout.add_widget(self.clear_btn)
        main_layout.add_widget(chatbox_layout)
    def clear_chat_history(self, instance):
        self.chat_log.text = "Javas LLM Assistant\n"
        self.scroll.scroll_y = 1

    def _update_llm_text_size(self, *args):
        self.local_llm_chat_log.text_size = (self.local_llm_chat_box.width - 20, None)
        self.local_llm_chat_log.height = self.local_llm_chat_log.texture_size[1]

    # open_video_chooser and play_video methods removed
    def toggle_always_listen(self, instance):
        if not self.always_listen:
            self.always_listen = True
            self.always_listen_btn.text = "🔴 Always Listening: ON"
            self.loading.text = "Always listening... Ask anything."
            self._always_listen_thread = threading.Thread(target=self._always_listen_loop, daemon=True)
            self._always_listen_thread.start()
        else:
            self.always_listen = False
            self.always_listen_btn.text = "👂 Always Listening: OFF"
            self.loading.text = ""

    def _always_listen_loop(self):
        r = sr.Recognizer()
        while self.always_listen:
            try:
                with sr.Microphone() as source:
                    audio = r.listen(source, timeout=5, phrase_time_limit=10)
                    try:
                        text = r.recognize_google(audio)
                        if text:
                            Clock.schedule_once(lambda dt, t=text: self._on_voice_input(t))
                    except sr.UnknownValueError:
                        continue
                    except Exception:
                        continue
            except Exception:
                continue
    def open_settings(self, instance):
        from kivy.uix.popup import Popup
        from kivy.uix.slider import Slider
        from kivy.uix.label import Label as KivyLabel
        from kivy.uix.gridlayout import GridLayout
        layout = GridLayout(cols=1, spacing=10, padding=10)
        delay_slider = Slider(min=0, max=60, value=60, step=1)
        delay_label = KivyLabel(text=f"Thinking Delay: {int(delay_slider.value)}s")
        def on_value(instance, value):
            delay_label.text = f"Thinking Delay: {int(value)}s"
            self.thinking_delay = int(value)
        delay_slider.bind(value=on_value)
        layout.add_widget(delay_label)
        layout.add_widget(delay_slider)
        popup = Popup(title="Settings", content=layout, size_hint=(0.5, 0.3))
        popup.open()
        self.thinking_delay = 60

    def toggle_wake_word(self, instance):
        if not self.wake_word_active:
            self.wake_word_active = True
            self.wake_btn.text = "🔴 Wake Word: ON"
            self.loading.text = "Wake word listening... Say 'Hey Javas'"
            self.wake_word_thread = threading.Thread(target=self.wake_word_listener, daemon=True)
            self.wake_word_thread.start()
        else:
            self.wake_word_active = False
            self.wake_btn.text = "🟢 Wake Word: OFF"
            self.loading.text = ""

    def wake_word_listener(self):
        r = sr.Recognizer()
        while self.wake_word_active:
            try:
                with sr.Microphone() as source:
                    audio = r.listen(source, timeout=5, phrase_time_limit=4)
                    try:
                        text = r.recognize_google(audio).lower()
                        if "hey javas" in text:
                            Clock.schedule_once(lambda dt: self._wake_word_triggered())
                    except sr.UnknownValueError:
                        continue
                    except Exception:
                        continue
            except Exception:
                continue

    def _wake_word_triggered(self):
        self.loading.text = "Listening..."
        self.speak_as_ironman("Yes sir, I am listening.")
        self.listen_to_user(None)
    def listen_to_user(self, instance):
        self.loading.text = "Listening..."
        self.send_btn.disabled = True
        self.input_box.disabled = True
        self.listen_btn.disabled = True
        def recognize():
            r = sr.Recognizer()
            with sr.Microphone() as source:
                try:
                    audio = r.listen(source, timeout=5, phrase_time_limit=10)
                    text = r.recognize_google(audio)
                    Clock.schedule_once(lambda dt: self._on_voice_input(text))
                except sr.WaitTimeoutError:
                    Clock.schedule_once(lambda dt: self._on_voice_input(""))
                except sr.UnknownValueError:
                    Clock.schedule_once(lambda dt: self._on_voice_input("Sorry, I could not understand you."))
                except Exception as e:
                    Clock.schedule_once(lambda dt: self._on_voice_input(f"Error: {e}"))
        threading.Thread(target=recognize).start()

    def _on_voice_input(self, text):
        self.listen_btn.disabled = False
        self.send_btn.disabled = False
        self.input_box.disabled = False
        if text and not text.startswith("Error") and not text.startswith("Sorry"):
            self.input_box.text = text
            self.send_message(None)
        else:
            self.loading.text = ""
            if text:
                self.append_message(f"[Mic] {text}", color="[color=FF6347]")

    def _update_text_size(self, *args):
        self.chat_log.text_size = (self.scroll.width - 20, None)
        self.chat_log.height = self.chat_log.texture_size[1]
        self.scroll.scroll_y = 0  # Always scroll to bottom

    def send_message(self, instance):
        user_text = self.input_box.text.strip()
        if not user_text:
            return
        self.append_message(f"You: {user_text}", color="[color=00BFFF]")
        self.input_box.text = ""
        self.loading.text = "Javas is thinking..."
        self.send_btn.disabled = True
        self.input_box.disabled = True
        # Animate face while thinking (always 60 seconds max)
        import time
        import threading
        def animate_thinking():
            try:
                for _ in range(60*10):
                    Clock.schedule_once(lambda dt: self.face_widget.animate(thinking=True), 0)
                    time.sleep(0.1)
                Clock.schedule_once(lambda dt: self.face_widget.animate(thinking=False), 0)
            except Exception:
                import sys
                sys.excepthook(*sys.exc_info())
        threading.Thread(target=animate_thinking, daemon=True).start()
        def delayed_response():
            try:
                time.sleep(60)
                self._get_llm_response(user_text)
            except Exception:
                import sys
                sys.excepthook(*sys.exc_info())
        threading.Thread(target=delayed_response).start()

    def append_message(self, msg, color="[color=FFFFFF]"):
        # Add colored message to chat log
        self.chat_log.text += f"\n{color}{msg}[/color]"
        Clock.schedule_once(lambda dt: self._update_text_size(), 0.01)

    def _get_llm_response(self, prompt):
        # Check for app launch intent first
        launch_result = parse_and_launch(prompt)
        if launch_result:
            Clock.schedule_once(lambda dt: self._append_response(launch_result))
            return
        # Otherwise, use selected LLM
        model = self.model_spinner.text
        if model == 'Gemini':
            response = self.query_gemini(prompt)
            Clock.schedule_once(lambda dt: self._append_response(response))
        elif model == 'Local LLM':
            response = self.query_local_llm(prompt)
            # If response is not helpful, try Wikipedia, then web search
            if isinstance(response, str) and ("error" in response.lower() or len(response.strip()) < 10):
                try:
                    summary = wikipedia.summary(prompt, sentences=2)
                    wiki_response = f"[From Wikipedia] {summary}"
                    Clock.schedule_once(lambda dt: self._append_local_llm_response(prompt, response))
                    Clock.schedule_once(lambda dt: self._append_local_llm_response(prompt, wiki_response))
                    return
                except Exception:
                    # Wikipedia failed, try web search
                    try:
                        web_summary = self.web_search_summary(prompt)
                        web_response = f"[From Web] {web_summary}"
                        Clock.schedule_once(lambda dt: self._append_local_llm_response(prompt, response))
                        Clock.schedule_once(lambda dt: self._append_local_llm_response(prompt, web_response))
                        return
                    except Exception:
                        pass
            Clock.schedule_once(lambda dt: self._append_local_llm_response(prompt, response))
        else:
            response = self.query_llm(prompt)
            Clock.schedule_once(lambda dt: self._append_response(response))
        # If LLM response is not helpful, try Wikipedia (only for non-local)
        if model != 'Local LLM' and (isinstance(response, str) and ("error" in response.lower() or len(response.strip()) < 10)):
            try:
                summary = wikipedia.summary(prompt, sentences=2)
                response = f"[From Wikipedia] {summary}"
            except Exception:
                pass
            Clock.schedule_once(lambda dt: self._append_response(response))

    def web_search_summary(self, query):
        # Use DuckDuckGo Instant Answer API for a quick summary
        import requests
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_redirect=1&no_html=1"
        resp = requests.get(url, timeout=8)
        data = resp.json()
        if data.get('AbstractText'):
            return data['AbstractText']
        elif data.get('RelatedTopics') and len(data['RelatedTopics']) > 0:
            topic = data['RelatedTopics'][0]
            if isinstance(topic, dict) and topic.get('Text'):
                return topic['Text']
        return "No web summary found."

    def _append_local_llm_response(self, prompt, response):
        # Add user prompt and LLM response to the Iron Man chatbox
        self.local_llm_chat_log.text += f"\n[color=00BFFF]You:[/color] {prompt}"
        self.local_llm_chat_log.text += f"\n[color=FFD700]Iron Man:[/color] {response}"
        Clock.schedule_once(lambda dt: self._update_llm_text_size(), 0.01)
        # Speak the answer in Iron Man-like voice
        self.speak_as_ironman(response)
        self.loading.text = ""
        self.send_btn.disabled = False
        self.input_box.disabled = False
        self.input_box.focus = True

    def query_local_llm(self, prompt):
        try:
            if self.local_llm is None:
                self.local_llm = Llama(model_path=PHI3_MODEL_PATH, n_ctx=2048, n_threads=4)
            # Prompt Phi-3 in instruct mode
            system_prompt = "You are Javas, a helpful Windows voice assistant."
            full_prompt = f"<|system|> {system_prompt}\n<|user|> {prompt}\n<|assistant|>"
            output = self.local_llm(full_prompt, max_tokens=256, stop=["<|user|>", "<|system|>"])
            if 'choices' in output and output['choices']:
                return output['choices'][0]['text'].strip()
            return str(output)
        except Exception as e:
            return f"Local LLM Error: {e}"

    def _append_response(self, response):
        # Always answer in Javas tone and clarify it's a Windows software
        javas_intro = "[b][color=FFD700]Javas[/color][/b]: Hello! I'm Javas, your Windows assistant. "
        # If the response already starts with 'Javas', don't repeat
        if isinstance(response, str) and response.strip().lower().startswith("javas"):
            answer = response
        else:
            answer = javas_intro + str(response)
        self.append_message(answer, color="[color=FFD700]")
        # Speak the answer in Iron Man-like voice
        self.speak_as_ironman(answer)
        self.loading.text = ""
        self.send_btn.disabled = False
        self.input_box.disabled = False
        self.input_box.focus = True

    def speak_as_ironman(self, text):
        # Remove markup tags for TTS
        import re
        clean = re.sub(r'\[/?[a-zA-Z0-9=]+\]', '', text)
        clean = clean.replace('Javas:', 'Sir,')  # Iron Man's JARVIS style
        # Animate face as speaking with emotion
        import threading
        import time
        emotion = getattr(self, 'current_emotion', 'neutral')
        def animate_speaking():
            try:
                for _ in range(20):
                    if emotion == 'happy':
                        self.face_widget.eye_offset = 2
                        self.face_widget.mouth_open = 10
                    elif emotion == 'sad':
                        self.face_widget.eye_offset = -2
                        self.face_widget.mouth_open = 2
                    else:
                        self.face_widget.eye_offset = 0
                        self.face_widget.mouth_open = 5
                    Clock.schedule_once(lambda dt: self.face_widget.update_face(), 0)
                    time.sleep(0.08)
                # Reset to neutral
                self.face_widget.eye_offset = 0
                self.face_widget.mouth_open = 0
                Clock.schedule_once(lambda dt: self.face_widget.update_face(), 0)
            except Exception:
                import sys
                sys.excepthook(*sys.exc_info())
        threading.Thread(target=animate_speaking, daemon=True).start()
        # Adjust TTS pitch/rate for emotion
        try:
            if emotion == 'happy':
                self.tts_engine.setProperty('rate', 170)
                self.tts_engine.setProperty('volume', 1.0)
            elif emotion == 'sad':
                self.tts_engine.setProperty('rate', 120)
                self.tts_engine.setProperty('volume', 0.7)
            else:
                self.tts_engine.setProperty('rate', 150)
                self.tts_engine.setProperty('volume', 1.0)
            self.tts_engine.say(clean)
            self.tts_engine.runAndWait()
        except Exception:
            pass


    def query_llm(self, prompt):
        try:
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                api_key=OPENAI_API_KEY
            )
            # Defensive: ensure choices and message exist
            if hasattr(completion, 'choices') and completion.choices:
                msg = completion.choices[0]
                if hasattr(msg, 'message') and hasattr(msg.message, 'content'):
                    return msg.message.content.strip()
                elif hasattr(msg, 'text'):
                    return msg.text.strip()
                else:
                    return str(msg)
            else:
                return str(completion)
        except Exception as e:
            return f"OpenAI Error: {e}"

    def query_gemini(self, prompt):
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            # Try to extract the text in a robust way
            if hasattr(response, 'text') and response.text:
                return response.text.strip()
            # Gemini API: candidates[0].content.parts[0].text
            if hasattr(response, 'candidates') and response.candidates:
                try:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts') and candidate.content.parts:
                        part = candidate.content.parts[0]
                        if hasattr(part, 'text'):
                            return str(part.text)
                        else:
                            return str(part)
                    else:
                        return str(candidate)
                except Exception:
                    return str(response.candidates[0])
            if hasattr(response, 'result') and response.result:
                return str(response.result)
            # Fallback: try to get any string representation
            return str(response)
        except Exception as e:
            return f"Gemini Error: {e}"



class JavasApp(App):
    def build(self):
        self.title = "Javas LLM Assistant"
        return JavasChat()

# Global exception handler to prevent auto-close
def handle_exception(exc_type, exc_value, exc_traceback):
    import traceback
    # Log the exception but do not exit the app
    print("\n[Unhandled Exception]", exc_type, exc_value)
    traceback.print_tb(exc_traceback)
    # Optionally, show a popup in Kivy
    try:
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        msg = f"{exc_type.__name__}: {exc_value}"
        popup = Popup(title="Error", content=Label(text=msg), size_hint=(0.6, 0.3))
        popup.open()
    except Exception:
        pass

import sys
sys.excepthook = handle_exception

if __name__ == "__main__":
    JavasApp().run()
