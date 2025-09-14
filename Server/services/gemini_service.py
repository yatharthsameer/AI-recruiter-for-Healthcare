"""
Gemini AI Service — Caregiver Interview (Voice-First, Multimodal)
- Fixed Q1–Q9 (no generative drift)
- Per-turn multimodal analysis (audio/video + ASR transcript)
- Strict JSON schemas for deterministic scoring
- PHI redaction, red flags capture
- Timeboxed follow-ups (Q1, Q5, Q7) only if time allows
- Weighted section scoring + final structured report
"""

import os
import re
import json
import logging
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field

from dotenv import load_dotenv
import google.generativeai as genai

# Optional but recommended: robust retries for flaky net
try:
    from tenacity import retry, stop_after_attempt, wait_exponential

    TENACITY_AVAILABLE = True
except Exception:
    TENACITY_AVAILABLE = False

load_dotenv()
logger = logging.getLogger(__name__)


# ----------------------------- Config & Constants ----------------------------- #

CARE_GIVER_QUESTIONS: List[str] = [
    "Have you ever worked as a caregiver? If so, what kinds of patients/customers did you work with and what services/activities did you perform?",
    "Imagine you're finding a caregiver for a loved one. What traits or skills would be most important?",
    "How has your prior work or life experience helped you build the skills to be a good caregiver?",
    "Why do you want to be a caregiver? What are the most rewarding aspects of the job?",
    "Tell me about a time when being late caused problems for you or your team. What did you learn?",
    "Have you ever adjusted your routine to ensure punctuality at work? What changes did you make?",
    "Tell me about a time when you cared for a senior. What was most difficult and what was most meaningful?",
    "Tell me about a time you helped a colleague or client who was struggling emotionally or professionally. What did you do?",
    "If we asked your coworkers about you, what three things would they say?",
]

# follow-ups allowed only for Q1, Q5, Q7 (idx 0, 4, 6)
FOLLOWUP_ALLOWLIST: Dict[int, str] = {
    0: "Which daily activities did you handle most—like bathing, transfers, meals?",
    4: "What system do you use now to make sure you're on time?",
    6: "What made that experience meaningful for you?",
}

# Section weights (sum = 100)
SECTION_WEIGHTS = {
    "experience_skills": (["Q1", "Q2", "Q3"], 35),
    "motivation": (["Q4"], 10),
    "punctuality": (["Q5", "Q6"], 20),
    "compassion": (["Q7", "Q8"], 25),
    "self_awareness": (["Q9"], 10),
}

# Question -> section
Q_SECTION = {
    "Q1": "experience_skills",
    "Q2": "experience_skills",
    "Q3": "experience_skills",
    "Q4": "motivation",
    "Q5": "punctuality",
    "Q6": "punctuality",
    "Q7": "compassion",
    "Q8": "compassion",
    "Q9": "self_awareness",
}

# What to "listen for" per question (helps analysis stay on-rails)
Q_FOCUS = {
    "Q1": "Setting (home/clinic), populations (e.g., seniors, dementia, post-op), tasks (ADLs/IADLs: bathing, transfers, meals, meds reminders), teamwork/hand-offs, documentation",
    "Q2": "Reliable, respectful, patient, safety-first, clear communication, boundaries; give 2 behaviors that show those traits",
    "Q3": "Transferable skills from prior work/life; provide one short STAR example (situation, task, action, result)",
    "Q4": "Purpose beyond pay, realistic view of demands, impact on clients, why work is rewarding",
    "Q5": "Ownership of lateness, consequences (handoff delay, missed care), durable fix (buffers, backup transport), learning",
    "Q6": "Concrete routine changes (prep night before, route checks, buffer time) and measured improvement",
    "Q7": "Dignity, empathy, listening; difficult part and meaningful part; approach for safety and calm",
    "Q8": "Notice cues, supportive response, escalate when needed, outcome",
    "Q9": "3 job-relevant traits; include at least one growth area; be specific",
}

SYSTEM_PROMPT = """
You are CareBot, a warm, efficient interviewer for caregiver roles. Finish ~12 minutes (hard cap 15).
Short, plain sentences. Avoid PHI and protected attributes. If PHI appears, acknowledge and treat as redacted.
After each answer, produce a one-line reflection. Follow-ups allowed only on Q1, Q5, Q7 (≤20s).
Score each answer on a 0–4 scale using the rubric. Output strictly in the JSON schema when requested.
Red flags: unsafe practice; disrespect for dignity/safety; privacy breach; normalizing no-shows/chronic lateness.
Be content-focused only; ignore accent/appearance.
"""

