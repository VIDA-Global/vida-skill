# Vida API skill

This repository is the source of truth for Vida's `vida-api` agent skill.

The skill teaches agents how to use Vida's API for account onboarding, Agent configuration,
contacts, Tasks, integrations, optional reseller administration, Computer Agent setup and
operations, logs, and conversations. Review [SKILL.md](./SKILL.md) here.

For the complementary end-to-end workflow that turns a software opportunity into a configured,
tested Vida Agent—with optional browser helpers, schedules, Canvas, demo videos, landing pages, and
launch content—use the public
[`build-vida-agent` skill](https://github.com/VIDA-Global/build-vida-agent-skill). It uses this skill
as the source of truth for exact Vida API execution.

The generated [OpenAPI reference](https://vida.io/docs/apiv2.json) defines exact endpoint schemas.
Vida's [API guides](https://vida.io/docs/api-reference/overview) explain product concepts and
multi-step workflows. This skill supplies the execution order, safety rules, and verification
requirements an API-using agent needs to perform those workflows reliably.
