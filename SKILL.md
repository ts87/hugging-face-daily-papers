---
name: hugging-face-daily-papers
description: Fetch and summarize Hugging Face Daily Papers from hf-mirror.com. Use when the user asks for "Hugging Face每日论文", "HF 每日论文", "Hugging Face papers today/yesterday", or wants the previous day's hf-mirror.com/papers/date/yyyy-mm-dd papers filtered by vote count, sorted by votes, with introductions or abstracts.
---

# Hugging Face Daily Papers

> Source: `hugging-face-daily-papers` is a portable skill for Claude Code, Codex, and other local coding-agent environments. Keep generated reports focused on the papers; do not include this provenance line in user-facing paper summaries unless the user asks about the skill itself.

## Workflow

Use the bundled script first; it handles date calculation, list-page parsing, vote filtering, detail-page fetching, and Markdown output.

```bash
python3 scripts/fetch_daily_papers.py
```

Defaults:

- Date: yesterday in `Asia/Shanghai`.
- Source: `https://hf-mirror.com/papers/date/YYYY-MM-DD`.
- Filter: vote count greater than `5`.
- Sort: descending by vote count.
- Detail source: each paper's `https://hf-mirror.com/papers/<id>.md`.

Useful options:

```bash
python3 scripts/fetch_daily_papers.py --date 2026-05-22
python3 scripts/fetch_daily_papers.py --min-votes 10 --limit 20
python3 scripts/fetch_daily_papers.py --base-url https://huggingface.co
```

If the current working directory is not the skill directory, resolve `scripts/fetch_daily_papers.py` relative to this `SKILL.md` file.

## Output Guidance

When answering the user in Chinese, turn each paper into the following structured note. Use this as the default format unless the user asks for a shorter list:

```markdown
### <English title>
<Chinese title>

论文链接：<prefer https://arxiv.org/pdf/<paper_id> when the id is an arXiv id; otherwise use the HF URL>
作者单位：<institutions if available from the markdown detail; otherwise "未在摘要中明确">
投票数：<votes>

问题：<1-2 sentences>

方法：<1-3 sentences>

创新点：
- <point 1>
- <point 2>
- <point 3 when useful>

结论：<1-2 sentences with benchmark/result details when available>
```

Guidelines:

- Keep vote count and paper link.
- Sort exactly by vote count descending.
- Prefer `https://arxiv.org/pdf/<paper_id>` for arXiv papers such as `2605.21467`.
- Add a Chinese title translation under the English title.
- Extract institutions from the paper detail when obvious. If not obvious, say `未在摘要中明确` instead of guessing.
- Summarize `问题`, `方法`, `创新点`, and `结论` from the abstract/detail page.
- Prefer 1-3 concise sentences per field; keep the whole answer scan-friendly when many papers pass the threshold.
- Mention the effective page date if `hf-mirror.com` redirects from the requested date to another date.
- If no papers pass the vote threshold, say so and include the source URL checked.

If the script fails because the page layout changed, inspect the relevant list/detail HTML and patch `scripts/fetch_daily_papers.py` rather than hand-collecting results.
