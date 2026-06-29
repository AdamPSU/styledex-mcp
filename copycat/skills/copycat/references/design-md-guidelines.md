# DESIGN.md guidelines

@DESIGN.md is the agent-facing design guide. It should combine observed tokens with judgment about how to use them.

Write for an implementation agent. Prefer concrete instructions over vague design language.

Good:

```text
Use the accent color only for primary CTAs, active navigation, and focused form states.
```

Weak:

```text
The design uses a nice blue.
```

## Recommended sections

Use the sections below when evidence supports them. Omit low-value sections or explicitly mark unknowns instead of inventing motion, interaction, typography, or responsive rules that were not observed.

### Visual theme and atmosphere

Describe the mood, density, shape language, depth model, and overall design philosophy. This section orients the agent before it reads tokens.

### Color palette and roles

List values with roles. Roles matter more than raw frequency. Mark backgrounds, surfaces, text, muted text, borders, accents, and status colors.

### Typography rules

Include primary fonts, role-specific fonts, type scale, weights, line heights, and letter spacing. Explain how display text differs from body and UI text.

### Layout and spacing principles

Describe the spacing scale, base grid, container widths, section rhythm, and whitespace philosophy.

### Component styling

Document buttons, cards, inputs, navigation, badges, and common UI atoms. Include states when known.

### Depth, surfaces, borders, and shadows

Explain whether hierarchy comes from shadows, borders, opacity, luminance steps, blur, or flat layers.

### Motion and interaction feel

Record transition durations, easing, hover behavior, focus treatment, and whether motion is restrained or expressive.

### Responsive behavior

Explain how hierarchy changes between desktop and mobile. Mention nav collapse, type scaling, columns, touch targets, and section spacing.

### Do's and don'ts

Give explicit guardrails. Include what to avoid so agents do not overgeneralize or add generic AI visual tropes.

### Agent application guide

Provide direct guidance the next agent can follow when building UI with the saved style.

### Source evidence and caveats

List source URLs, capture date, screenshots, known noise, and confidence level. Distinguish the primary seed URL from autodiscovered supporting pages.

## Writing rules

- Say how to use values, not just what values exist.
- Use semantic roles for colors and tokens.
- Include concrete examples for components.
- Separate stable brand/system choices from one-off page decoration.
- Prefer patterns repeated across multiple captured pages over one-off page flourishes.
- When pages disagree, state which page type each pattern came from and how confident the agent should be when applying it.
- Call out uncertainty instead of filling gaps.
- Keep legal boundaries visible.
