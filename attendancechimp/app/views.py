"""
views.py — HTTP request handlers for AttendanceChimp.

Each view corresponds to one URL endpoint.  Views receive an HTTP request,
interact with the database via models.py, and return an HTTP response.
"""
import secrets

from django.contrib.auth import login
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import Course, InstructorProfile, Lecture, QRCodeUpload, StudentProfile
from django.shortcuts import render, redirect
from django.http import (HttpResponse, HttpResponseForbidden,
                         HttpResponseBadRequest, JsonResponse)
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.views.decorators.http import require_GET, require_POST
from datetime import datetime
from .models import Course, InstructorProfile, Lecture, QRCodeUpload, StudentProfile
from django.db import IntegrityError, transaction
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

def _instructor_profile(user):
    """The InstructorProfile of a logged-in instructor, else None."""
    if not user.is_authenticated:
        return None
    return InstructorProfile.objects.filter(user=user).first()
 
 
def _student_profile(user):
    """The StudentProfile of a logged-in student, else None."""
    if not user.is_authenticated:
        return None
    return StudentProfile.objects.filter(user=user).first()

@require_GET
def new_course(request):
    return render(request, "app/new_course.html")
 
 
@require_GET
def new_lecture(request):
    courses = Course.objects.order_by("course")
    return render(request, "app/new_lecture.html", {"courses": courses})
 
 
@require_GET
def new_qr_upload(request):
    return render(request, "app/new_qr_upload.html")

# api endpoints
DAY_FIELDS = [("day-mon", "Mon"), ("day-tue", "Tue"), ("day-wed", "Wed"),
              ("day-thu", "Thu"), ("day-fri", "Fri")]
 
 
def _checked(request, field):
    """True if a checkbox-style POST field was sent (browser sends 'on')."""
    value = request.POST.get(field)
    return value is not None and value.strip().lower() not in ("", "0", "false", "off")
 
 
@csrf_exempt
@require_POST
def createCourse(request):
    """Instructor only. Creates a Course from the new_course form fields."""
    instructor = _instructor_profile(request.user)
    if instructor is None:
        return HttpResponse("Instructor login required.", status=401)
 
    name = request.POST.get("course-name", "").strip()
    start = request.POST.get("start-time", "").strip()
    end = request.POST.get("end-time", "").strip()
    days = [label for field, label in DAY_FIELDS if _checked(request, field)]
 
    if not (name and start and end and days):
        return HttpResponse("course-name, start-time, end-time and at least one day are required.",
                            status=400)
    if len(name) > 100 or len(start) > 20 or len(end) > 20:
        return HttpResponse("A field is too long.", status=400)
 
    schedule = f"{','.join(days)} {start}-{end}"   # e.g. "Mon,Wed 10:00-11:15"
 
    try:
        course = Course.objects.filter(course=name).first()
        if course is None:
            # Course.course is unique and is what createLecture's `choice` refers to.
            Course.objects.create(course=name, course_name=name, department="",
                                  meeting_schedule=schedule, instructor=instructor)
        elif course.instructor_id == instructor.id:
            course.meeting_schedule = schedule   # same instructor re-submitting: update, still 200
            course.save()
        else:
            return HttpResponse("A course with that name already exists.", status=409)
    except IntegrityError:
        return HttpResponse("A course with that name already exists.", status=409)
    return HttpResponse("Course saved.", status=200)
 
 
@csrf_exempt
@require_POST
def createLecture(request):
    """Instructor only. Creates a Lecture (with a random QR identifier) for the chosen course."""
    if _instructor_profile(request.user) is None:
        return HttpResponse("Instructor login required.", status=401)
 
    choice = request.POST.get("choice", "").strip()
    if not choice:
        return HttpResponse("choice is required.", status=400)
 
    course = (Course.objects.filter(course=choice).first()
              or Course.objects.filter(course_name=choice).first())
    if course is None:
        return HttpResponse("No such course.", status=404)
 
    Lecture.objects.create(date=datetime.now(CDT),
                           qr_identifier=secrets.token_urlsafe(12),  # random, unique in practice
                           course_id=course)   # (the FK field is literally named course_id)
    return HttpResponse("Lecture created.", status=200)
 
 
@csrf_exempt
@require_POST
def createQRCodeUpload(request):
    """Student only. Records that the logged-in student uploaded a QR-code image."""
    student = _student_profile(request.user)
    if student is None:
        return HttpResponse("Student login required.", status=401)
 
    if request.FILES.get("imageUpload") is None:
        return HttpResponse("imageUpload file is required.", status=400)
 
    QRCodeUpload.objects.create(lecture=None,
                                upload_time=datetime.now(CDT).strftime("%Y-%m-%d %H:%M:%S"),
                                student=student)
    return HttpResponse("Upload recorded.", status=200)
 
 
@require_GET
def dumpUploads(request):
    """Instructor only. JSON list of {"username", "upload_time"} for every upload."""
    if _instructor_profile(request.user) is None:
        return HttpResponse("Instructor login required.", status=401)
 
    rows = QRCodeUpload.objects.select_related("student__user").order_by("id")
    data = [{"username": r.student.user.username, "upload_time": r.upload_time} for r in rows]
    return JsonResponse(data, safe=False)

# ---------------------------------------------------------------------------
# HW6  — getUploads
# ---------------------------------------------------------------------------



