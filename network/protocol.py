import struct

class Protocol:
    @staticmethod
    def build_command(command: str, *args: str) -> bytes:
        message = f"{command} {' '.join(args)}"
        payload = message.encode('utf-8')
        length_prefix = struct.pack("!I", len(payload))
        return length_prefix + payload

    @staticmethod
    def extract_command(byte_msg: bytes) -> tuple[str, list[str]]:
        msg = byte_msg.decode('utf-8')
        parts = msg.strip().split()
        if not parts:
            return None, []
        return parts[0], parts[1:]

    @staticmethod
    def decode_stream(buffer: bytes) -> tuple[list[bytes], bytes]:
        messages = []
        offset = 0
        while len(buffer) - offset >= 4:
            msg_len = struct.unpack("!I", buffer[offset:offset + 4])[0]
            if len(buffer) - offset - 4 < msg_len:
                break
            payload = buffer[offset + 4:offset + 4 + msg_len]
            messages.append(payload)
            offset += 4 + msg_len
        return messages, buffer[offset:]

    @staticmethod
    def register(nick: str, udp_port: str) -> bytes:
        return Protocol.build_command("REGISTER", nick, udp_port)

    @staticmethod
    def welcome(nick: str) -> bytes:
        return Protocol.build_command("WELCOME", nick)

    @staticmethod
    def error(reason: str) -> bytes:
        return Protocol.build_command("ERROR", reason)

    @staticmethod
    def broadcast(nick: str, message: str) -> bytes:
        return Protocol.build_command("BROADCAST", nick, message)

    @staticmethod
    def user_list(*entries: str) -> bytes:
        return Protocol.build_command("USERLIST", *entries)

    @staticmethod
    def user_joined(nick: str, ip: str, udp: str) -> bytes:
        return Protocol.build_command("USER_JOINED", nick, ip, udp)

    @staticmethod
    def user_left(nick: str) -> bytes:
        return Protocol.build_command("USER_LEFT", nick)

    @staticmethod
    def quit() -> bytes:
        return Protocol.build_command("QUIT")

    @staticmethod
    def chat_request(port: int) -> bytes:
        return Protocol.build_command("CHAT_REQUEST", str(port))

    @staticmethod
    def chat_rejected() -> bytes:
        return Protocol.build_command("CHAT_REJECTED")

    @staticmethod
    def read_register(args: list[str]) -> tuple[str, str]:
        if len(args) != 2:
            raise ValueError("REGISTER erwartet 2 Argumente: nickname, udp_port")
        return args[0], args[1]

    @staticmethod
    def read_broadcast(args: list[str]) -> tuple[str, str]:
        if len(args) < 2:
            raise ValueError("BROADCAST erwartet mindestens 2 Argumente: sender, message")
        return args[0], " ".join(args[1:])

    @staticmethod
    def read_user_joined(args: list[str]) -> tuple[str, str, str]:
        if len(args) != 3:
            raise ValueError("USER_JOINED erwartet 3 Argumente: nick, ip, udp")
        return tuple(args)

    @staticmethod
    def read_user_left(args: list[str]) -> str:
        if len(args) != 1:
            raise ValueError("USER_LEFT erwartet 1 Argument: nick")
        return args[0]

    @staticmethod
    def read_chat_request(args: list[str]) -> int:
        if len(args) != 1:
            raise ValueError("CHAT_REQUEST erwartet 1 Argument: port")
        return int(args[0])

    @staticmethod
    def read_chat_rejected(args: list[str]) -> None:
        if args:
            raise ValueError("CHAT_REJECTED erwartet keine Argumente")

    @staticmethod
    def read_user_list(args: list[str]) -> list[str]:
        for entry in args:
            if entry.count(":") != 2:
                raise ValueError(f"Ungültiger USERLIST-Eintrag: {entry}")
        return args

    @staticmethod
    def read_error(args: list[str]) -> str:
        return " ".join(args)

    # Optional: UDP-Nachricht ohne Längenpräfix parsen (falls nötig)
    @staticmethod
    def extract_udp_message(data: bytes) -> tuple[str, list[str]]:
        if len(data) < 4:
            raise ValueError("UDP-Daten zu kurz für Längenpräfix.")
        length = struct.unpack("!I", data[:4])[0]
        payload = data[4:4+length]
        return Protocol.extract_command(payload)

