from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from .ai_router import AIProviderError, generate_reply


class ChatRateThrottle(UserRateThrottle):
    rate = "20/min"


@api_view(["GET"])
@permission_classes([])
def health(request):
    return Response({"status": "ok", "service": "jarvis-api"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
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

    privacy_mode = privacy_mode.strip().lower()

    if privacy_mode not in {"local", "cloud", "hybrid"}:
        return Response(
            {"error": "Invalid privacy_mode. Use local, cloud, or hybrid."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not isinstance(allow_cloud, bool):
        return Response(
            {"error": "allow_cloud must be true or false."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not isinstance(history, list):
        return Response(
            {"error": "history must be a list of messages."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(history) > 12:
        history = history[-12:]

    messages = [{
        "role": "system",
        "content": (
            "You are JARVIS, a helpful personal AI assistant. Be clear, calm, capable, "
            "and concise. Do not claim to have taken actions you have not taken."
        ),
    }]

    total_history_length = 0

    for item in history:
        if not isinstance(item, dict):
            return Response(
                {"error": "Each history item must be an object."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        role = item.get("role")
        content = item.get("content")

        if role not in ("user", "assistant") or not isinstance(content, str):
            return Response(
                {"error": "History items must contain a valid role and text content."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(content) > 4000:
            return Response(
                {"error": "Each history message must be 4000 characters or fewer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        total_history_length += len(content)

        if total_history_length > 20000:
            return Response(
                {"error": "Total chat history is too large."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        messages.append({
            "role": role,
            "content": content,
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

        return Response(
            {"error": message_text},
            status=http_status,
        )
