-- ===== Hệ thống thư viện số đa chi nhánh - MySQL 8 / MariaDB 10.5+ =====
-- Quy ước: tên bảng số nhiều, viết hoa chữ đầu (Readers); khóa ngoại <số_ít>_id;
-- cột thời gian có hậu tố _at; giá trị cố định (status, reader_type...) giữ tiếng Việt không dấu.
-- LƯU Ý: trên Linux, tên bảng phân biệt hoa thường -> luôn viết đúng Readers, không viết readers.
-- Thứ tự nạp: schema.sql -> seed.sql -> triggers.sql
SET NAMES utf8mb4;
CREATE DATABASE IF NOT EXISTS library CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE library;

-- Chi nhánh thư viện
CREATE TABLE Branches (
  id INT AUTO_INCREMENT PRIMARY KEY,                -- Mã chi nhánh
  name VARCHAR(100) NOT NULL,                       -- Tên chi nhánh
  address VARCHAR(255) NOT NULL                     -- Địa chỉ chi nhánh
);

-- Tài liệu chung (dùng cho cả bản cứng và bản mềm)
CREATE TABLE Sources (
  id INT AUTO_INCREMENT PRIMARY KEY,                -- Mã tài liệu
  title VARCHAR(255) NOT NULL,                      -- Tên tài liệu
  author VARCHAR(100) NOT NULL,                     -- Tác giả
  genre VARCHAR(50),                                -- Thể loại (vd: Trí tuệ nhân tạo)
  publication_year SMALLINT                         -- Năm xuất bản
    CHECK (publication_year BETWEEN 1000 AND 2100),
  page_count INT CHECK (page_count > 0),            -- Số trang
  price DECIMAL(12,2) NOT NULL DEFAULT 0.00         -- Giá bìa hiện tại (VNĐ)
    CHECK (price >= 0)
);

-- Bản cứng: 1 bản sao vật lý của tài liệu tại 1 chi nhánh
CREATE TABLE Hard_books (
  id INT AUTO_INCREMENT PRIMARY KEY,                -- Mã bản sao (mã vạch)
  source_id INT NOT NULL,                           -- Thuộc tài liệu nào
  branch_id INT NOT NULL,                           -- Đang đặt tại chi nhánh nào
  status VARCHAR(10) NOT NULL DEFAULT 'SanSang',    -- Trạng thái: SanSang / DangCho / DangMuon / MatSach
  CONSTRAINT chk_hard_books_status
    CHECK (status IN ('SanSang','DangCho','DangMuon','MatSach')),
  FOREIGN KEY (source_id) REFERENCES Sources(id) ON DELETE RESTRICT,
  FOREIGN KEY (branch_id) REFERENCES Branches(id) ON DELETE RESTRICT
);

-- Bản mềm (ebook): mỗi tài liệu có tối đa 1 file số
CREATE TABLE Ebooks (
  id INT AUTO_INCREMENT PRIMARY KEY,                -- Mã bản mềm
  source_id INT NOT NULL UNIQUE,                    -- Thuộc tài liệu nào (1-1)
  file_size_mb INT CHECK (file_size_mb > 0),        -- Dung lượng file (MB)
  FOREIGN KEY (source_id) REFERENCES Sources(id) ON DELETE RESTRICT
);

-- Độc giả
CREATE TABLE Readers (
  id INT AUTO_INCREMENT PRIMARY KEY,                -- Mã độc giả
  full_name VARCHAR(100) NOT NULL,                  -- Họ và tên
  date_of_birth DATE NOT NULL,                      -- Ngày sinh (trigger kiểm tra phải đủ 16 tuổi)
  email VARCHAR(100) NOT NULL UNIQUE,               -- Email (không trùng)
  phone VARCHAR(20),                                -- Số điện thoại (có thể để trống)
  national_id VARCHAR(12) UNIQUE,                   -- Số CCCD (không trùng, có thể để trống)
  reader_type VARCHAR(20) NOT NULL                  -- Hạng độc giả: Sinh vien / Giang vien / Nghien cuu sinh
    CHECK (reader_type IN ('Sinh vien','Giang vien','Nghien cuu sinh'))
);

-- Lịch sử truy cập tài liệu số
CREATE TABLE Access_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,                -- Mã lượt truy cập
  reader_id INT NOT NULL,                           -- Độc giả nào truy cập
  ebook_id INT NOT NULL,                            -- Truy cập bản mềm nào
  started_at DATETIME NOT NULL,                     -- Thời điểm bắt đầu truy cập
  ended_at DATETIME NULL,                           -- Thời điểm kết thúc (NULL = đang truy cập)
  CHECK (ended_at IS NULL OR ended_at >= started_at),
  FOREIGN KEY (reader_id) REFERENCES Readers(id) ON DELETE RESTRICT,
  FOREIGN KEY (ebook_id) REFERENCES Ebooks(id) ON DELETE RESTRICT
);

-- Lịch sử mượn sách cứng (mỗi dòng = 1 bản sao được mượn 1 lần)
CREATE TABLE Loans (
  id INT AUTO_INCREMENT PRIMARY KEY,                -- Mã lượt mượn
  reader_id INT NOT NULL,                           -- Độc giả nào mượn
  hard_book_id INT NOT NULL,                        -- Mượn bản sao nào
  borrowed_at DATETIME NOT NULL,                    -- Thời điểm mượn
  due_at DATETIME NOT NULL,                         -- Hạn trả (được cập nhật khi gia hạn)
  CHECK (due_at > borrowed_at),
  FOREIGN KEY (reader_id) REFERENCES Readers(id) ON DELETE RESTRICT,
  FOREIGN KEY (hard_book_id) REFERENCES Hard_books(id) ON DELETE RESTRICT
);

