# Issue tracker: GitHub

Issues and specs live in GitHub Issues for `naufalahmadfauz/cognigy-grab-poc`. Use the `gh` CLI.

## Conventions

Run commands inside this clone. Outside it, specify `--repo naufalahmadfauz/cognigy-grab-poc`.

- Create: `gh issue create --title "..." --body-file -`; supply multiline bodies through a heredoc.
- Read: `gh issue view <number> --json number,title,body,labels,comments`.
- List: `gh issue list --state open --json number,title,body,labels,comments`; add appropriate label/state filters and a sufficient `--limit`.
- Comment: `gh issue comment <number> --body-file -`.
- Apply/remove labels: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`.
- Close: `gh issue close <number> --comment "..."`.
- Create a sub-issue: `gh issue create --parent <parent> ...`. If native sub-issues are unavailable, put `Part of #<parent>` at the top of the child body and link it from the parent.
- Use native GitHub issue dependencies for blockers. If unavailable, put `Blocked by: #<number>` at the top of the blocked issue. It becomes unblocked when every blocker is closed.

## Pull requests as a triage surface

**PRs as a request surface: no.**

## Skill operations

When a skill says "publish to the issue tracker", create a GitHub issue.
When it says "fetch the relevant ticket", read the GitHub issue.

## Wayfinding operations

- Map: one issue labelled `wayfinder:map`, holding Notes / Decisions-so-far / Fog.
- Child ticket: link it to the map as a sub-issue, or use the parent/task-list fallback above. Use `wayfinder:<type>` labels for research, prototype, grilling, or task.
- Frontier: inspect the map's open children; exclude assigned tickets and tickets with open blockers; take the first remaining ticket in map order.
- Claim: `gh issue edit <number> --add-assignee @me`.
- Resolve: comment with the answer, close the ticket, and add a gist/link to the map's Decisions-so-far.
