from pathlib import Path

ROOT = Path(__file__).resolve().parent
MARKER = "/_vercel/insights/script.js"
SNIPPET = """  <!-- Vercel Web Analytics -->
  <script>
    window.va = window.va || function () {
      (window.vaq = window.vaq || []).push(arguments);
    };
  </script>
  <script defer src="/_vercel/insights/script.js"></script>
"""

EXCLUDE_DIRS = {".git", ".github", "node_modules", "__pycache__", ".vercel"}
EXCLUDE_ROOT_PREFIXES = ("google", "naver")

def should_process(path):
    rel = path.relative_to(ROOT)
    if path.suffix.lower() != ".html":
        return False
    if any(part in EXCLUDE_DIRS for part in rel.parts):
        return False
    if len(rel.parts) == 1 and rel.name.lower().startswith(EXCLUDE_ROOT_PREFIXES):
        return False
    return True

def inject(path):
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        return False

    lower = text.lower()
    pos = lower.rfind("</body>")
    if pos != -1:
        new_text = text[:pos] + SNIPPET + "\n" + text[pos:]
    else:
        pos = lower.rfind("</html>")
        if pos != -1:
            new_text = text[:pos] + SNIPPET + "\n" + text[pos:]
        else:
            new_text = text + ("" if text.endswith("\n") else "\n") + SNIPPET

    path.write_text(new_text, encoding="utf-8")
    return True

changed = []
for path in sorted(ROOT.rglob("*.html")):
    if should_process(path) and inject(path):
        changed.append(path.relative_to(ROOT).as_posix())

print(f"Changed: {len(changed)}")
for item in changed:
    print(" -", item)
