import importlib.util
import subprocess
import sys

# パッケージがインストールされているか確認する関数
def is_package_installed(package_name):
    return importlib.util.find_spec(package_name) is not None

# 必要ならパッケージをインストールする関数
def install_package(package_name):
    if not is_package_installed(package_name):
        print(f"{package_name}が見つかりません。インストールを試みます...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"{package_name}がインストールされました。")
    else:
        print(f"{package_name}は既にインストールされています。")

package_list = ["japanize-kivy", "pusher", "pysher"]

for item in package_list:
    install_package(item)

import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
import japanize_kivy
import pusher
import pysher
import json
import threading

# Pusherの設定
APP_ID = "1940001"
APP_KEY = "128fd68c3a8f3bdde537"
APP_SECRET = "873dbe1ad082944f6f5b"
APP_CLUSTER = "ap3"

# Pusherクライアント
pusher_client = pusher.Pusher(
    app_id=APP_ID,
    key=APP_KEY,
    secret=APP_SECRET,
    cluster=APP_CLUSTER,
    ssl=True
)

# Pusherの接続
pusher_socket = pysher.Pusher(APP_KEY, cluster=APP_CLUSTER)

class ChatApp(App):
    def build(self):
        self.layout = BoxLayout(orientation="vertical")

        self.chat_display = Label(text="チャットメッセージ", size_hint=(1, 0.7))
        self.layout.add_widget(self.chat_display)

        self.name_input = TextInput(hint_text="名前を入力", size_hint=(1, 0.1))
        self.layout.add_widget(self.name_input)

        self.message_input = TextInput(hint_text="メッセージを入力", size_hint=(1, 0.1))
        self.layout.add_widget(self.message_input)

        self.send_button = Button(text="送信", size_hint=(1, 0.1))
        self.send_button.bind(on_press=self.send_message)
        self.layout.add_widget(self.send_button)

        # Pusherの接続を開始
        threading.Thread(target=self.start_pusher).start()

        return self.layout

    def send_message(self, instance):
        name = self.name_input.text.strip()
        message = self.message_input.text.strip()
        if name and message:
            pusher_client.trigger("public-chat", "new-message", {"user": name, "message": message})
            self.message_input.text = ""

    def start_pusher(self):
        def message_handler(data):
            try:
                # データをJSONとしてパース
                parsed_data = json.loads(data)
                update_text = f"\n{parsed_data['user']}: {parsed_data['message']}"
                # KivyのUIをスレッドセーフに更新
                Clock.schedule_once(lambda dt: self.update_chat_display(update_text))
            except json.JSONDecodeError:
                print("Failed to decode JSON:", data)
            except KeyError:
                print("Missing key in parsed data:", data)

        def connect_handler(_):
            channel = pusher_socket.subscribe("public-chat")
            channel.bind("new-message", message_handler)

        pusher_socket.connection.bind("pusher:connection_established", connect_handler)
        pusher_socket.connect()

    def update_chat_display(self, update_text):
        self.chat_display.text += update_text

if __name__ == "__main__":
    ChatApp().run()