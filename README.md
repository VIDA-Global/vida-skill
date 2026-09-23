# Vida API skill

This repository is the source of truth for Vida's `vida-api` agent skill. The skill 
teaches agents how to use Vida's API for account onboarding, Agent configuration,
contacts, Tasks, integrations, optional reseller administration, Computer Agent setup and
operations, safe Computer Agent cloning, logs, and conversations. 
Review [SKILL.md](./SKILL.md) here.

Give your coding assistant this repository URL and ask it to install the skill and guide you
through API access:

> Install the Vida API skill from https://github.com/VIDA-Global/vida-skill for my
> agent environment. Read its README and SKILL.md, keep the `references/` directory
> with it, then help me set up `VIDA_API_KEY` privately and verify access with a
> read-only account request. Do not ask me to paste the key into chat.

## Install the skill

The repository root is the skill directory: `SKILL.md` and `references/` must stay
together. An assistant should check whether `vida-api` is already installed and
update that installation if possible. For a new local installation, clone this
repository as the `vida-api` directory in the host's personal skills location:

| Host | Personal skill directory |
| --- | --- |
| Codex | `~/.agents/skills/vida-api/` |
| Claude Code | `~/.claude/skills/vida-api/` |

For example, in Codex:

```bash
mkdir -p ~/.agents/skills
git clone https://github.com/VIDA-Global/vida-skill.git ~/.agents/skills/vida-api
```

For Claude Code, use the same command with `~/.claude/skills` in both paths. For an
existing Git clone, run `git -C <skill-directory> pull --ff-only` after checking
for local changes. If your host uses a different skill location or installer, use
its supported method and verify that `SKILL.md` and `references/` are present.
Codex also supports its built-in `$skill-installer` for GitHub repositories. If the
skill does not appear after installation, start a new agent session.

## Get and supply a Vida API key

If you are the assistant helping with setup, walk the user through this section in
chat after installing the skill. Tell them where to create the key and give them
the instructions that fit their environment. For a local Bash CLI, show the
private-entry commands below and tell the user to run them in their own terminal.
For a desktop or remote agent, explain how to use that host's private secret
mechanism if one is available. Do not stop at a link to this README or ask the
user to send you the key. Once the user has supplied it privately, check for it
without displaying it and perform the read-only account check below.

1. Sign in to [Vida](https://vida.io/app), open your default Agent, and go to
   **Settings → Developer → API Keys**. The direct page is
   `https://vida.io/app/agent/{accountId}/settings/developer`, where `accountId`
   is that Agent's account ID.
2. Select **New Key**, name it for the assistant or workflow, and copy the value.
   For work on one Agent, use that Agent's key. The skill explains when a reseller
   or partner key is appropriate.
3. Make the value available to your agent runtime as `VIDA_API_KEY` through a
   secure secret store or a private environment variable. Do not paste it into
   chat, a repository, a `.env` file, a Task, or an assistant work log.

For a local Codex or Claude Code CLI session in Bash, you can enter the key without
echoing it or saving it in shell history:

```bash
read -r -s -p 'Vida API key: ' VIDA_API_KEY
printf '\n'
export VIDA_API_KEY
```

Then launch `codex` or `claude` from that same terminal so the process inherits
the variable. An already-running app or a remote agent will not inherit this
terminal's variable; use that host's private secret mechanism, or switch to a
local CLI session if it has none. Do not print the variable or put its value in
a command you send to the assistant.

Ask the assistant to verify that the variable is available without showing it,
then call `GET /api/v2/account` without a target account. Vida requires the key in
the `token` query parameter, so request URLs containing it must be kept out of
logs and responses. If access fails, the assistant should diagnose the status
without exposing the key. Rotate a key that has been exposed.

See [Vida's authentication guide](https://vida.io/docs/api-reference/authentication)
for account scopes and eligibility. API key creation may require an eligible plan.

## API reference

The generated [OpenAPI reference](https://vida.io/docs/apiv2.json) defines exact endpoint schemas.
Vida's [API guides](https://vida.io/docs/api-reference/overview) explain product concepts and
multi-step workflows. This skill supplies the execution order, safety rules, and verification
requirements an API-using agent needs to perform those workflows reliably.
