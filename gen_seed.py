#!/usr/bin/env python3
"""Sinh dữ liệu mẫu cho CSDL thư viện -> seed.sql

Mô phỏng 1 năm hoạt động (17/11/2025 -> 16/11/2026) theo thứ tự thời gian, tuân thủ luật nghiệp vụ:
  - Sinh viên mượn song song tối đa 5 cuốn
  - Phạt chưa trả > 100.000đ thì không được mượn
  - Chỉ đặt trước bản đang SanSang; bản được đặt trước chuyển DangCho
Vì seed.sql nạp TRƯỚC triggers.sql nên script tự điền các giá trị mà trigger sẽ sinh
(Hard_books.status, Fines, Reservations.status) theo đúng công thức của trigger.

Chạy:  python3 gen_seed.py   (kết quả cố định vì random.seed cố định)
"""
import random, heapq, itertools, unicodedata, datetime as dt
from collections import defaultdict

random.seed(20261116)
NOW = dt.datetime(2026, 11, 16, 18, 0, 0)
START = dt.datetime(2025, 11, 17, 0, 0, 0)
FINE_PER_DAY, FINE_DAMAGED, FINE_LOST = 5000, 50000, 200000

# ----------------------------------------------------------------- chi nhánh
BRANCHES = [
    ("Chi nhánh Cầu Giấy", "144 Xuân Thủy, Cầu Giấy, Hà Nội"),
    ("Chi nhánh Đống Đa", "1 Tây Sơn, Đống Đa, Hà Nội"),
    ("Chi nhánh Hai Bà Trưng", "17 Tạ Quang Bửu, Hai Bà Trưng, Hà Nội"),
    ("Chi nhánh Thanh Xuân", "334 Nguyễn Trãi, Thanh Xuân, Hà Nội"),
    ("Chi nhánh Quận 5", "227 Nguyễn Văn Cừ, Quận 5, TP. Hồ Chí Minh"),
    ("Chi nhánh Thủ Đức", "Khu phố 6, Linh Trung, Thủ Đức, TP. Hồ Chí Minh"),
    ("Chi nhánh Bình Thạnh", "475A Điện Biên Phủ, Bình Thạnh, TP. Hồ Chí Minh"),
    ("Chi nhánh Tân Bình", "12 Cộng Hòa, Tân Bình, TP. Hồ Chí Minh"),
    ("Chi nhánh Đà Nẵng", "54 Nguyễn Lương Bằng, Liên Chiểu, Đà Nẵng"),
    ("Chi nhánh Cần Thơ", "Khu II, đường 3/2, Ninh Kiều, Cần Thơ"),
]

