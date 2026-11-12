from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import health, chat
from .agent.views import plan as agent_plan

urlpatterns = [
    path("health/", health, name="health"),
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("chat/", chat, name="chat"),
    path("agent/plan/", agent_plan, name="agent-plan"),
]
