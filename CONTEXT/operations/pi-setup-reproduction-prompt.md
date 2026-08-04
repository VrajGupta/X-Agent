# Pi setup reproduction prompt

You are a Pi coding-agent setup/reprovisioning agent. Reproduce the reference Pi environment described below as faithfully as possible. This is a **global user setup**, not a project feature. Work in the current user's home directory and do not modify the active project except where explicitly required for verification.

The goal is logical and visual parity with the reference: same Pi settings, same discovered resources, same extension behavior, same skills, same model defaults, same header/footer, same tool names, same commands, and the same dependency versions. Do not substitute generic third-party extensions when the reference source is available.

## Non-negotiable safety rules

1. Never print, log, paste, commit, or put in this prompt any secret from `auth.json`, `.env`, shell key files, API-key environment variables, or OAuth tokens.
2. Never copy `~/.pi/agent/auth.json` from the reference. Re-authenticate on the target with `/login` or environment variables. The reference only records credential *types*, not credentials.
3. Before replacing an existing target file, make a timestamped backup outside the active resource paths. Preserve unrelated user resources.
4. Do not run `pi update --all`, unpinned package upgrades, or a floating `npm install` when an exact lockfile/source snapshot is available. Use the supplied lockfiles and `npm ci`.
5. Do not add package entries, `settings.extensions`, `settings.skills`, custom prompts, or project-local `.pi` files unless this prompt explicitly calls for them. The reference uses automatic global discovery.
6. Do not claim exact/byte-identical reproduction without source/hash evidence. If the exact extension or skill source is unavailable, implement the documented behavior, label the result “behaviorally equivalent,” and report what could not be made byte-identical.
7. Ask before enabling/configuring Firecrawl. The reference has the Firecrawl extension installed but currently has no `.env` and no `FIRECRAWL_API_KEY` configured. If the user declines, remove only that optional integration and clearly report the intentional difference.

## Source-of-truth priority

Use these modes in order:

### A. Exact source mode

If a reference checkout, archive, or mounted directory is available, copy its non-secret files verbatim. The reference setup root is normally `~/.pi/agent`. On the original machine it was `/Users/vraj/.pi/agent`.

Copy the following classes of files, excluding `node_modules`, `sessions`, `auth.json`, `.env`, private summary config, generated caches, and machine-specific binaries unless the target has the same platform:

- `package.json`, `package-lock.json`, `tsconfig.json`, `.gitignore`, `.env.example`, `README.md`, `SETUP.md`, `AGENTS.md`
- `extensions/**` source, tests, docs, `package.json`, `package-lock.json`, and `tsconfig.json`
- `themes/github-dark-default.json`
- `skills/**`
- optionally `models-store.json` only when offline catalog parity is required

After copying, install dependencies with the exact lockfiles and verify the hashes listed below. Do not reimplement source that can be copied.

### B. Public-source mode

The custom skills source is available at:

- `https://github.com/VrajGupta/skills.git`
- reference branch: `fix-vkg-rename-and-npx-bug`
- reference HEAD: `6bc49e305159039e1bcb4eb1835e62f8d492a909`

Clone that commit into a working checkout and run its installer (`node bin/vskills.js init`) only after inspecting existing target skills and backing them up. Do not silently use the moving default branch when exact parity is requested.

The installed skill snapshot also contains material from these upstream sources, recorded by the reference lock data:

- `mattpocock/skills`
- `vercel-labs/skills` (`find-skills`)
- `jakubkrehel/skills` (`better-colors`, `better-typography`, `better-ui`)

If those exact source revisions are not available, copy the reference `~/.agents/skills` tree instead of pulling latest content. Do not overwrite drifted installed skills without a backup and explicit confirmation.

### C. Reconstruction mode

If no source bundle or reference checkout is available, recreate the setup from the exact configuration blocks and behavior contract below. Preserve the paths and names exactly. Write tests for the key behavior. Do not claim source-level identity.

## Required execution sequence

Follow this sequence rather than making ad hoc changes:

