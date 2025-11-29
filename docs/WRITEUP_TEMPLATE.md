# Smart Study Buddy – Kaggle Submission Template

Use this template as a starting point for the required Kaggle writeup. Replace the placeholder text with details from your own build, experiment logs, and demo screenshots.

---

## Title
Smart Study Buddy: AI Tutor for Fast Active Recall

## Subtitle
Concierge Agent that researches, quizzes, and coaches in under a minute.

## Track
Concierge Agents

## Problem (Why)
Learners waste time collecting trustworthy study material and often fall into passive reading, which hurts retention. The last 24–48 hours before an exam are especially critical, yet most students spend it searching, summarizing, and manually crafting practice problems.

## Solution (What)
Smart Study Buddy automates the revision loop by chaining three Gemini-powered agents:
1. **Researcher** – uses a web-search tool to gather the latest facts and distill them into a concise study note.
2. **Quiz Master** – turns the note into JSON-formatted multiple-choice questions for active recall.
3. **Tutor** – grades the learner, explains the reasoning, and stores takeaways for future sessions.

## Value (Impact)
- Cuts prep time by ~90% for new topics (from ~30 minutes of manual prep to <3 minutes).
- Reinforces memory with immediate feedback and context-aware coaching.
- Produces reusable study notes plus quiz logs that can be revisited anytime.

## Architecture Overview
```
User Prompt -> Researcher (Gemini + DuckDuckGo Tool)
              -> Quiz Master (Gemini, structured JSON output)
              -> Tutor (Gemini + session memory)
```
- Session memory keeps the last 10 artifacts (study notes, quizzes, feedback) to ground later agents.
- Observability: console logging shows tool usage, agent calls, and failures for quick debugging.

## Key Implementation Highlights
- **Multi-agent (Sequential)**: Researcher → Quiz Master → Tutor pipeline with isolated instructions.
- **Tool Use**: Custom DuckDuckGo search wrapper acts as the Researcher’s tool for fresh references.
- **Sessions & Memory**: Minimal replay buffer appended after each agent call to maintain context.
- **Structured Generation**: Quiz Master outputs strict JSON to keep the CLI deterministic.
- **CLI UX**: `python smart_study_buddy.py --topic "Photosynthesis" --questions 2` for reproducible demos.

## Setup & Repro Steps
1. `pip install -r requirements.txt`
2. `cp .env.example .env` and set `GEMINI_API_KEY` (or export it directly).
3. `python smart_study_buddy.py --topic "Quantum Dots" --questions 2`
4. Record a screen capture (≤3 minutes) showing the full loop for the video bonus.

## Metrics / Evaluation
- Manual smoke tests across 5 topics (biology, algorithms, finance, history, pop-science).
- Conversion rate of correct first-try answers increased from 40% to 70% after Tutor feedback review.
- Latency per question on Kaggle Notebook ≈ 8–12 seconds with `gemini-1.5-flash`.

## Bonus Evidence (Optional but Recommended)
- **Gemini Usage**: All agents run on Gemini 1.5 Flash (mention in README + video).
- **Deployment**: If you deploy via Cloud Run / Agent Engine, link the service and describe infra.
- **Video**: Include a YouTube link demonstrating the workflow (problem → agent flow → live demo).

## Future Work
- Add spaced-repetition scheduling with persistent storage.
- Plug in RAG for proprietary documents.
- Expand to multimodal study aids (e.g., diagrams, code walkthroughs).

---
Fill in quantitative claims, screenshots, and any additional experimentation details before submitting to Kaggle.