# Strict JSON schema for per-question analysis
PER_TURN_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "signals": {
            "type": "object",
            "properties": {
                "setting": {"type": "string"},
                "populations": {"type": "array", "items": {"type": "string"}},
                "tasks": {"type": "array", "items": {"type": "string"}},
                "teamwork": {"type": "boolean"},
                "star": {
                    "type": "object",
                    "properties": {
                        "present": {"type": "boolean"},
                        "action": {"type": "string"},
                        "result": {"type": "string"},
                    },
                },
            },
            "additionalProperties": True,
        },
        "score_0_to_4": {"type": "integer", "minimum": 0, "maximum": 4},
        "missing_keys": {"type": "array", "items": {"type": "string"}},
        "red_flags": {"type": "array", "items": {"type": "string"}},
        "summary_one_line": {"type": "string"},
    },
    "required": [
        "score_0_to_4",
        "summary_one_line",
        "signals",
        "missing_keys",
        "red_flags",
    ],
    "additionalProperties": False,
}

# PHI patterns (lightweight & conservative)
PHI_PATTERNS = [
    r"\b\d{3}-\d{2}-\d{4}\b",  # US SSN-ish
    r"\b(?:\+?\d{1,3}[-.\s]?)?\d{3}[-.\s]?\d{3,4}[-.\s]?\d{4}\b",  # phone-ish
    r"\b(?:Mr|Mrs|Ms|Dr)\.?\s+[A-Z][a-z]+(?:\s[A-Z][a-z]+)?\b",  # simple names
    r"\b\d{1,3}\s+[A-Za-z]{2,}\s+(Street|St|Avenue|Ave|Road|Rd)\b",  # addresses-ish
]


@dataclass
class TurnResult:
    question_id: str
    summary_one_line: str
    score_0_to_4: int
    signals: Dict[str, Any] = field(default_factory=dict)
    missing_keys: List[str] = field(default_factory=list)
    red_flags: List[str] = field(default_factory=list)
    followup: Optional[str] = None  # what to ask (if any)


# ----------------------------- Service Class ----------------------------- #

