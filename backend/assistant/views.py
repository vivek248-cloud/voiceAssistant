import os

from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from .ai_router import AIProviderError, generate_reply


class ChatRateThrottle(AnonRateThrottle):
    rate = "20/min"


@api_view(["GET"])
def health(request):
    return Response({"status": "ok", "service": "jarvis-api"})


@api_view(["POST"])
@throttle_classes([ChatRateThrottle])
def chat(request):
    message = request.data.get("message", "")
    history = request.data.get("history", [])
    privacy_mode = request.data.get("privacy_mode", "local")
    allow_cloud = request.data.get("allow_cloud", False)

    if not isinstance(message, str) or not message.strip():
        return Response(
            {"error": "A non-empty message is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if len(message) > 8000:
        return Response(
            {"error": "Message is too long (max 8000 characters)."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not isinstance(privacy_mode, str):
        return Response(
            {"error": "privacy_mode must be local, cloud, or hybrid."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not isinstance(allow_cloud, bool):
        return Response(
            {"error": "allow_cloud must be true or false."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    messages = [{
        "role": "system",
        "content": (
            "You are JARVIS, a helpful personal AI assistant. Be clear, calm, capable, "
            "and concise. Do not claim to have taken actions you have not taken."
        ),
    }]

    # Keep only a small, validated recent history. Client roles are restricted.
    if isinstance(history, list):
        for item in history[-12:]:
            if (
                isinstance(item, dict)
                and item.get("role") in ("user", "assistant")
                and isinstance(item.get("content"), str)
            ):
                messages.append({
                    "role": item["role"],
                    "content": item["content"][:8000],
                })

    messages.append({"role": "user", "content": message.strip()})

    try:
        answer, model, provider = generate_reply(
            messages,
            privacy_mode=privacy_mode,
            allow_cloud=allow_cloud,
        )
        return Response({
            "answer": answer,
            "model": model,
            "provider": provider,
        })
    except AIProviderError as exc:
        message_text = str(exc)
        http_status = (
            status.HTTP_504_GATEWAY_TIMEOUT
            if "timed out" in message_text.lower()
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        return Response({"error": message_text}, status=http_status)
