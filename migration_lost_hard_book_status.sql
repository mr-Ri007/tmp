-- Migration: keep lost physical copies unavailable permanently.
-- Run against the library database after the existing schema migrations.
USE library;

-- Replace the existing Hard_books status CHECK constraint, regardless of its name.
SET @hard_books_status_check = (
  SELECT CONSTRAINT_NAME
  FROM information_schema.TABLE_CONSTRAINTS
  WHERE CONSTRAINT_SCHEMA = DATABASE()
    AND TABLE_NAME = 'Hard_books'
    AND CONSTRAINT_TYPE = 'CHECK'
  LIMIT 1
);
SET @drop_status_check_sql = IF(
  @hard_books_status_check IS NULL,
  'SELECT ''No existing Hard_books CHECK constraint''',
  CONCAT('ALTER TABLE Hard_books DROP CHECK `', REPLACE(@hard_books_status_check, '`', '``'), '`')
);
PREPARE drop_status_check FROM @drop_status_check_sql;
EXECUTE drop_status_check;
DEALLOCATE PREPARE drop_status_check;

ALTER TABLE Hard_books
  ADD CONSTRAINT chk_hard_books_status
  CHECK (status IN ('SanSang', 'DangCho', 'DangMuon', 'MatSach'));

-- Replace a legacy Fines type CHECK that may not allow Lost.
SET @fines_type_check = (
  SELECT tc.CONSTRAINT_NAME
  FROM information_schema.TABLE_CONSTRAINTS tc
  JOIN information_schema.CHECK_CONSTRAINTS cc
    ON cc.CONSTRAINT_SCHEMA = tc.CONSTRAINT_SCHEMA
    AND cc.CONSTRAINT_NAME = tc.CONSTRAINT_NAME
  WHERE tc.CONSTRAINT_SCHEMA = DATABASE()
    AND tc.TABLE_NAME = 'Fines'
    AND tc.CONSTRAINT_TYPE = 'CHECK'
    AND LOWER(cc.CHECK_CLAUSE) LIKE '%fine_type%'
  LIMIT 1
);
SET @drop_fines_type_check_sql = IF(
  @fines_type_check IS NULL,
  'SELECT ''No existing Fines fine_type CHECK constraint''',
  CONCAT('ALTER TABLE Fines DROP CHECK `', REPLACE(@fines_type_check, '`', '``'), '`')
);
PREPARE drop_fines_type_check FROM @drop_fines_type_check_sql;
EXECUTE drop_fines_type_check;
DEALLOCATE PREPARE drop_fines_type_check;

ALTER TABLE Fines
  ADD CONSTRAINT chk_fines_type
  CHECK (fine_type IN ('Late', 'Lost', 'Damaged'));

-- Legacy reason values were codes; current triggers store descriptive text.
SET @fines_reason_check = (
  SELECT tc.CONSTRAINT_NAME
  FROM information_schema.TABLE_CONSTRAINTS tc
  JOIN information_schema.CHECK_CONSTRAINTS cc
    ON cc.CONSTRAINT_SCHEMA = tc.CONSTRAINT_SCHEMA
    AND cc.CONSTRAINT_NAME = tc.CONSTRAINT_NAME
  WHERE tc.CONSTRAINT_SCHEMA = DATABASE()
    AND tc.TABLE_NAME = 'Fines'
    AND tc.CONSTRAINT_TYPE = 'CHECK'
    AND LOWER(cc.CHECK_CLAUSE) LIKE '%reason%'
  LIMIT 1
);
SET @drop_fines_reason_check_sql = IF(
  @fines_reason_check IS NULL,
  'SELECT ''No existing Fines reason CHECK constraint''',
  CONCAT('ALTER TABLE Fines DROP CHECK `', REPLACE(@fines_reason_check, '`', '``'), '`')
);
PREPARE drop_fines_reason_check FROM @drop_fines_reason_check_sql;
EXECUTE drop_fines_reason_check;
DEALLOCATE PREPARE drop_fines_reason_check;