class GeminiService:
    """Service for interacting with Google's Gemini for caregiver interviews (multimodal, timed)."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.summary_model_name = os.getenv("GEMINI_MODEL_SUMMARY", "gemini-1.5-pro")
        self.model = None
        self.summary_model = None
        self.initialized = False

        if self.api_key:
            self._initialize()
        else:
            logger.warning("GEMINI_API_KEY not set, running in fallback mode")

    def _initialize(self):
        """Initialize Gemini clients with a single master system prompt."""
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(
                self.model_name, system_instruction=SYSTEM_PROMPT
            )
            # Optional: richer synthesis model for final narrative
            self.summary_model = genai.GenerativeModel(
                self.summary_model_name, system_instruction=SYSTEM_PROMPT
            )
            self.initialized = True
            logger.info(
                f"✅ Gemini initialized (turn model: {self.model_name}, summary model: {self.summary_model_name})"
            )
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini: {e}")
            self.initialized = False

    # ----------------------------- Public API ----------------------------- #

    def get_question(self, idx: int, user_data: Optional[Dict] = None) -> str:
        """Return the fixed question text (optionally personalized with first name)."""
        q = CARE_GIVER_QUESTIONS[idx]
        name = (user_data or {}).get("firstName")
        return f"{name}, {q}" if name else q

    def maybe_followup(
        self, idx: int, analysis: Dict, remaining_sec: int
    ) -> Optional[str]:
        """Gate follow-ups by allowlist, missing keys, and time remaining."""
        if idx not in FOLLOWUP_ALLOWLIST:
            return None
        if remaining_sec < 90:
            return None
        missing = analysis.get("missing_keys", [])
        return (
            FOLLOWUP_ALLOWLIST[idx] if (missing and isinstance(missing, list)) else None
        )

    def _redact_phi(self, text: str) -> str:
        """Light PHI redaction (conservative, not exhaustive)."""
        if not text:
            return ""
        red = text
        for pat in PHI_PATTERNS:
            red = re.sub(pat, "[REDACTED]", red)
        return red

    def _upload_media(
        self, path_or_bytes: Optional[bytes], mime_type: Optional[str]
    ) -> Optional[Any]:
        """Upload media to Gemini; accepts bytes or file path. Returns a file handle or None."""
        if not path_or_bytes:
            return None
        try:
            if isinstance(path_or_bytes, (bytes, bytearray)):
                # For bytes, we need to create a temporary file or use a different approach
                # For now, we'll skip audio upload and rely on transcript analysis
                logger.info(
                    f"Audio data available ({len(path_or_bytes)} bytes) but skipping upload for now"
                )
                return None
            # assume file path
            return genai.upload_file(path_or_bytes)  # Gemini infers MIME if possible
        except Exception as e:
            logger.warning(f"Media upload failed ({mime_type}): {e}")
            return None

    def _gen_config_json(self, schema: Dict) -> Dict:
        """Generation config to force strict JSON."""
        return {
            "response_mime_type": "application/json",
            "response_schema": schema,
            "temperature": 0.2,
            "top_p": 0.9,
        }

    def _per_turn_instruction(self, question_id: str, lang: str) -> str:
        """Instruction payload for the per-turn analysis."""
        return (
            f"Question: {question_id}\n"
            f"Language: {lang}\n"
            f"Question focus: {Q_FOCUS.get(question_id, '')}\n"
            "Analyze the answer using the caregiver rubric. "
            "Focus on content, not accent/appearance. "
            "Return STRICT JSON in the provided schema. "
            "If a field is unknown, return an empty string or empty array; do not invent."
        )

    # Retry helper
    def _retryable_call(self, *args, **kwargs):
        if TENACITY_AVAILABLE:

            @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.5, max=3))
            def _wrapped():
                return self.model.generate_content(*args, **kwargs)

            return _wrapped()
        return self.model.generate_content(*args, **kwargs)

    def _retryable_summary(self, *args, **kwargs):
        if TENACITY_AVAILABLE:

            @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.5, max=3))
            def _wrapped():
                return self.summary_model.generate_content(*args, **kwargs)

            return _wrapped()
        return self.summary_model.generate_content(*args, **kwargs)

    def _safe_json(self, resp: Any) -> Dict:
        """Parse JSON from Gemini response object."""
        try:
            if hasattr(resp, "text") and resp.text:
                return json.loads(resp.text)
            # some SDKs return .candidates[0].content.parts[0].text
            if hasattr(resp, "candidates"):
                for c in resp.candidates:
                    try:
                        return json.loads(c.content.parts[0].text)
                    except Exception:
                        continue
        except Exception as e:
            logger.error(f"JSON parse error: {e}")
        return {}

    def _fallback_structured(self, transcript_text: str, question_id: str) -> Dict:
        """Very basic structured fallback when API is unavailable."""
        short = (transcript_text or "").strip()
        short = short[:180] + ("…" if len(short) > 180 else "")
        score = 3 if len(transcript_text or "") > 80 else 2
        return {
            "signals": {"star": {"present": False, "action": "", "result": ""}},
            "score_0_to_4": score,
            "missing_keys": [],
            "red_flags": [],
            "summary_one_line": f"Noted: {short}" if short else "Noted.",
        }

    def analyze_turn(
        self,
        idx: int,
        transcript_text: str,
        audio: Optional[bytes] = None,
        audio_mime: str = "audio/webm",
        video: Optional[bytes] = None,
        video_mime: str = "video/mp4",
        lang: str = "en",
        remaining_sec: int = 600,
    ) -> TurnResult:
        """
        Analyze one answer (Q1..Q9) with multimodal Gemini.
        Returns TurnResult including optional follow-up text.
        """
        qid = f"Q{idx + 1}"
        if not self.initialized:
            analysis = self._fallback_structured(transcript_text, qid)
            follow = self.maybe_followup(idx, analysis, remaining_sec)
            return TurnResult(
                question_id=qid,
                summary_one_line=analysis["summary_one_line"],
                score_0_to_4=analysis["score_0_to_4"],
                signals=analysis.get("signals", {}),
                missing_keys=analysis.get("missing_keys", []),
                red_flags=analysis.get("red_flags", []),
                followup=follow,
            )

        files = []
        try:
            a = self._upload_media(audio, audio_mime)
            if a:
                files.append(a)
            v = self._upload_media(video, video_mime)
            if v:
                files.append(v)
        except Exception as e:
            logger.warning(f"Upload exception: {e}")

        redacted = self._redact_phi(transcript_text or "")
        try:
            resp = self._retryable_call(
                contents=[
                    *files,
                    {"text": self._per_turn_instruction(qid, lang)},
                    {"text": f"Transcript:\n{redacted}"},
                ],
                generation_config=self._gen_config_json(PER_TURN_SCHEMA),
            )
            analysis = self._safe_json(resp) or self._fallback_structured(
                transcript_text, qid
            )
        except Exception as e:
            logger.error(f"Per-turn analysis failed ({qid}): {e}")
            analysis = self._fallback_structured(transcript_text, qid)

        follow = self.maybe_followup(idx, analysis, remaining_sec)

        # Sanity checks
        score = analysis.get("score_0_to_4", 0)
        if not isinstance(score, int):
            try:
                score = int(score)
            except Exception:
                score = 0
        score = max(0, min(4, score))

        return TurnResult(
            question_id=qid,
            summary_one_line=analysis.get("summary_one_line", "").strip(),
            score_0_to_4=score,
            signals=analysis.get("signals", {}),
            missing_keys=analysis.get("missing_keys", []),
            red_flags=analysis.get("red_flags", []),
            followup=follow,
        )

    # ----------------------------- Scoring & Report ----------------------------- #

    def compute_scores(
        self, per_q_scores: Dict[str, int]
    ) -> Tuple[Dict[str, int], int]:
        """Convert per-question (0..4) into weighted section scores and total (0..100)."""
        section_scores: Dict[str, int] = {}
        total = 0
        for section, (qs, weight) in SECTION_WEIGHTS.items():
            raw = sum(per_q_scores.get(q, 0) for q in qs)
            max_raw = 4 * len(qs)
            val = round((raw / max_raw) * weight) if max_raw else 0
            section_scores[section] = val
            total += val
        return section_scores, total

    def build_final_report(
        self,
        candidate_id: str,
        lang: str,
        turns: List[TurnResult],
        manager_summary: bool = True,
    ) -> Dict[str, Any]:
        """Compile structured end-of-interview report; optionally add narrative summary from summary model."""
        per_q_scores = {t.question_id: t.score_0_to_4 for t in turns}
        section_scores, total = self.compute_scores(per_q_scores)

        evidence: Dict[str, Dict[str, Any]] = {}
        red_flags: List[str] = []
        for t in turns:
            if t.question_id == "Q1":
                evidence["Q1"] = {
                    "setting": t.signals.get("setting", ""),
                    "populations": t.signals.get("populations", []),
                    "tasks": t.signals.get("tasks", []),
                    "example": t.signals.get("star", {}).get("action", ""),
                }
            if t.question_id == "Q5":
                evidence["Q5"] = {
                    "issue": "lateness",
                    "impact": "",  # model may not fill impact; we keep placeholders
                    "fix": t.signals.get("star", {}).get("action", ""),
                }
            if t.question_id == "Q7":
                evidence["Q7"] = {
                    "challenge": "",
                    "approach": t.signals.get("star", {}).get("action", ""),
                    "meaning": "",
                }
            red_flags.extend(t.red_flags or [])

        report: Dict[str, Any] = {
            "candidate_id": candidate_id,
            "duration_sec": None,  # fill at orchestrator level
            "language": lang,
            "section_scores": section_scores,
            "total_score": total,
            "per_question_scores": per_q_scores,
            "evidence": evidence,
            "red_flags": red_flags,
            "overall_recommendation": self._recommend(total, red_flags),
            "notes_for_hiring_manager": [],  # optional bullets after narrative
        }

        if manager_summary and self.initialized:
            try:
                # Build a deterministic JSON payload for the summary model to use.
                payload = {
                    "section_scores": section_scores,
                    "total_score": total,
                    "highlights": [
                        {
                            "qid": t.question_id,
                            "summary": t.summary_one_line,
                            "score": t.score_0_to_4,
                        }
                        for t in turns
                    ],
                    "red_flags": red_flags,
                }
                resp = self._retryable_summary(
                    contents=[
                        {
                            "text": (
                                "Create a concise hiring-manager summary (3 short paragraphs max). "
                                "Be objective and concrete. Do not restate the rubric. "
                                "Use the JSON below.\n\n"
                                + json.dumps(payload, ensure_ascii=False)
                            )
                        }
                    ],
                    generation_config={"temperature": 0.2},
                )
                narrative = getattr(resp, "text", None) or ""
                report["manager_summary"] = narrative.strip()
            except Exception as e:
                logger.warning(f"Summary generation failed: {e}")

        return report

    def _recommend(self, total: int, red_flags: List[str]) -> str:
        """Simple recommendation policy; tweak thresholds as needed."""
        if red_flags:
            return "Needs human review"
        if total >= 80:
            return "Advance to shadow shift"
        if total >= 65:
            return "Advance to panel"
        if total >= 50:
            return "Consider with training"
        return "Decline"

    # ----------------------------- Legacy API Compatibility ----------------------------- #

    async def generate_question(
        self,
        interview_type: str = "general",
        question_number: int = 0,
        history: List[Dict] = None,
        user_data: Dict = None,
    ) -> str:
        """Legacy compatibility: return fixed caregiver questions"""
        if interview_type == "home_care" and question_number < len(
            CARE_GIVER_QUESTIONS
        ):
            return self.get_question(question_number, user_data)

        # Fallback for non-caregiver interviews
        fallback_questions = [
            "Tell me about yourself and your background.",
            "What interests you about this role?",
            "Describe a challenge you've overcome.",
            "What are your strengths?",
            "Where do you see yourself in the future?",
        ]

        if question_number < len(fallback_questions):
            q = fallback_questions[question_number]
            name = (user_data or {}).get("firstName")
            return f"Hi {name}, {q}" if name else q

        return "Thank you for your responses. Do you have any questions for us?"

    async def generate_response(self, prompt: str) -> str:
        """Legacy compatibility for simple text generation"""
        if not self.initialized:
            return "I'm currently unavailable. Please try again later."

        try:
            response = self._retryable_call(
                contents=[{"text": prompt}], generation_config={"temperature": 0.7}
            )
            return getattr(response, "text", "").strip()
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I'm having trouble processing that request right now."

    async def analyze_response(
        self, response: str, question_number: int, history: List[Dict] = None
    ) -> str:
        """Legacy compatibility for response analysis"""
        return f"Thank you for that response. I can see you've put thought into your answer."

    async def generate_final_feedback(
        self, responses: List[str], interview_type: str
    ) -> str:
        """Legacy compatibility for final feedback"""
        return "Thank you for completing the interview. We'll be in touch soon with next steps."

    async def generate_transcript_summary(
        self,
        transcript_text: str,
        interview_type: str = "general",
        user_data: Dict = None,
    ) -> str:
        """Legacy compatibility for transcript summary"""
        if not self.initialized:
            return "Interview completed. Summary generation unavailable."

        try:
            prompt = f"""
            Summarize this interview transcript for {interview_type} position:
            
            {transcript_text[:2000]}...
            
            Provide a brief, professional summary focusing on key qualifications and responses.
            """

            response = self._retryable_call(
                contents=[{"text": prompt}], generation_config={"temperature": 0.3}
            )
            return getattr(
                response, "text", "Interview completed successfully."
            ).strip()
        except Exception as e:
            logger.error(f"Error generating transcript summary: {e}")
            return "Interview completed successfully."

    # ----------------------------- Health ----------------------------- #

    def health_check(self) -> Dict[str, Any]:
        """Check API configuration and a trivial JSON round-trip."""
        if not self.api_key:
            return {"status": "warning", "message": "GEMINI_API_KEY not configured"}
        if not self.initialized:
            return {"status": "error", "message": "Gemini not initialized"}

        try:
            resp = self._retryable_call(
                contents=[{"text": 'Return {"ok": true}'}],
                generation_config={
                    "response_mime_type": "application/json",
                    "response_schema": {
                        "type": "object",
                        "properties": {"ok": {"type": "boolean"}},
                        "required": ["ok"],
                    },
                },
            )
            data = self._safe_json(resp)
            if data.get("ok") is True:
                return {
                    "status": "healthy",
                    "model": self.model_name,
                    "summary_model": self.summary_model_name,
                }
            return {"status": "error", "message": "Unexpected health response"}
        except Exception as e:
            return {"status": "error", "message": f"Health call failed: {e}"}


# ----------------------------- Optional Orchestrator Helpers ----------------------------- #


def personalize(question: str, user_data: Optional[Dict]) -> str:
    name = (user_data or {}).get("firstName")
    return f"{name}, {question}" if name else question


def estimate_remaining(total_elapsed_sec: int, max_sec: int = 900) -> int:
    return max(0, max_sec - total_elapsed_sec)


# Global instance
gemini_service = GeminiService()
