from __future__ import annotations

class ContextBudgeter:
    """256: keep codebase context useful without sending the entire repository."""

    def trim(self, context, max_chars=90000):
        files = list(context.get("files", []))
        ranked = sorted(
            files,
            key=lambda x: (
                0 if str(x.get("path", "")).startswith(("tests/", "agents/", "companyos_")) else 1,
                len(str(x.get("content", ""))),
            ),
        )
        out, used = [], 0
        for item in ranked:
            content = str(item.get("content", ""))
            if used + len(content) > int(max_chars):
                continue
            out.append(item)
            used += len(content)
        return {"files": out, "file_count": len(out), "char_count": used, "max_chars": int(max_chars)}
