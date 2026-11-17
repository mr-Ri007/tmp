#!/usr/bin/env python3
"""Kiểm thử tự động logic tính tiền phạt theo 8 Test Cases bắt buộc.

Mô phỏng chính xác hoạt động của Schema, Triggers và Constraints trong MySQL:
  1. Sách trả đúng hạn → không có khoản phạt.
  2. Sách trả trước hạn → không có khoản phạt.
  3. Sách giá 200.000đ, quá hạn 3 ngày → phạt 60.000đ.
  4. Sách giá 200.000đ, bị mất → phạt 200.000đ.
  5. Sách giá 200.000đ, quá hạn 3 ngày rồi bị mất → chỉ phạt 200.000đ.
  6. Sách bị hỏng → chưa có khoản phạt tự động.
  7. Nhân viên xác nhận sách hỏng và nhập mức phạt 50.000đ → lưu khoản phạt 50.000đ.
  8. Một lần trả sách không được tạo khoản phạt trùng lặp.
"""
from decimal import Decimal
import datetime as dt

class MockDatabase:
    def __init__(self):
        self.sources = {}
        self.hard_books = {}
        self.readers = {}
        self.loans = {}
        self.return_records = {}
        self.fines = {}
        self.next_fine_id = 1

    def add_source(self, id, title, price):
        self.sources[id] = {"id": id, "title": title, "price": Decimal(str(price))}

    def add_reader(self, id, name):
        self.readers[id] = {"id": id, "name": name}

    def add_hard_book(self, id, source_id, status="SanSang"):
        self.hard_books[id] = {"id": id, "source_id": source_id, "status": status}

    def add_loan(self, id, reader_id, hard_book_id, borrowed_at, due_at):
        self.loans[id] = {
            "id": id,
            "reader_id": reader_id,
            "hard_book_id": hard_book_id,
            "borrowed_at": borrowed_at,
            "due_at": due_at
        }
        self.hard_books[hard_book_id]["status"] = "DangMuon"

    def insert_return_record(self, id, loan_id, return_code, returned_at, return_condition):
        # Trigger trg_returns_before
        loan = self.loans[loan_id]
        if returned_at < loan["borrowed_at"]:
            raise ValueError("Ngay tra phai >= ngay muon")

        record = {
            "id": id,
            "loan_id": loan_id,
            "return_code": return_code,
            "returned_at": returned_at,
            "return_condition": return_condition
        }
        self.return_records[id] = record

        # Trigger trg_returns_after
        self._trg_returns_after(record)

    def _trg_returns_after(self, new_record):
        loan = self.loans[new_record["loan_id"]]
        v_due = loan["due_at"]
        v_book = loan["hard_book_id"]
        source = self.sources[self.hard_books[v_book]["source_id"]]
        v_price = source["price"]

        # Bản sao mất bị loại khỏi kho; các bản sao khác sẵn sàng trở lại
        self.hard_books[v_book]["status"] = (
            "MatSach" if new_record["return_condition"] == "Mat" else "SanSang"
        )

        # DATEDIFF(DATE(returned_at), DATE(due_at))
        v_late = (new_record["returned_at"].date() - v_due.date()).days

        # TH B: Mat
        if new_record["return_condition"] == "Mat":
            self.insert_fine(
                return_record_id=new_record["id"],
                fine_type="Lost",
                amount=v_price,
                reason="Mat sach",
                late_amount=Decimal("0.00"),
                damaged_amount=None,
                assessed_by=None
            )
        # TH C: Hong
        elif new_record["return_condition"] == "Hong":
            # Không tự động tạo khoản phạt
            pass
        # TH A: Tot va qua han
        elif v_late > 0:
            fine_amt = Decimal(str(round(0.10 * float(v_price) * v_late, 2)))
            self.insert_fine(
                return_record_id=new_record["id"],
                fine_type="Late",
                amount=fine_amt,
                reason=f"Tra sach qua han {v_late} ngay",
                late_amount=fine_amt,
                damaged_amount=None,
                assessed_by=None
            )

    def insert_fine(self, return_record_id, fine_type, amount, reason, assessed_by=None, late_amount=Decimal("0.00"), damaged_amount=None):
        # Trigger trg_fines_before_ins & UNIQUE constraint
        for f in self.fines.values():
            if f["return_record_id"] == return_record_id:
                raise ValueError("Mot phieu tra sach khong duoc co khoan phat trung lap")

        fine_id = self.next_fine_id
        self.next_fine_id += 1
        fine = {
            "id": fine_id,
            "return_record_id": return_record_id,
            "fine_type": fine_type,
            "amount": Decimal(str(amount)),
            "reason": reason,
            "late_amount": late_amount,
            "damaged_amount": damaged_amount,
            "assessed_by": assessed_by
        }
        self.fines[fine_id] = fine
        return fine

