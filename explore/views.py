from datetime import date, timedelta
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.utils.http import url_has_allowed_host_and_scheme
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import localdate
from django.views.decorators.http import require_http_methods, require_POST, require_safe
from collections import Counter
from .data import ELEMENTS, INFP_SECTIONS, QUALITIES, SIGN_DETAILS, build_sections, sign_harmony, MOODS, MOOD_ART, OPTIONS, QUESTIONS, SIGNS, TAGS, TYPES, score
from .forms import EntryForm, LoginForm, SignupForm
from .models import Entry

NAV = (("home","Нүүр"),("quiz","Тест"),("types","Зан төлөв"),
       ("zodiac","Зурхай"),("mood","Мэдрэмж"),("journal","Миний тэмдэглэл"))

def page(request, template, active, **context):
    return render(request, f"explore/{template}.html", {"active":active,"nav":NAV,**context})

@require_safe
def home(request):
    return page(request,"home","home",featured=[TYPES[c] for c in ("INFP","ENFP","INTJ","ISFJ")], moods=MOOD_ART, signs=SIGNS)

@require_http_methods(["GET","HEAD","POST"])
def quiz(request):
    answers = request.session.get("answers", {})
    step = request.session.get("step",1)
    error = ""
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "reset":
            request.session.pop("answers",None)
            request.session.pop("step",None)
            return redirect("explore:quiz")
        if request.POST.get("step") != str(step):
            return redirect("explore:quiz")
        if action == "back":
            request.session["step"] = max(1,step-1)
            return redirect("explore:quiz")
        value = request.POST.get("answer","")
        if value in ("1","2","3","4","5","6","7"):
            answers[str(step)] = int(value)
            request.session["answers"] = answers
            if step == len(QUESTIONS):
                return redirect("explore:result")
            request.session["step"] = step+1
            return redirect("explore:quiz")
        error = "Дараах асуулт руу орохын өмнө хариултаа сонгоорой."
    return page(request,"quiz","quiz", step=step,total=len(QUESTIONS), question=QUESTIONS[step-1][2],
                options=list(reversed(list(enumerate(OPTIONS,1)))),selected=answers.get(str(step)),error=error)

@require_safe
def result(request):
    answers = request.session.get("answers",{})
    if any(str(i) not in answers for i in range(1,len(QUESTIONS)+1)):
        return redirect("explore:quiz")
    code, bars = score([answers[str(i)] for i in range(1,len(QUESTIONS)+1)])
    sections = INFP_SECTIONS if code == "INFP" else build_sections(code)
    return page(request,"result","quiz",profile=TYPES[code],bars=bars,sections=sections,
                tied=sum(b["tied"] for b in bars))

@require_safe
def types(request):
    q = request.GET.get("q","").strip()[:80]
    profiles = [t for t in TYPES.values() if q.casefold() in " ".join((t["code"],t["name"],t["summary"])).casefold()]
    return page(request,"types","types",profiles=profiles,q=q)

@require_safe
def type_detail(request,code):
    profile = TYPES.get(code.upper())
    if not profile:
        raise Http404("Төрөл олдсонгүй.")
    sections = INFP_SECTIONS if profile["code"] == "INFP" else build_sections(profile["code"])
    return page(request,"detail","types",profile=profile,sections=sections,
                related=[t for t in TYPES.values() if t!=profile and sum(a!=b for a,b in zip(t["code"],profile["code"]))==1][:3])

@require_safe
def zodiac(request):
    month,day=request.GET.get("month",""),request.GET.get("day","")
    index=error=None
    if "month" in request.GET or "day" in request.GET:
        try:
            birthday=date(2000,int(month),int(day))
        except (ValueError,OverflowError):
            error="Бодит сар, өдрийн хослол сонгоорой."
        else:
            # Month boundaries are inclusive for the sign that starts here.
            limits=(20,19,21,20,21,21,23,23,23,23,22,22)
            first=(9,10,11,0,1,2,3,4,5,6,7,8)
            index=(first[birthday.month-1]+int(birthday.day>=limits[birthday.month-1]))%12
    elif request.GET.get("sign","").isdigit() and int(request.GET["sign"])<12:
        index=int(request.GET["sign"])   # картнаас шууд ордыг сонгох
    sign=SIGNS[index] if index is not None else None
    detail=None
    if index is not None:
        detail={**SIGN_DETAILS[index],"harmony":sign_harmony(index),"prev":(index-1)%12,"next":(index+1)%12,
                "quality_text":QUALITIES[SIGN_DETAILS[index]["quality"]]}
    return page(request,"zodiac","zodiac", signs=list(enumerate(SIGNS)), sign=sign, detail=detail,error=error,
                elements=[(k,v[0],[SIGNS[i][0] for i in v[1]]) for k,v in ELEMENTS.items()],
                qualities=QUALITIES.items(),months=range(1,13),days=range(1,32),month=month,day=day,
                sign_names=[x[0] for x in SIGNS])

