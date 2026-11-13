from datetime import date, timedelta
from uuid import uuid4
from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import localdate
from django.views.decorators.http import require_http_methods, require_safe
from .data import INFP_SECTIONS, MOODS, MOOD_ART, OPTIONS, QUESTIONS, SIGNS, TAGS, TYPES, score
from .forms import EntryForm
from .models import Entry

NAV = (("home","Нүүр"),("quiz","Тест"),("types","Зан төлөв"),
       ("zodiac","Зурхай"),("mood","Мэдрэмж"),("journal","Миний тэмдэглэл"))

def page(request, template, active, **context):
    return render(request, f"explore/{template}.html", {"active":active,"nav":NAV,**context})

@require_safe
def home(request):
    return page(request,"home","home",featured=[TYPES[c] for c in ("INFP","ENFP","INTJ","ISFJ")], moods=MOOD_ART)

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
    return page(request,"result","quiz",profile=TYPES[code],bars=bars)

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
    advice = {
      "E":"Санаагаа ярилцаад, дараа нь өөрийн бодлыг тусад нь тэмдэглээд үзээрэй.",
      "I":"Ганцаар бодох хугацаа гаргаад, санаагаа итгэлтэй хүнтэй хуваалцаарай.",
      "N":"Шинэ хувилбаруудаасаа нэгийг сонгож, бодит жижиг туршилт хийгээрэй.",
      "S":"Бодит жишээн дээр тулгуурлаад, өөр нэг боломжит хувилбар төсөөлөөд үзээрэй.",
      "T":"Шалгуураа тодорхой хэлэхийн зэрэгцээ сонголт бусдад яаж нөлөөлөхийг асуугаарай.",
      "F":"Хүмүүсийн хэрэгцээг анзаарахын зэрэгцээ шийдвэрийн шалгуураа бичээд үзээрэй.",
      "J":"Дараагийн алхмаа төлөвлөөд, өөрчлөлтөд багахан зай үлдээгээрэй.",
      "P":"Уян хатан байдлаа хадгалж, эхлэх нэг хугацаа товлоод үзээрэй.",
    }
    sections = INFP_SECTIONS if profile["code"] == "INFP" else [
        ("Ерөнхий хандлага", profile["name"], profile["summary"]),
        *[(title, title, advice[letter]) for title,letter in zip(
            ("Эрч хүчээ нөхөх","Мэдээллийг ойлгох","Шийдвэр гаргах","Ажлаа зохион байгуулах"),profile["code"])],
    ]
    return page(request,"detail","types",profile=profile,sections=sections,
                related=[t for t in TYPES.values() if t!=profile and sum(a!=b for a,b in zip(t["code"],profile["code"]))==1][:3])

@require_safe
def zodiac(request):
    month,day=request.GET.get("month",""),request.GET.get("day","")
    sign=error=None
    if "month" in request.GET or "day" in request.GET:
        try:
            birthday=date(2000,int(month),int(day))
        except (ValueError,OverflowError):
            error="Бодит сар, өдрийн хослол сонгоорой."
        else:
            # Month boundaries are inclusive for the sign that starts here.
            limits=(20,19,21,20,21,21,23,23,23,23,22,22)
            first=(9,10,11,0,1,2,3,4,5,6,7,8)
            index=first[birthday.month-1]
            sign=SIGNS[(index+int(birthday.day>=limits[birthday.month-1]))%12]
    return page(request,"zodiac","zodiac", signs=SIGNS, sign=sign,error=error,
                months=range(1,13),days=range(1,32),month=month,day=day)

def own_entries(request):
    return Entry.objects.filter(owner=request.session.get("journal_owner")) if request.session.get("journal_owner") else Entry.objects.none()

@require_http_methods(["GET","HEAD","POST"])
def mood(request,pk=None):
    entry = get_object_or_404(own_entries(request),pk=pk) if pk else None
    today=localdate()
    initial = {"mood":entry.mood,"tags":entry.tags,"note":entry.note,"day":entry.day} if entry else {
        "day":today, "mood":request.GET.get("mood") if request.GET.get("mood") in {"1","2","3","4","5"} else None}
    form=EntryForm(request.POST if request.method=="POST" else None,initial=initial)
    if request.method=="POST" and form.is_valid():
        owner=request.session.get("journal_owner")
        if not owner:
            owner=str(uuid4())
            request.session["journal_owner"]=owner
        if entry:
            for field,value in form.cleaned_data.items():
                setattr(entry,field,value)
            entry.save()
        else:
            Entry.objects.create(owner=owner,**form.cleaned_data)
        messages.success(request,"Тэмдэглэл хадгалагдлаа.")
        return redirect("explore:journal")
    return page(request,"mood","journal" if entry else "mood",form=form,entry=entry,today=today,
                moods=MOOD_ART,tags=TAGS,chosen=str(form["mood"].value() or ""),checked=form["tags"].value() or [])

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
    return page(request,"journal","journal",entries=entries,start=start,end=end,week=week,error=error)

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
