from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from .intent import classify_intent


class AgentPlanRateThrottle(UserRateThrottle):
    rate = "30/min"


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AgentPlanRateThrottle])
def plan(request):
    text = request.data.get("message", "")
    if not isinstance(text, str) or not text.strip():
        return Response(
            {"error": "A non-empty message is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if len(text) > 8000:
        return Response(
            {"error": "Message is too long (max 8000 characters)."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        result = classify_intent(text)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        "plan": result,
        "executed": False,
        "notice": "Planning only: no external action has been performed.",
    })
