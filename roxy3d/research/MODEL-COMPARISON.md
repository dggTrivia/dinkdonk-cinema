# Which model should evaluate and improve the DINK DONK Blender scene?

Researched 2 Nov 2026. Sources: Reddit, read through the Arctic Shift archive, plus the benchmarks and vendor pages those threads link to. Nothing was run and no existing file was changed.

## Verdict

No model is a clear winner. Two camps of Reddit opinion conflict, and the two public benchmarks give different results:

- **Benchmarks favor OpenAI.** BlenderWorld (Qwen, Oct 2026) ranks GPT-6 Astra first. In the blind Render Arena, OpenAI models hold most of the top spots. Both mostly test building a scene from a prompt.
- **Recent Reddit opinion favors Claude Opus 5.5.** This holds even in r/codex. Commenters praise its taste, how well it reads intent, how long it stays on task and its usage limits. Astra is called a token hog. A few say Astra spots problems that Opus misses.
- **Art critique was barely tested.** No source cleanly tests judging renders, which is the task that matters most for us.

**For us:** keep Astra (or try GPT-6.1 Sol xhigh) for building, and add Opus 5.5 as a second-model art critic. Before changing anything, run a cheap blind test on our own scene (see the last section).

## Per model

### GPT-6 Astra (Codex), plus Sol and Terra

