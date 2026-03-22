import anthropic
from pathlib import Path
import clients as client_store

SYSTEM_PROMPT_FILE = Path(__file__).parent / "social-media-agent-prompt.md"
ANTHROPIC_CLIENT = anthropic.Anthropic()


def _load_system_prompt() -> str:
    with open(SYSTEM_PROMPT_FILE) as f:
        return f.read()


def _build_client_context(client: dict) -> str:
    """Prepend client-specific context to the first user message."""
    lines = [f"## Active Client: {client['name']}"]
    if client.get("niche"):
        lines.append(f"- **Niche/Industry**: {client['niche']}")
    if client.get("platforms"):
        lines.append(f"- **Platforms**: {', '.join(client['platforms'])}")
    if client.get("social_links"):
        links = ", ".join(f"{k}: {v}" for k, v in client["social_links"].items())
        lines.append(f"- **Social Links**: {links}")
    if client.get("notes"):
        lines.append(f"- **Notes**: {client['notes']}")
    return "\n".join(lines)


def chat(client_name: str, user_message: str, stream: bool = True) -> str:
    """Send a message and get a response. Persists history to disk."""
    client = client_store.get_client(client_name)
    if not client:
        raise ValueError(f"Client '{client_name}' not found.")

    system_prompt = _load_system_prompt()
    history = client_store.get_history(client_name)

    # Inject client context into first user turn if history is empty
    if not history:
        context_prefix = _build_client_context(client)
        full_message = f"{context_prefix}\n\n---\n\n{user_message}"
    else:
        full_message = user_message

    # Build messages list
    messages = list(history) + [{"role": "user", "content": full_message}]

    if stream:
        response_text = ""
        with ANTHROPIC_CLIENT.messages.stream(
            model="claude-opus-4-6",
            max_tokens=8192,
            system=system_prompt,
            messages=messages,
            thinking={"type": "adaptive"},
        ) as stream_obj:
            for text in stream_obj.text_stream:
                print(text, end="", flush=True)
                response_text += text
        print()  # newline after stream ends
    else:
        response = ANTHROPIC_CLIENT.messages.create(
            model="claude-opus-4-6",
            max_tokens=8192,
            system=system_prompt,
            messages=messages,
            thinking={"type": "adaptive"},
        )
        response_text = next(
            (b.text for b in response.content if b.type == "text"), ""
        )

    # Persist both turns
    client_store.append_message(client_name, "user", full_message)
    client_store.append_message(client_name, "assistant", response_text)

    return response_text
