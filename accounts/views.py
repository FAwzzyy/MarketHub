from django.http import HttpResponse

def index(request):
    return HttpResponse("Welcome to MarketHub")


def register(request):
    form = UserCreationForm()

    return render(request, "registration/register.html", {
        "form": form
    })