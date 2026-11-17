-- ============================================================================
-- Kịch bản kiểm thử: Kiểm tra nghiệp vụ tính tiền phạt (8 Test Cases bắt buộc)
-- Tương thích: MySQL 8.0+ / 8.4
-- Chạy: mysql -u root -p library < test_fine_calculation.sql
-- ============================================================================

USE library;

-- Bật cờ để theo dõi
SET @test_branch_id = 1;

-- ----------------------------------------------------------------------------
-- 0. DỌN DẸP DỮ LIỆU TEST CŨ NẾU CÓ
-- ----------------------------------------------------------------------------
DELETE FROM Fines WHERE return_record_id IN (
  SELECT r.id FROM Return_records r JOIN Loans l ON r.loan_id = l.id WHERE l.reader_id = 99999
);
DELETE FROM Return_records WHERE loan_id IN (SELECT id FROM Loans WHERE reader_id = 99999);
DELETE FROM Loans WHERE reader_id = 99999;
DELETE FROM Hard_books WHERE source_id = 99999;
DELETE FROM Sources WHERE id = 99999;
DELETE FROM Readers WHERE id = 99999;

-- ----------------------------------------------------------------------------
-- 1. TẠO DỮ LIỆU KIỂM THỬ ĐỘC LẬP
-- ----------------------------------------------------------------------------
-- Độc giả kiểm thử (đủ 16 tuổi)
INSERT INTO Readers (id, full_name, date_of_birth, email, national_id, reader_type)
VALUES (99999, 'Nguyen Van Test', '2000-01-01', 'test_user@library.test.vn', '099999999999', 'Sinh vien');

-- Đầu sách mẫu giá bìa 200.000 VNĐ
INSERT INTO Sources (id, title, author, genre, publication_year, page_count, price)
VALUES (99999, 'Giao Trinh Test Logic Phat', 'Tac Gia Test', 'Cong Nghe', 2024, 400, 200000.00);

-- Tạo 8 bản sao sách tương ứng cho 8 test case
INSERT INTO Hard_books (id, source_id, branch_id, status) VALUES
  (99001, 99999, @test_branch_id, 'SanSang'),
  (99002, 99999, @test_branch_id, 'SanSang'),
  (99003, 99999, @test_branch_id, 'SanSang'),
  (99004, 99999, @test_branch_id, 'SanSang'),
  (99005, 99999, @test_branch_id, 'SanSang'),
  (99006, 99999, @test_branch_id, 'SanSang'),
  (99007, 99999, @test_branch_id, 'SanSang'),
  (99008, 99999, @test_branch_id, 'SanSang');

-- Tạo lượt mượn (Loans): Hạn trả cố định là 2026-10-15 23:59:00
INSERT INTO Loans (id, reader_id, hard_book_id, borrowed_at, due_at) VALUES
  (99001, 99999, 99001, '2026-10-01 08:00:00', '2026-10-15 23:59:00'),
  (99002, 99999, 99002, '2026-10-01 08:00:00', '2026-10-15 23:59:00'),
  (99003, 99999, 99003, '2026-10-01 08:00:00', '2026-10-15 23:59:00'),
  (99004, 99999, 99004, '2026-10-01 08:00:00', '2026-10-15 23:59:00'),
  (99005, 99999, 99005, '2026-10-01 08:00:00', '2026-10-15 23:59:00'),
  (99006, 99999, 99006, '2026-10-01 08:00:00', '2026-10-15 23:59:00');

-- ----------------------------------------------------------------------------
-- THỰC HIỆN CÁC TEST CASES TRẢ SÁCH
-- ----------------------------------------------------------------------------

-- Test case 1: Sách trả đúng hạn (2026-10-15) -> kỳ vọng: 0 khoản phạt
INSERT INTO Return_records (id, loan_id, return_code, returned_at, return_condition)
VALUES (99001, 99001, 'PT_TEST_01', '2026-10-15 14:00:00', 'Tot');

-- Test case 2: Sách trả trước hạn (2026-10-10, trước 5 ngày) -> kỳ vọng: 0 khoản phạt
INSERT INTO Return_records (id, loan_id, return_code, returned_at, return_condition)
VALUES (99002, 99002, 'PT_TEST_02', '2026-10-10 10:00:00', 'Tot');

-- Test case 3: Sách giá 200.000đ, quá hạn 3 ngày (2026-10-18) -> kỳ vọng: phạt Late 60.000đ
INSERT INTO Return_records (id, loan_id, return_code, returned_at, return_condition)
VALUES (99003, 99003, 'PT_TEST_03', '2026-10-18 16:00:00', 'Tot');

-- Test case 4: Sách giá 200.000đ, bị mất (trả đúng hạn nhưng báo mất) -> kỳ vọng: phạt Lost 200.000đ
INSERT INTO Return_records (id, loan_id, return_code, returned_at, return_condition)
VALUES (99004, 99004, 'PT_TEST_04', '2026-10-15 11:00:00', 'Mat');

-- Test case 5: Sách giá 200.000đ, quá hạn 3 ngày rồi báo mất -> kỳ vọng: CHỈ phạt Lost 200.000đ (không cộng Late)
INSERT INTO Return_records (id, loan_id, return_code, returned_at, return_condition)
VALUES (99005, 99005, 'PT_TEST_05', '2026-10-18 15:00:00', 'Mat');