1. **Inventory:** resolve the target home, current `PI_CODING_AGENT_DIR`, Pi/Node/npm versions, platform/architecture, terminal capabilities, existing `~/.pi/agent`, `~/.agents/skills`, `~/.claude/skills`, auth presence (metadata only), and project trust state. Do not print secrets.
2. **Confirm optional Firecrawl:** ask the user whether to keep/configure Firecrawl. Preserve the extension by default to match the reference; do not request a key in chat. If enabled, tell the user to put it in `~/.pi/agent/.env` with mode 600 or export it in the shell.
3. **Back up:** create a timestamped backup of only conflicting target files/resources before replacing them. Never delete unrelated skills or extensions.
4. **Acquire source:** use exact source mode when a reference directory/archive is available; otherwise pin the public skills checkout to the stated commit and use reconstruction mode only for unavailable Pi extension source.
5. **Install runtime:** ensure Node >=22.19 and Pi CLI compatibility; copy the setup source; run `npm ci` at the root and in every extension directory with a lockfile; install native `fd`, `rg`, `gh`, and optional `claude`/`codex` as needed.
6. **Configure resources:** write the exact settings/theme/context files, leave absent files absent, put global skills in `~/.agents/skills`, and do not add explicit package/resource settings.
7. **Authenticate safely:** use `/login` for `openai-codex` first, then any other provider the user wants. Never copy or display `auth.json` values.
8. **Verify source and discovery:** compare hashes where exact source exists, run the full check/format/test gate, start a fresh Pi session, and verify every listed command/tool/header/footer behavior.
9. **Report honestly:** distinguish exact source parity, behavioral parity, and unavoidable host-dependent visual differences. Include every command run and its result.

Do not stop after writing files; the finished state is not verified until the fresh Pi session discovers the resources and the native checks pass.

## Reference machine/runtime

These are observations from the reference session, not credentials:

- OS/architecture: macOS arm64 (`darwin/arm64`)
- Node: `v22.22.3`
- npm: `10.9.8`
- Pi CLI in the managed terminal: `0.83.0`
- Pi config directory: default `~/.pi/agent` (`PI_CODING_AGENT_DIR` was not set)
- terminal: `TERM_PROGRAM=Superconductor`, `TERM_PROGRAM_VERSION=0.1.0`
- terminal protocol: `TERM=xterm-256color`, `COLORTERM=truecolor`
- `fd`: bundled `~/.pi/agent/bin/fd`, version `10.4.2`, macOS arm64
- `rg`: system `/opt/homebrew/bin/rg`, version `15.2.0`
- `gh`: installed and used by the git-info extension
- `claude` and `codex`: installed for the Claude and Codex subagent backends
- the reference had `PATH` beginning with `~/.pi/agent/bin`

On another OS or terminal, install the native equivalents. Do not fake `TERM_PROGRAM` or claim pixel identity unless the actual terminal, font, font size, cell dimensions, window size, DPI/scaling, color mode, and Pi version also match. The source can reproduce layout and colors; terminal hardware determines physical pixels.

## Pi installation and discovery model

Install/use the Pi coding agent with Node >=22.19.0. The reference's setup project depends on the following resolved versions:

- `@earendil-works/pi-coding-agent@0.82.0`
- `@earendil-works/pi-ai@0.82.0`
- `@earendil-works/pi-tui@0.82.0`
- `firecrawl@4.30.1`
- `typebox@1.3.7`
- `acorn@8.17.0`
- `typescript@7.0.2`
- `prettier@3.9.6`
- `@types/node@26.1.1`

The reference managed terminal itself reports Pi CLI `0.83.0`; retain that CLI/runtime version when it is available, while preserving the setup project's locked extension API dependencies above.

The global resource layout is:

```text
~/.pi/agent/
├── AGENTS.md
├── README.md
├── SETUP.md
├── .env.example
├── .gitignore
├── package.json
├── package-lock.json
├── tsconfig.json
├── settings.json
├── themes/github-dark-default.json
├── extensions/
│   ├── ask-user/
│   ├── background-terminals/
│   ├── copy-all/
│   ├── file-search/
│   ├── firecrawl-search/
│   ├── git-info/
│   ├── model-info/
│   ├── shared/
│   ├── subagents/
│   ├── summaries/
│   └── ui-customization/
├── skills/
│   ├── background-terminals/SKILL.md
│   └── subagents/SKILL.md
└── bin/
    └── fd                 # native fallback; do not copy cross-platform

~/.agents/skills/          # global shared Agent Skills tree, loaded by Pi
~/.agents/skills/.vskills-manifest.json # vskills source/hash/install metadata
~/.agents/.skill-lock.json # additional installer metadata
```

