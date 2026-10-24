from django.db import models
from django.contrib.auth.models import User


# I used Claude
# Prompt: [uploaded models.py template] Fill in the blanks for an app
# to scan QR codes for attendance using Django.

# ---------------------------------------------------------------------------
# User profiles
# ---------------------------------------------------------------------------

class InstructorProfile(models.Model):
    """An instructor. Name, email, and login live on Django's built-in
    User; this table adds instructor-only data and links 1-to-1."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class StudentProfile(models.Model):
    """A student, linked 1-to-1 to a User, plus a university ID."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


# ---------------------------------------------------------------------------
# Course
# ---------------------------------------------------------------------------

class Course(models.Model):
    """A course with exactly one instructor. Students are linked to it
    through the Enrollment table."""
    name = models.CharField(max_length=100)
    instructor = models.ForeignKey(InstructorProfile, on_delete=models.PROTECT)
    meeting_schedule = models.CharField(max_length=100)  # e.g. "MWF 10:00-10:50"

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Enrollment
# ---------------------------------------------------------------------------

class Enrollment(models.Model):
    """Join table: one row = one student enrolled in one course.
    This is what makes the student-course relationship many-to-many."""
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("student", "course")  # no duplicate enrollments

    def __str__(self):
        return f"{self.student} in {self.course}"


# ---------------------------------------------------------------------------
# Lecture
# ---------------------------------------------------------------------------

class Lecture(models.Model):
    """One class meeting. qr_identifier is the unique string encoded in
    that meeting's QR code, so a code can't be reused for another lecture."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date = models.DateTimeField()
    qr_identifier = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return f"{self.course} on {self.date:%Y-%m-%d}"


# ---------------------------------------------------------------------------
# QR code uploads
# ---------------------------------------------------------------------------

class QRCodeUpload(models.Model):
    """A photo of a QR code uploaded by a student. upload_time is set
    automatically so it can be compared with the lecture time to flag
    late or suspicious uploads. lecture is optional (e.g. the code could
    not be matched to a lecture yet)."""
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    lecture = models.ForeignKey(Lecture, null=True, blank=True,
                                on_delete=models.SET_NULL)
    image = models.ImageField(upload_to="qr_uploads/")
    upload_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} @ {self.upload_time:%Y-%m-%d %H:%M}"