# ----------------------------------------------------------------- tài liệu
# genre -> (là sách kỹ thuật?, danh sách 10 chủ đề)
GENRES = {
    "Trí tuệ nhân tạo": (True, ["Học máy cơ bản", "Học sâu và mạng nơ-ron", "Xử lý ngôn ngữ tự nhiên",
        "Thị giác máy tính", "Học tăng cường", "Trí tuệ nhân tạo tạo sinh", "Khai phá dữ liệu",
        "Đạo đức và quản trị AI", "Biểu diễn tri thức và hệ chuyên gia", "Robot tự hành và AI"]),
    "Cơ sở dữ liệu": (True, ["Nhập môn cơ sở dữ liệu", "Thiết kế CSDL quan hệ", "SQL từ cơ bản đến nâng cao",
        "Chuẩn hóa dữ liệu và dạng chuẩn 3NF", "Quản trị MySQL", "Cơ sở dữ liệu NoSQL", "Kho dữ liệu và OLAP",
        "Giao dịch và điều khiển đồng thời", "Tối ưu hóa truy vấn", "Đại số quan hệ"]),
    "Mạng máy tính": (True, ["Nhập môn mạng máy tính", "TCP/IP chi tiết", "Định tuyến và chuyển mạch",
        "Bảo mật mạng", "Mạng không dây", "Lập trình socket", "Điện toán đám mây", "Quản trị hệ thống Linux",
        "An toàn thông tin", "Mạng cảm biến và IoT"]),
    "Lập trình": (True, ["Lập trình Python cơ bản", "Lập trình C++ nâng cao", "Java hướng đối tượng",
        "Phát triển web với JavaScript", "Lập trình hướng đối tượng", "Kiểm thử phần mềm",
        "Phát triển ứng dụng di động", "Lập trình hàm", "Kiến trúc phần mềm", "Làm việc nhóm với Git"]),
    "Thuật toán": (True, ["Cấu trúc dữ liệu và giải thuật", "Quy hoạch động", "Lý thuyết đồ thị",
        "Thuật toán sắp xếp và tìm kiếm", "Độ phức tạp tính toán", "Thuật toán tham lam",
        "Thuật toán xử lý chuỗi", "Hình học tính toán", "Thuật toán song song", "Lập trình thi đấu"]),
    "Toán học": (True, ["Giải tích 1", "Giải tích 2", "Đại số tuyến tính", "Xác suất thống kê", "Toán rời rạc",
        "Phương trình vi phân", "Giải tích số", "Lý thuyết số", "Tối ưu hóa", "Logic toán"]),
    "Vật lý": (True, ["Cơ học đại cương", "Điện từ học", "Nhiệt động lực học", "Quang học",
        "Vật lý lượng tử nhập môn", "Vật lý chất rắn", "Vật lý hạt nhân", "Thiên văn học đại cương",
        "Vật lý thống kê", "Sóng và dao động"]),
    "Hóa học": (True, ["Hóa đại cương", "Hóa hữu cơ", "Hóa phân tích", "Hóa lý", "Hóa vô cơ", "Hóa sinh",
        "Hóa học môi trường", "Hóa học polymer", "Điện hóa học", "Hóa học vật liệu"]),
    "Kinh tế": (True, ["Kinh tế vi mô", "Kinh tế vĩ mô", "Nguyên lý kế toán", "Quản trị marketing",
        "Tài chính doanh nghiệp", "Kinh tế lượng", "Quản trị nhân sự", "Thương mại điện tử", "Khởi nghiệp",
        "Kinh tế quốc tế"]),
    "Kỹ thuật điện tử": (True, ["Mạch điện", "Điện tử số", "Điện tử tương tự", "Vi xử lý và vi điều khiển",
        "Xử lý tín hiệu số", "Kỹ thuật điều khiển tự động", "Máy điện", "Hệ thống nhúng", "Truyền thông số",
        "Năng lượng tái tạo"]),
    "Văn học": (False, ["Tuyển tập truyện ngắn Việt Nam", "Thơ Việt Nam hiện đại", "Lý luận văn học",
        "Văn học dân gian", "Văn học thế giới thế kỷ 20", "Tiểu thuyết Việt Nam đương đại", "Phê bình văn học",
        "Kịch nói Việt Nam", "Hồi ký và tùy bút", "Văn học thiếu nhi"]),
    "Lịch sử": (False, ["Lịch sử Việt Nam cổ trung đại", "Lịch sử Việt Nam cận đại", "Lịch sử thế giới cổ đại",
        "Lịch sử thế giới hiện đại", "Lịch sử Đông Nam Á", "Lịch sử khoa học kỹ thuật",
        "Lịch sử văn minh phương Đông", "Khảo cổ học đại cương", "Lịch sử tư tưởng", "Lịch sử quân sự"]),
    "Tâm lý học": (False, ["Tâm lý học đại cương", "Tâm lý học phát triển", "Tâm lý học xã hội",
        "Tâm lý học giáo dục", "Tâm lý học nhận thức", "Tâm lý học tổ chức", "Phương pháp nghiên cứu tâm lý",
        "Tâm lý học lâm sàng", "Tâm lý học tiêu dùng", "Kỹ năng giao tiếp"]),
    "Ngoại ngữ": (False, ["Giáo trình tiếng Anh học thuật", "Ngữ pháp tiếng Anh nâng cao", "Luyện thi IELTS",
        "Từ vựng tiếng Anh chuyên ngành CNTT", "Tiếng Nhật sơ cấp", "Tiếng Hàn sơ cấp", "Tiếng Trung giao tiếp",
        "Tiếng Pháp cơ bản", "Kỹ năng viết tiếng Anh", "Dịch thuật cơ bản"]),
    "Y học": (False, ["Giải phẫu học", "Sinh lý học", "Vi sinh y học", "Dược lý học", "Dinh dưỡng và sức khỏe",
        "Y học cộng đồng", "Điều dưỡng cơ bản", "Miễn dịch học", "Bệnh học đại cương", "Sơ cấp cứu"]),
    "Triết học và Xã hội": (False, ["Triết học Mác–Lênin", "Kinh tế chính trị", "Chủ nghĩa xã hội khoa học",
        "Tư tưởng Hồ Chí Minh", "Logic học", "Xã hội học đại cương", "Pháp luật đại cương", "Đạo đức học",
        "Nhân học văn hóa", "Phương pháp nghiên cứu khoa học"]),
}
AI_YEARS = [2024, 2023, 2025, 2022, 2023, 2021, 2022, 2019, 2025, 2020]   # >= 2022: 7 cuốn

