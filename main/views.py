import csv
import os

from django.db.models import Sum
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseRedirect
from main import forms
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from Pushplata_STC_Leaderboard import settings
from main.models import Student, Marks, Quiz, Log
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


def home_view(request):
    quizzes = Quiz.objects.all()

    performers = overall_top_performers()

    return render(
        request=request,
        template_name='main/homeView.html',
        context={
            'quizzes': quizzes,
            'performers': performers
        }
    )


def overall_top_performers():

    # Longest Django Query I've written till date (20 July 2020)
    mm = Marks.objects.values(
        'student',
        'student__first_name',
        'student__last_name'
    ).annotate(
        total_marks=Sum("marks")
    ).order_by(
        '-total_marks'
    )[:7]

    performers = []
    # print(type(mm))
    for m in mm:
        # print(m)
        student_fn = m['student__first_name']
        student_ln = m['student__last_name']

        if student_ln == '-':
            student_ln = ''

        full_name = student_fn + " " + student_ln
        performers.append(full_name)

    return performers


def site_admin_login(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect("/siteadmin/upload/?already_authenticated=true")

    if request.method == 'POST':
        form = forms.LoginForm(request.POST)

        # print(form)
        print("form.is_valid(): {}".format(form.is_valid()))

        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        # print(user)

        if user is None:
            data = {'error': 'Invalid User'}
            return JsonResponse(data=data, status=404)
        else:
            login(request, user)
            # print(request.GET.get('next'))
            if request.GET.get('next') is not None:
                return HttpResponseRedirect(request.GET.get('next'))

            return HttpResponseRedirect("/siteadmin/upload/")

    elif request.method == 'GET':
        messages = {}
        info = []
        if request.GET.get("next"):
            info.append('You need to login to continue')
            messages.update({'info': info})

        form = forms.LoginForm()
        return render(
            request=request,
            template_name='siteadmin/login.html',
            context={
                'form': form,
                'messages': messages
            }
        )
    else:
        data = {'error_code': 405, 'error_description': 'Method Not Allowed'}
        return JsonResponse(data=data)


def site_admin_logout(request):
    logout(request)
    return HttpResponseRedirect("/siteadmin/login/")


@login_required()
def upload_quiz_data(request):
    # if request.GET.get('already_authenticated'):
    #     data = {'success': 1, 'message': 'You are already authenticated'}

    form = forms.CSVReportUploadForm()

    if request.method == "POST":
        form = forms.CSVReportUploadForm(request.POST, request.FILES)
        # print(form)
        # print(form.is_valid())
        # print(request.FILES)
        handle_uploaded_file(request.FILES["file"])

    return render(request, template_name="siteadmin/upload_reports.html", context={'form': form})


def create_log(log_type, message):
    Log.objects.create(
        type=log_type,
        message=message
    )


def handle_uploaded_file(f):
    report_dir_loc = os.path.join(settings.BASE_DIR, "csv_reports")

    if os.path.exists(report_dir_loc):
        print("csv_reports exists")
    else:
        print("csv_reports does not exists")
        os.mkdir(report_dir_loc)
        print("Creating csv_reports directory\n")

    report_location = os.path.join(report_dir_loc, f.name)

    # Storing the csv file at {BASE_DIR}/csv_reports
    with open(report_location, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

    # After storing read the csv file and store the quiz details in the database.
    with open(report_location, 'r') as csv_report:

        quiz = None

        report = csv.reader(csv_report)
        line_count = 0
        max_marks = None

        split_list = f.name.split("STC10-2020")
        split_list = split_list[len(split_list)-1]
        split_list = split_list.split("-grades.csv")
        split_list = split_list[len(split_list)-2]

        quiz_name = split_list
        print("Quiz Name: {}".format(quiz_name))

        # String spaces from front and back
        i = 0
        while True:
            if quiz_name[i] == ' ' or quiz_name[i] == '-':
                quiz_name = quiz_name[:i] + quiz_name[(i + 1):]
                i += 1
            else:
                print("Replaced {} space/hyphens at front".format(i))
                break

        i = len(quiz_name) - 1
        while True:
            if quiz_name[i] == ' ' or quiz_name[i] == '-':
                quiz_name = quiz_name[:i] + quiz_name[(i + 1):]
                i -= 1
            else:
                print("Replaced {} space/hyphens at back".format(len(quiz_name) - 1 - i))
                break

        print("\nQuiz Name: {}".format(quiz_name))

        for row in report:
            # get the max_marks from the eighth(index: 7) col in header row.
            if line_count == 0:
                max_marks = float(row[7].split("/")[1])
                print("MM: {}".format(max_marks))
                quiz, created = Quiz.objects.get_or_create(quiz_name=quiz_name, max_marks=max_marks)

                if created:
                    create_log("Info", "New Quiz Created ({})".format(quiz))
                    #     If new quiz is created, no need to check models.marks for present entries
                    #     corresponding to students who has already taken the quiz.
                else:
                    create_log("Info", "Quiz Report Updated ({})".format(quiz))
                    #   If the quiz is available already, then delete all the models.marks entries for
                    #   that quiz.
                    quiz_marks = Marks.objects.filter(quiz=quiz)
                    print("Number of Already Existing Marks: {}".format(len(quiz_marks)))
                    print("Delete all the existing {} marks records.".format(len(quiz_marks)))
                    quiz_marks.delete()

            # Quiz Created/Fetched
            else:
                # If line_count is not 0, these are students' rows

                # column_number  -----  Attribute
                # 0              -----  Surname
                # 1              -----  First Name
                # 2              -----  Email
                # 3              -----  State (Quiz State) (In Progress/Finished)
                # 4              -----  Started on
                # 5              -----  Completed
                # 6              -----  Time taken
                # 7              -----  Grade (Marks Scored)

                email = row[2]
                last_name = row[0]
                first_name = row[1]
                marks = float(row[7])

                is_email = None

                try:
                    validate_email(email)
                    is_email = True
                except ValidationError:
                    is_email = False

                if is_email:
                    # print("Email is valid")
                    student, created = Student.objects.get_or_create(
                        first_name=first_name,
                        last_name=last_name,
                        email=email
                    )

                    if created:
                        create_log("Info", "New Student Created: ({})".format(student))
                        print("New Student Created: ({})".format(student))

                    # Student Created/Fetched

                    # Create Marks
                    print(student)
                    Marks.objects.create(student=student, quiz=quiz, marks=marks)
                else:
                    print("Invalid Email: {}".format(email))
                    break

            line_count += 1


def top_performers(quiz):
    marks = Marks.objects.filter(quiz=quiz).order_by('-marks')[:7]

    performers = []
    for m in marks:
        performers.append(m.student.get_name())

    return performers


def quiz_leaderboard(request):
    quiz_pk = request.GET.get('id')

    quiz = Quiz.objects.get(pk=quiz_pk)
    performers = top_performers(quiz)

    return render(
        request,
        template_name="main/quiz_leaderboard.html",
        context={
            'top_performers': performers,
            'quiz': quiz
        }
    )
