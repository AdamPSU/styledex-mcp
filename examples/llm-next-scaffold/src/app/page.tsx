const evidenceCards = [
  {
    label: "Screenshots",
    value: "desktop + mobile",
    detail: "Fold, full-page, and responsive captures stay with the alias.",
  },
  {
    label: "Design notes",
    value: "agent-readable",
    detail: "Typography, rhythm, surfaces, caveats, and do-not-copy rules.",
  },
  {
    label: "Tokens",
    value: "structured JSON",
    detail: "Colors, type, radii, borders, shadows, and interaction feel.",
  },
];

const workflow = [
  "Capture a reference once with screenshots and page evidence.",
  "Save the visual system under a lowercase alias.",
  "Ask your coding agent to reuse that direction in a new UI.",
];

const savedProfiles = ["linear", "mintlify", "stripe", "vercel"];

export default function Home() {
  return (
    <main className="min-h-screen overflow-hidden bg-[#fefdfb] text-[#121715]">
      <div className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[760px] bg-[radial-gradient(circle_at_78%_24%,rgba(24,226,153,0.22),transparent_28%),linear-gradient(180deg,#ffffff_0%,#fefdfb_58%,#faf8f5_100%)]" />

      <header className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-5 sm:px-8">
        <a className="flex items-center gap-2 text-sm font-semibold" href="#top">
          <span className="grid size-7 place-items-center rounded-md border border-black/10 bg-white shadow-[0_1px_2px_rgba(0,0,0,0.04)]">
            <span className="size-2.5 rounded-full bg-[#0c8c5e]" />
          </span>
          Copycat MCP
        </a>
        <nav aria-label="Primary" className="hidden items-center gap-7 text-sm font-medium text-[#485450] md:flex">
          <a className="transition hover:text-[#121715]" href="#workflow">
            Workflow
          </a>
          <a className="transition hover:text-[#121715]" href="#evidence">
            Evidence
          </a>
          <a className="transition hover:text-[#121715]" href="#profiles">
            Profiles
          </a>
        </nav>
        <a
          className="rounded-lg bg-black px-4 py-2 text-sm font-medium text-white shadow-[0_1px_2px_rgba(0,0,0,0.08)] transition hover:bg-[#121715] focus:outline-none focus:ring-2 focus:ring-[#0c8c5e] focus:ring-offset-2"
          href="#start"
        >
          Try the flow
        </a>
      </header>

      <section id="top" className="mx-auto grid w-full max-w-6xl gap-12 px-5 pb-20 pt-16 sm:px-8 lg:grid-cols-[0.92fr_1.08fr] lg:pb-28 lg:pt-24">
        <div className="flex flex-col items-start">
          <div className="mb-6 rounded-full border border-black/10 bg-white px-3 py-1.5 text-sm text-[#485450] shadow-[0_1px_2px_rgba(0,0,0,0.04)]">
            <span className="font-medium text-[#0c8c5e]">Design memory</span> for coding agents
          </div>
          <p className="mb-4 text-sm font-semibold uppercase tracking-[0.24em] text-[#0c8c5e]">
            Design memory for coding agents
          </p>
          <h1 className="font-serif text-[3.4rem] font-medium leading-[0.98] tracking-[-0.055em] text-[#121715] sm:text-[4.8rem] lg:text-[5.8rem]">
            Stop rebriefing your agent on visual direction.
          </h1>
          <p className="mt-7 max-w-xl text-lg leading-8 text-[#485450]">
            Copycat stores the screenshots, tokens, notes, and design guidance your agent needs so every new interface can start from a durable style reference instead of a forgotten chat message.
          </p>
          <div className="mt-9 flex w-full flex-col gap-3 sm:w-auto sm:flex-row">
            <a
              className="inline-flex h-[42px] items-center justify-center rounded-lg bg-black px-5 text-sm font-medium text-white shadow-[0_1px_2px_rgba(0,0,0,0.08)] transition hover:bg-[#121715] focus:outline-none focus:ring-2 focus:ring-[#0c8c5e] focus:ring-offset-2"
              href="#start"
            >
              Save a reference
            </a>
            <a
              className="inline-flex h-[42px] items-center justify-center rounded-lg border border-black/10 bg-white px-5 text-sm font-medium text-[#121715] shadow-[0_1px_2px_rgba(0,0,0,0.04)] transition hover:border-black/20 focus:outline-none focus:ring-2 focus:ring-[#0c8c5e] focus:ring-offset-2"
              href="#evidence"
            >
              See what gets saved
            </a>
          </div>
        </div>

        <div className="relative min-h-[520px] lg:min-h-[620px]">
          <div aria-hidden="true" className="absolute left-8 top-8 h-[420px] w-[420px] rounded-full border border-[#18e299]/35 opacity-70" />
          <div aria-hidden="true" className="absolute right-0 top-0 h-full w-full bg-[linear-gradient(115deg,transparent_0_33%,rgba(24,226,153,0.18)_33.2%,transparent_33.7%_52%,rgba(12,140,94,0.2)_52.2%,transparent_52.7%)]" />

          <div className="relative ml-auto rounded-[1.45rem] border border-black/10 bg-white p-3 shadow-[0_24px_80px_rgba(18,23,21,0.08)]">
            <div className="overflow-hidden rounded-[1.05rem] border border-black/10 bg-[#fbfaf7]">
              <div className="flex items-center justify-between border-b border-black/10 bg-white px-4 py-3">
                <div className="flex items-center gap-2">
                  <span className="size-2.5 rounded-full bg-[#ffa3d3]" />
                  <span className="size-2.5 rounded-full bg-[#ffa723]" />
                  <span className="size-2.5 rounded-full bg-[#18e299]" />
                </div>
                <div className="rounded-full border border-black/10 px-3 py-1 text-xs font-medium text-[#485450]">
                  ~/.copycat/designs
                </div>
              </div>

              <div className="grid min-h-[520px] grid-cols-[150px_1fr] bg-white sm:grid-cols-[184px_1fr]">
                <aside className="border-r border-black/10 bg-[#f7f5f1] p-4">
                  <p className="mb-4 text-xs font-semibold uppercase tracking-[0.18em] text-[#717d79]">
                    Profiles
                  </p>
                  <div className="space-y-2">
                    {savedProfiles.map((profile) => (
                      <div
                        className={`rounded-lg px-3 py-2 text-sm ${profile === "mintlify" ? "bg-[#d2f7ea] font-semibold text-[#0c8c5e]" : "text-[#485450]"}`}
                        key={profile}
                      >
                        {profile}
                      </div>
                    ))}
                  </div>
                </aside>

                <div className="p-4 sm:p-6">
                  <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#0c8c5e]">
                        Active style
                      </p>
                      <h2 className="mt-1 font-serif text-3xl font-medium tracking-[-0.04em]">
                        mintlify profile
                      </h2>
                    </div>
                    <span className="rounded-full border border-[#0c8c5e]/20 bg-[#d2f7ea] px-3 py-1 text-xs font-semibold text-[#0c8c5e]">
                      valid profile
                    </span>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-3">
                    {evidenceCards.map((card) => (
                      <article className="rounded-2xl border border-black/10 bg-[#fefdfb] p-4" key={card.label}>
                        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#717d79]">
                          {card.label}
                        </p>
                        <p className="mt-3 text-sm font-semibold text-[#121715]">{card.value}</p>
                        <p className="mt-2 text-sm leading-5 text-[#485450]">{card.detail}</p>
                      </article>
                    ))}
                  </div>

                  <div className="mt-4 rounded-2xl border border-black/10 bg-[#121715] p-4 text-white">
                    <div className="mb-3 flex items-center justify-between text-xs text-white/55">
                      <span>agent prompt</span>
                      <span>style context attached</span>
                    </div>
                    <p className="font-mono text-sm leading-6 text-white/86">
                      Use the mintlify Copycat profile as visual direction for a landing page. Keep the product original and do not copy source assets.
                    </p>
                  </div>

                  <div className="mt-4 rounded-2xl border border-black/10 bg-white p-4">
                    <p className="mb-3 text-xs font-semibold uppercase tracking-[0.16em] text-[#717d79]">
                      saved artifacts
                    </p>
                    <div className="grid gap-2 text-sm text-[#485450] sm:grid-cols-2">
                      <span className="rounded-lg bg-[#faf8f5] px-3 py-2">DESIGN.md</span>
                      <span className="rounded-lg bg-[#faf8f5] px-3 py-2">tokens.json</span>
                      <span className="rounded-lg bg-[#faf8f5] px-3 py-2">notes.md</span>
                      <span className="rounded-lg bg-[#faf8f5] px-3 py-2">screenshots/</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="workflow" className="border-y border-black/10 bg-white">
        <div className="mx-auto grid max-w-6xl gap-8 px-5 py-20 sm:px-8 lg:grid-cols-[0.8fr_1.2fr]">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.22em] text-[#0c8c5e]">Workflow</p>
            <h2 className="mt-4 font-serif text-4xl font-medium leading-tight tracking-[-0.045em] sm:text-5xl">
              Capture the taste once. Reuse it without another briefing.
            </h2>
          </div>
          <div className="grid gap-3">
            {workflow.map((step, index) => (
              <article className="rounded-2xl border border-black/10 bg-[#fefdfb] p-5" key={step}>
                <div className="mb-5 flex size-8 items-center justify-center rounded-lg bg-[#d2f7ea] text-sm font-bold text-[#0c8c5e]">
                  {index + 1}
                </div>
                <p className="text-lg leading-7 text-[#121715]">{step}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="evidence" className="mx-auto max-w-6xl px-5 py-20 sm:px-8">
        <div className="max-w-2xl">
          <p className="text-sm font-semibold uppercase tracking-[0.22em] text-[#0c8c5e]">Evidence, not vibes</p>
          <h2 className="mt-4 font-serif text-4xl font-medium leading-tight tracking-[-0.045em] sm:text-5xl">
            Every alias becomes a usable design brief.
          </h2>
        </div>
        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {evidenceCards.map((card) => (
            <article className="rounded-[1.25rem] border border-black/10 bg-white p-6 shadow-[0_1px_2px_rgba(0,0,0,0.04)]" key={card.label}>
              <p className="text-sm font-semibold text-[#0c8c5e]">{card.label}</p>
              <h3 className="mt-4 font-serif text-3xl font-medium tracking-[-0.04em] text-[#121715]">
                {card.value}
              </h3>
              <p className="mt-4 leading-7 text-[#485450]">{card.detail}</p>
            </article>
          ))}
        </div>
      </section>

      <section id="profiles" className="mx-auto max-w-6xl px-5 pb-24 sm:px-8">
        <div className="rounded-[1.5rem] border border-black/10 bg-white p-6 shadow-[0_20px_70px_rgba(18,23,21,0.06)] sm:p-8 lg:p-10">
          <div className="grid gap-10 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.22em] text-[#0c8c5e]">For the next session</p>
              <h2 className="mt-4 font-serif text-4xl font-medium leading-tight tracking-[-0.045em] sm:text-5xl">
                Your agent can pull the style back by name.
              </h2>
              <p className="mt-5 text-lg leading-8 text-[#485450]">
                Instead of pasting screenshots and explaining tone again, point the agent at a saved profile and let it apply the visual system to new product work.
              </p>
            </div>
            <div className="rounded-2xl border border-black/10 bg-[#faf8f5] p-4">
              <div className="rounded-xl bg-[#121715] p-5 text-sm leading-7 text-white/84">
                <p className="text-white/45">$ opencode</p>
                <p className="mt-3 text-white">Use mintlify as visual direction for this settings page.</p>
                <p className="mt-5 text-[#18e299]">profile loaded: DESIGN.md, tokens.json, screenshots</p>
                <p className="text-white/55">identity guardrails active: no copied logos, assets, or source copy</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="start" className="bg-[#121715] px-5 py-20 text-white sm:px-8">
        <div className="mx-auto flex max-w-6xl flex-col items-start justify-between gap-8 md:flex-row md:items-end">
          <div className="max-w-2xl">
            <p className="text-sm font-semibold uppercase tracking-[0.22em] text-[#18e299]">Start small</p>
            <h2 className="mt-4 font-serif text-4xl font-medium leading-tight tracking-[-0.045em] sm:text-5xl">
              Save one reference. Give every future agent the same visual compass.
            </h2>
          </div>
          <a
            className="inline-flex h-[42px] items-center justify-center rounded-lg bg-white px-5 text-sm font-semibold text-[#121715] transition hover:bg-[#d2f7ea] focus:outline-none focus:ring-2 focus:ring-[#18e299] focus:ring-offset-2 focus:ring-offset-[#121715]"
            href="#workflow"
          >
            Read the flow
          </a>
        </div>
      </section>
    </main>
  );
}