- **Blender work:** OpenAI launched Astra on 3 Sep 2026 with Blender and Unreal demos. Coverage describes a loop of writing bpy, rendering and revising ([runtimewire](https://runtimewire.com/article/gpt-6-astra-blender-scene-control-stefan-vaskevich), [decrypt](https://decrypt.co/377514/openai-gpt-6-astra-review-shockingly-good)). In September, r/LocalLLaMA treated Astra as clearly the best at Blender, with "no models come close" ([19 Sep](https://www.reddit.com/r/LocalLLaMA/comments/1wk7yzr/)). The top comment in an r/ClaudeAI thread (+21) said Opus wins for daily use but Astra is kept "for art and blender work" ([27 Sep](https://www.reddit.com/r/ClaudeAI/comments/1wrlr29/)).
- **Benchmarks:** On [BlenderWorld](https://arxiv.org/abs/2610.23986) (14 Oct 2026), Astra scores 79.9, ahead of Opus 5 at 73.0 and GPT-5.6 Sol at 67.7. Opus 5.5 was not listed. On [Render Arena](https://render-arena.izolight.xyz), GPT-6.1 Sol xhigh is #1 (Elo 1934) and Astra high is #4 (1878), both in the pi harness. Astra xhigh in Codex with MCP is #14 (1769, 4 runs). One voter could recognize OpenAI scenes by their lighting, and said they "win quite often" ([LocalLLaMA thread](https://www.reddit.com/r/LocalLLaMA/comments/1wyklnj/)).
- **Visual critique:** Several users say Astra catches things Opus overlooks ([Astra vs Opus, 21 Oct](https://www.reddit.com/r/codex/comments/1xbpg3w/)). One heavy user of all three vendors prefers GPT for "auditing, vision, orchestration" and Opus for Blender creative work ([23 Oct](https://www.reddit.com/r/codex/comments/1xcwh10/)). Another finds Astra weak at copying a reference image (r/codex, 27 Oct).
- **bpy reliability and long sessions:** Commenters say Astra misreads prompts and spends hours on impossible tasks, and that it gets "tunnel vision" ([1xbpg3w](https://www.reddit.com/r/codex/comments/1xbpg3w/); [1xcl58u](https://www.reddit.com/r/codex/comments/1xcl58u/)). Others report "dozens of hours" of good Blender scenes with Astra and MCP, provided the user knows basic Blender ([20 Oct](https://www.reddit.com/r/codex/comments/1xanu9o/)). Terra 6.1 was advertised for 3D but was widely panned. It stopped halfway and claimed work it had not done ([27 Oct](https://www.reddit.com/r/codex/comments/1xgnfmm/)).
- **Cost and speed:** This is the most consistent complaint. Astra is unusable on the $20 plan ([29 Oct](https://www.reddit.com/r/ClaudeAI/comments/1xiudqe/)), and one user had Astra medium take 50 minutes for 10 simple trees ([30 Oct](https://www.reddit.com/r/codex/comments/1xjshr2/)). In the arena, Sol 6.1 xhigh costs about $0.46 per run against about $1.80 for Astra. Opinions on Sol conflict: some call Sol "laughable" in Blender.

### Claude Opus 5.5 (released 22 Sep 2026)

- **Blender work:** A 3D modeler with 20+ years' experience posted Opus 5.5 work that drew +359 votes ([21 Oct](https://www.reddit.com/r/ClaudeAI/comments/1xblwzf/)). The workflow was heavy: four 20x plans for two weeks, an orchestrator with sub-agents for grading and lighting, and every render compared against a moodboard. The poster says moving from medium to high effort is "EXTREME" in quality. In r/codex, several commenters call Opus better for 3D, including "far superior in 3d tasks over Astra" ([1xbpg3w](https://www.reddit.com/r/codex/comments/1xbpg3w/)). Another said Codex was "absolutely trash in Blender" next to Claude ([23 Oct](https://www.reddit.com/r/ClaudeAI/comments/1xcwhbo/)).
- **Visual critique:** The workflows that succeed all use the same loop. Claude renders stills or a contact sheet, reads them and fixes "only the worst thing" against a reference photo ([2 Nov](https://www.reddit.com/r/ClaudeAI/comments/1xkwtkd/); [31 Oct](https://www.reddit.com/r/ClaudeAI/comments/1xk94xo/)). One user notes it "can't automatically recognize what looks natural" in animation. The 3D modeler adds external vision tools (SAM3, DINOv3).
- **bpy reliability and long sessions:** Users say Opus keeps the goal in mind and writes more "normal" code than Astra ([22 Oct](https://www.reddit.com/r/codex/comments/1xcl58u/)). The counter-reports: it forgets or regresses in very long sessions, and one user saw it refuse to run a render.
- **Cost and speed:** Users say it uses far fewer of their plan's limits than Astra or Sol. The arena tells a different story for one-shot runs: Opus high in Claude Code with MCP is #5 (Elo 1875) but averages about $4.10 and 195 minutes per run. One $20-plan user burned 90% of a 5-hour window on a single Opus prompt.

### Claude Fable 5.1 (about 1 Sep 2026)

- **Blender work:** There are vendor and creator demos of Fable driving Blender through Python ([mindstudio](https://www.mindstudio.ai/blog/claude-fable-5-1-blender-video-generation)), but almost no Reddit head-to-heads. The arena has a single Fable 5.1 run, at low effort (#122). That tells us nothing.
- **Visual critique:** Users run Fable as an auditor or evaluator, not a builder. Astra and Fable 5.1 are "both great but I now use both as evaluators" ([27 Sep](https://www.reddit.com/r/ClaudeAI/comments/1wrlr29/)). Another user says "I only use fable to audit it" ([2 Nov](https://www.reddit.com/r/ClaudeAI/comments/1xllq08/)).
- **Cost:** Fable is the most expensive tier. Coverage says Opus 5.5 matches Fable 5.1 on most tasks (*unverified*). Fable 5.5 is rumored but unconfirmed.

### Claude Sonnet 5.5

The arena ranks it #6 at xhigh in Claude Code with MCP (Elo 1821), but at about $6.20 per run because it burns many tokens. One voter liked its results. Reddit has little else. One user got poor animation results with both Sonnet 5.5 max and Astra max ([1xanu9o](https://www.reddit.com/r/codex/comments/1xanu9o/)). It shows up mainly as a cheap sub-agent under Opus.

### Gemini (4 Argon, 3.8 Flash)

- Gemini 4 Argon arrived around 11–14 Oct 2026. Google pitched Argon for Blender MCP and 3D-world workflows ([Google blog, 27 Oct](https://blog.google/products-and-platforms/products/gemini/gemini-4-argon-in-action/)). One user rebuilt a creature from two views in almost one shot, for about 1% of weekly usage ([20 Oct](https://www.reddit.com/r/GeminiAI/comments/1xb6a75/)).
- The 3D modeler found Argon "good at shading and lighting" but needing 2–3x more iterations than Claude ([1xblwzf](https://www.reddit.com/r/ClaudeAI/comments/1xblwzf/)). An Argon-as-adversarial-reviewer loop was harsh but regressed parts nobody asked it to touch ([19 Oct](https://www.reddit.com/r/GeminiAI/comments/1x9qb9t/); three.js, not Blender, and the poster works for a vendor).
- Argon is not in the arena. Gemini 3.8 Flash ranks mid-table.

### Others

On the arena, DeepSeek V4.1 Flash is the best cheap open model, at around #15 and about $0.46 per run. Haiku 5.5 is "not worth it". Local Qwen 3.8 27B works but trails the frontier models ([1wtlxa9](https://www.reddit.com/r/LocalLLaMA/comments/1wtlxa9/)).

## How consistent are the opinions?

- **Consistent:** Astra is costly and slow on usage. One-shot prompts give poor results, and a render-and-review loop against references is what works. A Blender-literate human steering the model matters more than which model is used. Pairing two models, with one building and one reviewing, is a common pattern.
- **Split:** which model has the better 3D output. Late September leaned Astra. Since Opus 5.5 shipped, Reddit leans Opus. The benchmarks lean OpenAI.
- **Untested:** critique of an existing scene, the same .blend handed to two models, and fixed-camera stills. Every source tests building from a prompt.

## Caveats

- The sample is small and anecdotal, usually one person and one project per claim. Few comments have more than 10 upvotes.
- **Subreddit bias and hype:** r/ClaudeAI favors Claude, and r/codex is in a moment of fatigue with OpenAI usage limits. Some posts are promotional or vendor-affiliated, and several were removed by moderators.
- **Fast churn:** Astra (Sep), Opus 5.5 (22 Sep), Argon (Oct), Sol and Terra 6.1 (Oct), with Fable 5.5 rumored. Users also allege silent "nerfs" of both vendors' models (*unverified*).
- **Benchmarks:**
  - BlenderWorld lists only the top three and has no Opus 5.5 entry.
  - The arena is one-shot modeling, with few runs per configuration and no confidence intervals.
  - Results depend on the harness: pi versus Codex shifts Elo by 100+.
- **Excluded:** an AskGrok bot reply in r/codex claimed "Blender MCP leaderboards" favor Opus 5.5. I found no such leaderboard.

## Recommendation for our scene

The scene is a fixed camera, pre-rendered, isometric and built headless. That means no animation, no topology for games and no interactivity: the work is lighting, materials, composition and the compositor, judged from stills. This is the part of the work closest to what users say the render-and-review loop handles well.

1. **Building:** keep GPT-6 Astra xhigh in Codex. Our pipeline works, Astra leads both benchmarks, and switching mid-project has a real cost.
   - Its real weaknesses are cost and tunnel vision on long runs.
   - Mitigate them with short, scoped passes: one issue per pass and a fixed list of checks.
   - Consider GPT-6.1 Sol xhigh for routine passes. In the arena it rates higher at about a quarter of the cost (*not verified on our scene*).
2. **Art critique:** use a different model from the builder. Opus 5.5 is already the main session, so have it judge every render:
   - against the brief and reference images ("late-90s pre-rendered, rainy neon");
   - one numbered worst-problem list per round;
   - with no write access to the .blend.

   Fable 5.1 is the higher-cost option for the final art review only. This cross-model pattern is the most repeated advice on Reddit.
3. **Head-to-head test:** worth doing, because it costs a few hours and is the only evidence that fits our case.
   - **Setup:**
     - Copy the current .blend and scripts into one folder per model.
     - Lock the camera, frame, resolution (for example 960×540), samples (for example 128 with denoise) and seed.
     - Give the same brief and the same budget (for example 3 passes or 60 minutes).
   - **Contenders:** Astra xhigh (Codex), Sol 6.1 xhigh (Codex) and Opus 5.5 high (Claude Code, bpy CLI). Argon is optional.
   - **Critique track:** plant 3–4 known defects in one render, then count which model finds them and how specifically:
     - a light leak;
     - a stretched texture;
     - a clipped emissive sign;
     - a misaligned isometric edge.
   - **Build track:** each model improves its own copy. Then the owner compares the final renders blind (randomized A/B/C labels).
   - **Hard checks:**
     - The script reruns headless without errors.
     - The camera is unchanged.
     - Peak VRAM fits within 6 GB on the RTX 3050.
     - Render time per frame is recorded.
     - Usage spent is recorded.
   - Choose the builder and critic from the result, not from Reddit.
