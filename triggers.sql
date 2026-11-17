USE library;
DELIMITER $$

-- ---------- Readers: du 16 tuoi ----------
CREATE TRIGGER trg_readers_age_ins BEFORE INSERT ON Readers FOR EACH ROW
BEGIN
  IF NEW.date_of_birth > DATE_SUB(CURDATE(), INTERVAL 16 YEAR) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Doc gia phai du 16 tuoi';
  END IF;
END$$

CREATE TRIGGER trg_readers_age_upd BEFORE UPDATE ON Readers FOR EACH ROW
BEGIN
  IF NEW.date_of_birth > DATE_SUB(CURDATE(), INTERVAL 16 YEAR) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Doc gia phai du 16 tuoi';
  END IF;
END$$

-- ---------- Loans: 3 business rules ----------
CREATE TRIGGER trg_loans_before BEFORE INSERT ON Loans FOR EACH ROW
BEGIN
  DECLARE v_type VARCHAR(20);
  DECLARE v_status VARCHAR(10);
  DECLARE v_active INT;
  DECLARE v_unpaid INT;

  SELECT status INTO v_status FROM Hard_books WHERE id = NEW.hard_book_id;
  IF v_status = 'MatSach' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Ban sao da mat, khong the cho muon';
  ELSEIF v_status = 'DangMuon' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Ban sao dang duoc muon';
  END IF;
  -- DangCho: chi nguoi da dat truoc moi duoc muon
  IF v_status = 'DangCho' AND NOT EXISTS (
       SELECT 1 FROM Reservations
       WHERE hard_book_id = NEW.hard_book_id AND reader_id = NEW.reader_id
         AND status = 'ChoNhan') THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Ban sao dang duoc giu cho nguoi khac';
  END IF;

  -- Sinh vien: toi da 5 cuon dong thoi
  SELECT reader_type INTO v_type FROM Readers WHERE id = NEW.reader_id;
  SELECT COUNT(*) INTO v_active FROM v_active_loans WHERE reader_id = NEW.reader_id;
  IF v_type = 'Sinh vien' AND v_active >= 5 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Sinh vien khong duoc muon qua 5 cuon';
  END IF;

  -- Phat chua tra > 100.000
  SELECT COALESCE(SUM(f.amount), 0) INTO v_unpaid
  FROM Fines f
  JOIN Return_records r ON r.id = f.return_record_id
  JOIN Loans l ON l.id = r.loan_id
  WHERE l.reader_id = NEW.reader_id AND f.paid_at IS NULL;
  IF v_unpaid > 100000 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Phat chua tra vuot 100.000 VND';
  END IF;
END$$

CREATE TRIGGER trg_loans_after AFTER INSERT ON Loans FOR EACH ROW
BEGIN
  UPDATE Hard_books SET status = 'DangMuon' WHERE id = NEW.hard_book_id;
  UPDATE Reservations SET status = 'DaNhan'
  WHERE hard_book_id = NEW.hard_book_id AND reader_id = NEW.reader_id
    AND status = 'ChoNhan';
END$$

-- ---------- Renewals ----------
CREATE TRIGGER trg_renewals_before BEFORE INSERT ON Renewals FOR EACH ROW
BEGIN
  IF EXISTS (SELECT 1 FROM Return_records WHERE loan_id = NEW.loan_id) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Luot muon da tra, khong gia han duoc';
  END IF;
  IF NEW.old_due_at <> (SELECT due_at FROM Loans WHERE id = NEW.loan_id) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'old_due_at khong khop han tra hien tai';
  END IF;
END$$

CREATE TRIGGER trg_renewals_after AFTER INSERT ON Renewals FOR EACH ROW
BEGIN
  UPDATE Loans SET due_at = NEW.new_due_at WHERE id = NEW.loan_id;
END$$

-- ---------- Return_records: check ngay + tu sinh phat ----------
CREATE TRIGGER trg_returns_before BEFORE INSERT ON Return_records FOR EACH ROW
BEGIN
  IF NEW.returned_at < (SELECT borrowed_at FROM Loans WHERE id = NEW.loan_id) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Ngay tra phai >= ngay muon';
  END IF;
