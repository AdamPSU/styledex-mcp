# Apply guidelines

Applying a saved style means adapting visual language to the user's current product. It does not mean recreating the source site.

Start with @DESIGN.md, then consult the other files based on the implementation question:

1. @DESIGN.md for the core style judgment
2. @tokens.json for exact values
3. @metadata.json for source breadth and caveats
4. screenshots for visual judgment about density, composition, rhythm, and mobile hierarchy
5. @notes.md for unresolved context or prior enrichment notes

Use the saved style for:

- type hierarchy
- color roles
- spacing rhythm
- border radius scale
- surface and elevation treatment
- component density
- interaction feel
- responsive hierarchy

Keep the user's work original:

- Use the user's content and information architecture.
- Use the user's product names, flows, and entities.
- Build components that fit the user's app, not the source website's app.
- Adapt the style when domain needs differ.

Use user overrides as temporary unless the user explicitly asks to update the saved design. For example, `Use stripe, but less glossy` should guide the current implementation without changing the saved `stripe` profile.

Before finishing, check for drift:

- Are fonts and sizes close to the saved type scale?
- Are colors used by role rather than decoration?
- Is spacing consistent with the saved rhythm?
- Are shadows, radii, and borders from the saved system?
- Does the result preserve the user's product identity?

If the saved profile has multiple source pages, favor patterns that @DESIGN.md marks as stable across pages. Treat source-specific flourishes as optional unless the user's current UI needs that exact page type.
