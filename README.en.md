# Hugging Face Daily Papers Skill

An agent skill for Claude Code, Codex, and similar local coding-agent environments.

It fetches Hugging Face Daily Papers from `https://hf-mirror.com/papers/date/YYYY-MM-DD`, filters papers by vote count, sorts them by votes, and helps agents produce structured Chinese research notes.

## 30-second start

```bash
npx skills add https://github.com/ts87/hugging-face-daily-papers --skill hugging-face-daily-papers
```

Or install manually:

```bash
git clone https://github.com/ts87/hugging-face-daily-papers.git ~/.claude/skills/hugging-face-daily-papers
```

For Codex:

```bash
git clone https://github.com/ts87/hugging-face-daily-papers.git ~/.codex/skills/hugging-face-daily-papers
```

Restart your agent after installation.

## Usage

From the skill directory:

```bash
python3 scripts/fetch_daily_papers.py --date 2026-05-22
```

Useful options:

```bash
python3 scripts/fetch_daily_papers.py
python3 scripts/fetch_daily_papers.py --date 2026-05-22
python3 scripts/fetch_daily_papers.py --min-votes 10 --limit 20
python3 scripts/fetch_daily_papers.py --base-url https://huggingface.co
```

Defaults:

- Date: yesterday in Asia/Shanghai
- Source: `https://hf-mirror.com/papers/date/YYYY-MM-DD`
- Filter: votes greater than `5`
- Sort: descending by votes

## Output

The skill asks the agent to summarize each paper with:

- English and Chinese title
- Paper link
- Institution
- Vote count
- Problem
- Method
- Novelty
- Conclusion

## License

MIT
