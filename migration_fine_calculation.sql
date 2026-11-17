-- ============================================================================
-- Migration: Cập nhật nghiệp vụ tính tiền phạt (Fine Calculation Logic)
-- Tương thích: MySQL 8.0+ / MySQL 8.4
-- Thứ tự chạy trên database hiện có:
--   mysql -u root -p library < migration_fine_calculation.sql
-- ============================================================================

USE library;

-- ----------------------------------------------------------------------------
-- 1. BẢNG Sources: Thêm cột price nếu chưa có và cập nhật dữ liệu an toàn
-- ----------------------------------------------------------------------------
SET @col_price_exists = (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'Sources'
    AND COLUMN_NAME = 'price'
);

SET @sql_add_price = IF(@col_price_exists = 0,
  'ALTER TABLE Sources ADD COLUMN price DECIMAL(12,2) NOT NULL DEFAULT 0.00 CHECK (price >= 0)',
  'SELECT "Column Sources.price already exists" AS notice');
PREPARE stmt FROM @sql_add_price;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Cập nhật giá bìa mặc định cho các đầu sách cũ đang có giá 0.00 hoặc NULL
-- Đảm bảo dữ liệu cũ có giá trị hợp lệ để tính tiền phạt
UPDATE Sources
SET price = 100000.00
WHERE price = 0.00 OR price IS NULL;

-- ----------------------------------------------------------------------------
-- 2. BẢNG Fines: Thêm cột assessed_by nếu chưa có
-- ----------------------------------------------------------------------------
SET @col_assessed_exists = (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'Fines'
    AND COLUMN_NAME = 'assessed_by'
);

SET @sql_add_assessed = IF(@col_assessed_exists = 0,
  'ALTER TABLE Fines ADD COLUMN assessed_by VARCHAR(100) NULL COMMENT "Nhan vien danh gia sach bi hu hai"',
  'SELECT "Column Fines.assessed_by already exists" AS notice');
PREPARE stmt FROM @sql_add_assessed;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ----------------------------------------------------------------------------
-- 3. XỬ LÝ DỮ LIỆU CŨ TRONG BẢNG Fines: Chuẩn hóa và chống trùng lặp
-- ----------------------------------------------------------------------------
-- Nếu trong dữ liệu cũ có trường hợp 1 lần trả sách sinh 2 khoản phạt (Late + Lost/Damaged):
-- Theo nghiệp vụ mới: Nếu sách Lost, chỉ áp dụng đền bù Lost, loại bỏ khoản Late thừa.
DELETE f_late FROM Fines f_late
JOIN Fines f_other ON f_late.return_record_id = f_other.return_record_id AND f_late.id <> f_other.id
WHERE f_late.fine_type = 'Late' AND f_other.fine_type IN ('Lost', 'Damaged');

-- Nếu vẫn còn bản ghi trùng lặp cho cùng một return_record_id, chỉ giữ lại bản ghi đầu tiên (id nhỏ nhất)
DELETE f_dup FROM Fines f_dup
JOIN Fines f_keep ON f_dup.return_record_id = f_keep.return_record_id AND f_dup.id > f_keep.id;

-- ----------------------------------------------------------------------------
-- 4. BẢNG Fines: Thêm ràng buộc UNIQUE (return_record_id) nếu chưa có
-- ----------------------------------------------------------------------------
SET @uq_exists = (
  SELECT COUNT(*)
  FROM information_schema.TABLE_CONSTRAINTS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'Fines'
    AND CONSTRAINT_NAME = 'uq_fines_return_record'
);

SET @sql_add_uq = IF(@uq_exists = 0,
  'ALTER TABLE Fines ADD CONSTRAINT uq_fines_return_record UNIQUE (return_record_id)',
  'SELECT "Constraint uq_fines_return_record already exists" AS notice');
PREPARE stmt FROM @sql_add_uq;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ----------------------------------------------------------------------------
-- 5. CẬP NHẬT TRIGGER trg_returns_after
-- ----------------------------------------------------------------------------
DELIMITER $$

DROP TRIGGER IF EXISTS trg_returns_after$$

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

  -- 2. Cap nhat trang thai ban sao ve SanSang
  UPDATE Hard_books SET status = 'SanSang' WHERE id = v_book;

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
  ELSEIF NEW.return_condition = 'Hong' THEN
    -- Khong tu dong tao khoan phat, cho nhan vien danh gia

  -- A. Tra sach qua han (Late):
  -- fine = 10% * Sources.price * so ngay qua han (chi khi qua han > 0)
  ELSEIF v_late > 0 THEN
    INSERT INTO Fines(return_record_id, fine_type, amount, reason, late_amount, damaged_amount, assessed_by)
    VALUES (NEW.id, 'Late', ROUND(0.10 * v_price * v_late, 2), CONCAT('Tra sach qua han ', v_late, ' ngay'), ROUND(0.10 * v_price * v_late, 2), NULL, NULL);
  END IF;
END$$

-- ----------------------------------------------------------------------------
-- 6. TẠO TRIGGER trg_fines_before_ins (Chặn khoản phạt trùng lặp)
-- ----------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_fines_before_ins$$

CREATE TRIGGER trg_fines_before_ins BEFORE INSERT ON Fines FOR EACH ROW
BEGIN
  IF EXISTS (SELECT 1 FROM Fines WHERE return_record_id = NEW.return_record_id) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Mot phieu tra sach khong duoc co khoan phat trung lap';
  END IF;
END$$

DELIMITER ;