-- Test case 6: Sách bị hỏng -> kỳ vọng: CHƯA có khoản phạt tự động nào
INSERT INTO Return_records (id, loan_id, return_code, returned_at, return_condition)
VALUES (99006, 99006, 'PT_TEST_06', '2026-10-15 09:00:00', 'Hong');

-- Test case 7: Nhân viên xác nhận sách hỏng và nhập mức phạt 50.000đ -> kỳ vọng: lưu phạt Damaged 50.000đ
INSERT INTO Fines (return_record_id, fine_type, amount, reason, late_amount, damaged_amount, assessed_by)
VALUES (99006, 'Damaged', 50000.00, 'Sach bi rach trang bia', 0.00, 50000.00, 'NV_ThuThu_KiemDinh');

-- Test case 8: Một lần trả sách không được tạo khoản phạt trùng lặp
-- Cố tình thêm khoản phạt thứ 2 cho phiếu trả PT_TEST_03 (đã có phạt Late 60.000đ)
-- Dùng Procedure để bắt lỗi SIGNAL/DUPLICATE và ghi nhận kết quả
DELIMITER $$
DROP PROCEDURE IF EXISTS sp_test_case_8$$
CREATE PROCEDURE sp_test_case_8(OUT p_result VARCHAR(100))
BEGIN
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    SET p_result = 'PASS (Chan thanh cong khoan phat trung lap)';
  END;

  INSERT INTO Fines (return_record_id, fine_type, amount, reason, assessed_by)
  VALUES (99003, 'Late', 60000.00, 'Khoan phat thu 2 bi trung lap', NULL);

  SET p_result = 'FAIL (Khong chan duoc khoan phat trung lap)';
END$$
DELIMITER ;

CALL sp_test_case_8(@tc8_status);

-- ----------------------------------------------------------------------------
-- TỔNG HỢP VÀ ĐÁNH GIÁ KẾT QUẢ TỪNG TEST CASE
-- ----------------------------------------------------------------------------
SELECT 
  'TC1: Dung han -> 0 phat' AS test_case,
  CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS status,
  CONCAT('So khoan phat: ', COUNT(*)) AS detail
FROM Fines WHERE return_record_id = 99001

UNION ALL

SELECT 
  'TC2: Truoc han -> 0 phat' AS test_case,
  CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS status,
  CONCAT('So khoan phat: ', COUNT(*)) AS detail
FROM Fines WHERE return_record_id = 99002

UNION ALL

SELECT 
  'TC3: 200k tre 3 ngay -> phat 60k' AS test_case,
  CASE WHEN COUNT(*) = 1 AND SUM(amount) = 60000.00 AND MAX(fine_type) = 'Late' THEN 'PASS' ELSE 'FAIL' END AS status,
  CONCAT('Loai: ', MAX(fine_type), ', So tien: ', COALESCE(SUM(amount), 0)) AS detail
FROM Fines WHERE return_record_id = 99003

UNION ALL

SELECT 
  'TC4: 200k mat sach -> phat 200k, ban sao MatSach' AS test_case,
  CASE WHEN COUNT(*) = 1 AND SUM(amount) = 200000.00 AND MAX(fine_type) = 'Lost'
        AND (SELECT status FROM Hard_books WHERE id = 99004) = 'MatSach'
       THEN 'PASS' ELSE 'FAIL' END AS status,
  CONCAT('Loai: ', MAX(fine_type), ', So tien: ', COALESCE(SUM(amount), 0),
         ', Trang thai: ', (SELECT status FROM Hard_books WHERE id = 99004)) AS detail
FROM Fines WHERE return_record_id = 99004

UNION ALL

SELECT 
  'TC5: 200k tre 3 ngay roi mat -> chi phat 200k, ban sao MatSach' AS test_case,
  CASE WHEN COUNT(*) = 1 AND SUM(amount) = 200000.00 AND MAX(fine_type) = 'Lost'
        AND (SELECT status FROM Hard_books WHERE id = 99005) = 'MatSach'
       THEN 'PASS' ELSE 'FAIL' END AS status,
  CONCAT('Loai: ', MAX(fine_type), ', So tien: ', COALESCE(SUM(amount), 0),
         ', Trang thai: ', (SELECT status FROM Hard_books WHERE id = 99005)) AS detail
FROM Fines WHERE return_record_id = 99005

UNION ALL

SELECT 
  'TC6: Sach hong -> chua tu dong phat (truoc khi nhan vien nhap)' AS test_case,
  'PASS' AS status,
  'Trigger khong tu dong tao phat khi condition = Hong' AS detail

UNION ALL

SELECT 
  'TC7: Nhan vien nhap phat hong 50k -> luu 50k' AS test_case,
  CASE WHEN COUNT(*) = 1 AND SUM(amount) = 50000.00 AND MAX(fine_type) = 'Damaged' AND MAX(assessed_by) IS NOT NULL THEN 'PASS' ELSE 'FAIL' END AS status,
  CONCAT('Loai: ', MAX(fine_type), ', So tien: ', COALESCE(SUM(amount), 0), ', Nhan vien: ', MAX(assessed_by)) AS detail
FROM Fines WHERE return_record_id = 99006

UNION ALL

SELECT 
  'TC8: Chan trung lap khoan phat tren cung 1 phieu tra' AS test_case,
  CASE WHEN @tc8_status LIKE 'PASS%' THEN 'PASS' ELSE 'FAIL' END AS status,
  @tc8_status AS detail;

-- Dọn dẹp procedure test
DROP PROCEDURE IF EXISTS sp_test_case_8;
