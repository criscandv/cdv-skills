---
name: ui-ux
description: Design expert for screens, components and interfaces when there is no mockup, no design system to follow, or the existing UI needs to be improved. Use this skill whenever the user asks for design decisions — colour choices, palette, contrast, typography, spacing, layout, visual hierarchy, component arrangement, accessibility, loading/empty/error states, "improve this UI", "what colours should I use", "design this screen", "I have no mockup". Trigger it whenever a task involves visual design, layout, theming, design tokens or accessibility, even if the user does not say "UI/UX". It is framework-agnostic — outputs land in Tailwind via tailwindcss-v4, and any user-facing text it sketches should be refined by copywriting.
---

# UI/UX

How to make design decisions when there is no mockup and no existing system to copy. The output of this skill is **design intent expressed as tokens and rules** — palette, type scale, spacing scale, layout pattern, component states, accessibility constraints — that another layer (Tailwind, see **tailwindcss-v4**) implements. Microcopy decisions land in **copywriting**.

The guiding idea: **constraint produces coherence**. A small palette, a fixed type scale, one spacing base and a handful of layout patterns repeated everywhere read as a designed product. Improvising per screen reads as chaos.

---

## Start by clarifying intent, not pixels

Before sketching anything ask (or note from context):

- **Purpose of the screen** — what is the user trying to accomplish in one sentence?
- **Primary action** — the one thing the screen exists for; everything else is supporting.
- **Audience and context** — who, on what device, under what time pressure or attention budget?
- **Tone** — utilitarian (an internal CRM) vs warm (a consumer product) vs serious (a financial/legal app). Tone drives colour, type and copy together.
- **Constraints** — brand colours that exist, accessibility level required (most products: WCAG AA), languages, dark mode.

Without these, you're guessing. A good prompt for yourself: "If I built this and it failed, what would the user have wanted instead?"

---

## Hierarchy — earn the eye in this order

The eye prioritises **size → weight → colour → spacing → position**, in roughly that order. Use them deliberately and don't fight yourself:

- The primary action is the largest, heaviest, highest-contrast element in its region.
- Secondary actions de-emphasise (lighter weight, neutral colour, ghost/outline style) — never the same emphasis as primary, or both become noise.
- Group related elements with proximity (smaller gap), separate unrelated ones with whitespace (larger gap), not with rules/dividers as the first move.
- One focal point per region. If two things compete, you're saying "I don't know what matters" to the user.

---

## Colour — pick a small palette and stick to it

A workable palette is **5 roles, each with a tint/shade scale**:

- **Brand / primary** — used for the primary action and key accents. One hue.
- **Neutrals** — backgrounds, surfaces, borders, body text. Cool grey or warm grey; pick one family.
- **Accent** — sparingly, for highlights or secondary brand presence. Optional.
- **Semantic** — success / warning / danger / info. Each one colour with a tint range; reuse for icons and state.
- **Text** — usually derived from neutrals: high-emphasis (≈90% opacity on light bg), medium (≈70%), low (≈50%).

For each role, generate a **50–950 scale** (50 lightest → 950 darkest). Pick the actual shades you'll use (e.g. `primary-500` for the button, `primary-600` for hover, `primary-100` for the soft background). Define them once as design tokens; every component reads from the tokens.

**Use OKLCH (or HSL) for the scale**, not raw hex. Stepping `lightness` in a perceptual space (OKLCH) gives even-looking ramps; hex steps look uneven because RGB isn't perceptual. Tailwind v4 supports OKLCH directly.

### Contrast — non-negotiable

WCAG AA is the floor:

- **Body text**: ≥ **4.5:1** against its background.
- **Large text** (≥ 18 px regular or ≥ 14 px bold) and **UI components/graphics**: ≥ **3:1**.
- **Focus indicators**: ≥ **3:1** against the adjacent colour.

If the primary action doesn't pass at the brand colour, darken/lighten the shade until it does — don't compromise contrast for brand purity. Test with a contrast checker, not by eye.

### Dark mode is its own design, not an inversion

Don't invert; design it. Dark surfaces use slightly raised neutrals (`neutral-900` body, `neutral-800` card, `neutral-700` elevated) — never pure black, which is too harsh and shows banding. Saturated brand colours often need a softer variant on dark backgrounds.

---

## Typography — one or two fonts, a fixed scale

- **One typeface** for everything, or one for headings + one for body. More than two is almost always a mistake.
- **Type scale** — a fixed ladder, no off-ladder sizes. A workable default:
  `12, 14, 16, 18, 20, 24, 30, 36, 48, 60` (px / rem).
  Body sits at 14–16; UI labels 12–14; headings 20+. Pick what each size means and reuse.
- **Line height** — body around 1.4–1.6 for comfortable reading; tighter (1.1–1.25) for large display headings.
- **Line length** — 45–75 characters per line for body text. Wider lines tire the eye.
- **Weight** — bold (600/700) sparingly. Hierarchy doesn't need everything bold; size + colour does most of the work.

---

## Spacing — one base, used everywhere

