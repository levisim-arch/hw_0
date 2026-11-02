"""
views.py — HTTP request handlers for AttendanceChimp.

Each view corresponds to one URL endpoint.  Views receive an HTTP request,
interact with the database via models.py, and return an HTTP response.
"""

from django.shortcuts import render, redirect
from django.http import (HttpResponse, HttpResponseForbidden,
                         HttpResponseBadRequest, JsonResponse)
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.views.decorators.http import require_GET, require_POST
from datetime import datetime
import zoneinfo
import json
import io

# from .models import (InstructorProfile, StudentProfile, Course, Enrollment,
#                      Lecture, QRCodeUpload, is_instructor, is_student,
#                      getUploadsForCourse)

CDT = zoneinfo.ZoneInfo("America/Chicago")


# ---------------------------------------------------------------------------
# HW2  — index, time, sum
# ---------------------------------------------------------------------------

def index(request):
    """Render the home page (index.html)."""

    now = datetime.now(CDT)
    context = {
        "current_time": now.strftime("%H:%M"),
        "user_name": request.user.get_username() if request.user.is_authenticated else None}
    
    return render(request, 'app/index.html', context)

def time_view(request):
    """Return the current CST time as HH:MM."""
    now = datetime.now(CDT)
    return HttpResponse(now.strftime("%H:%M"))

def sum_view(request):
    """Return {n1 + n2}"""
    n1 = float(request.GET.get("n1", 0))
    n2 = float(request.GET.get("n2", 0))
    total = n1 + n2
    if total.is_integer():
        total = int(total)
    return HttpResponse(f"<p>{total}</p>")

# ---------------------------------------------------------------------------
# HW4  — user creation
# ---------------------------------------------------------------------------

@require_GET
def new(request):
    """Sign-up form."""
    return render(request, "app/new.html")


@csrf_exempt
@require_POST
def createUser(request):
    """Create a User plus a student/instructor profile, then sign them in."""

    email = request.POST.get("email", "").strip()
    user_name = request.POST.get("user_name", "").strip()
    password = request.POST.get("password", "")
    is_student = request.POST.get("is_student", "") in ("1", "true", "True")
 
    if not (email and user_name and password):
        return HttpResponse("Missing required field.", status=400)
    if len(user_name) > 100:
        return HttpResponse("Username too long.", status=400)
    if User.objects.filter(email__iexact=email).exists():
        return HttpResponse("A user with that email already exists.", status=409)
    if User.objects.filter(username=user_name).exists():
        return HttpResponse("That username is already taken.", status=409)
 
    with transaction.atomic(): 
        user = User.objects.create_user(username=user_name, email=email, password=password)
        if is_student:
            StudentProfile.objects.create(user=user, student=user_name, student_name=user_name)
        else:
            InstructorProfile.objects.create(user=user, instructor_name=user_name)
 
    login(request, user)
    return HttpResponse("User created.", status=200)

# ---------------------------------------------------------------------------
# HW5  — courses, lectures, QR uploads, dump
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# HW6  — getUploads
# ---------------------------------------------------------------------------