-- Repair copies whose latest recorded loan ended with a lost-book report.
UPDATE Hard_books hb
JOIN Loans l ON l.hard_book_id = hb.id
JOIN Return_records rr ON rr.loan_id = l.id
SET hb.status = 'MatSach'
WHERE rr.return_condition = 'Mat'
  AND NOT EXISTS (
    SELECT 1
    FROM Loans newer
    WHERE newer.hard_book_id = hb.id
      AND (
        newer.borrowed_at > l.borrowed_at
        OR (newer.borrowed_at = l.borrowed_at AND newer.id > l.id)
      )
  );

-- A reservation cannot remain claimable for a copy that has been marked lost.
UPDATE Reservations r
JOIN Hard_books hb ON hb.id = r.hard_book_id
SET r.status = 'Huy'
WHERE r.status = 'ChoNhan'
  AND hb.status = 'MatSach';

DELIMITER $$

DROP TRIGGER IF EXISTS trg_loans_before$$
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

  IF v_status = 'DangCho' AND NOT EXISTS (
    SELECT 1 FROM Reservations
    WHERE hard_book_id = NEW.hard_book_id
      AND reader_id = NEW.reader_id
      AND status = 'ChoNhan'
  ) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Ban sao dang duoc giu cho nguoi khac';
  END IF;

  SELECT reader_type INTO v_type FROM Readers WHERE id = NEW.reader_id;
  SELECT COUNT(*) INTO v_active FROM v_active_loans WHERE reader_id = NEW.reader_id;
  IF v_type = 'Sinh vien' AND v_active >= 5 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Sinh vien khong duoc muon qua 5 cuon';
  END IF;

  SELECT COALESCE(SUM(f.amount), 0) INTO v_unpaid
  FROM Fines f
  JOIN Return_records r ON r.id = f.return_record_id
  JOIN Loans l ON l.id = r.loan_id
  WHERE l.reader_id = NEW.reader_id AND f.paid_at IS NULL;
  IF v_unpaid > 100000 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Phat chua tra vuot 100.000 VND';
  END IF;
END$$

DROP TRIGGER IF EXISTS trg_returns_after$$
CREATE TRIGGER trg_returns_after AFTER INSERT ON Return_records FOR EACH ROW
BEGIN
  DECLARE v_due DATETIME;
  DECLARE v_book INT;
  DECLARE v_price DECIMAL(12,2);
  DECLARE v_late INT;

  SELECT l.due_at, l.hard_book_id, s.price
  INTO v_due, v_book, v_price
  FROM Loans l
  JOIN Hard_books hb ON hb.id = l.hard_book_id
  JOIN Sources s ON s.id = hb.source_id
  WHERE l.id = NEW.loan_id;

  IF NEW.return_condition = 'Mat' THEN
    UPDATE Hard_books SET status = 'MatSach' WHERE id = v_book;
  ELSE
    UPDATE Hard_books SET status = 'SanSang' WHERE id = v_book;
  END IF;

  SET v_late = DATEDIFF(DATE(NEW.returned_at), DATE(v_due));

  IF NEW.return_condition = 'Mat' THEN
    INSERT INTO Fines(return_record_id, fine_type, amount, reason, late_amount, damaged_amount, assessed_by)
    VALUES (NEW.id, 'Lost', v_price, 'Mat sach', 0.00, NULL, NULL);
  ELSEIF NEW.return_condition <> 'Hong' AND v_late > 0 THEN
    INSERT INTO Fines(return_record_id, fine_type, amount, reason, late_amount, damaged_amount, assessed_by)
    VALUES (
      NEW.id,
      'Late',
      ROUND(0.10 * v_price * v_late, 2),
      CONCAT('Tra sach qua han ', v_late, ' ngay'),
      ROUND(0.10 * v_price * v_late, 2),
      NULL,
      NULL
    );
  END IF;
END$$

DELIMITER ;
