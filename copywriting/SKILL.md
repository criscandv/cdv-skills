---
name: copywriting
description: Expert in user-facing text for product interfaces — microcopy, CTAs, error messages, empty states, headlines, descriptions, onboarding flows, confirmations. Use this skill whenever the user needs words written for a UI: "what should this button say", "write the error message for", "I have no idea what to put here", "write the empty state", "headline for this section", "onboarding copy". Trigger it whenever a task involves user-facing text decisions, not only when copywriting is named. Writes in the language of the surrounding interface by default (detects Spanish vs English from context, asks if ambiguous), and stays consistent with the project's voice if one is documented. Pairs with ui-ux (which decides what surfaces need text) and tailwindcss-v4 (which lays the text out).
---

# Copywriting

Writing the words on the interface — buttons, errors, empty states, headlines, descriptions — when there's no draft to polish and the rest of the screen is waiting on the text. The output is short, clear, useful copy that earns its space.

The guiding idea: **the text is part of the UX**. A button that says "Submit" tells the user nothing; "Send invite" does the same job and makes the screen understandable at a glance. Every word on screen is taking up the user's attention budget — make it worth it.

---

## Language

Write in the **language of the interface**:

- If the surrounding strings, the project's docs/AGENTS.md, or the user's message are in Spanish, write in Spanish.
- If they're in English, write in English.
- If it's ambiguous or a brand-new project, **ask once** which language; don't assume.

Don't switch mid-string ("Click here para continuar"). Match the locale's conventions for capitalisation, punctuation and number/date formatting.

---

## Voice and tone

**Voice** is constant across the product; **tone** adapts to context.

- Pick a voice in one sentence: "*concise, expert, no fluff*" or "*friendly, plain, encouraging*" or "*neutral, factual*". When in doubt, lean **neutral and clear**.
- Adapt the tone to the moment: **calm and helpful** in errors, **direct** in confirmations, **encouraging** in empty states and onboarding, **factual** in settings, **brief** in tooltips.
- Don't whiplash. A friendly "Hi! 👋" header above a cold-system error message reads as fake.

If the project documents a voice or brand tone, **follow it**. If not, surface a one-sentence voice proposal alongside the copy so the user can confirm it.

---

## Clarity wins

- **Plain language.** Replace nouns made from verbs ("the deletion of records was initiated") with the verbs ("we deleted the records"). Subject → verb → object.
- **Concrete > abstract.** "Save changes" beats "Confirm". "Send to 12 recipients" beats "Send".
- **Cut what doesn't earn its place.** "Please" rarely adds anything; "successfully" is implied; "click here" is wallpaper. Read each line and remove every word that doesn't change the meaning.
- **Don't make the user translate.** No jargon, no internal terms, no error codes without context. If you must show an ID for support, label it.

A test: read it aloud. If it sounds like a person, it works.

---

## CTAs (buttons, links)

Two or three words. Imperative + object. Says exactly what happens.

- ✅ "Save changes", "Send invite", "Create project", "Delete account", "Continue with email".
- ❌ "OK", "Submit", "Yes" (alone), "Click here", "Done" (unless it really means "done").

The button text + the title above it should make the action unambiguous when the user scans only those two. If a destructive action is irreversible, name it that way — "Delete invoice" not "Delete".

---

## Error messages

Three jobs, in order: **what happened**, **why** (if it helps), **what they can do**. Tone is calm and on the user's side, not the system's. Never blame the user.

- ✅ "We couldn't send the invite. The email address looks invalid — check for typos and try again."
- ❌ "Error: invalid input." / "Oops! Something went wrong." / "An unexpected error occurred."

Don't leak internals: not stack traces, not raw status codes, not internal IDs unless they're for support reference (then label them). For server-side failures the user can't fix, apologise briefly, say what we're doing about it, and offer a next step ("try again", "contact support").

Inline errors sit next to the field they describe; banner errors at the top of the form summarise. Don't say the same thing twice.

