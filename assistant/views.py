import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .services import process_command

def home(request):
    return render(request, "assistant/index.html")

@csrf_exempt
def voice_api(request):
    if request.method == "POST":
        data = json.loads(request.body)
        result = process_command(data.get("text", ""))
        return JsonResponse(result)

    return JsonResponse({"error": "Invalid request"}, status=400)
