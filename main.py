#!/usr/bin/env python3
"""
Social Media Agent — Multi-Client CLI
Usage: python3 main.py [command] [args]
"""

import sys
import os
import json
import clients as client_store
import agent


# ── ANSI colours ──────────────────────────────────────────────────────────────
BOLD = "\033[1m"
DIM  = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED  = "\033[31m"
RESET = "\033[0m"

BANNER = f"""
{BOLD}{CYAN}╔══════════════════════════════════════════╗
║   Social Media Agent  ·  Multi-Client   ║
╚══════════════════════════════════════════╝{RESET}
"""

HELP = f"""
{BOLD}Commands:{RESET}
  {CYAN}list{RESET}                        List all clients
  {CYAN}new{RESET}                         Create a new client (interactive)
  {CYAN}chat <client>{RESET}               Start/resume a chat session
  {CYAN}history <client>{RESET}            Show conversation history
  {CYAN}reset <client>{RESET}              Clear conversation history for a client
  {CYAN}info <client>{RESET}               Show client profile
  {CYAN}edit <client>{RESET}               Edit client profile (interactive)
  {CYAN}delete <client>{RESET}             Delete a client
  {CYAN}help{RESET}                        Show this message

{BOLD}Examples:{RESET}
  python3 main.py new
  python3 main.py chat "Nike"
  python3 main.py list
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def prompt(text: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"  {text}{suffix}: ").strip()
    return val if val else default


def confirm(text: str) -> bool:
    return input(f"  {text} (y/N): ").strip().lower() == "y"


def print_client_card(c: dict) -> None:
    msgs = len(c.get("history", []))
    turns = msgs // 2
    print(f"  {BOLD}{c['name']}{RESET}")
    if c.get("niche"):
        print(f"    Niche    : {c['niche']}")
    if c.get("platforms"):
        print(f"    Platforms: {', '.join(c['platforms'])}")
    if c.get("social_links"):
        for k, v in c["social_links"].items():
            print(f"    {k:8} : {v}")
    if c.get("notes"):
        print(f"    Notes    : {c['notes']}")
    print(f"    History  : {turns} conversation turn(s)")
    print()


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_list():
    clients = client_store.list_clients()
    if not clients:
        print(f"  {DIM}No clients yet. Run: python3 main.py new{RESET}")
        return
    print(f"\n{BOLD}Clients ({len(clients)}):{RESET}\n")
    for c in clients:
        print_client_card(c)


def cmd_new():
    print(f"\n{BOLD}Create New Client{RESET}\n")
    name = prompt("Client / Brand name")
    if not name:
        print(f"{RED}Name is required.{RESET}")
        return
    if client_store.get_client(name):
        print(f"{RED}Client '{name}' already exists.{RESET}")
        return

    niche = prompt("Niche / Industry (e.g. food, fitness, fashion)")
    platforms_raw = prompt("Platforms (comma-separated: tiktok, instagram, youtube)")
    platforms = [p.strip().lower() for p in platforms_raw.split(",") if p.strip()]

    social_links = {}
    print(f"  {DIM}Enter social links (leave blank to skip):{RESET}")
    for platform in platforms:
        link = prompt(f"  {platform.capitalize()} URL")
        if link:
            social_links[platform] = link

    notes = prompt("Any extra notes (optional)")

    c = client_store.create_client(
        name=name,
        niche=niche,
        platforms=platforms,
        social_links=social_links,
        notes=notes,
    )
    print(f"\n{GREEN}✓ Client '{name}' created.{RESET}")
    print(f"  Run: {CYAN}python3 main.py chat \"{name}\"{RESET}\n")


def cmd_chat(client_name: str):
    client = client_store.get_client(client_name)
    if not client:
        print(f"{RED}Client '{client_name}' not found.{RESET}")
        print(f"  Run {CYAN}python3 main.py list{RESET} to see all clients.")
        return

    history_len = len(client.get("history", []))
    turns = history_len // 2
    status = f"resuming — {turns} prior turn(s)" if turns else "new session"

    print(f"\n{BOLD}{CYAN}━━ {client['name']} ({status}) ━━{RESET}")
    print(f"{DIM}Type your message and press Enter. Type 'exit' or 'quit' to stop.{RESET}\n")

    while True:
        try:
            user_input = input(f"{BOLD}You:{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{DIM}Session ended.{RESET}")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "bye"):
            print(f"{DIM}Session saved. Goodbye!{RESET}")
            break

        print(f"\n{BOLD}{CYAN}Agent:{RESET} ", end="")
        try:
            agent.chat(client_name, user_input, stream=True)
        except Exception as e:
            print(f"\n{RED}Error: {e}{RESET}")
        print()


def cmd_history(client_name: str):
    client = client_store.get_client(client_name)
    if not client:
        print(f"{RED}Client '{client_name}' not found.{RESET}")
        return

    history = client_store.get_history(client_name)
    if not history:
        print(f"  {DIM}No conversation history for '{client_name}'.{RESET}")
        return

    print(f"\n{BOLD}History for {client_name}:{RESET}\n")
    for msg in history:
        role_label = f"{BOLD}You{RESET}" if msg["role"] == "user" else f"{CYAN}Agent{RESET}"
        # Truncate long messages for readability
        content = msg["content"]
        if len(content) > 500:
            content = content[:500] + f" {DIM}[...]{RESET}"
        print(f"{role_label}: {content}\n")


def cmd_reset(client_name: str):
    client = client_store.get_client(client_name)
    if not client:
        print(f"{RED}Client '{client_name}' not found.{RESET}")
        return
    if confirm(f"Reset all history for '{client_name}'?"):
        client_store.reset_history(client_name)
        print(f"{GREEN}✓ History cleared for '{client_name}'.{RESET}")


def cmd_info(client_name: str):
    client = client_store.get_client(client_name)
    if not client:
        print(f"{RED}Client '{client_name}' not found.{RESET}")
        return
    print(f"\n{BOLD}Client Profile:{RESET}\n")
    print_client_card(client)


def cmd_edit(client_name: str):
    client = client_store.get_client(client_name)
    if not client:
        print(f"{RED}Client '{client_name}' not found.{RESET}")
        return

    print(f"\n{BOLD}Edit Client: {client_name}{RESET} {DIM}(leave blank to keep current){RESET}\n")

    niche = prompt("Niche / Industry", client.get("niche", ""))
    platforms_raw = prompt(
        "Platforms (comma-separated)",
        ", ".join(client.get("platforms", [])),
    )
    platforms = [p.strip().lower() for p in platforms_raw.split(",") if p.strip()]

    social_links = dict(client.get("social_links", {}))
    print(f"  {DIM}Social links:{RESET}")
    for platform in platforms:
        current = social_links.get(platform, "")
        link = prompt(f"  {platform.capitalize()} URL", current)
        if link:
            social_links[platform] = link
        elif platform in social_links:
            del social_links[platform]

    notes = prompt("Notes", client.get("notes", ""))

    client_store.update_client_info(
        client_name,
        niche=niche,
        platforms=platforms,
        social_links=social_links,
        notes=notes,
    )
    print(f"\n{GREEN}✓ Client '{client_name}' updated.{RESET}")


def cmd_delete(client_name: str):
    client = client_store.get_client(client_name)
    if not client:
        print(f"{RED}Client '{client_name}' not found.{RESET}")
        return
    if confirm(f"Permanently delete '{client_name}' and all their history?"):
        client_store.delete_client(client_name)
        print(f"{GREEN}✓ Deleted '{client_name}'.{RESET}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    print(BANNER)
    args = sys.argv[1:]

    if not args or args[0] in ("help", "--help", "-h"):
        print(HELP)
        return

    cmd = args[0].lower()

    if cmd == "list":
        cmd_list()

    elif cmd == "new":
        cmd_new()

    elif cmd == "chat":
        if len(args) < 2:
            print(f"{RED}Usage: python3 main.py chat <client-name>{RESET}")
            return
        cmd_chat(" ".join(args[1:]))

    elif cmd == "history":
        if len(args) < 2:
            print(f"{RED}Usage: python3 main.py history <client-name>{RESET}")
            return
        cmd_history(" ".join(args[1:]))

    elif cmd == "reset":
        if len(args) < 2:
            print(f"{RED}Usage: python3 main.py reset <client-name>{RESET}")
            return
        cmd_reset(" ".join(args[1:]))

    elif cmd == "info":
        if len(args) < 2:
            print(f"{RED}Usage: python3 main.py info <client-name>{RESET}")
            return
        cmd_info(" ".join(args[1:]))

    elif cmd == "edit":
        if len(args) < 2:
            print(f"{RED}Usage: python3 main.py edit <client-name>{RESET}")
            return
        cmd_edit(" ".join(args[1:]))

    elif cmd == "delete":
        if len(args) < 2:
            print(f"{RED}Usage: python3 main.py delete <client-name>{RESET}")
            return
        cmd_delete(" ".join(args[1:]))

    else:
        print(f"{RED}Unknown command: '{cmd}'{RESET}")
        print(HELP)


if __name__ == "__main__":
    main()
