# Smart Study Buddy – Agents Intensive Capstone

Concierge-style AI tutor that researches any topic, generates a concise study brief, quizzes the learner, and provides coaching feedback — all within one CLI workflow. The project is optimized for the **Kaggle Agents Intensive Capstone** rubric so you can ship a compliant MVP in under a weekend.

## Why this project scores well
- **Category 1 – Pitch**: Clear problem (manual study prep is slow), focused solution (auto research + quiz + tutoring), and measurable value (minutes to insights).
- **Category 2 – Implementation**: Demonstrates three required concepts out of the box:
  - Multi-agent chain (Researcher → Quiz Master → Tutor).
  - Custom tool usage (DuckDuckGo search wrapper for fresh context).
  - Sessions & memory (rolling log of study notes, quizzes, and feedback grounding later agents).
  - Bonus: structured JSON generation + CLI observability logs for easier debugging.
- **Bonus hooks**: Built on Gemini (5 pts). Ready for quick screen recording (10 pts) and easy to redeploy on Cloud Run / Agent Engine if you want the extra 5 pts.

## Repo layout
```
README.md                 -> You are here
smart_study_buddy.py      -> Main CLI orchestration + agents
requirements.txt          -> Minimal deps (Gemini SDK, duckduckgo-search, dotenv)
.env.example              -> Copy to .env and set credentials
docs/WRITEUP_TEMPLATE.md  -> Drop-in Kaggle submission draft
```

## Quickstart
1. **Install dependencies**
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Configure secrets**
   ```bash
   cp .env.example .env
   # Edit .env or export the variables manually
   export GEMINI_API_KEY="your-key"
   ```
3. **Run the agent**
   ```bash
   python smart_study_buddy.py --topic "Photosynthesis" --questions 2
   ```
   - The Researcher fetches live snippets via DuckDuckGo and writes a study note.
   - Quiz Master emits JSON-formatted MCQs.
   - Tutor grades your answer, references the note, and adds coaching tips.

### Running on Kaggle Notebook
```python
!pip install -q -U google-generativeai duckduckgo-search python-dotenv
from kaggle_secrets import UserSecretsClient
secret = UserSecretsClient()
os.environ["GEMINI_API_KEY"] = secret.get_secret("GEMINI_API_KEY")
!python smart_study_buddy.py --topic "Quantum Dots" --questions 1
```
Record the cell output for your submission video.

## Architecture cheat sheet
```
+-------------+      +-------------+      +-----------+
| Researcher  | ---> | Quiz Master | ---> |   Tutor   |
| (Gemini +   |      | (Gemini,    |      | (Gemini + |
| DuckDuckGo) |      | JSON output)|      | memory)   |
+-------------+      +-------------+      +-----------+
        ^                                           |
        |-------------- Memory Buffer --------------|
```
- **Tooling**: `SearchTool` wraps duckduckgo-search and logs every query for observability.
- **Memory**: Last 10 artifacts (notes, quizzes, feedback) are appended after each stage and replayed as context.
- **Structured output**: Quiz Master forces `application/json` MIME type, keeping the CLI deterministic and easy to demo.

## Kaggle submission checklist
- [ ] Update `docs/WRITEUP_TEMPLATE.md` with screenshots, metrics, and any deployment notes.
- [ ] Capture a ≤3-minute screen recording that shows: problem intro → CLI demo → quick architecture slide.
- [ ] Publish code (GitHub or Kaggle Notebook) and link it in the Kaggle writeup attachments.
- [ ] (Optional) Deploy via Cloud Run / Agent Engine and mention the endpoint for the extra 5 bonus points.

## Troubleshooting
| Issue | Fix |
| --- | --- |
| `EnvironmentError: GEMINI_API_KEY is not set` | Create `.env`, export the key, or use Kaggle secrets. |
| Quiz JSON parsing failures | Re-run the command; Gemini sometimes emits trailing prose. The parser strips ``` fences automatically. |
| DuckDuckGo blocks repeated calls | Reduce `--max-results`, add a pause between runs, or switch IP (Kaggle notebooks are usually fine). |

## Next steps
- Persist memory between sessions (e.g., SQLite) for spaced repetition.
- Add a second tool (e.g., WolframAlpha) for computation-heavy topics.
- Swap the CLI for a Streamlit UI when you have more time — the agent core will stay the same.

Happy shipping, and good luck on the leaderboard!
