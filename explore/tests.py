from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.utils.timezone import localdate
from .data import QUESTIONS, TYPES
from .models import Entry

class InnerMeFlows(TestCase):
    def test_public_pages_and_type_search(self):
        for url in ("/","/test/","/types/","/zodiac/","/about/","/login/","/signup/"):
            self.assertEqual(self.client.get(url).status_code, 200, url)
        for code in TYPES:
            self.assertContains(self.client.get(f"/types/{code}/"),TYPES[code]["name"])
        self.assertEqual(self.client.get("/types/NOPE/").status_code,404)
        found=self.client.get("/types/",{"q":"infp"})
        self.assertContains(found,"Эргэцүүлэгч")
        self.assertNotContains(found,"Тууштай бүтээгч")

    def test_quiz_back_result_and_reset(self):
        self.assertRedirects(self.client.get("/test/result/"),"/test/")
        self.assertContains(self.client.post("/test/",{"step":1,"action":"next"}),"хариултаа сонгоорой")
        self.client.post("/test/",{"step":1,"action":"next","answer":4})
        self.client.post("/test/",{"step":2,"action":"back"})
        self.assertEqual(self.client.get("/test/").context["selected"],4)
        for step,(_,direction,_) in enumerate(QUESTIONS,1):
            r=self.client.post("/test/",{"step":step,"action":"next","answer":7 if direction==1 else 1})
        self.assertRedirects(r,"/test/result/")
        result=self.client.get("/test/result/")
        self.assertEqual(result.context["profile"]["code"],"ENTJ")
        self.assertTrue(all(bar["percent"]==100 for bar in result.context["bars"]))
        self.client.post("/test/",{"action":"reset"})
        self.assertRedirects(self.client.get("/test/result/"),"/test/")

    def test_zodiac_boundaries_and_invalid_date(self):
        for month,day,sign in ((1,19,"Матар"),(1,20,"Хумх"),(2,29,"Загас"),
                               (3,20,"Загас"),(3,21,"Хонь"),(12,21,"Нум"),(12,22,"Матар")):
            r=self.client.get("/zodiac/",{"month":month,"day":day})
            self.assertEqual(r.context["sign"][0],sign)
        self.assertContains(self.client.get("/zodiac/",{"month":4,"day":31}),"Бодит сар")

    def signup(self, client, identifier="99112233", password="Tegshbayar-77"):
        return client.post("/signup/",{"identifier":identifier,"password1":password,"password2":password})

    def test_journal_requires_login(self):
        for url in ("/mood/","/journal/"):
            self.assertRedirects(self.client.get(url),f"/login/?next={url}")

    def test_signup_login_logout_with_phone_and_email(self):
        self.assertRedirects(self.signup(self.client,"99 11-22-33"),"/journal/")
        user=get_user_model().objects.get()
        self.assertEqual(user.username,"+97699112233")
        self.assertEqual(user.email,"")
        self.client.post("/logout/")
        self.assertRedirects(self.client.get("/journal/"),"/login/?next=/journal/")
        r=self.client.post("/login/",{"identifier":"+976 9911 2233","password":"Tegshbayar-77"})
        self.assertRedirects(r,"/journal/")
        self.client.post("/logout/")
        self.assertRedirects(self.signup(self.client,"Ana@Example.COM"),"/journal/")
        self.assertEqual(get_user_model().objects.get(username="ana@example.com").email,"ana@example.com")

    def test_signup_and_login_errors(self):
        self.signup(self.client)
        self.client.post("/logout/")
        self.assertContains(self.signup(self.client,"+97699112233"),"бүртгэл үүссэн")
        self.assertContains(self.signup(self.client,"hello"),"зөв оруулна уу")
        weak=self.client.post("/signup/",{"identifier":"88112233","password1":"12345678","password2":"12345678"})
        self.assertEqual(get_user_model().objects.count(),1)
        self.assertEqual(weak.status_code,200)
        mismatch=self.client.post("/signup/",{"identifier":"88112233","password1":"Tegshbayar-77","password2":"x"})
        self.assertContains(mismatch,"таарахгүй")
        bad=self.client.post("/login/",{"identifier":"99112233","password":"wrong"})
        self.assertContains(bad,"буруу байна")

    def test_login_next_rejects_external_url(self):
        self.signup(Client(),"99112233")
        r=self.client.post("/login/",{"identifier":"99112233","password":"Tegshbayar-77","next":"https://evil.example/"})
        self.assertRedirects(r,"/journal/")

    def test_journal_crud_filter_and_account_isolation(self):
        self.signup(self.client)
        today=localdate()
        data={"mood":4,"day":today.isoformat(),"note":"Туршилтын бичвэр","tags":["Хичээл"]}
        self.assertRedirects(self.client.post("/mood/",data),"/journal/")
        entry=Entry.objects.get()
        self.assertEqual(entry.tags,["Хичээл"])
        self.assertEqual(entry.user.username,"+97699112233")
        self.assertContains(self.client.get("/journal/"),"Туршилтын бичвэр")
        self.assertNotContains(self.client.get("/journal/",{"end":(today-timedelta(days=1)).isoformat()}),"Туршилтын бичвэр")
        stranger=Client()
        self.signup(stranger,"stranger@example.com")
        self.assertNotContains(stranger.get("/journal/"),"Туршилтын бичвэр")
        self.assertEqual(stranger.post(f"/journal/{entry.pk}/edit/",data).status_code,404)
        self.assertEqual(stranger.post(f"/journal/{entry.pk}/delete/").status_code,404)
        data["note"]="Зассан бичвэр"
        self.assertRedirects(self.client.post(f"/journal/{entry.pk}/edit/",data),"/journal/")
        self.assertContains(self.client.get("/journal/"),"Зассан бичвэр")
        self.assertEqual(self.client.get(f"/journal/{entry.pk}/delete/").status_code,200)
        self.assertEqual(Entry.objects.count(),1)
        self.assertRedirects(self.client.post(f"/journal/{entry.pk}/delete/"),"/journal/")
        self.assertFalse(Entry.objects.exists())

    def test_entries_survive_new_login_session(self):
        self.signup(self.client)
        self.client.post("/mood/",{"mood":5,"day":localdate().isoformat(),"note":"Үлдэх бичвэр"})
        other_device=Client()
        other_device.post("/login/",{"identifier":"99112233","password":"Tegshbayar-77"})
        self.assertContains(other_device.get("/journal/"),"Үлдэх бичвэр")

    def test_invalid_entry_and_csrf(self):
        self.signup(self.client)
        future=localdate()+timedelta(days=1)
        self.assertContains(self.client.post("/mood/",{"mood":5,"day":future}),"Ирээдүйн огноо")
        self.assertFalse(Entry.objects.exists())
        self.assertEqual(Client(enforce_csrf_checks=True).post("/login/",{"identifier":"x"}).status_code,403)

    def test_zodiac_detail_pages_and_card_links(self):
        r=self.client.get("/zodiac/",{"month":5,"day":15})
        self.assertEqual(r.context["sign"][0],"Үхэр")
        self.assertContains(r,"Захирагч гараг")
        for index in range(12):
            r=self.client.get("/zodiac/",{"sign":index})
            self.assertEqual(r.status_code,200)
            self.assertContains(r,"Элементийн зохицол")
        self.assertIsNone(self.client.get("/zodiac/",{"sign":99}).context["sign"])

    def test_result_has_detailed_sections_for_every_type(self):
        for code in TYPES:
            page=self.client.get(f"/types/{code}/")
            self.assertContains(page,"Суралцах ба ажиллах хэв маяг")

