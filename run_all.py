from pathlib import Path
import subprocess
import sys

PROJECT_DIR = Path(__file__).resolve().parent


def main():
    scripts = ["convert_pages.py", "merge_pages.py"]

    for name in scripts:
        if not (PROJECT_DIR / name).is_file():
            print(f"Missing script: {PROJECT_DIR / name}")
            return 1

    for step, name in enumerate(scripts, start=1):
        print(f"\n[{step}/{len(scripts)}] Running {name}...", flush=True)

        try:
            subprocess.run(
                [sys.executable, str(PROJECT_DIR / name)],
                cwd=str(PROJECT_DIR),
                check=True,
            )
        except subprocess.CalledProcessError as error:
            print(
                f"\nStopped: {name} failed "
                f"with exit code {error.returncode}."
            )
            return 1
        except KeyboardInterrupt:
            print("\nCancelled.")
            return 130

    output = PROJECT_DIR / "final_book.docx"
    if not output.is_file():
        print("\nScripts finished, but final_book.docx was not created.")
        return 1

    print(f"\nCompleted. Output: {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())