# InnerMe

Web & AI хичээлийн бие даалт №1. Зан төлөвийн 20 асуулттай тест, 16 төрлийн лавлах, 20 орд болон мэдрэмжийн тэмдэглэл бүхий монгол хэлтэй Django веб.

## Windows PowerShell дээр асаах

ZIP-ийг задлаад `manage.py` байгаа **innerme** хавтсыг VS Code-оор нээнэ. Terminal дээр:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver 8001
```

Браузераар **http://127.0.0.1:8001/** хаягт орно. Серверийг Ctrl+C дарж зогсооно. 8001 ашиглагдаж байвал өөр сул порт сонгоно.

## Шалгах

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test
```

1. Нүүрээс тест рүү ороод 12 асуултад хариул. Өмнөх асуултын сонголт хэвээр үлдэхийг, үр дүнгээс төрлийн дэлгэрэнгүй рүү орж болохыг шалга.
2. Зан төлөв дээр `INFP` гэж хай. Зурхай дээр 3 сарын 20, 21-нийг сонгоод өөр орд гарахыг шалга.
3. Мэдрэмж дээр жишээ тэмдэглэл хадгал. Тэмдэглэлээ жагсаалтаас харах, огноогоор шүүх, засах, устгах боломжтой.
4. Браузерын responsive горимоор 390 px өргөн сонгон цэс нээж, картууд шинэ мөрөнд шилжихийг үз.

## Кодын зураглал

| Файл | Үүрэг |
|---|---|
| `config/settings.py` | Django тохиргоо, SQLite, static, session |
| `explore/urls.py` | Хуудас ба үйлдлийн URL |
| `explore/views.py` | Тест, хайлт, орд, тэмдэглэл боловсруулах |
| `explore/data.py` | Асуулт, онооны алгоритм, 16 төрөл, 12 ордын агуулга |
| `explore/forms.py` | Тэмдэглэлийн өгөгдлийг сервер дээр шалгах |
| `explore/models.py` | Тэмдэглэлийн өгөгдлийн бүтэц |
| `explore/templates/explore/` | Хуудасны HTML, дахин ашиглах цэс, карт |
| `explore/static/explore/` | Flexbox, Grid, media query, гар утасны цэс, Figma дүрслэл |
| `explore/tests.py` | Таван урсгалын автомат шалгалт |

Тэмдэглэл SQLite-д хадгалагдаж, тухайн браузерын Django session-д холбогдоно. Өөр браузер эсвэл cookie устгасан үед өмнөх тэмдэглэл харагдахгүй. ZIP-д жишээ өгөгдлийн сан, хэрэглэгчийн тэмдэглэл, виртуал орчин ороогүй. Тест нь албан ёсны MBTI үнэлгээ биш; зурхай нь сонирхлын агуулга.

Figma: https://www.figma.com/design/XPjdNJJQchgAD4ShguIrV6/Untitled?node-id=0-1
