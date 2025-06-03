# 💬 GroupChat Peer-to-Peer System

Ein Netzwerk-Chatclient mit zentralem Server für Teilnehmerverwaltung und Peer-to-Peer-Kommunikation über TCP/UDP.

## 📌 Projektbeschreibung

Dieses Projekt wurde im Rahmen der Lehrveranstaltung *Rechnernetze* umgesetzt. Ziel war es, einen Gruppenchat mit folgenden Eigenschaften zu entwickeln:

- zentrale Nutzerverwaltung über einen Server
- Kommunikation im Gruppenchat (Broadcast)
- direkte Peer-to-Peer-Kommunikation zwischen Clients
- Nutzung von TCP (für Datenübertragung) & UDP (für Verbindungsaufbau)
- GUI für einfache Bedienung

Das System besteht aus einem Server und mehreren Clients mit einer grafischen Oberfläche (Tkinter).

---

## ⚙️ Installation

1. **Python 3.10+** installieren
2. Repository klonen oder Projektdateien kopieren
3. Im Projektverzeichnis:

```bash
python run_server.py  # startet den Server
python chat_client_gui.py   # startet den Client
