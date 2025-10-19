from django.shortcuts import render

# Create your views here.

def index(request):
    return render(request, "home/index.html")


def help_center(request):
    return render(request, "home/help_center.html")


def contact_us(request):
    return render(request, "home/contact_us.html")


def security_center(request):
    return render(request, "home/security_center.html")


def dispute_resolution(request):
    return render(request, "home/dispute_resolution.html")


def accessibility(request):
    return render(request, "home/accessibility.html")