def run_tests():
    db = MockDatabase()
    db.add_reader(1, "Doc Gia Test")
    db.add_source(100, "Giao Trinh 200k", Decimal("200000.00"))

    # Tạo 8 bản sao sách
    for i in range(1, 9):
        db.add_hard_book(1000 + i, 100)

    due_date = dt.datetime(2026, 10, 15, 23, 59, 0)
    borrow_date = dt.datetime(2026, 10, 1, 8, 0, 0)

    results = []

    # TC 1: Sách trả đúng hạn → không có khoản phạt
    db.add_loan(1, 1, 1001, borrow_date, due_date)
    db.insert_return_record(1, 1, "PT001", dt.datetime(2026, 10, 15, 14, 0, 0), "Tot")
    fines_tc1 = [f for f in db.fines.values() if f["return_record_id"] == 1]
    results.append(("TC1: Sách trả đúng hạn", len(fines_tc1) == 0, f"Số khoản phạt = {len(fines_tc1)} (kỳ vọng 0)"))

    # TC 2: Sách trả trước hạn → không có khoản phạt
    db.add_loan(2, 1, 1002, borrow_date, due_date)
    db.insert_return_record(2, 2, "PT002", dt.datetime(2026, 10, 10, 9, 0, 0), "Tot")
    fines_tc2 = [f for f in db.fines.values() if f["return_record_id"] == 2]
    results.append(("TC2: Sách trả trước hạn", len(fines_tc2) == 0, f"Số khoản phạt = {len(fines_tc2)} (kỳ vọng 0)"))

    # TC 3: Sách giá 200.000đ, quá hạn 3 ngày → phạt 60.000đ
    # 2026-10-18 - 2026-10-15 = 3 ngày. 10% * 200.000 * 3 = 60.000đ
    db.add_loan(3, 1, 1003, borrow_date, due_date)
    db.insert_return_record(3, 3, "PT003", dt.datetime(2026, 10, 18, 10, 0, 0), "Tot")
    fines_tc3 = [f for f in db.fines.values() if f["return_record_id"] == 3]
    tc3_pass = len(fines_tc3) == 1 and fines_tc3[0]["amount"] == Decimal("60000.00") and fines_tc3[0]["fine_type"] == "Late"
    results.append(("TC3: Sách 200k, quá hạn 3 ngày → phạt 60k", tc3_pass, f"Phạt: {fines_tc3[0]['amount'] if fines_tc3 else None} VNĐ, Loại: {fines_tc3[0]['fine_type'] if fines_tc3 else None}"))

    # TC 4: Sách giá 200.000đ, bị mất → phạt 200.000đ
    db.add_loan(4, 1, 1004, borrow_date, due_date)
    db.insert_return_record(4, 4, "PT004", dt.datetime(2026, 10, 15, 11, 0, 0), "Mat")
    fines_tc4 = [f for f in db.fines.values() if f["return_record_id"] == 4]
    tc4_pass = (
        len(fines_tc4) == 1
        and fines_tc4[0]["amount"] == Decimal("200000.00")
        and fines_tc4[0]["fine_type"] == "Lost"
        and db.hard_books[1004]["status"] == "MatSach"
    )
    results.append(("TC4: Sách 200k, bị mất → phạt 200k và loại khỏi kho", tc4_pass, f"Phạt: {fines_tc4[0]['amount'] if fines_tc4 else None} VNĐ, Trạng thái: {db.hard_books[1004]['status']}"))

    # TC 5: Sách giá 200.000đ, quá hạn 3 ngày rồi bị mất → chỉ phạt 200.000đ
    db.add_loan(5, 1, 1005, borrow_date, due_date)
    db.insert_return_record(5, 5, "PT005", dt.datetime(2026, 10, 18, 14, 0, 0), "Mat")
    fines_tc5 = [f for f in db.fines.values() if f["return_record_id"] == 5]
    tc5_pass = (
        len(fines_tc5) == 1
        and fines_tc5[0]["amount"] == Decimal("200000.00")
        and fines_tc5[0]["fine_type"] == "Lost"
        and db.hard_books[1005]["status"] == "MatSach"
    )
    results.append(("TC5: Sách 200k, quá hạn rồi mất → chỉ phạt 200k và loại khỏi kho", tc5_pass, f"Phạt: {fines_tc5[0]['amount'] if fines_tc5 else None} VNĐ, Trạng thái: {db.hard_books[1005]['status']}"))

    # TC 6: Sách bị hỏng → chưa có khoản phạt tự động
    db.add_loan(6, 1, 1006, borrow_date, due_date)
    db.insert_return_record(6, 6, "PT006", dt.datetime(2026, 10, 15, 16, 0, 0), "Hong")
    fines_tc6 = [f for f in db.fines.values() if f["return_record_id"] == 6]
    results.append(("TC6: Sách bị hỏng → chưa có khoản phạt tự động", len(fines_tc6) == 0, f"Số khoản phạt = {len(fines_tc6)} (kỳ vọng 0)"))

    # TC 7: Nhân viên xác nhận sách hỏng và nhập mức phạt 50.000đ → lưu khoản phạt 50.000đ
    db.insert_fine(
        return_record_id=6,
        fine_type="Damaged",
        amount=Decimal("50000.00"),
        reason="Sach rach trang bia",
        assessed_by="NV_ThuThu_01",
        late_amount=Decimal("0.00"),
        damaged_amount=Decimal("50000.00")
    )
    fines_tc7 = [f for f in db.fines.values() if f["return_record_id"] == 6]
    tc7_pass = len(fines_tc7) == 1 and fines_tc7[0]["amount"] == Decimal("50000.00") and fines_tc7[0]["fine_type"] == "Damaged" and fines_tc7[0]["assessed_by"] == "NV_ThuThu_01"
    results.append(("TC7: Nhân viên nhập phạt hỏng 50k → lưu thành công", tc7_pass, f"Phạt: {fines_tc7[0]['amount']} VNĐ, Nhân viên: {fines_tc7[0]['assessed_by']}"))

    # TC 8: Một lần trả sách không được tạo khoản phạt trùng lặp
    tc8_blocked = False
    try:
        # Cố tình insert khoản phạt thứ 2 cho cùng return_record_id = 3 (đã có phạt ở TC3)
        db.insert_fine(
            return_record_id=3,
            fine_type="Late",
            amount=Decimal("60000.00"),
            reason="Khoan phat trung lap thu 2"
        )
    except ValueError as e:
        tc8_blocked = True
        err_msg = str(e)

    results.append(("TC8: Chặn khoản phạt trùng lặp trên cùng 1 lần trả", tc8_blocked, f"Kết quả: Đã chặn thành công ({err_msg if tc8_blocked else 'Không chặn được'})"))

    print("=" * 78)
    print("KẾT QUẢ KIỂM THỬ NGHIỆP VỤ TÍNH TIỀN PHẠT THƯ VIỆN (8 TEST CASES)")
    print("=" * 78)
    all_pass = True
    for name, passed, detail in results:
        status_str = "[PASS]" if passed else "[FAIL]"
        if not passed:
            all_pass = False
        print(f"{status_str:<8} | {name:<50} | {detail}")
    print("=" * 78)
    if all_pass:
        print("TẤT CẢ 8 TEST CASES ĐÃ ĐẠT (100% PASS)!")
    else:
        print("CÓ TEST CASE CHƯA ĐẠT!")
    print("=" * 78)

if __name__ == "__main__":
    run_tests()
