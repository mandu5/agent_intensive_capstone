"""Smart Study Buddy CLI.

This script demonstrates a multi-agent study assistant that:
- Uses a web-search tool (DuckDuckGo) to gather up-to-date references.
- Chains three specialized Gemini-powered agents (Researcher, QuizMaster, Tutor).
- Maintains a lightweight in-memory session log to ground future prompts.

Run locally:
    pip install -r requirements.txt
    export GEMINI_API_KEY="your-key"
    python smart_study_buddy.py --topic "Photosynthesis" --questions 2
"""
from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import dataclass
from textwrap import dedent
from typing import List, Optional

from duckduckgo_search import DDGS
from dotenv import load_dotenv
import google.generativeai as genai

# ----------------------------------------------------------------------------
# Configuration & logging
# ----------------------------------------------------------------------------
load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
LOGGER = logging.getLogger("smart-study-buddy")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise EnvironmentError(
        "GEMINI_API_KEY is not set. Use a .env file or export the variable first."
    )

genai.configure(api_key=GEMINI_API_KEY)
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


# ----------------------------------------------------------------------------
# Tooling layer
# ----------------------------------------------------------------------------
@dataclass
class SearchTool:
    """Simple wrapper around DuckDuckGo Search to serve as an agent tool."""

    max_results: int = 3

    def run(self, query: str) -> str:
        if not query:
            return "No query provided."

        LOGGER.info("[Tool] Searching web for '%s' (top %d results)", query, self.max_results)
        snippets: List[str] = []
        try:
            with DDGS() as ddgs:
                for row in ddgs.text(query, max_results=self.max_results):
                    body = row.get("body") or ""
                    title = row.get("title") or "Untitled"
                    snippets.append(f"- {title}: {body}")
        except Exception as err:  # pragma: no cover - network variances
            LOGGER.warning("DuckDuckGo search failed: %s", err)
            return f"Search failed: {err}"

        return "\n".join(snippets) if snippets else "No public snippets were found."


# ----------------------------------------------------------------------------
# Base agent abstraction
# ----------------------------------------------------------------------------
@dataclass
class Agent:
    """Wrapper around a GenerativeModel with role-specific instructions."""

    name: str
    instructions: str
    model_name: str = DEFAULT_MODEL
    response_mime_type: str = "text/plain"

    def __post_init__(self) -> None:
        self._model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={"response_mime_type": self.response_mime_type},
        )

    def run(self, context: str, memory: Optional[List[str]] = None) -> str:
        compiled_prompt = dedent(
            f"""
            You are the {self.name} agent.
            Instructions: {self.instructions}

            Session memory (may be empty):
            {os.linesep.join(memory or []) or 'None yet.'}
            ---
            Focused input:
            {context}
            """
        ).strip()

        try:
            response = self._model.generate_content(compiled_prompt)
        except Exception as exc:  # pragma: no cover - SDK surface
            LOGGER.error("%s agent call failed: %s", self.name, exc)
            raise

        return (response.text or "").strip()


# ----------------------------------------------------------------------------
# Pipeline logic
# ----------------------------------------------------------------------------
@dataclass
class QuizItem:
    question: str
    options: List[str]
    correct_answer: str
    explanation: Optional[str] = None


