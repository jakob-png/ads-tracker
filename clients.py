import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

CLIENTS_DIR = Path(__file__).parent / "clients"
CLIENTS_DIR.mkdir(exist_ok=True)


def _client_file(name: str) -> Path:
    safe = name.lower().replace(" ", "_")
    return CLIENTS_DIR / f"{safe}.json"


def list_clients() -> list[dict]:
    clients = []
    for f in sorted(CLIENTS_DIR.glob("*.json")):
        with open(f) as fh:
            data = json.load(fh)
        clients.append(data)
    return clients


def get_client(name: str) -> Optional[dict]:
    path = _client_file(name)
    if not path.exists():
        # Try case-insensitive match
        for f in CLIENTS_DIR.glob("*.json"):
            with open(f) as fh:
                data = json.load(fh)
            if data["name"].lower() == name.lower():
                return data
        return None
    with open(path) as fh:
        return json.load(fh)


def save_client(data: dict) -> None:
    path = _client_file(data["name"])
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2)


def create_client(name: str, niche: str = "", platforms: list[str] = None,
                  social_links: dict = None, notes: str = "") -> dict:
    data = {
        "name": name,
        "niche": niche,
        "platforms": platforms or [],
        "social_links": social_links or {},
        "notes": notes,
        "created_at": datetime.now().isoformat(),
        "history": [],
    }
    save_client(data)
    return data


def delete_client(name: str) -> bool:
    path = _client_file(name)
    client = get_client(name)
    if client:
        _client_file(client["name"]).unlink(missing_ok=True)
        return True
    return False


def append_message(name: str, role: str, content: str) -> None:
    client = get_client(name)
    if not client:
        raise ValueError(f"Client '{name}' not found.")
    client["history"].append({"role": role, "content": content})
    save_client(client)


def reset_history(name: str) -> None:
    client = get_client(name)
    if not client:
        raise ValueError(f"Client '{name}' not found.")
    client["history"] = []
    save_client(client)


def get_history(name: str) -> list[dict]:
    client = get_client(name)
    if not client:
        return []
    return client.get("history", [])


def update_client_info(name: str, **kwargs) -> dict:
    client = get_client(name)
    if not client:
        raise ValueError(f"Client '{name}' not found.")
    for key, value in kwargs.items():
        if key != "history":  # protect history
            client[key] = value
    save_client(client)
    return client
