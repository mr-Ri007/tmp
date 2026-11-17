-- Add optional phone numbers to existing library databases without changing reader data.
SET @phone_column_exists = (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'Readers'
    AND COLUMN_NAME = 'phone'
);

SET @add_phone_sql = IF(
  @phone_column_exists = 0,
  'ALTER TABLE Readers ADD COLUMN phone VARCHAR(20) NULL',
  'SELECT ''Readers.phone already exists'' AS migration_status'
);

PREPARE add_phone_statement FROM @add_phone_sql;
EXECUTE add_phone_statement;
DEALLOCATE PREPARE add_phone_statement;