class SmartStudyBuddy:
    """Coordinates the tool + agents to deliver a study session."""

    def __init__(self, search_tool: Optional[SearchTool] = None) -> None:
        self.memory: List[str] = []
        self.search_tool = search_tool or SearchTool()

        self.researcher = Agent(
            name="Researcher",
            instructions=(
                "Aggregate the most important definitions, core principles,"
                " and real-world examples. Cite search snippets concisely."
            ),
        )
        self.quiz_master = Agent(
            name="QuizMaster",
            instructions=(
                "Create a single multiple-choice question based on the study note."
                " Respond with strict JSON containing keys question, options (list),"
                " correct_answer, explanation."
            ),
            response_mime_type="application/json",
        )
        self.tutor = Agent(
            name="Tutor",
            instructions=(
                "Evaluate the learner's answer, explain correctness, and add a follow-up tip."
                " Encourage active recall and reference the study note when helpful."
            ),
        )

    # --------------------------- public API ---------------------------
    def interactive_session(self, topic: str, questions: int = 1) -> None:
        """Run an end-to-end study session via the terminal."""
        study_note = self._generate_study_note(topic)
        LOGGER.info("Study note ready. Generating %d quiz question(s)...", questions)

        correct = 0
        for idx in range(1, questions + 1):
            quiz = self._generate_quiz(study_note)
            if not quiz:
                LOGGER.error("Quiz generation failed. Aborting session.")
                return

            print(f"\n==== Quiz {idx} / {questions} ====")
            print(quiz.question)
            for option_idx, option in enumerate(quiz.options, start=1):
                print(f"  {option_idx}. {option}")

            user_input = input("Your answer (number or text, 'q' to quit): ").strip()
            if user_input.lower() == "q":
                break

            normalized = self._normalize_answer(user_input, quiz.options)
            feedback = self._grade_and_feedback(quiz, normalized, study_note)
            print("\nFeedback:\n" + feedback)

            if normalized and normalized.lower() == quiz.correct_answer.lower():
                correct += 1

        if questions:
            print(
                f"\nSession complete. Score: {correct}/{questions}"
                f" ({(correct/questions)*100:.0f}% accuracy)."
            )

    # -------------------------- internals ----------------------------
    def _remember(self, entry: str) -> None:
        self.memory.append(entry)
        # Keep memory bounded to avoid prompt bloat
        if len(self.memory) > 10:
            self.memory = self.memory[-10:]

    def _generate_study_note(self, topic: str) -> str:
        search_digest = self.search_tool.run(topic)
        context = dedent(
            f"""
            Topic: {topic}
            Use the search digest as factual grounding. Provide:
            - A brief overview
            - 3-5 bullet points of core insights
            - One memorable example or analogy

            Search digest:
            {search_digest}
            """
        ).strip()

        note = self.researcher.run(context, self.memory)
        self._remember(f"StudyNote::{note}")
        return note

    def _generate_quiz(self, study_note: str) -> Optional[QuizItem]:
        context = dedent(
            f"""
            You must return valid JSON only.
            Study note source:
            {study_note}
            """
        ).strip()

        raw_response = self.quiz_master.run(context, self.memory)
        quiz = self._parse_quiz(raw_response)
        if quiz:
            self._remember(f"Quiz::{quiz.question}")
        return quiz

    def _grade_and_feedback(
        self, quiz: QuizItem, user_answer: Optional[str], study_note: str
    ) -> str:
        context = dedent(
            f"""
            Question: {quiz.question}
            Options: {quiz.options}
            Correct Answer: {quiz.correct_answer}
            Learner Answer: {user_answer or 'No answer provided'}
            Study Note:
            {study_note}
            """
        ).strip()

        feedback = self.tutor.run(context, self.memory)
        self._remember(f"Feedback::{feedback}")
        return feedback

    @staticmethod
    def _normalize_answer(user_input: str, options: List[str]) -> Optional[str]:
        if not user_input:
            return None

        if user_input.isdigit():
            idx = int(user_input) - 1
            if 0 <= idx < len(options):
                return options[idx]

        user_input_lower = user_input.lower()
        for option in options:
            if option.lower().startswith(user_input_lower):
                return option
        return user_input  # fallback to raw text

    @staticmethod
    def _parse_quiz(payload: str) -> Optional[QuizItem]:
        if not payload:
            return None

        cleaned = payload.strip()
        if "```" in cleaned:
            cleaned = cleaned.split("```", 2)[-2] if cleaned.count("```") >= 2 else cleaned
            cleaned = cleaned.replace("json", "", 1).strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            LOGGER.error("Quiz JSON parsing failed: %s\nPayload was:\n%s", exc, payload)
            return None

        question = data.get("question")
        options = data.get("options", [])
        answer = data.get("correct_answer")
        explanation = data.get("explanation")

        if not question or not options or not answer:
            LOGGER.error("Quiz JSON missing fields: %s", data)
            return None

        return QuizItem(question=question, options=options, correct_answer=answer, explanation=explanation)


# ----------------------------------------------------------------------------
# CLI entrypoint
# ----------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Smart Study Buddy agent.")
    parser.add_argument("--topic", "-t", help="Topic to study. If omitted you'll be prompted.")
    parser.add_argument("--questions", "-q", type=int, default=1, help="Number of quiz questions to generate.")
    parser.add_argument(
        "--max-results",
        type=int,
        default=3,
        help="How many search results to fetch for grounding context.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    topic = args.topic or input("Enter a topic to study: ").strip()
    if not topic:
        raise ValueError("A topic is required to run the study buddy.")

    buddy = SmartStudyBuddy(search_tool=SearchTool(max_results=args.max_results))
    buddy.interactive_session(topic=topic, questions=max(1, args.questions))


if __name__ == "__main__":
    main()
