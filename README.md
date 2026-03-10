# LIN2002 Grading Assistant

An AI-powered essay grading tool built for a linguistics and film studies course. Students write essays analyzing films and citing specific scenes with timestamps — this app grades those essays and generates written feedback in the instructor's voice.

Built with SvelteKit and Google Gemini. Feel free to take it and make it your own.

---

## What It Does

You paste in a student essay, select the film module it belongs to, and click Grade. The app sends the essay to Gemini along with a detailed system prompt, few-shot examples drawn from previously graded work, and the specific rubric for that assignment. It returns a numerical score and a paragraph of written feedback ready to copy and send.

The feedback follows a "sandwich" structure: open with something genuine about what the student did well, address what's missing or needs improvement, close with encouragement. The tone is warm and direct — not robotic.

### Grading Rubric

| Category | Weight | Notes |
|---|---|---|
| Length | 10% | Essays under 200 words are capped at 70 |
| Timestamps | 20% | Students must cite specific scenes |
| Expression | 20% | Clarity, organization, academic register |
| Content | 50% | Depth of analysis, engagement with the film |

---

## Tech Stack

- **SvelteKit** — frontend and API routes
- **Tailwind CSS** — styling with dark mode support
- **TypeScript** — throughout
- **Google Gemini** (`gemini-3.1-pro-preview`) — the grading model
- **Vercel** — deployment target

---

## Project Structure

```
src/
├── routes/
│   ├── +page.svelte          # Main grading UI
│   ├── +layout.svelte        # Header, footer, theme toggle
│   └── api/grade/+server.ts  # Grading endpoint
├── lib/
│   ├── components/
│   │   ├── Modal.svelte       # Essay question / film details popups
│   │   └── Toast.svelte       # "Copied" confirmation
│   ├── data/
│   │   ├── prompts.ts         # System prompt defining grading philosophy
│   │   ├── modules.json       # Film modules (question, details, ID)
│   │   └── examples.json      # Few-shot examples from graded essays
│   └── types.ts               # GradeRequest / GradeResponse interfaces
data/                          # Training corpus (see below)
```

---

## How the Grading Works

The API endpoint (`/api/grade`) builds a conversation history before calling Gemini:

1. **System prompt** — describes the grading philosophy, rubric weights, tone, and structure
2. **Few-shot examples** — real graded essays from the same module, showing the model how the instructor actually grades
3. **User message** — the student's essay, word count, film details, essay question, and the full rubric

Gemini returns a structured JSON response `{ score: number, feedback: string }` enforced by a strict schema. If parsing fails it retries once before returning an error.

---

## The `data/` Folder

The `data/` folder is a work-in-progress training corpus — don't worry too much about the state of it.

The idea: take a semester's worth of graded assignments (essays + scores + written feedback), analyze patterns in how the instructor grades, and use those real examples to inform the prompting. The Python scripts analyze grading consistency across modules and extract characteristic feedback patterns. The output feeds into `examples.json`, which is what actually gets used in the app.

It's a rough pipeline, but the goal is to ground the AI's grading in real instructor behavior rather than generic rubric logic.

---

## Setup

1. Clone the repo
2. Copy `.env.example` to `.env` and add your Google API key:
   ```
   GOOGLE_API_KEY=your_key_here
   ```
3. Install dependencies:
   ```bash
   npm install
   ```
4. Run the dev server:
   ```bash
   npm run dev
   ```

---

## Making It Your Own

This was built for one specific course, but the pattern is general: pick a writing assignment, define a rubric, collect some graded examples, write a system prompt that captures how you grade, and drop it all in.

To adapt it:

- **Add or edit modules** — `src/lib/data/modules.json`. Each module needs an `id`, `movie` (or topic), `question`, and `details`.
- **Swap in your examples** — `src/lib/data/examples.json`. Include `module_id`, `student_essay`, `grade`, and `feedback`.
- **Rewrite the prompt** — `src/lib/data/prompts.ts`. This is where the grading personality lives. The more specific you are about tone, priorities, and what good feedback looks like, the better the output.
- **Change the model** — edit the model string in `src/routes/api/grade/+server.ts` if you want to use a different Gemini version or swap to a different provider.

The rubric weighting, length penalty, and feedback structure are all in the system prompt — no magic elsewhere.

---

## Deployment

The app uses the Vercel adapter. Deploy by connecting the repo to a Vercel project and setting `GOOGLE_API_KEY` as an environment variable in the Vercel dashboard.
