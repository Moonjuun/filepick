
from django.http import JsonResponse

def root_health(request):
    return JsonResponse({"message": "Welcome to FilePick API!"})