def own_entries(request):
    return Entry.objects.filter(user=request.user)

def safe_next(request):
    target = request.POST.get("next") or request.GET.get("next") or ""
    ok = url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}, require_https=request.is_secure())
    return target if ok else ""

@require_http_methods(["GET","HEAD","POST"])
def signup(request):
    if request.user.is_authenticated:
        return redirect("explore:journal")
    form = SignupForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        try:
            user = form.save()
        except IntegrityError:
            form.add_error("identifier", "Энэ имэйл эсвэл утасны дугаараар бүртгэл үүссэн байна. Нэвтэрнэ үү.")
        else:
            auth_login(request, user)
            messages.success(request, "Бүртгэл амжилттай үүслээ. Тавтай морил!")
            return redirect(safe_next(request) or "explore:journal")
    return page(request, "signup", "signup", form=form, next=safe_next(request))

@require_http_methods(["GET","HEAD","POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("explore:journal")
    form = LoginForm(request.POST if request.method == "POST" else None, request=request)
    if request.method == "POST" and form.is_valid():
        auth_login(request, form.user)
        return redirect(safe_next(request) or "explore:journal")
    return page(request, "login", "login", form=form, next=safe_next(request))

@require_POST
def logout_view(request):
    auth_logout(request)
    return redirect("explore:home")

@login_required
@require_http_methods(["GET","HEAD","POST"])
def mood(request,pk=None):
    entry = get_object_or_404(own_entries(request),pk=pk) if pk else None
    today=localdate()
    initial = {"mood":entry.mood,"tags":entry.tags,"note":entry.note,"day":entry.day} if entry else {
        "day":today, "mood":request.GET.get("mood") if request.GET.get("mood") in {"1","2","3","4","5"} else None}
    form=EntryForm(request.POST if request.method=="POST" else None,initial=initial)
    if request.method=="POST" and form.is_valid():
        if entry:
            for field,value in form.cleaned_data.items():
                setattr(entry,field,value)
            entry.save()
        else:
            Entry.objects.create(user=request.user,**form.cleaned_data)
        messages.success(request,"Тэмдэглэл хадгалагдлаа.")
        return redirect("explore:journal")
    return page(request,"mood","journal" if entry else "mood",form=form,entry=entry,today=today,
                moods=MOOD_ART,tags=TAGS,chosen=str(form["mood"].value() or ""),checked=form["tags"].value() or [])

@login_required
@require_safe
def journal(request):
    all_entries=own_entries(request)
    start,end=request.GET.get("start",""),request.GET.get("end","")
    entries=all_entries
    error=""
    try:
        since=date.fromisoformat(start) if start else None
        until=date.fromisoformat(end) if end else None
        if since and until and since>until:
            raise ValueError
        if since: entries=entries.filter(day__gte=since)
        if until: entries=entries.filter(day__lte=until)
    except ValueError:
        error="Эхлэх огноо дуусах огнооноос хойш байж болохгүй. Огноогоо шалгаарай."
    monday=localdate()-timedelta(days=localdate().weekday())
    mood_by_day={}
    for entry in all_entries.filter(day__range=(monday,monday+timedelta(days=6))):
        mood_by_day.setdefault(entry.day,entry.mood)
    labels={v:label for v,label,_ in MOODS}
    icons={v:icon for v,_,icon in MOODS}
    week=[]
    for i, label in enumerate(("Да","Мя","Лх","Пү","Ба","Бя","Ня")):
        day=monday+timedelta(days=i)
        value=mood_by_day.get(day)
        week.append({"label":label,"day":day,"icon":icons.get(value,"·"),"mood":labels.get(value,"Тэмдэглэлгүй")})
    summary=None
    if entries:
        counts=Counter(e.mood for e in entries)
        top_value,top_count=counts.most_common(1)[0]
        summary={"total":len(entries),"top":labels[top_value],"top_count":top_count,
                 "average":round(sum(e.mood for e in entries)/len(entries),1)}
    return page(request,"journal","journal",entries=entries,start=start,end=end,week=week,error=error,summary=summary)

@login_required
@require_http_methods(["GET","HEAD","POST"])
def delete(request,pk):
    entry=get_object_or_404(own_entries(request),pk=pk)
    if request.method=="POST":
        entry.delete()
        messages.success(request,"Тэмдэглэл устгагдлаа.")
        return redirect("explore:journal")
    return page(request,"delete","journal",entry=entry)

@require_safe
def about(request):
    return page(request,"about","about")