END$$

CREATE TRIGGER trg_returns_after AFTER INSERT ON Return_records FOR EACH ROW
BEGIN
  DECLARE v_due DATETIME;
  DECLARE v_book INT;
  DECLARE v_price DECIMAL(12,2);
  DECLARE v_late INT;

  -- 1. Lay thong tin han tra, ban sao va gia bia sach tu Sources
  SELECT l.due_at, l.hard_book_id, s.price
  INTO v_due, v_book, v_price
  FROM Loans l
  JOIN Hard_books hb ON hb.id = l.hard_book_id
  JOIN Sources s ON s.id = hb.source_id
  WHERE l.id = NEW.loan_id;

  -- 2. Ban sao mat se bi loai khoi kho; cac truong hop khac san sang tro lai
  IF NEW.return_condition = 'Mat' THEN
    UPDATE Hard_books SET status = 'MatSach' WHERE id = v_book;
  ELSE
    UPDATE Hard_books SET status = 'SanSang' WHERE id = v_book;
  END IF;

  -- 3. Tinh so ngay qua han (overdue_days = returned_at - due_at)
  SET v_late = DATEDIFF(DATE(NEW.returned_at), DATE(v_due));

  -- 4. Xu ly nghiep vu tinh phat:
  -- B. Tra sach bi mat (Lost): fine = 100% * Sources.price
  -- Khong tinh them phi qua han ke ca khi da qua han truoc do
  IF NEW.return_condition = 'Mat' THEN
    INSERT INTO Fines(return_record_id, fine_type, amount, reason, late_amount, damaged_amount, assessed_by)
    VALUES (NEW.id, 'Lost', v_price, 'Mat sach', 0.00, NULL, NULL);

  -- C. Tra sach bi hong (Damaged):
  -- Khong tu dong tao khoan phat; nhan vien kiem tra va tu quyet dinh muc phat sau
  -- A. Tra sach qua han (Late):
  -- fine = 10% * Sources.price * so ngay qua han (chi khi qua han > 0)
  ELSEIF NEW.return_condition <> 'Hong' AND v_late > 0 THEN
    INSERT INTO Fines(return_record_id, fine_type, amount, reason, late_amount, damaged_amount, assessed_by)
    VALUES (NEW.id, 'Late', ROUND(0.10 * v_price * v_late, 2), CONCAT('Tra sach qua han ', v_late, ' ngay'), ROUND(0.10 * v_price * v_late, 2), NULL, NULL);
  END IF;
END$$

-- ---------- Fines: ngan chan khoan phat trung lap cho cung mot phieu tra ----------
CREATE TRIGGER trg_fines_before_ins BEFORE INSERT ON Fines FOR EACH ROW
BEGIN
  IF EXISTS (SELECT 1 FROM Fines WHERE return_record_id = NEW.return_record_id) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Mot phieu tra sach khong duoc co khoan phat trung lap';
  END IF;
END$$

-- ---------- Reservations ----------
CREATE TRIGGER trg_reservations_before BEFORE INSERT ON Reservations FOR EACH ROW
BEGIN
  IF (SELECT status FROM Hard_books WHERE id = NEW.hard_book_id) <> 'SanSang' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Ban sao khong san sang de dat truoc';
  END IF;
END$$

CREATE TRIGGER trg_reservations_after AFTER INSERT ON Reservations FOR EACH ROW
BEGIN
  UPDATE Hard_books SET status = 'DangCho' WHERE id = NEW.hard_book_id;
END$$

-- het han / huy -> tra ban sao ve SanSang
CREATE TRIGGER trg_reservations_update AFTER UPDATE ON Reservations FOR EACH ROW
BEGIN
  IF OLD.status = 'ChoNhan' AND NEW.status IN ('HetHan','Huy') THEN
    UPDATE Hard_books SET status = 'SanSang'
    WHERE id = NEW.hard_book_id AND status = 'DangCho';
  END IF;
END$$

DELIMITER ;