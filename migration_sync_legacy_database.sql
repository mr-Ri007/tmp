-- One-time, data-preserving migration for the legacy library database.
-- Run only against the existing library database; do not run schema.sql over it.
USE library;

ALTER TABLE Sources
  ADD COLUMN price DECIMAL(12,2) NOT NULL DEFAULT 0.00;

ALTER TABLE Fines
  MODIFY COLUMN reason VARCHAR(255) NOT NULL,
  MODIFY COLUMN amount DECIMAL(12,2) NOT NULL,
  ADD COLUMN fine_type VARCHAR(10) NULL AFTER return_record_id,
  ADD COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  ADD COLUMN late_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  ADD COLUMN damaged_amount DECIMAL(12,2) NULL,
  ADD COLUMN assessed_by VARCHAR(100) NULL;

UPDATE Fines
SET fine_type = CASE reason
      WHEN 'Hong' THEN 'Damaged'
      WHEN 'Mat' THEN 'Lost'
      WHEN 'QuaHan' THEN 'Late'
    END,
    late_amount = CASE WHEN reason = 'QuaHan' THEN amount ELSE 0.00 END,
    damaged_amount = CASE WHEN reason = 'Hong' THEN amount ELSE NULL END;

ALTER TABLE Fines
  MODIFY COLUMN fine_type VARCHAR(10) NOT NULL;

DROP TRIGGER IF EXISTS trg_returns_after;

DELIMITER $$

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
  ELSEIF NEW.return_condition = 'Tot' AND v_late > 0 THEN
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

DROP TRIGGER IF EXISTS trg_fines_before_ins$$

CREATE TRIGGER trg_fines_before_ins BEFORE INSERT ON Fines FOR EACH ROW
BEGIN
  IF EXISTS (SELECT 1 FROM Fines WHERE return_record_id = NEW.return_record_id) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Mot phieu tra sach khong duoc co khoan phat trung lap';
  END IF;
END$$

DELIMITER ;
