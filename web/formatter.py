from datetime import datetime

def format_for_prompt(results: list[str]) -> str:
    timestamp = datetime.utcnow().isoformat()
    lines = "\n".join(f"- {r}" for r in results)

    return (
        f"[Web search results | fetched {timestamp} UTC]\n"
        f"{lines}"
    )
