# Hugging Face Daily Papers Skill

![Skill](https://img.shields.io/badge/Skill-Agent-111111?style=flat-square)
![Claude Code](https://img.shields.io/badge/Claude%20Code-Supported-6B5B95?style=flat-square)
![Codex](https://img.shields.io/badge/Codex-Supported-222222?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)

一个适配 Claude Code / Codex 等本地 Agent 环境的论文日报 skill。

它会抓取 `https://hf-mirror.com/papers/date/YYYY-MM-DD`，筛选投票数大于阈值的 Hugging Face Daily Papers，按投票数倒序输出，并整理成中文结构化笔记，包含：

- 论文标题与中文标题
- 论文链接
- 作者单位
- 投票数
- 问题、方法、创新点、结论

## 30 秒开始

```bash
npx skills add https://github.com/ts87/hugging-face-daily-papers --skill hugging-face-daily-papers
```

也可以直接把这段话发给有 shell 权限的 AI Agent：

```text
帮我安装 hugging-face-daily-papers。请把 https://github.com/ts87/hugging-face-daily-papers 克隆到 ~/.claude/skills/hugging-face-daily-papers，然后检查 SKILL.md、scripts/fetch_daily_papers.py 是否存在。
```

Codex 用户也可以安装到 `~/.codex/skills/`：

```bash
git clone https://github.com/ts87/hugging-face-daily-papers.git ~/.codex/skills/hugging-face-daily-papers
```

安装后重启 Agent，然后直接说：

```text
用 hugging-face-daily-papers 看一下 2026-05-22 的论文，按投票数倒序整理。
```

## 使用方式

在 skill 目录内运行：

```bash
python3 scripts/fetch_daily_papers.py --date 2026-05-22
```

常用参数：

```bash
python3 scripts/fetch_daily_papers.py
python3 scripts/fetch_daily_papers.py --date 2026-05-22
python3 scripts/fetch_daily_papers.py --min-votes 10 --limit 20
python3 scripts/fetch_daily_papers.py --base-url https://huggingface.co
```

默认规则：

- 日期：北京时间昨天
- 来源：`https://hf-mirror.com/papers/date/YYYY-MM-DD`
- 过滤：投票数 `> 5`
- 排序：按投票数倒序
- 摘要：优先读取每篇论文的 `.md` 详情页

## 输出格式

Skill 会要求 Agent 将每篇论文整理成：

```markdown
### English Title
中文标题

论文链接：https://arxiv.org/pdf/xxxx.xxxxx
作者单位：...
投票数：...

问题：...
方法：...
创新点：
- ...
- ...

结论：...
```

## 适合 / 不适合

适合：

- 做 AI 论文日报
- 挑选 Hugging Face Daily Papers 高票论文
- 自动化生成中文技术简报

不适合：

- 严格学术综述，仍需人工读原文复核
- 需要论文全文深度审稿的场景
- 没有网络访问能力的 Agent 环境

## 更新

```bash
cd ~/.claude/skills/hugging-face-daily-papers
git pull
```

或 Codex：

```bash
cd ~/.codex/skills/hugging-face-daily-papers
git pull
```

## License

MIT
