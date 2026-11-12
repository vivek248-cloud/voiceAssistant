import re
from dataclasses import asdict, dataclass


EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,}", re.I)


@dataclass
class AgentPlan:
    intent: str
    confidence: float
    requires_confirmation: bool
    entities: dict
    missing_fields: list
    next_step: str
    message: str


def classify_intent(text: str) -> dict:
    """Create a safe, non-executing plan for a user request.

    This first milestone only classifies and plans. It never sends email,
    creates reminders, reads health data, or processes files.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("A non-empty message is required.")

    original = text.strip()
    value = original.lower()
    emails = EMAIL_RE.findall(original)

    if any(word in value for word in ("email", "e-mail", "mail to", "send a mail")):
        is_send = any(word in value for word in ("send", "email to", "mail to"))
        missing = []
        if not emails:
            missing.append("recipient_email")
        if not any(word in value for word in ("subject", "about", "regarding")):
            missing.append("subject_or_purpose")
        if is_send:
            missing.append("message_confirmation")
        return asdict(AgentPlan(
            intent="email_send" if is_send else "email_draft",
            confidence=0.94,
            requires_confirmation=bool(is_send),
            entities={"recipient_emails": emails},
            missing_fields=missing,
            next_step="collect_email_details" if missing else "prepare_email_preview",
            message="I can prepare an email. Sending will require your explicit approval."
        ))

    schedule_words = ("remind", "reminder", "schedule", "every day", "every week",
                      "tomorrow", "at 9", "at 10", "at 8", "on monday")
    if any(word in value for word in schedule_words):
        return asdict(AgentPlan(
            intent="task_schedule",
            confidence=0.90,
            requires_confirmation=True,
            entities={"email_addresses": emails},
            missing_fields=["task_description", "scheduled_datetime"],
            next_step="collect_schedule_details",
            message="I can prepare a scheduled task. It will not run until you review and confirm it."
        ))

    if any(word in value for word in ("image", "photo", "picture", "screenshot",
                                      "analyse this", "analyze this", "extract text")):
        return asdict(AgentPlan(
            intent="image_analysis",
            confidence=0.88,
            requires_confirmation=False,
            entities={},
            missing_fields=["image_upload"],
            next_step="request_image_upload",
            message="Please attach an image so I can analyze it."
        ))

    if any(word in value for word in ("health", "medicine", "medication", "symptom",
                                      "blood pressure", "blood sugar", "sleep", "workout")):
        return asdict(AgentPlan(
            intent="health_assistance",
            confidence=0.86,
            requires_confirmation=False,
            entities={},
            missing_fields=[],
            next_step="health_chat_or_record",
            message="I can help organize health information and reminders. I cannot diagnose or replace a clinician."
        ))

    return asdict(AgentPlan(
        intent="general_chat",
        confidence=0.70,
        requires_confirmation=False,
        entities={},
        missing_fields=[],
        next_step="continue_chat",
        message="This request can be handled as a normal JARVIS conversation."
    ))