-- Lịch sử gia hạn
CREATE TABLE Renewals (
  id INT AUTO_INCREMENT PRIMARY KEY,                -- Mã lượt gia hạn
  loan_id INT NOT NULL,                             -- Gia hạn cho lượt mượn nào
  old_due_at DATETIME NOT NULL,                     -- Hạn trả cũ
  new_due_at DATETIME NOT NULL,                     -- Hạn trả mới
  CHECK (new_due_at > old_due_at),
  FOREIGN KEY (loan_id) REFERENCES Loans(id) ON DELETE RESTRICT
);

-- Phiếu trả sách (1 lượt mượn có tối đa 1 phiếu trả)
CREATE TABLE Return_records (
  id INT AUTO_INCREMENT PRIMARY KEY,                -- Mã phiếu trả (nội bộ)
  loan_id INT NOT NULL UNIQUE,                      -- Trả cho lượt mượn nào (1-1)
  return_code VARCHAR(30) NOT NULL UNIQUE,          -- Mã phiếu trả in trên phiếu (không trùng)
  returned_at DATETIME NOT NULL,                    -- Thời điểm trả thực tế (trigger kiểm tra >= ngày mượn)
  return_condition VARCHAR(5) NOT NULL DEFAULT 'Tot'   -- Tình trạng sách khi trả: Tot / Hong / Mat
    CHECK (return_condition IN ('Tot','Hong','Mat')),
  FOREIGN KEY (loan_id) REFERENCES Loans(id) ON DELETE RESTRICT
);

-- Khoản phạt (Damaged chỉ được thêm sau khi nhân viên xác nhận)
CREATE TABLE Fines (
  id INT AUTO_INCREMENT PRIMARY KEY,                -- Mã khoản phạt
  return_record_id INT NOT NULL,                    -- Phát sinh từ phiếu trả nào
  fine_type VARCHAR(10) NOT NULL                    -- Late / Lost / Damaged
    CHECK (fine_type IN ('Late','Lost','Damaged')),
  amount DECIMAL(12,2) NOT NULL CHECK (amount >= 0), -- Số tiền thực tế (VNĐ)
  reason VARCHAR(255) NOT NULL,                     -- Lý do/ghi chú phạt
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  late_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00
    CHECK (late_amount >= 0),                        -- Cấu phần quá hạn được ghi nhận
  damaged_amount DECIMAL(12,2) NULL
    CHECK (damaged_amount IS NULL OR damaged_amount >= 0), -- NULL = chưa đánh giá hỏng
  assessed_by VARCHAR(100) NULL,                    -- Nhân viên thực hiện đánh giá (trường hợp Damaged)
  paid_at DATETIME NULL,                            -- Thời điểm đã nộp phạt (NULL = chưa nộp)
  CONSTRAINT uq_fines_return_record UNIQUE (return_record_id),
  FOREIGN KEY (return_record_id) REFERENCES Return_records(id) ON DELETE RESTRICT
);

-- Đặt trước bản cứng
CREATE TABLE Reservations (
  id INT AUTO_INCREMENT PRIMARY KEY,                -- Mã lượt đặt trước
  reader_id INT NOT NULL,                           -- Độc giả nào đặt
  hard_book_id INT NOT NULL,                        -- Đặt bản sao nào (phải đang SanSang)
  reserved_at DATETIME NOT NULL,                    -- Thời điểm đặt
  pickup_deadline DATETIME NOT NULL,                -- Hạn đến nhận sách
  status VARCHAR(10) NOT NULL DEFAULT 'ChoNhan'     -- Trạng thái: ChoNhan / DaNhan / HetHan / Huy
    CHECK (status IN ('ChoNhan','DaNhan','HetHan','Huy')),
  CHECK (pickup_deadline > reserved_at),
  FOREIGN KEY (reader_id) REFERENCES Readers(id) ON DELETE RESTRICT,
  FOREIGN KEY (hard_book_id) REFERENCES Hard_books(id) ON DELETE RESTRICT
);

-- Môn học (cho Query 7 - phép chia)
CREATE TABLE Courses (
  id INT AUTO_INCREMENT PRIMARY KEY,                -- Mã môn học
  name VARCHAR(100) NOT NULL UNIQUE                 -- Tên môn học
);

-- Danh mục giáo trình của từng môn
CREATE TABLE Course_resources (
  course_id INT NOT NULL,                           -- Môn học nào
  source_id INT NOT NULL,                           -- Tài liệu nào
  is_required BOOLEAN NOT NULL DEFAULT TRUE,        -- TRUE = giáo trình bắt buộc, FALSE = tham khảo
  PRIMARY KEY (course_id, source_id),
  FOREIGN KEY (course_id) REFERENCES Courses(id) ON DELETE RESTRICT,
  FOREIGN KEY (source_id) REFERENCES Sources(id) ON DELETE RESTRICT
);

-- Thay cho bảng Sách_đang_mượn: các lượt mượn chưa có phiếu trả
CREATE VIEW v_active_loans AS
SELECT l.*
FROM Loans l LEFT JOIN Return_records r ON r.loan_id = l.id
WHERE r.id IS NULL;