LAST = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Vũ", "Đặng", "Bùi", "Đỗ", "Ngô", "Dương", "Lý", "Phan", "Võ"]
MID_M = ["Văn", "Minh", "Quốc", "Hữu", "Đức", "Thanh", "Xuân", "Gia"]
MID_F = ["Thị", "Ngọc", "Thu", "Hồng", "Diệu", "Bích"]
FIRST_M = ["An", "Bình", "Cường", "Dũng", "Hải", "Hiếu", "Hùng", "Khoa", "Long", "Nam", "Phong", "Phúc",
           "Quân", "Sơn", "Tâm", "Thắng", "Tuấn", "Vinh", "Đạt", "Kiên", "Lâm", "Nghĩa"]
FIRST_F = ["Hà", "Hạnh", "Hoa", "Lan", "Linh", "Mai", "Thảo", "Trang", "Yến", "Ngọc", "Phương", "Châu", "Vy",
           "Chi", "Nhung", "Oanh", "Quỳnh", "Thủy"]


def unaccent(s):
    s = s.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


used_names = set()


def make_name(female=None):
    while True:
        f = random.random() < 0.5 if female is None else female
        n = f"{random.choice(LAST)} {random.choice(MID_F if f else MID_M)} {random.choice(FIRST_F if f else FIRST_M)}"
        if n not in used_names:
            used_names.add(n)
            return n


AUTHORS = [make_name() for _ in range(36)]

sources = []          # dict: id, title, author, genre, year, pages
raw = []
for gi, (genre, (tech, topics)) in enumerate(GENRES.items()):
    authors = [AUTHORS[(gi * 2 + k) % 36] for k in range(3)]
    wts = [0.55, 0.30, 0.15]
    for ti, topic in enumerate(topics):
        year = AI_YEARS[ti] if gi == 0 else random.randint(2005, 2025)
        raw.append(dict(title=topic, author=random.choices(authors, wts)[0], genre=genre,
                        year=year, pages=random.randint(180, 760)))
        if tech and ti < 4:
            raw.append(dict(title="Bài tập và lời giải: " + topic, author=random.choices(authors, wts)[0],
                            genre=genre, year=min(2025, year + random.randint(0, 2)),
                            pages=random.randint(160, 380)))