---

## Empty states

The riskiest copy on a screen — first impressions form here. Three jobs:

1. **Explain what would be here**, briefly.
2. **Make it inviting**, not apologetic.
3. **Offer the primary action** to fill it.

```
No invoices yet
Create your first invoice to start tracking what clients owe you.
[ Create invoice ]
```

Avoid "Oops, nothing here!" and stock illustrations replacing the explanation. The user is new to this screen; tell them what it's for.

---

## Onboarding and first-run

The shortest path from arrival to first value. Rules:

- **One thing at a time.** Don't introduce six features on day one.
- **Show, then explain.** A tiny demo data set + a sentence beats a tour.
- **No fake personality** ("Hi friend! Ready to crush it? 🚀"). State the benefit and get out of the way.
- **Skip should be present and obvious.** Forced tours are resented.

A good opener answers: "what does this do for me?" in one sentence and shows the first action.

---

## Headlines and descriptions

- **Lead with the benefit, not the feature.** "Get paid faster" before "Automated invoicing".
- **Be specific.** Numbers, concrete nouns, named outcomes. "Save 3 hours a week" beats "Save time".
- **Don't shout.** Sentence case reads more human than Title Case for most product copy. Caps Lock is for warnings.
- **One promise per headline.** If you're squeezing two ideas in, split into headline + subhead.

---

## Length by surface

Hold these as soft caps; shorter is almost always better.

- **Buttons** — 1–3 words.
- **Tooltips** — up to 10 words; one idea.
- **Labels** — 1–4 words; nouns, sentence case.
- **Placeholders** — short example of the format ("name@example.com"); **never a substitute for a label**.
- **Inline errors** — up to two short sentences.
- **Empty states** — title + 1 sentence + CTA.
- **Confirmation toasts** — one sentence past tense ("Invite sent").
- **Headlines** — under ~8 words.
- **Body paragraphs** — 2–4 sentences; break up otherwise.

When in doubt, cut a third.

---

## Inclusive and accessible language

- **Gender-neutral by default.** In Spanish use neutral phrasing when possible (`tu cuenta` over gendered constructions; "personas" over "usuarios" when natural). Don't reach for forms (`@`, `x`) that hurt screen readers.
- **Don't assume the user's situation** — age, ability, role, family. Write for the action, not a persona.
- **Avoid idioms and cultural references** that don't translate ("hit it out of the park").
- **No demeaning errors** ("You forgot to…" → "Please add…").

---

## Numbers, dates and units

- Locale formats (`1,234.56` vs `1.234,56`). The framework usually formats these; the copy should match the format the rest of the product uses.
- Spell out small numbers in prose (`one`, `two`); use digits for everything in UI text and any number worth comparing (`3 invoices`, `12 users`).
- Relative time when fresh ("hace 2 min"), absolute when not ("12 Mar 2024").

---

## What to avoid

- **Filler greetings and apologies**: "Hi!", "Oops!", "Please…", "Sorry about that…" without need.
- **Faux-friendly chatter**: "Awesome!", "You're crushing it!". Often reads as patronising.
- **Buzzwords**: "leverage", "unlock", "powerful", "seamless". Strip them and the sentence usually improves.
- **Mystery language**: "An error occurred", "Something went wrong", "Invalid input". Be specific.
- **Threats**: "You will lose your data permanently." → "This can't be undone." is enough.
- **Lorem ipsum** shipping by accident — name placeholder strings clearly so they're easy to find.

---

## When asked for "the copy" with no context

Ask, briefly:

1. **Surface** — what is it (button, empty state, error, headline)?
2. **What it should do** for the user — the goal in one sentence.
3. **Voice** — friendly / neutral / expert / serious, if a project voice isn't already established.
4. **Constraints** — max length, language, anything that mustn't be said.

Then propose 2–3 short options with a one-line rationale each ("shorter, direct", "warmer, longer", "feature-first") so the user can pick or steer. Don't dump one option as if it's final.