Pick a **base of 4 px** (8-pt grid with half-steps) and use multiples: `4, 8, 12, 16, 20, 24, 32, 40, 48, 64`. Every gap, padding and margin in the design comes from this scale. Off-scale values (`17px`, `23px`) break visual rhythm and should never appear.

Inside vs between:
- **Inside** a component: tight, related (`8–16`).
- **Between** components in a group: medium (`16–24`).
- **Between** unrelated groups / sections: generous (`32–64`).

If two regions feel "stuck together", you need more space between them; if a card looks empty, you may need less inside.

---

## Layout — pick a pattern and repeat it

A few patterns cover most screens:

- **Single column, centred, max-width** — content/reading, settings, forms. Cap at ~640–720 px for readability.
- **Sidebar + content** — apps with persistent navigation. Sidebar 240–280 px; content fills.
- **Three-pane (master / list / detail)** — email, chats, inboxes.
- **Card grid** — collections (products, posts). 1/2/3/4 columns responsive; equal aspect ratios per card.
- **Dashboard** — primary metric strip → secondary widgets → details. Most-important top-left for LTR.

Reading flow follows **F-pattern** (content-heavy) or **Z-pattern** (sparse). Put the primary action where the eye lands.

### Alignment and repetition

- One alignment per region. Mixing left-aligned and centred labels in the same form is a tell.
- Repetition is invisible when it's right; inconsistency is what people notice.

---

## Every interactive thing has states

For each interactive element, design **default / hover / focus / active / disabled** — and for things that load, **loading**; for things that can be empty, **empty**; for things that can fail, **error**.

- **Hover** — subtle (a touch darker/lighter); reserved for affordance, not for whole rows unless that's the design.
- **Focus** — visible **always**. A 2 px ring with ≥ 3:1 contrast on the surface. Don't disable focus to make it "cleaner"; you've broken keyboard navigation.
- **Active** (pressed) — a click feedback (slightly darker / inset).
- **Disabled** — reduced opacity (≈40–50%) and `cursor: not-allowed`. Tell the user *why* it's disabled when reasonable.
- **Loading** — skeletons (preferred for content), spinners (for actions). Don't block the whole screen for partial loads.
- **Empty** — explain what would normally be here, why it's empty, and **the action to fill it**.
- **Error** — what went wrong, in plain language; what they can do; recovery action. See **copywriting**.

A screen with only the default state designed is an unfinished screen.

---

## Accessibility — the design constraint that improves everything

- **Contrast** as above (WCAG AA minimum).
- **Touch targets** ≥ **44×44 px** (mobile); ≥ 32 px on dense desktop UIs.
- **Keyboard reach** — every interactive element reachable and operable by keyboard; visible focus ring.
- **Semantic structure** — headings (`h1`–`h6`) in order; landmarks (`nav`, `main`, `aside`); labels associated with inputs.
- **Motion** — animations under ~250 ms and respect `prefers-reduced-motion` for users who opt out.
- **Don't rely on colour alone** to convey state (add an icon or label).
- **Form fields** — visible labels (placeholders are not labels), inline errors near the field they describe.

Accessibility makes the design better for everyone, not only for the assistive-tech case.

---

## Design tokens — the output other layers consume

Express decisions as **tokens**, not as ad-hoc values in components. The token names are stable; their values can be re-themed:

```
color.background.default       # surface body sits on
color.surface.raised           # cards
color.text.high                # primary body text
color.text.medium              # secondary
color.brand.primary            # main action
color.brand.primary.hover
color.semantic.danger
spacing.4 / .8 / .12 / .16 ...
radius.sm / .md / .lg
font.size.body / .h1 / .h2 ...
font.weight.regular / .medium / .bold
```

These map cleanly onto Tailwind v4's `@theme` block — see **tailwindcss-v4** for the implementation. Tokens are how UI/UX and CSS speak the same language.

---

## When there is no mockup — propose a minimal first cut

If the user hasn't decided, don't invent details; propose the **smallest viable design** and iterate:

1. State the screen's purpose and primary action in one sentence.
2. Pick a layout pattern from the catalogue above; justify it.
3. Suggest a 5-role palette (brand seed + neutral family + semantic) and a type scale.
4. Sketch the layout in words/ASCII: regions, their job, and the primary action's location.
5. List every state the screen needs (default + loading + empty + error + auth states if relevant).
6. Flag accessibility constraints that may push back on visual choices.

Then ask the user what to adjust before moving to Tailwind/copy.

---

## Common pitfalls

- **Too many type sizes** — every screen has its own. Fix the scale and use only those rungs.
- **Off-scale spacing** (`17px`, `23px`) — break the rhythm; round to the nearest scale step.
- **Primary and secondary buttons styled equally** — both become noise; pick one to win.
- **Low-contrast "elegant" greys** for body text — fails WCAG; users squint or leave.
- **Pure black on pure white** — too harsh; soften both to a near-neutral.
- **Hidden focus ring** — kills keyboard accessibility for an aesthetic gain that doesn't exist.
- **Only the default state** designed — loading/empty/error are part of the screen, not nice-to-have.
- **Inversion as dark mode** — design dark surfaces, don't flip values.
- **Decorative motion** that runs every interaction — fatigues users and ignores reduced-motion.
