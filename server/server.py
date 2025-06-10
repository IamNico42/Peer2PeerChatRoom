import socket
import threading
import unicodedata
from ..network.protocol import Protocol

class Client:
    def __init__(self, conn, ip, udp_port):
        self.conn = conn
        self.ip = ip
        self.udp_port = udp_port

class ChatServer:
    def __init__(self, host='0.0.0.0', port=9000):
        self.host = host
        self.port = port
        self.clients = {}
        self.lock = threading.Lock()
        self.running = False
        self._sock = None

    def start(self):
        self.running = True
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self.host, self.port))
        self._sock.listen()
        self._sock.settimeout(1.0)

        print(f"[SERVER] Listening on {self.host}:{self.port}")
        while self.running:
            try:
                conn, addr = self._sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            print(f"[NEW CONNECTION] {addr}")
            threading.Thread(target=self.handle_client, args=(conn,), daemon=True).start()

        self.cleanup()

    def cleanup(self):
        try:
            self._sock.close()
        except:
            pass
        with self.lock:
            for client in self.clients.values():
                try:
                    client.conn.shutdown(socket.SHUT_RDWR)
                    client.conn.close()
                except:
                    pass
            self.clients.clear()
        print("[SERVER] Shutdown complete.")

    def shutdown(self):
        self.running = False
        try:
            self._sock.close()
        except:
            pass

    def list_clients(self):
        with self.lock:
            return [f"{nick} @ {c.ip}:{c.udp_port}" for nick, c in self.clients.items()]

    def handle_client(self, conn):
        nickname = None
        recv_buffer = b""
        try:
            while True:
                data = conn.recv(4096)
                if not data:
                    break
                recv_buffer += data
                messages, recv_buffer = Protocol.decode_stream(recv_buffer)

                for raw in messages:
                    cmd, args = Protocol.extract_command(raw)

                    if cmd == "REGISTER":
                        try:
                            nickname, udp = Protocol.read_register(args)
                        except ValueError as e:
                            conn.sendall(Protocol.error(str(e)))
                            continue

                        client_ip = conn.getpeername()[0]
                        with self.lock:
                            if nickname in self.clients:
                                conn.sendall(Protocol.error("Nickname bereits vergeben"))
                                conn.close()
                                return
                            self.clients[nickname] = Client(conn, client_ip, udp)

                        conn.sendall(Protocol.welcome(nickname))
                        self.send_userlist_initial(conn)
                        self.notify_all(Protocol.user_joined(nickname, client_ip, udp))

                    elif cmd == "BROADCAST":
                        try:
                            sender, message = Protocol.read_broadcast(args)
                            # Unicode-Normalisierung für Emojis
                            message = unicodedata.normalize("NFC", message)
                            print(f"[DEBUG Server] Broadcast von {sender}: {message}")
                            self.broadcast(sender, message)
                        except ValueError as e:
                            conn.sendall(Protocol.error(str(e)))

                    elif cmd == "QUIT":
                        return
        finally:
            with self.lock:
                if nickname in self.clients and self.clients[nickname].conn == conn:
                    del self.clients[nickname]
            conn.close()
            print(f"[INFO] {nickname or 'Unbekannt'} disconnected.")
            if nickname:
                self.notify_all(Protocol.user_left(nickname))

    def broadcast(self, sender, message):
        with self.lock:
            for client in self.clients.values():
                try:
                    client.conn.sendall(Protocol.broadcast(sender, message))
                except:
                    pass

    def send_userlist_initial(self, conn):
        with self.lock:
            entries = [
                f"{nick}:{client.ip}:{client.udp_port}"
                for nick, client in self.clients.items()
            ]
        message = Protocol.user_list(*entries)
        conn.sendall(message)

    def notify_all(self, msg):
        with self.lock:
            for c in self.clients.values():
                try:
                    c.conn.sendall(msg)
                except:
                    pass