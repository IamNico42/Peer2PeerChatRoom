import socket
import threading
from ..network.protocol import Protocol
from datetime import datetime

class ChatCore:
    def __init__(self, nickname, server_ip, server_port):
        self.nickname = nickname
        self.server_ip = server_ip
        self.server_port = server_port
        self.sock = None
        self.udp_sock = None
        self.udp_port = None
        self.running = False
        self.tcp_thread = None
        self.udp_thread = None
        self.callbacks = {}

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.server_ip, self.server_port))
            self.udp_port = UDPPortChooser.choose()
            self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_sock.bind(('0.0.0.0', self.udp_port))
            self.sock.sendall(Protocol.register(self.nickname, str(self.udp_port)))
            buffer = b""
            while True:
                data = self.sock.recv(1024)
                if not data:
                    raise Exception("Keine Antwort vom Server.")
                buffer += data
                messages, buffer = Protocol.decode_stream(buffer)
                if messages:
                    cmd, args = Protocol.extract_command(messages[0])
                    break
            if cmd == "WELCOME":
                self.own_nickname = args[0]
                self.running = True
                self.tcp_thread = TCPReceiverThread(self.sock, self.handle_tcp_command)
                self.tcp_thread.start()
                self.udp_thread = UDPListenerThread(self.udp_sock, self.handle_udp_command)
                self.udp_thread.start()
                self._trigger("on_connect", True, self.own_nickname)
            elif cmd == "ERROR":
                self.sock.close()
                self.sock = None
                self._trigger("on_connect", False, ' '.join(args))
        except Exception as e:
            self.sock = None
            self._trigger("on_connect", False, str(e))

    def disconnect(self):
        if self.running:
            try:
                self.sock.sendall(Protocol.quit())
            except:
                pass
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
            except:
                pass
            try:
                self.udp_sock.close()
            except:
                pass
            self.running = False
            self.sock = None
            self.udp_sock = None
            self._trigger("on_disconnect")

    def send_broadcast(self, message):
        if message and self.sock:
            self.sock.sendall(Protocol.broadcast(self.nickname, message))

    def send_chat_request(self, target_ip, target_udp_port, target_nick=None):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('', 0))
        server.listen(1)
        tcp_port = server.getsockname()[1]
        threading.Thread(target=self.accept_chat, args=(server, target_nick), daemon=True).start()
        try:
            msg = Protocol.chat_request(tcp_port)
            self.udp_sock.sendto(msg, (target_ip, target_udp_port))
            self._trigger("on_log", f"[INFO] Chat-Anfrage an {target_ip}:{target_udp_port} gesendet")
        except Exception as e:
            self._trigger("on_log", f"[FEHLER] Chat-Anfrage konnte nicht gesendet werden: {e}")

    def accept_chat(self, server_sock, expected_nick=None):
        server_sock.settimeout(10)
        try:
            conn, addr = server_sock.accept()
            peer_nickname = conn.recv(1024).decode().strip()
            conn.sendall(self.nickname.encode())
            self._trigger("on_private_chat", conn, addr[0], addr[1], peer_nickname, self.nickname)
        except socket.timeout:
            self._trigger("on_log", "[INFO] Deine Chat-Anfrage wurde nicht beantwortet.")
        finally:
            server_sock.close()

    def set_callback(self, event, callback):
        self.callbacks[event] = callback

    def _trigger(self, event, *args, **kwargs):
        if event in self.callbacks:
            self.callbacks[event](*args, **kwargs)

    @staticmethod
    def current_time():
        return datetime.now().strftime("%H:%M")

    def handle_tcp_command(self, cmd, args):
        self._trigger("on_tcp_command", cmd, args)

    def handle_udp_command(self, cmd, addr, args):
        self._trigger("on_udp_command", cmd, addr, args)

class UDPPortChooser:
    @staticmethod
    def choose():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', 0))
        port = sock.getsockname()[1]
        sock.close()
        return port

class TCPReceiverThread(threading.Thread):
    def __init__(self, sock, callback):
        super().__init__(daemon=True)
        self.sock = sock
        self.callback = callback
        self.running = True
    def run(self):
        buffer = b""
        while self.running:
            try:
                data = self.sock.recv(1024)
                if not data:
                    break
                buffer += data
                messages, buffer = Protocol.decode_stream(buffer)
                for payload in messages:
                    cmd, args = Protocol.extract_command(payload)
                    self.callback(cmd, args)
            except:
                break
    def stop(self):
        self.running = False

class UDPListenerThread(threading.Thread):
    def __init__(self, udp_sock, callback):
        super().__init__(daemon=True)
        self.udp_sock = udp_sock
        self.callback = callback
        self.running = True
    def run(self):
        while self.running:
            try:
                data, addr = self.udp_sock.recvfrom(1024)
                cmd, args = Protocol.extract_udp_message(data)
                self.callback(cmd, addr, args)
            except OSError:
                break
    def stop(self):
        self.running = False
