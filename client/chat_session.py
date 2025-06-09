#chat_session.py
import threading
from datetime import datetime

class PrivateChatSession:
    def __init__(self, conn, gui_callback, local_nick, peer_nick, peer_ip, peer_port):
        self.conn = conn
        self.gui_callback = gui_callback  # Methode zum Anzeigen von Nachrichten
        self.local_nick = local_nick
        self.peer_nick = peer_nick
        self.peer_ip = peer_ip
        self.peer_port = peer_port
        self.stop_event = threading.Event()

    def start(self):
        threading.Thread(target=self._recv_loop, daemon=True).start()

    def send(self, message):
        try:
            self.conn.sendall(message.encode())
            self._log_local(message)
        except:
            self.close()

    def close(self):
        self.stop_event.set()
        try:
            self.conn.sendall(b"[DISCONNECT]")
        except:
            pass
        self.conn.close()

    def _recv_loop(self):
        while not self.stop_event.is_set():
            try:
                data = self.conn.recv(1024)
                if not data:
                    break
                decoded = data.decode().strip()
                if decoded == "[DISCONNECT]":
                    self.gui_callback(f"[INFO] {self.peer_nick} hat den Chat beendet.")
                    break
                self._log_peer(decoded)
            except:
                break
        self.stop_event.set()
        self.conn.close()

    def _log_peer(self, msg):
        timestamp = datetime.now().strftime("%H:%M")
        self.gui_callback(f"[{self.peer_nick}] ({timestamp}): {msg}")

    def _log_local(self, msg):
        timestamp = datetime.now().strftime("%H:%M")
        self.gui_callback(f"[{self.local_nick}] ({timestamp}): {msg}")