Pi automatically discovers all `~/.pi/agent/extensions/*/index.ts` directories and all skills under `~/.pi/agent/skills` and `~/.agents/skills`. There is intentionally no `extensions` or `skills` array in the reference `settings.json`. Do not convert this to a Pi package or add explicit extension paths.

Each extension with dependencies has its own `package.json`, lockfile, and `node_modules`. After copying source:

```bash
cd ~/.pi/agent
npm ci
for d in extensions/*; do
  if [ -f "$d/package-lock.json" ]; then npm --prefix "$d" ci; fi
done
```

The root project uses this exact `package.json` shape:

```json
{
  "dependencies": {
    "@earendil-works/pi-ai": "^0.82.0",
    "@earendil-works/pi-coding-agent": "^0.82.0",
    "@earendil-works/pi-tui": "^0.82.0",
    "acorn": "^8.17.0",
    "firecrawl": "^4.30.0",
    "typebox": "^1.3.6"
  },
  "devDependencies": {
    "@types/node": "^26.1.1",
    "prettier": "^3.9.5",
    "typescript": "^7.0.2"
  },
  "type": "module",
  "scripts": {
    "check": "tsc --noEmit",
    "format": "prettier --write \"extensions/**/*.{ts,cjs}\" \"*.json\"",
    "format:check": "prettier --check \"extensions/**/*.{ts,cjs}\" \"*.json\"",
    "test": "node --test --experimental-strip-types extensions/*/*.test.ts && npm --prefix extensions/file-search test"
  }
}
```

The root `tsconfig.json` is:

```json
{
  "compilerOptions": {
    "allowImportingTsExtensions": true,
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "noEmit": true,
    "skipLibCheck": true,
    "strict": true,
    "target": "ES2022",
    "types": ["node"],
    "verbatimModuleSyntax": true
  },
  "include": ["extensions/**/*.ts"]
}
```

Extension dependency contracts:

- `ask-user`, `background-terminals`, `summaries`: runtime `effect`; dev `@effect/tsgo`, `typescript`
- `copy-all`, `model-info`, `ui-customization`: dev `@effect/tsgo`, `typescript`
- `file-search`: runtime `@effect/platform-node`, `effect`; dev `@effect/tsgo`, `@effect/vitest`, `typescript`, `vitest@4.1.10`
- `firecrawl-search`: runtime `effect`, `firecrawl`; dev `@effect/tsgo`, `typescript`
- `git-info`: runtime `@effect/platform-node`, `effect`; dev `@effect/tsgo`, `typescript`
- `subagents`: runtime `@anthropic-ai/claude-agent-sdk`, `effect`; dev `@effect/tsgo`, `typescript`
- the extension lockfiles resolve `effect@4.0.0-beta.101`, `@effect/tsgo@0.24.3`, `@effect/platform-node@4.0.0-beta.101`, `@effect/vitest@4.0.0-beta.101`, `@anthropic-ai/claude-agent-sdk@0.3.218`, and `typescript@7.0.2`

## Exact global Pi settings

Write `~/.pi/agent/settings.json` exactly as follows, preserving valid JSON formatting:

```json
{
  "lastChangelogVersion": "0.83.0",
  "theme": "github-dark-default",
  "defaultProvider": "openai-codex",
  "defaultModel": "gpt-5.6-luna",
  "defaultThinkingLevel": "max",
  "compaction": {
    "enabled": true
  },
  "steeringMode": "all",
  "followUpMode": "one-at-a-time",
  "transport": "auto",
  "defaultProjectTrust": "ask"
}
```

Important defaults/absence are intentional:

