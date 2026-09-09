"""Load trusted, bundled persona text without relying on the working directory."""

from pathlib import Path


class PersonaManager:
    """An empty name preserves webot's legacy chat behavior."""

    @staticmethod
    def load(name: str = "") -> str:
        """Return a bundled prompt; reject unknown names and broken resources.

        Only ``jason`` is supported. Names are identifiers, never file paths.
        ``__file__`` also resolves next to bundled data inside PyInstaller.
        """
        name = name.strip().lower()
        if not name:
            return ""
        if name != "jason":
            raise ValueError("Unknown PERSONA_NAME. Use 'jason' or leave it empty.")

        path = Path(__file__).resolve().with_name("jason.md")
        try:
            prompt = path.read_text(encoding="utf-8").strip()
        except (OSError, UnicodeError) as exc:
            raise RuntimeError("Unable to load bundled Jason persona (jason.md).") from exc
        if not prompt:
            raise RuntimeError("Bundled Jason persona (jason.md) is empty.")
        return prompt
