# The golden brief: one step, test first, small enough to finish alone

A brief is read by a model that cannot see the chat: an open model (path A or B) or a Sonnet subagent (path C).
It gets one attempt of about 40 minutes, and the slow gate at the end takes about 10 of them. So a brief is ONE step.
Copy the template, fill every line, and check it before you send it:

    TASK="$(cat brief.txt)" python3 lifecycle/autobuild_ci.py check     # prints nothing when the brief is fit

## The template (6 lines, at most 1,500 characters)

```
<Area>: <the outcome in the owner's words, one sentence> (owner <date>; queue id <id>, slice <n> of <m>).
Test first: add <path/testNN.js or path/test_x.py>. It must fail now for this reason: <what is missing>. It passes when: <2 or 3 exact things the test asserts>.
Change: <file 1> (<function or section to edit>); <file 2> (<what>). At most four files. Do not touch: <files that look related but are not part of this step>.
Reuse: <the existing helper, class or pattern to copy, with its name>, never a new one.
Paperwork: one CHANGELOG.md line under [Unreleased]; python3 tools/readme_sync.py; <add the test to npm test in guiding-map/package.json | none>.
Out of scope (a later slice): <what you deliberately left out>.
```

## A filled example

```
Life OS Property tab: a let-out home with no monthly rent shows one calm line, "Add the monthly rent to track it", with a button that puts the cursor in the rent field (owner 2026-11-15; queue id landlord-desk, slice 2 of 5).
Test first: add guiding-map/tests/test121.js (jsdom, copy the set-up of test115.js). It must fail now because no such line exists. It passes when: a let-out home without rent shows the line once; a home with rent does not; a lived-in home does not.
Change: guiding-map/ops.js (the card of one let-out home on the Property tab). Then node build.js. Do not touch: the landlord desk, the profile, any other tab.
Reuse: the gm-inl quiet-action button and K.t for the words, never a new class or a bare string.
Paperwork: one CHANGELOG.md line under [Unreleased]; python3 tools/readme_sync.py; add test121 to npm test in guiding-map/package.json.
Out of scope (a later slice): rent seen in bank messages, the calendar.
```

## The rules behind it

1. **One step.** One outcome a person can see, one test, at most four files. A task with three steps is three briefs, sent in order,
   each on the branch the one before it produced (`DELEGATE_BASE=origin/<branch>`).
2. **Test first, and name it.** Give the test file its name and the two or three things it asserts. The model writes it, sees it
   fail, and works until that one test passes. A brief with no test file is refused by the check.
3. **Say where, not how.** Name the file and the function to edit, and the helper to reuse. `grep -n` for them yourself first
   (seconds for you, minutes for the model). Do not paste code.
4. **Never a slow check.** No browser audit and no sandbox in a brief: the navigator runs those on the green branch. If the fix
   comes from an audit, run the audit first and paste the exact list of breaks.
5. **Say what is out of scope.** The models over-build when the edge is not drawn.
6. **Facts, not the story.** Leave out why the owner asked, the history and the principles: AGENTS.md is already in front of the model.

## What the model does with it (so you do not repeat it in the brief)

The agent's own prompt already tells it to: write the test and see it fail; run only that test while it works; run the fast gates
(`ruff`, `diffcheck`, `forge gate`); run `./securax verify` once, last; never commit, push, install or run a browser audit.
