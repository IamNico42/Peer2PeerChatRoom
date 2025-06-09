# client.py – refaktoriert für PrivateChatSession
from .core import ChatCore
from .gui import ChatGUI
import tkinter as tk
from tkinter import messagebox
import threading
import socket
import queue
from ..network.protocol import Protocol
from .chat_session import PrivateChatSession

class ChatClientController:
    def __init__(self):
        self.root = tk.Tk()
        self.core = None
        self.gui = None
        self.chat_requests = queue.Queue()

    def start(self):
        self.gui = ChatGUI(self.root, self)
        self.root.mainloop()

    def connect_from_gui(self):
        nickname = self.gui.nickname.get()
        server_ip = self.gui.server_ip.get()
        server_port = self.gui.server_port.get()
        if not server_ip or not nickname:
            messagebox.showerror("Fehler", "Bitte Server-IP und Nickname eingeben.")
            return
        self.connect(nickname, server_ip, server_port)

    def connect(self, nickname, server_ip, server_port):
        self.core = ChatCore(nickname, server_ip, server_port)
        self.core.set_callback("on_connect", self.on_connect)
        self.core.set_callback("on_disconnect", self.on_disconnect)
        self.core.set_callback("on_log", self.gui.log)
        self.core.set_callback("on_tcp_command", self.handle_tcp_command)
        self.core.set_callback("on_udp_command", self.handle_udp_command)
        self.core.set_callback("on_private_chat", self.gui.show_private_chat)
        threading.Thread(target=self.core.connect, daemon=True).start()

    def on_connect(self, success, info):
        if success:
            self.gui.status_label.config(text="Verbunden", fg="green")
            self.gui.connect_button.config(state="disabled")
            self.gui.disconnect_button.config(state="normal")
        else:
            messagebox.showerror("Fehler", f"Verbindung fehlgeschlagen: {info}")
            self.gui.status_label.config(text="Nicht verbunden", fg="red")

    def disconnect(self):
        if self.core:
            self.core.disconnect()

    def on_disconnect(self):
        self.gui.status_label.config(text="Nicht verbunden", fg="red")
        self.gui.connect_button.config(state="normal")
        self.gui.disconnect_button.config(state="disabled")

    def send_broadcast_from_gui(self, event=None):
        message = self.gui.input_entry.get().strip()
        if message:
            self.send_broadcast(message)
            self.gui.input_entry.delete(0, 'end')

    def send_broadcast(self, message):
        if self.core:
            self.core.send_broadcast(message)

    def handle_user_click(self, event):
        selection = self.gui.user_list.get(tk.ACTIVE)
        try:
            nick, ip, udp = selection.split(":")
            udp_port = int(udp)
            self.core.send_chat_request(ip, udp_port, nick)
        except:
            messagebox.showerror("Fehler", "Ungültiger Eintrag in der Userliste.")

    def handle_tcp_command(self, cmd, args):
        if cmd == "BROADCAST":
            sender, msg = Protocol.read_broadcast(args)
            self.gui.log(f"[{sender}]: {msg}")
        elif cmd == "USERLIST":
            entries = Protocol.read_user_list(args)
            filtered = [entry for entry in entries if not entry.startswith(self.core.own_nickname + ":")]
            self.gui.update_user_list(filtered)
        elif cmd == "USER_JOINED":
            nick, ip, udp = Protocol.read_user_joined(args)
            if nick != self.core.own_nickname:
                self.gui.user_list.insert(tk.END, f"{nick}:{ip}:{udp}")
            self.gui.log(f"[INFO] {nick} ist beigetreten")
        elif cmd == "USER_LEFT":
            left_nick = Protocol.read_user_left(args)
            for i in range(self.gui.user_list.size()):
                if self.gui.user_list.get(i).startswith(left_nick + ":"):
                    self.gui.user_list.delete(i)
                    break
            self.gui.log(f"[INFO] {left_nick} hat den Chat verlassen")
        elif cmd == "ERROR":
            reason = Protocol.read_error(args)
            self.gui.log(f"[SERVER FEHLER] {reason}")

    def handle_udp_command(self, cmd, addr, args):
        if cmd == "CHAT_REQUEST":
            try:
                port = Protocol.read_chat_request(args)
                self.chat_requests.put((addr[0], addr[1], port))
                self.root.after(1000, self.check_chat_requests)
            except ValueError:
                self.gui.log(f"[UDP] Ungültige CHAT_REQUEST von {addr}")
        elif cmd == "CHAT_REJECTED":
            self.gui.log(f"[UDP] Chat-Anfrage von {addr} abgelehnt")

    def check_chat_requests(self):
        while not self.chat_requests.empty():
            ip, udp_port, tcp_port = self.chat_requests.get()
            if messagebox.askyesno("Chat-Anfrage", f"{ip}:{tcp_port} möchte mit dir chatten. Annehmen?"):
                try:
                    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    conn.connect((ip, tcp_port))
                    conn.sendall(self.core.nickname.encode())
                    peer_nickname = conn.recv(1024).decode().strip()
                    session = PrivateChatSession(
                        conn=conn,
                        gui_callback=self.gui.log,
                        local_nick=self.core.nickname,
                        peer_nick=peer_nickname,
                        peer_ip=ip,
                        peer_port=tcp_port
                    )
                    session.start()
                    self.gui.show_private_chat(session)
                except Exception as e:
                    self.gui.log(f"[FEHLER] Verbindung fehlgeschlagen: {e}")
            else:
                try:
                    self.core.udp_sock.sendto(Protocol.chat_rejected(), (ip, udp_port))
                except Exception as e:
                    self.gui.log(f"[WARNUNG] CHAT_REJECTED konnte nicht gesendet werden: {e}")
        self.root.after(1000, self.check_chat_requests)

    def on_closing(self):
        self.disconnect()
        self.root.destroy()

if __name__ == "__main__":
    client = ChatClientController()
    client.start()