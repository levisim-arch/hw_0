"""
models.py — Data model for AttendanceChimp.

AttendanceChimp is an electronic class attendance tool.  Instructors create
courses and lectures; each lecture is assigned a random QR code.  Students
photograph the QR code and upload the image.  The system decodes the QR code,
matches it to a lecture, and records the attendance.

Entities
--------
- CourseProfile   : extends Django User → instructor-specific data
- StudentProfile  : extends Django User → student-specific data
- Course          : a course taught by one instructor
- Enrollment      : junction table linking students to courses
- Lecture         : a single class meeting (has a QR-code identifier)
- QRCodeUpload    : a student's uploaded QR-code photograph
"""

from django.db import models
from django.contrib.auth.models import User

import logging
import string
import random

logger = logging.getLogger(__name__) # set up tracking, auditing, and debugging
                                                               # allows using logger.warning(), logger.error(), 
                                                               # logger.info(), etc. Better than print() for debuggin... 


# ---------------------------------------------------------------------------
# User profiles
# ---------------------------------------------------------------------------

class StudentProfile(models.Model):
    '''Student user linked one to one with Django user.'''
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student = models.CharField(unique=True, max_length=100)
    student_name = models.CharField(max_length=100)


# ---------------------------------------------------------------------------
# Instructor profiles
# ---------------------------------------------------------------------------

# note that this class was not in the template but suggested in ER diagram
class InstructorProfile(models.Model):
    '''Instructor profile'''
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    instructor_name = models.CharField(max_length=100)


# ---------------------------------------------------------------------------
# Course
# ---------------------------------------------------------------------------

class Course(models.Model):
    '''Taught by an instructor, linked to students through enrollment table'''
    course = models.CharField(unique=True, max_length=100)
    course_name = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    meeting_schedule = models.CharField(max_length=100)
    instructor = models.ForeignKey(InstructorProfile, on_delete=models.CASCADE)


# ---------------------------------------------------------------------------
# Enrollment
# ---------------------------------------------------------------------------

class Enrollment(models.Model):
    '''Connects students with course.'''
    student = models.ForeignKey(StudentProfile, on_delete=models.PROTECT)
    course = models.ForeignKey(Course, on_delete=models.PROTECT)


# ---------------------------------------------------------------------------
# Lecture
# ---------------------------------------------------------------------------

class Lecture(models.Model):
    '''Notes an individual lecture within a course.'''
    date = models.DateTimeField()
    qr_identifier = models.CharField(unique=True, max_length=100)
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE)


# ---------------------------------------------------------------------------
# QR Code Upload
# ---------------------------------------------------------------------------

class QRCodeUpload(models.Model):
    '''Notes the QR upload of a student checking in to class.'''
    lecture = models.ForeignKey(Lecture, on_delete=models.SET_NULL, null=True)
    upload_time = models.CharField(max_length=100)
    student = models.ForeignKey(StudentProfile, on_delete=models.PROTECT)

# ---------------------------------------------------------------------------
# Helper / API functions
# ---------------------------------------------------------------------------



