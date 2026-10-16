"""Write docs/reference/cli.md from `./securax help`, so the command reference can never drift from the CLI."""
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/reference/cli.md"


def main() -> None:
    text = subprocess.run([str(ROOT / "securax"), "help"], capture_output=True, text=True, timeout=60, check=True).stdout
    OUT.write_text(
        "# Command reference\n\n"
        "Every command runs from the SecuRAX folder as `./securax <command>`, or as `securax <command>` from any folder "
        "after `./securax shortcut`. This page is generated from `./securax help` on every docs build.\n\n"
        "!!! tip \"Copying commands\"\n"
        "    Use the copy button on a code block. Copy the commands only, never the ``` lines around them: "
        "pasted fence lines leave the terminal waiting at a `>` prompt (press Ctrl+C to get out).\n\n"
        "```text\n" + text.rstrip() + "\n```\n")


if __name__ == "__main__":
    main()