random.shuffle(raw)
for i, r in enumerate(raw, 1):
    r["id"] = i
    r["pop"] = random.lognormvariate(0, 1.0)       # độ "hot" của tài liệu
    base_price = (r["pages"] * 350 // 10000) * 10000
    r["price"] = float(max(60000, min(300000, base_price)))
    sources.append(r)
by_title = {s["title"]: s for s in sources}
source_by_id = {s["id"]: s for s in sources}

# ----------------------------------------------------------------- bản cứng
hard_books = []        # dict: id, source_id, branch_id, state, hold
copies_of = defaultdict(list)
for s in sources:
    n = random.choices([1, 2, 3, 4], [3, 4, 3, 2])[0] + (1 if s["pop"] > 2 else 0)
    for b in random.sample(range(1, len(BRANCHES) + 1), n):
        c = dict(id=len(hard_books) + 1, source_id=s["id"], branch_id=b, state="SanSang", hold=None)
        hard_books.append(c)
        copies_of[s["id"]].append(c)

# ----------------------------------------------------------------- bản mềm
ebooks = []
ebook_of = {}
for s in sources:
    if random.random() < 0.68:
        e = dict(id=len(ebooks) + 1, source_id=s["id"], size=random.randint(2, 85), pop=s["pop"])
        ebooks.append(e)
        ebook_of[s["id"]] = e

# ----------------------------------------------------------------- độc giả
readers = []
used_email, used_cccd = set(), set()


def add_reader(rtype, dob_lo, dob_hi):
    female = random.random() < 0.5
    name = make_name(female)
    parts = unaccent(name).lower().split()
    dom = {"Sinh vien": "sv", "Giang vien": "gv", "Nghien cuu sinh": "ncs"}[rtype]
    while True:
        email = f"{parts[-1]}.{parts[0]}{random.randint(10, 99)}@{dom}.example.edu.vn"
        if email not in used_email:
            used_email.add(email)
            break
    cccd = None
    if random.random() > 0.04:
        while True:
            cccd = "0" + "".join(random.choice("0123456789") for _ in range(11))
            if cccd not in used_cccd:
                used_cccd.add(cccd)
                break
    span = (dob_hi - dob_lo).days
    dob = dob_lo + dt.timedelta(days=random.randint(0, span))
    readers.append(dict(id=len(readers) + 1, name=name, dob=dob, email=email, cccd=cccd, type=rtype,
                        w=random.lognormvariate(0, 0.9)))


for _ in range(68):
    add_reader("Sinh vien", dt.date(2002, 1, 1), dt.date(2007, 12, 31))
for _ in range(20):
    add_reader("Giang vien", dt.date(1965, 1, 1), dt.date(1990, 12, 31))
for _ in range(12):
    add_reader("Nghien cuu sinh", dt.date(1993, 1, 1), dt.date(2001, 12, 31))
readers[0]["dob"] = dt.date(2010, 3, 10)          # sinh viên trẻ nhất, vừa đủ 16 tuổi
random.shuffle(readers)
for i, r in enumerate(readers, 1):
    r["id"] = i
sv = [r for r in readers if r["type"] == "Sinh vien"]

# ----------------------------------------------------------------- môn học & giáo trình
COURSES = {
    "Cơ sở dữ liệu": (["Nhập môn cơ sở dữ liệu", "Thiết kế CSDL quan hệ", "SQL từ cơ bản đến nâng cao",
                       "Chuẩn hóa dữ liệu và dạng chuẩn 3NF", "Đại số quan hệ"],
                      ["Cơ sở dữ liệu NoSQL", "Quản trị MySQL"]),
    "Mạng máy tính": (["Nhập môn mạng máy tính", "TCP/IP chi tiết", "Định tuyến và chuyển mạch"], ["Bảo mật mạng"]),
    "Trí tuệ nhân tạo": (["Học máy cơ bản", "Học sâu và mạng nơ-ron", "Xử lý ngôn ngữ tự nhiên"],
                         ["Đạo đức và quản trị AI"]),
    "Cấu trúc dữ liệu và giải thuật": (["Cấu trúc dữ liệu và giải thuật", "Quy hoạch động", "Lý thuyết đồ thị"],
                                       ["Thuật toán sắp xếp và tìm kiếm"]),
    "Lập trình Python": (["Lập trình Python cơ bản", "Lập trình hướng đối tượng"], []),
    "Xác suất thống kê": (["Xác suất thống kê", "Đại số tuyến tính"], ["Toán rời rạc"]),
}
REQ_CSDL = [by_title[t]["id"] for t in COURSES["Cơ sở dữ liệu"][0]]

# ----------------------------------------------------------------- mô phỏng
loans, reservations, fines, renewals, returns = [], [], [], [], []
active = defaultdict(int)
reader_fines = defaultdict(list)
seq = itertools.count()
heap = []


def push(t, kind, data=None):
    heapq.heappush(heap, (t, next(seq), kind, data))


debtors = set(r["id"] for r in random.sample(readers, 8))
forced_lost = list(debtors)[:3]            # 3 người làm mất sách và không nộp phạt -> bị chặn mượn


def unpaid(rid, t):
    return sum(f["amount"] for f in reader_fines[rid]
               if f["created"] <= t and (f["paid"] is None or f["paid"] > t))


def rand_time(day):
    return dt.datetime.combine(day, dt.time()) + dt.timedelta(seconds=random.randint(8 * 3600, 20 * 3600))


def can_borrow(rd, t):
    limit = 5 if rd["type"] == "Sinh vien" else 8
    return active[rd["id"]] < limit and unpaid(rd["id"], t) <= 100000


def try_loan(rd, copy, t, force_cond=None):
    if not can_borrow(rd, t):
        return None
    P = 14 if rd["type"] == "Sinh vien" else 30
    due = (t + dt.timedelta(days=P)).replace(hour=23, minute=59, second=0, microsecond=0)
    k = 0
    # chỉ gia hạn nếu đã đủ thời gian để việc gia hạn xảy ra trước NOW
    if force_cond is None and t + dt.timedelta(days=P * 0.6) <= NOW:
        k = random.choices([0, 1, 2], [0.91, 0.07, 0.02])[0]
    final_due = due + dt.timedelta(days=7 * k)
    # kết quả trả sách: 86% đúng hạn, 13% trễ 1-25 ngày, 1% không bao giờ trả
    rnd = random.random()
    ret, cond = None, "Tot"
    if force_cond:
        ret, cond = t + dt.timedelta(days=random.uniform(3, P - 1)), force_cond
    elif rnd < 0.86:
        lo = P * 0.95 if k else 1
        ret = t + dt.timedelta(days=random.uniform(lo, P + 7 * k - 0.2))
    elif rnd < 0.99:
        ret = final_due + dt.timedelta(days=random.uniform(0.6, 25))
    if ret is not None:
        ret = ret.replace(hour=random.randint(8, 20), minute=random.randint(0, 59), second=random.randint(0, 59))
        if ret < t + dt.timedelta(hours=1):
            ret += dt.timedelta(days=1)
        if not force_cond:
            cond = random.choices(["Tot", "Hong", "Mat"], [0.95, 0.035, 0.015])[0]
    loan = dict(reader=rd["id"], copy=copy["id"], borrowed=t, due=final_due, orig_due=due, k=k,
                ret=ret, cond=cond, rtype=rd["type"])
    loans.append(loan)
    copy["state"], copy["hold"] = "DangMuon", None
    active[rd["id"]] += 1
    if ret is not None and ret <= NOW:
        push(ret, "return", (loan, copy, rd))
    return loan


def pick_available(source_id):
    free = [c for c in copies_of[source_id] if c["state"] == "SanSang"]
    return random.choice(free) if free else None


def handle_demand(t):
    rd = random.choices(readers, [r["w"] for r in readers])[0]
    if not can_borrow(rd, t):
        return
    for _ in range(4):
        s = random.choices(sources, [x["pop"] for x in sources])[0]
        c = pick_available(s["id"])
        if c:
            try_loan(rd, c, t)
            return


def handle_return(loan, copy, rd, t):
    copy["state"] = "SanSang"
    active[rd["id"]] -= 1
    ret = dict(loan=loan, returned=t, cond=loan["cond"])
    returns.append(ret)
    late = (t.date() - loan["due"].date()).days
    source_price = source_by_id[copy["source_id"]]["price"]

    fine_item = None
    # B. Sách bị mất (Lost): phạt 100% giá bìa, không tính phí quá hạn
    if loan["cond"] == "Mat":
        fine_item = ("Lost", "Mat sach", source_price, 0.0, None, None)
    # C. Sách bị hỏng (Damaged): Không tự động phạt; nhân viên kiểm tra và tự quyết định mức phạt
    # Mô phỏng: ~70% trường hợp nhân viên đã đánh giá và xác nhận khoản phạt
    elif loan["cond"] == "Hong":
        if random.random() < 0.70:
            assessed_staff = random.choice(["NV_ThuThu_01", "NV_ThuThu_02", "NV_ThuThu_03"])
            dmg_amount = float(max(30000, min(source_price, ((int(source_price * 0.4) // 5000) * 5000))))
            fine_item = ("Damaged", "Sach bi hu hai khi tra", dmg_amount, 0.0, dmg_amount, assessed_staff)
    # A. Sách bình thường (Tot) và quá hạn: fine = 10% * price * số ngày quá hạn
    elif late > 0:
        late_amount = round(0.10 * source_price * late, 2)
        fine_item = ("Late", f"Tra sach qua han {late} ngay", late_amount, late_amount, None, None)

    if fine_item:
        fine_type, reason, amount, late_amt, dmg_amt, assessed_by = fine_item
        paid = None
        if rd["id"] not in debtors and random.random() < 0.90:
            paid = t + dt.timedelta(days=random.uniform(0.1, 20))
            paid = paid if paid <= NOW else None
        f = dict(ret=ret, fine_type=fine_type, reason=reason, amount=amount,
                 late_amount=late_amt, damaged_amount=dmg_amt, assessed_by=assessed_by,
                 created=t, paid=paid)
        fines.append(f)
        reader_fines[rd["id"]].append(f)


def handle_reserve(t):
    rd = random.choice(readers)
    s = random.choices(sources, [x["pop"] for x in sources])[0]
    c = pick_available(s["id"])
    if not c:
        return
    deadline = t + dt.timedelta(days=3)
    res = dict(reader=rd["id"], copy=c["id"], at=t, deadline=deadline, status="ChoNhan")
    reservations.append(res)
    c["state"], c["hold"] = "DangCho", res
    r = random.random()
    if r < 0.55:
        when, outcome = t + dt.timedelta(hours=random.uniform(2, 70)), "DaNhan"
    elif r < 0.70:
        when, outcome = t + dt.timedelta(hours=random.uniform(2, 60)), "Huy"
    else:
        when, outcome = deadline, "HetHan"
    if when <= NOW:
        push(when, "res_resolve", (res, c, rd, outcome))


def handle_resolve(res, c, rd, outcome, t):
    if outcome == "DaNhan":
        c["state"] = "SanSang"
        if try_loan(rd, c, t):
            res["status"] = "DaNhan"
            return
        outcome = "Huy"           # không đủ điều kiện mượn (nợ phạt / quá 5 cuốn) -> bỏ đặt trước
    res["status"] = outcome
    c["state"], c["hold"] = "SanSang", None


def handle_forced(rd, source_id, t, cond, tries):
    c = pick_available(source_id)
    if c and try_loan(rd, c, t, force_cond=cond):
        return
    if tries > 0 and t + dt.timedelta(days=1) < NOW:
        push(t + dt.timedelta(days=1), "forced", (rd, source_id, cond, tries - 1))


# --- nhu cầu mượn hằng ngày
day = START.date()
while day <= NOW.date():
    wd = day.weekday()
    mean = 10 if wd < 5 else (5 if wd == 5 else 1.5)
    mean *= 0.6 if day.month in (6, 7, 8) else (0.7 if day.month in (1, 2) else 1.0)
    for _ in range(max(0, int(round(random.gauss(mean, 2.5))))):
        t = rand_time(day)
        if t <= NOW:
            push(t, "demand")
    if random.random() < 0.38 and wd < 6:
        t = rand_time(day)
        if t <= NOW:
            push(t, "reserve")
    day += dt.timedelta(days=1)

# --- mượn cưỡng bức để dữ liệu đủ cho Query 7 (phép chia) và có người nợ phạt
pool = [r for r in sv if r["id"] not in debtors]
random.shuffle(pool)
complete, partial = pool[:5], pool[5:13]
span_days = (NOW - START).days - 30
for rd in complete:
    for sid in REQ_CSDL:
        push(START + dt.timedelta(days=random.randint(5, span_days), hours=random.randint(8, 20)), "forced",
             (rd, sid, None, 25))
for rd in partial:
    for sid in random.sample(REQ_CSDL, random.choice([3, 4])):
        push(START + dt.timedelta(days=random.randint(5, span_days), hours=random.randint(8, 20)), "forced",
             (rd, sid, None, 25))
by_id = {r["id"]: r for r in readers}
for rid in forced_lost:
    sid = random.choice(sources)["id"]
    push(START + dt.timedelta(days=random.randint(40, 230), hours=random.randint(8, 20)), "forced",
         (by_id[rid], sid, "Mat", 25))

while heap:
    t, _, kind, data = heapq.heappop(heap)
    if t > NOW:
        break
    if kind == "demand":
        handle_demand(t)
    elif kind == "reserve":
        handle_reserve(t)
    elif kind == "return":
        handle_return(*data, t)
    elif kind == "res_resolve":
        handle_resolve(*data, t)
    elif kind == "forced":
        handle_forced(data[0], data[1], t, data[2], data[3])

# --- gia hạn: phải xảy ra TRƯỚC khi trả -> loại bỏ nếu mượn đã trả quá sớm (không xảy ra do lo = 0.55P)
loans.sort(key=lambda l: l["borrowed"])
for i, l in enumerate(loans, 1):
    l["id"] = i
    for j in range(l["k"]):
        renewals.append(dict(loan=l["id"], old=l["orig_due"] + dt.timedelta(days=7 * j),
                             new=l["orig_due"] + dt.timedelta(days=7 * (j + 1))))
returns.sort(key=lambda r: r["returned"])
for i, r in enumerate(returns, 1):
    r["id"] = i
    r["code"] = f"PT{i:06d}"
fines.sort(key=lambda f: (f["created"], f["reason"]))
for i, f in enumerate(fines, 1):
    f["id"] = i
reservations.sort(key=lambda r: r["at"])
for i, r in enumerate(reservations, 1):
    r["id"] = i

# --- trạng thái cuối của bản cứng (đúng như trigger sẽ để lại)
active_copy = {l["copy"] for l in loans if l["ret"] is None or l["ret"] > NOW}
for c in hard_books:
    if c["id"] in active_copy:
        c["state"] = "DangMuon"
    elif c["hold"] is not None and c["hold"]["status"] == "ChoNhan":
        c["state"] = "DangCho"
    else:
        c["state"] = "SanSang"

# --- lịch sử truy cập bản mềm
never_access = set(r["id"] for r in random.sample(readers, 12))
acc_readers = [r for r in readers if r["id"] not in never_access]
access = []
for _ in range(1500):
    rd = random.choices(acc_readers, [r["w"] for r in acc_readers])[0]
    e = random.choices(ebooks, [x["pop"] for x in ebooks])[0]
    s = START + dt.timedelta(seconds=random.randint(0, int((NOW - START).total_seconds()) - 4 * 3600))
    access.append(dict(reader=rd["id"], ebook=e["id"], start=s,
                       end=s + dt.timedelta(minutes=random.randint(3, 150))))
for _ in range(3):                       # 3 phiên đang mở lúc này
    rd = random.choice(acc_readers)
    e = random.choice(ebooks)
    access.append(dict(reader=rd["id"], ebook=e["id"], start=NOW - dt.timedelta(minutes=random.randint(15, 90)),
                       end=None))
access.sort(key=lambda a: a["start"])
for a in access:
    if a["end"] and a["end"] > NOW:
        a["end"] = None

# ----------------------------------------------------------------- xuất SQL


def q(v):
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, dt.datetime):
        return "'" + v.strftime("%Y-%m-%d %H:%M:%S") + "'"
    if isinstance(v, dt.date):
        return "'" + v.isoformat() + "'"
    return "'" + str(v).replace("\\", "\\\\").replace("'", "''") + "'"


out = ["-- Dữ liệu mẫu - sinh bởi gen_seed.py (nạp SAU schema.sql, TRƯỚC triggers.sql)",
       "SET NAMES utf8mb4;", "USE library;", "SET autocommit = 0;", ""]


def insert(table, cols, rows, batch=200):
    out.append(f"-- {table}: {len(rows)} dòng")
    for i in range(0, len(rows), batch):
        chunk = rows[i:i + batch]
        out.append(f"INSERT INTO {table} ({', '.join(cols)}) VALUES")
        out.append(",\n".join("  (" + ", ".join(q(v) for v in r) + ")" for r in chunk) + ";")
    out.append("")


insert("Branches", ["id", "name", "address"], [(i, n, a) for i, (n, a) in enumerate(BRANCHES, 1)])
insert("Sources", ["id", "title", "author", "genre", "publication_year", "page_count", "price"],
       [(s["id"], s["title"], s["author"], s["genre"], s["year"], s["pages"], s["price"]) for s in sources])
insert("Hard_books", ["id", "source_id", "branch_id", "status"],
       [(c["id"], c["source_id"], c["branch_id"], c["state"]) for c in hard_books])
insert("Ebooks", ["id", "source_id", "file_size_mb"], [(e["id"], e["source_id"], e["size"]) for e in ebooks])
insert("Readers", ["id", "full_name", "date_of_birth", "email", "national_id", "reader_type"],
       [(r["id"], r["name"], r["dob"], r["email"], r["cccd"], r["type"]) for r in readers])
insert("Courses", ["id", "name"], [(i, n) for i, n in enumerate(COURSES, 1)])
cr = []
for ci, (cname, (req, opt)) in enumerate(COURSES.items(), 1):
    cr += [(ci, by_title[t]["id"], True) for t in req] + [(ci, by_title[t]["id"], False) for t in opt]
insert("Course_resources", ["course_id", "source_id", "is_required"], cr)
insert("Access_logs", ["id", "reader_id", "ebook_id", "started_at", "ended_at"],
       [(i, a["reader"], a["ebook"], a["start"], a["end"]) for i, a in enumerate(access, 1)])
insert("Loans", ["id", "reader_id", "hard_book_id", "borrowed_at", "due_at"],
       [(l["id"], l["reader"], l["copy"], l["borrowed"], l["due"]) for l in loans])
insert("Renewals", ["id", "loan_id", "old_due_at", "new_due_at"],
       [(i, r["loan"], r["old"], r["new"]) for i, r in enumerate(renewals, 1)])
insert("Return_records", ["id", "loan_id", "return_code", "returned_at", "return_condition"],
       [(r["id"], r["loan"]["id"], r["code"], r["returned"], r["cond"]) for r in returns])
insert("Fines", ["id", "return_record_id", "fine_type", "amount", "reason", "created_at", "late_amount", "damaged_amount", "assessed_by", "paid_at"],
       [(f["id"], f["ret"]["id"], f["fine_type"], f["amount"], f["reason"], f["created"], f["late_amount"], f["damaged_amount"], f["assessed_by"], f["paid"]) for f in fines])
insert("Reservations", ["id", "reader_id", "hard_book_id", "reserved_at", "pickup_deadline", "status"],
       [(r["id"], r["reader"], r["copy"], r["at"], r["deadline"], r["status"]) for r in reservations])
out += ["COMMIT;", ""]

with open("seed.sql", "w", encoding="utf-8") as fh:
    fh.write("\n".join(out))

n_active = sum(1 for l in loans if l["ret"] is None or l["ret"] > NOW)
n_overdue = sum(1 for l in loans if (l["ret"] is None or l["ret"] > NOW) and l["due"] < NOW)
print(f"Branches={len(BRANCHES)} Sources={len(sources)} Hard_books={len(hard_books)} Ebooks={len(ebooks)} "
      f"Readers={len(readers)} Access_logs={len(access)}")
print(f"Loans={len(loans)} (đang mượn={n_active}, quá hạn={n_overdue}) Renewals={len(renewals)} "
      f"Returns={len(returns)} Fines={len(fines)} (chưa nộp={sum(1 for f in fines if f['paid'] is None)}) "
      f"Reservations={len(reservations)}")