- no custom `keybindings.json` (use Pi defaults)
- no `SYSTEM.md` or `APPEND_SYSTEM.md`
- no global `prompts/` directory or prompt templates
- no `models.json` (use Pi's built-in model catalogs plus generated `models-store.json`)
- no `enabledModels` restriction
- auto-compaction is on; reserve/keep-recent values remain Pi defaults
- project trust asks by default
- steering messages deliver `all`; follow-ups deliver one at a time
- provider transport is `auto`

## Exact GitHub Dark Default theme

Write `~/.pi/agent/themes/github-dark-default.json` exactly:

```json
{
  "$schema": "https://raw.githubusercontent.com/badlogic/pi-mono/main/packages/coding-agent/src/modes/interactive/theme/theme-schema.json",
  "name": "github-dark-default",
  "vars": {
    "bg": "#0d1117",
    "panel": "#010409",
    "surface": "#161b22",
    "border": "#30363d",
    "borderMuted": "#21262d",
    "accent": "#2f81f7",
    "focus": "#1f6feb",
    "text": "#e6edf3",
    "muted": "#7d8590",
    "dim": "#6e7681",
    "green": "#3fb950",
    "red": "#f85149",
    "yellow": "#d29922",
    "purple": "#d2a8ff",
    "orange": "#ffa657",
    "cyan": "#79c0ff",
    "string": "#a5d6ff",
    "softGreen": "#7ee787",
    "softRed": "#ff7b72"
  },
  "colors": {
    "accent": "accent",
    "border": "border",
    "borderAccent": "focus",
    "borderMuted": "borderMuted",
    "success": "green",
    "error": "red",
    "warning": "yellow",
    "muted": "muted",
    "dim": "dim",
    "text": "text",
    "thinkingText": "muted",
    "selectedBg": "#13233a",
    "userMessageBg": "surface",
    "userMessageText": "text",
    "customMessageBg": "surface",
    "customMessageText": "text",
    "customMessageLabel": "accent",
    "toolPendingBg": "surface",
    "toolSuccessBg": "surface",
    "toolErrorBg": "#2b1618",
    "toolTitle": "accent",
    "toolOutput": "muted",
    "mdHeading": "cyan",
    "mdLink": "accent",
    "mdLinkUrl": "muted",
    "mdCode": "cyan",
    "mdCodeBlock": "text",
    "mdCodeBlockBorder": "border",
    "mdQuote": "muted",
    "mdQuoteBorder": "border",
    "mdHr": "borderMuted",
    "mdListBullet": "orange",
    "toolDiffAdded": "green",
    "toolDiffRemoved": "red",
    "toolDiffContext": "muted",
    "syntaxComment": "#8b949e",
    "syntaxKeyword": "softRed",
    "syntaxFunction": "purple",
    "syntaxVariable": "orange",
    "syntaxString": "string",
    "syntaxNumber": "cyan",
    "syntaxType": "softGreen",
    "syntaxOperator": "text",
    "syntaxPunctuation": "dim",
    "thinkingOff": "dim",
    "thinkingMinimal": "muted",
    "thinkingLow": "accent",
    "thinkingMedium": "cyan",
    "thinkingHigh": "purple",
    "thinkingXhigh": "softRed",
    "bashMode": "green"
  },
  "export": {
    "pageBg": "bg",
    "cardBg": "panel",
    "infoBg": "surface"
  }
}
```

## Extensions: exact loaded surface and behavior

All ten extension entrypoints are auto-loaded. The `extensions/shared` directory is a helper module directory and is not itself an extension. If exact source is available, copy the whole directories, not only `index.ts`; the tests and helper modules encode important lifecycle and rendering details.

### `ask-user`

Registers the `ask_user` model tool. Schema: a question plus 2–5 labeled options, each with an optional description. Adds an always-present `Write my own answer…` option. In the TUI it is a bordered custom component using the active theme: arrows or number keys select, Enter confirms, Escape dismisses, and the custom option opens an inline editor. It returns structured details (`question`, labels, answer, `wasCustom`, `cancelled`) and renders selected/custom/dismissed states. In non-TUI modes it returns a no-UI result rather than trying to open a terminal component.

### `background-terminals`

Registers:

- `bg_start(command, title, working_dir?)`
- `bg_status(id)`
- `bg_list()`
- `bg_kill(ids)`

It starts long-running shell processes with stdin ignored, captures bounded output plus spill files, supports whole-process-tree termination (`SIGTERM` then `SIGKILL`), tracks at most 8 simultaneously running terminals, and cleans all processes on session shutdown/reload. Unconsumed settlements are delivered exactly once as follow-up messages. While one or more terminals run, a one-line widget above the editor says `N background terminal(s) running • /ps to view`. Registers `/ps`, which opens a list/detail overlay in TUI mode and a notification in non-TUI UI mode. Output is sanitized before rendering. Do not replace it with tmux or a generic background shell.

### `copy-all`

Registers `/copy-all`. Waits for Pi to become fully idle, extracts all prior user and assistant messages in the active branch, formats them as `USER:`/`ASSISTANT:` sections separated by `---`, copies the result with Pi's clipboard helper, and notifies how many messages were copied. It includes text and represents image blocks as `[image]`.

### `file-search`

Registers first-class model tools `fd` and `rg`, with custom compact call/result rendering. Resolution order per binary is: usable system command (`fd`/`fdfind`, or `rg`), existing `~/.pi/agent/bin` fallback, then an official HTTPS release download with SHA-256 verification. Current official versions are fd `10.4.2` (Intel macOS fallback `10.3.0`) and ripgrep `15.2.0`; downloads are bounded and installed atomically. Search calls time out after 60 seconds, distinguish no-match exits, cap results, and save full output to a spill file when truncated. Current reference uses the bundled arm64 fd and system rg. Preserve the `fd`/`rg` names and schemas.

### `firecrawl-search`

Registers `search`, `crawl`, and `scrape` model tools backed by the Firecrawl SDK. Reads `FIRECRAWL_API_KEY` first from the process environment and then from `~/.pi/agent/.env`. `search` defaults to 5 results and supports web/news/images and optional markdown scraping; `crawl` defaults to 20 pages and polls every 2 seconds, cancelling the remote crawl on interrupted failure; `scrape` returns markdown and optional metadata. Requests and output are bounded/truncated and cancellation/errors are explicit. The reference has `.env.example` containing only `FIRECRAWL_API_KEY=fc-YOUR-API-KEY`; it does not have a configured `.env`.

### `git-info`

Maintains a background dashboard state by polling every 3 seconds. It runs `git` with a 3-second command timeout and, when on a branch, `gh pr view <branch> --json number,url,state,isDraft` with a 10-second timeout. It publishes branch, changed-file count, and open PR data over the shared extension event bus. Registers `/lg` for a changed-files/diff browser and `/pr` to force-refresh git/PR state. It handles non-git directories without errors and stops all fibers on session shutdown.

### `model-info`

Tracks provider, model id/name, effective thinking level, context tokens/window/percentage, cumulative session cost, generation state, and estimated token-per-second. It uses assistant stream deltas, estimates text at 4 characters per token when necessary, updates live no faster than every 200ms, and publishes the state over the shared event bus. It resets run/message tracking correctly and refreshes on model/thinking/turn/settled events.

### `subagents`

Registers model tools:

- `subagent_spawn(prompt, name, harness, working_dir?, model?, reasoning_effort?)`
- `subagent_wait(ids)`
- `subagent_cancel(ids)`
- `subagent_check(id)`
- `subagent_list()`

It supports three backends: `pi` (in-process Pi SDK session), `claude` (Claude Agent SDK), and `codex` (Codex app-server JSON-RPC). It has a global cap of 4 running subagents, normalized transcripts/status/usage, bounded output, exact-once settlement delivery, context-utilization reporting, trust propagation for same/alternate working directories, and cleanup on shutdown. Registers `/btw` for a one-off Pi side question with a TUI takeover view and `/subagents` for a picker/full takeover view. Keep the backend model semantics: Pi accepts `provider/model-id`, Claude accepts its model alias, and Codex accepts its model slug. The target must have authenticated `claude` and `codex` executables if those backends are to work.

### `summaries`

After each fully settled TUI agent run, slices the current run transcript, calls a separate summary model, and appends a TUI-only `summary-recap` entry. Default private summary config is:

```json
{
  "provider": "openai-codex",
  "model": "gpt-5.6-luna",
  "reasoning": "medium"
}
```

The private file is `extensions/summaries/config.private.json`, mode 600, and is absent in the reference so the default is active. `/summary-model` chooses the summary model and reasoning level. The summary model receives a strict JSON prompt and returns `{ "recap": "...", "next": "..." }`; recap is bounded to 2,400 characters and next to 400. Invalid/failed summary calls render a sanitized local fallback and never block the next main-agent turn. Active summaries show a `✦ summarizing run…` footer status and are aborted/cleared on shutdown.

### `ui-customization`

This is the visual shell. On every TUI session it:

1. Replaces the header with centered six-line block-art Pi logo:

```text
  ██████╗  ██╗
  ██╔══██╗ ██║
  ██████╔╝ ██║
  ██╔═══╝  ██║
  ██║      ██║
  ╚═╝      ╚═╝
```

   It adds a blank line above and below, centers the art, and applies a per-character blue gradient using RGB stops `[22,83,189]`, `[48,129,247]`, `[93,171,255]`, `[151,205,255]`, `[93,171,255]`, `[48,129,247]`. The title is bold `pi` with the same gradient. The gradient is raw truecolor ANSI and is intentionally independent of the theme.

2. Replaces the footer with two dashboard lines plus extension status lines. Left/right columns are width-aware and ANSI-safe:
   - line 1: abbreviated cwd (`~`/`~/...`) on the left; `provider/model-id · thinking-level` on the right
   - line 2: `contextPercent%/formattedContextWindow · $cost.toFixed(2) · rounded tok/s` on the left; `branch · N file(s) changed · PR #number` on the right when available
   - statuses are sorted by extension key and rendered one row each

3. Sets the terminal title to `pi · <formatted cwd>`.

4. Hides the built-in `[Themes]` startup-header section after startup/resource discovery using the same staged cleanup delays (0ms, 50ms, 250ms, 1000ms).

Do not “improve” the logo, spacing, gradient, footer labels, colors, or border behavior. Those details are part of the requested visual parity.

## Skills

Pi loads the following 73 active global skills from `~/.agents/skills` in the reference. Preserve each directory's complete `SKILL.md`, references, scripts, and assets. Names are:

```text
ai-subscription-unit-economics
ask-matt
batch-grill-me
better-colors
better-typography
better-ui
caveman
claude-handoff
coach
code-review
codebase-audit
codebase-design
controlled-ticket-delivery
dependency-auditor
design-an-interface
diagnose
diagnosing-bugs
domain-modeling
edit-article
find-skills
git-guardrails-claude-code
github-projects-pipeline
grill-me
grill-with-docs
grilling
handoff
implement
improve-codebase-architecture
invariant-evidence-review
loop-engineer
loop-me
migrate-to-shoehorn
obsidian-vault
parallel-subagent-implementation
planner
coder
debugger
reviewer
profile-gated-delivery
prototype
provider-integration-tdd
push-handoff
qa
release-notes
request-refactor-plan
research
resolving-merge-conflicts
scaffold-exercises
setup-matt-pocock-skills
setup-obsidian
setup-pre-commit
setup-ts-deep-modules
setup-vskills
shared-worktree-delegation
shared-worktree-safety
specialist-profiles
state-driven-pipeline-recovery
subagent-batch-implementation
tdd
teach
ticket-implementation-tdd
to-spec
to-tickets
triage
ubiquitous-language
wayfinder
wizard
write-a-skill
writing-beats
writing-fragments
writing-great-skills
writing-shape
zoom-out
```

The two local Pi-only skills under `~/.pi/agent/skills` are:

- `background-terminals`: use `bg_start` for long-running commands; background processes receive no stdin, use `bg_status`/`bg_list`/`bg_kill`, and tell the user about `/ps`.
- `subagents`: use the native `subagent_spawn`/wait/check/list/cancel tools; children are headless, cannot ask the user, and must not spawn nested agents. Default native limit is 3 active children and tree depth is 1. It documents Pi/Claude/Codex harness selection and the fleet model map.

`~/.agents/skills` is the shared Agent Skills location, so do not add a `skills` setting to Pi. If cross-harness parity is desired, keep real skill content in `~/.agents/skills` and create/update symlinks in `~/.claude/skills`; Pi itself only requires the former. Exclude `.vskills-backup` directories from active discovery.

## Context files

For exact reference behavior, install these context instructions:

### `~/.pi/agent/AGENTS.md`

```text
- run check/format/lint commands when your done making a change. if they don't exist, suggest making them for the project you're in
- avoid explicit return types unless absolutely needed
- `as any` should be an absolute last resort. always use real type safety. lean on type inference instead of manually writing new types over and over again
```

### `~/AGENTS.md`

```markdown
# Global Agent Boundaries

These rules apply across all active workspaces and repositories.

## Hierarchy limits

- `MAX_SUBAGENTS = 3`: a top-level session may have at most three active native subagents at once. Keep the pipeline stages serial and do not use the limit as permission to claim multiple tickets.
- `MAX_TREE_DEPTH = 1`: the top-level parent of a session may spawn subagents; native subagents must never spawn, delegate to, or orchestrate other subagents.
- **Flat star topology per session:** the top-level session owns coordination, synthesis, task tracking, and follow-up for its children. A separately launched stage-parent session is not a child of another session and may run its own one-level child tree, subject to the same limits.

## Usage discipline

- Prefer direct execution by the main agent. Use a subagent only when its independent context materially improves speed or correctness.
- Reuse or resume an existing subagent instead of starting another one for related work.
- Prompts sent to subagents must explicitly say: "Do not spawn subagents; complete this task directly."
- Do not use multi-agent workflows unless the user explicitly asks for one. When explicitly requested, keep the workflow below the three-subagent ceiling and preserve a maximum tree depth of one.
- If the task cannot fit within these limits, stop and ask the user before increasing either limit.

## Fleet workflow and stage-parent model

The default delivery workflow is a serial four-stage fleet. GPT-5.6 Luna is the overall coordinator. It may dispatch the interactive planning work to an Opus 5 Claude Code child after the human decisions are known, while `/coder`, `/debugger`, and `/reviewer` run as independent top-level stage-parent chats. A stage parent is the chat/session that runs a stage and, when its harness supports it, may coordinate its own one-level child workers. A native child launched from another session is not a stage parent and must not spawn nested children.

| Stage | Stage-parent model / harness | Effort | Auth route |
|---|---|---|---|
| `/planner` | Opus 5 in Claude Code, dispatched by Luna or run visibly | medium; high for ambiguous/high-risk plans | Claude Code subscription/login |
| `/coder` | Kimi K3 in the Pi harness via OpenRouter | high | OpenRouter API key |
| `/debugger` | GPT-5.6 Luna in the Codex harness | **max** for adversarial debugging | Codex subscription |
| `/reviewer` | Grok 4.5 in the Pi harness via OpenRouter | high or xhigh | OpenRouter API key |

Coder may use Kimi K2.7 Code helpers and debugger may use auditor helpers only when Kimi/Codex is the independent top-level stage parent. If those stages are launched as native children, they work directly without nested dispatch. Reviewer remains blind: helpers, if used, receive only the ticket, diff, gate, and invariant docs.

If Luna dispatches Opus as a headless Claude child, the planning prompt must contain all decisions needed for the run; the child cannot ask the human. Use a visible Claude Code stage session when the `/planner` grill still needs interaction.

The stage handoff is carried by the GitHub Project item's `Status`, the GitHub issue, the git branch/PR, and the handoff document—not by parent-chat history. Run stages serially, work one ticket at a time, and let the next stage re-read those durable artifacts. `/planner` is interactive; a headless child cannot ask the human planning questions, so run its grill in a visible top-level session or provide all decisions in its prompt.

`max` is a reasoning-effort setting, not a model name. If a provider or harness changes, record the exact model ID and harness in the handoff while preserving the maker/debugger/reviewer separation.

## Runtime layer: super.engineering and Herdr

Use **super.engineering** as the managed-workspace authority for worktrees, target/base branches, app-managed sessions, and reviews when working inside this environment. Use **Herdr** as an optional local terminal multiplexer for visible, persistent panes and independent top-level stage-parent processes. Herdr can make the sessions easier to watch and reconnect to, but it does not replace GitHub Projects as workflow authority or git/GitHub as code truth. Do not let two tools independently create or mutate the same managed worktree; keep worktree ownership with super.engineering and use Herdr inside that workspace for process visibility.
```

The reference cwd `/Users/vraj/Work/miscellaneous` had no project-local `AGENTS.md`, `.pi/settings.json`, prompts, themes, or extensions. Do not create project-local resources for this setup.

## Authentication and generated state

The reference `~/.pi/agent/auth.json` is mode `0600` and has these provider entries, without exposing values:

- `anthropic`: OAuth credentials
- `openai-codex`: OAuth credentials (this is the default provider/model route)
- `openrouter`: API-key credential

On the target, run the appropriate `/login` flows or configure provider environment variables. Verify only provider names/types and whether authentication resolves; never print tokens.

The reference also has a generated `models-store.json` mode `0600` with catalogs for `anthropic` (15 models), `openai-codex` (7), and `openrouter` (300). It is cache/generated state, not hand-authored configuration. Copy it only for offline exact-catalog parity; otherwise run `pi update --models` after authentication and accept that catalog timestamps/model inventory may differ.

## Verification gate

After installation, reload/restart Pi and run all of these from `~/.pi/agent`:

```bash
node --version
npm --version
pi --version
npm run check
npm run format:check
npm test
```

Expected reference gate: TypeScript check passes, Prettier check passes, 101 Node tests pass, and the file-search Vitest suite passes with 22 tests. Test counts are evidence for this snapshot, not a reason to write brittle count assertions.

Then verify resource discovery in an interactive TUI session:

1. Startup lists the global context, skills, and all ten global extensions.
2. `/settings` shows `github-dark-default`, default provider `openai-codex`, default model `gpt-5.6-luna`, max thinking, steering `all`, follow-up `one-at-a-time`, and project trust `ask`.
3. Header shows the centered blue-gradient block-art Pi logo and no built-in Themes section.
4. Footer shows cwd/model on line 1, context/cost/tok/s and git/PR data on line 2, with extension statuses below when active.
5. `/hotkeys` shows Pi defaults because no custom keybindings file exists.
6. `/copy-all`, `/lg`, `/pr`, `/ps`, `/btw`, `/subagents`, and `/summary-model` are registered.
7. The model tools include `ask_user`, `bg_start`, `bg_status`, `bg_list`, `bg_kill`, `fd`, `rg`, `search`, `crawl`, `scrape`, and the five `subagent_*` tools.
8. Start and kill a harmless background process and confirm one completion message, then verify `/ps`.
9. Run `fd` and `rg` against a temporary directory.
10. Do not call Firecrawl unless the user configured a key.

For source-level verification, the reference hashes of the loaded extension entrypoints are:

```text
ask-user/index.ts             d17dfc151bd70a224d986e77f54a4f4e5abb6f1a2928aa9bb5efe01bc9485135
background-terminals/index.ts 668ce4c51f66a83ba18309d4b6701f5db28e4c6aa9ec321bc1d1e29202ec8b99
copy-all/index.ts             4f9758d6e151a6fded47d92b32f0dae160bbc15657c5dc44d97d1a6cc1c91c01
file-search/index.ts          6c86ad02183a9f19b3712e1c3e3f1615798127173fb8aeaf728f988d0d861360
firecrawl-search/index.ts     5ce5d86757f9721a916dcdc49faae6279a92b1017b83ed0b70d50dce42e32883
git-info/index.ts             e50ee381155ceee6f91f705ee397b0b0d04a48b4a4c5d73a7f9a57fd7d050c78
model-info/index.ts           fd05756dbdc864e0e94cbbeed772c3c74a8c96b078ee73c3ead3f112fae60887
subagents/index.ts            9f00315072ea41c3b13d40278171db229401c061d92048b5a45c7c92d13b1b29
summaries/index.ts            54e41cfb0160b93312816e28d84b67e4df6529b55cb1d6f9825b65968191fe1c
ui-customization/index.ts     1420c50c77d348e8e2f19c7126a87b930901b6a64d3a4b0dd74019d5c645f185
```

Reference config hashes:

```text
settings.json                       07e37c3a90c771065bc62ee9171ea982e00e4f54c0669e3556c0f0ccd993fb53
themes/github-dark-default.json     7257d53fb309b699bebee931875f8f9f4c0f7ae36099d48ad36d336aa846f40b
package.json                         99a8e4bada4b036c5459eb673b96265c41793457cca2716d75e65524597015c3
tsconfig.json                        f0f1f67fc44314bf753ca7c06ff337b8d72ba939384c2e96b061ba91c29bfd50
~/.pi/agent/AGENTS.md                dd11ed10d3649bdceb9e78ec43272e15c692b946179a0ca8f82e9fcfeaff337f
```

Finish with a concise report containing:

- what was copied/installed and from which source/revision;
- which files were intentionally not copied for security or portability;
- exact commands and results for every verification gate;
- authentication and Firecrawl status without secrets;
- any remaining visual differences caused by terminal/font/platform constraints;
- whether the result is exact source parity or only behavioral parity.

Do not stop at “looks good”; prove discovery, checks, tests, and the visual contract.
