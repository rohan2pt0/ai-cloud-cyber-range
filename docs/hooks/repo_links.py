"""MkDocs hook: links that work on GitHub also work on the documentation site.

Many pages link to files elsewhere in the repository (scripts, configs, CHANGELOG.md). On GitHub those links work; on the
site they would 404, because only docs/ is published. Before each page is converted this hook:
  * expands a snippet include of a repository file (--8<-- "CHANGELOG.md") itself, so the included links are read
    relative to THAT file, not to the page that includes it;
  * rewrites a link to a repository file outside docs/ to the file on GitHub (blob for a file, tree for a folder);
  * rewrites a link into docs/ from an included file so it is relative to the page, and MkDocs resolves it.
A link to something that exists nowhere is left alone, so MkDocs reports it and `mkdocs build --strict` fails (doc 99).
"""
from __future__ import annotations

import os
import posixpath
import re

LINK = re.compile(r"(\]\()([^)\s]+)((?:\s+\"[^\"]*\")?\))")
SNIPPET = re.compile(r'^--8<-- "([^"]+)"\s*$', re.M)
FENCE = re.compile(r"^(```|~~~).*?^\1", re.M | re.S)


def _root(config) -> str:
    return os.path.dirname(os.path.abspath(config["config_file_path"]))


def _blob(config, path: str, is_dir: bool) -> str:
    branch = (config.get("edit_uri") or "edit/main/").split("/")[1] or "main"
    return f"{config['repo_url'].rstrip('/')}/{'tree' if is_dir else 'blob'}/{branch}/{path}"


def rewrite(text: str, src_dir: str, page_dir: str, root: str, config) -> str:
    """src_dir: the repository folder the text was written in; page_dir: the repository folder of the page it lands in."""
    def one(m: re.Match) -> str:
        url = m.group(2)
        if re.match(r"^[a-z][a-z0-9+.-]*:", url, re.I) or url.startswith(("#", "/", "<")):
            return m.group(0)
        path, frag = (url.split("#", 1) + [""])[:2]
        if not path:
            return m.group(0)
        target = posixpath.normpath(posixpath.join(src_dir, path))
        full = os.path.join(root, target)
        if target.startswith("../") or not os.path.exists(full):
            return m.group(0)                                    # nowhere: MkDocs reports it
        anchor = f"#{frag}" if frag else ""
        if target == "docs" or target.startswith("docs/"):
            return f"{m.group(1)}{posixpath.relpath(target, page_dir)}{anchor}{m.group(3)}"
        return f"{m.group(1)}{_blob(config, target, os.path.isdir(full))}{anchor}{m.group(3)}"

    parts, last = [], 0
    for f in FENCE.finditer(text):                               # never touch links shown inside code blocks
        parts.append(LINK.sub(one, text[last:f.start()]))
        parts.append(f.group(0))
        last = f.end()
    parts.append(LINK.sub(one, text[last:]))
    return "".join(parts)


def on_page_markdown(markdown, page, config, files, **kw):
    root = _root(config)
    docs = os.path.relpath(config["docs_dir"], root).replace(os.sep, "/")
    page_dir = posixpath.dirname(posixpath.join(docs, page.file.src_uri))

    def include(m: re.Match) -> str:
        rel = m.group(1)
        for base in (root, config["docs_dir"]):
            full = os.path.join(base, rel)
            if os.path.isfile(full):
                src_dir = posixpath.dirname(os.path.relpath(full, root).replace(os.sep, "/"))
                with open(full, encoding="utf-8") as fh:
                    return rewrite(fh.read(), src_dir, page_dir, root, config)
        return m.group(0)

    markdown = SNIPPET.sub(include, markdown)
    return rewrite(markdown, page_dir, page_dir, root, config)
