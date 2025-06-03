def build_message(command: str, *args) -> str:
    return f"{command} {' '.join(args)}\n"

def parse_message(message: str):
    parts = message.strip().split()
    if not parts:
        return None, []
    return parts[0], parts[1:]
