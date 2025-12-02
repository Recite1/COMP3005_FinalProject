-- Clean up
DROP TABLE IF EXISTS payment CASCADE;
DROP TABLE IF EXISTS invoice CASCADE;
DROP TABLE IF EXISTS equipment CASCADE;
DROP TABLE IF EXISTS rooms CASCADE;
DROP TABLE IF EXISTS session_members CASCADE;
DROP TABLE IF EXISTS training_sessions CASCADE;
DROP TABLE IF EXISTS health_metric CASCADE;
DROP TABLE IF EXISTS fitness_goal CASCADE;
DROP TABLE IF EXISTS trainer CASCADE;
DROP TABLE IF EXISTS member CASCADE;

CREATE TABLE member (
  member_id    SERIAL PRIMARY KEY,
  full_name    VARCHAR(100) NOT NULL,
  date_of_birth DATE NOT NULL,
  phone        VARCHAR(20),
  gender       VARCHAR(10)
);

CREATE TABLE trainer (
  trainer_id         SERIAL PRIMARY KEY,
  full_name          VARCHAR(100) NOT NULL,
  phone              VARCHAR(20),
  availability_start TIME NOT NULL DEFAULT '00:00:00',
  availability_end   TIME NOT NULL DEFAULT '23:59:00',
  CHECK ( availability_end > availability_start)
);

CREATE TABLE fitness_goal (
  goal_id              SERIAL PRIMARY KEY,
  member_id            INTEGER NOT NULL REFERENCES member(member_id) ON DELETE CASCADE,
  weight               NUMERIC(5,2),
  target_date          DATE
);

CREATE TABLE health_metric (
  metric_id           SERIAL PRIMARY KEY,
  member_id           INTEGER NOT NULL REFERENCES member(member_id) ON DELETE CASCADE,
  height              NUMERIC(5,2),
  weight              NUMERIC(5,2),
  heart_rate          INTEGER,
  date                TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE rooms (
  room_id    SERIAL PRIMARY KEY,
  room_name  VARCHAR(20) NOT NULL,
  capacity INTEGER NOT NULL,
  isBooked BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE training_sessions (
  session_id    SERIAL PRIMARY KEY,
  trainer_id    INTEGER NOT NULL REFERENCES trainer(trainer_id),
  room_id       INTEGER REFERENCES rooms(room_id),
  session_type  VARCHAR(10) NOT NULL,
  start_time    TIME NOT NULL,
  end_time      TIME NOT NULL,
  status        VARCHAR(20) NOT NULL DEFAULT 'active',
  capacity      INTEGER NOT NULL,
  CHECK (end_time > start_time),
  CHECK (status IN ('cancelled' , 'active' , 'completed', 'full')),
  CHECK (session_type IN ('group' , 'personal'))
);

CREATE TABLE session_members (
  session_member_id  SERIAL PRIMARY KEY,
  session_id  INTEGER NOT NULL REFERENCES training_sessions(session_id),
  member_id  INTEGER NOT NULL REFERENCES member(member_id)
);


CREATE TABLE equipment (
  equipment_id    SERIAL PRIMARY KEY,
  room_id         INTEGER NOT NULL REFERENCES rooms(room_id) ON DELETE CASCADE,
  type            VARCHAR(20) NOT NULL,
  status          INTEGER NOT NULL
);


CREATE TABLE invoice (
  invoice_id   SERIAL PRIMARY KEY,
  member_id    INTEGER NOT NULL REFERENCES member(member_id) ON DELETE CASCADE,
  issue_date   DATE NOT NULL DEFAULT CURRENT_DATE,
  total_amount NUMERIC(10,2) NOT NULL CHECK (total_amount >= 0),
  status       VARCHAR(20) NOT NULL DEFAULT 'unpaid',
  CHECK (status IN ('unpaid','paid','cancelled'))
);


CREATE TABLE payment (
  payment_id   SERIAL PRIMARY KEY,
  invoice_id   INTEGER NOT NULL REFERENCES invoice(invoice_id) ON DELETE CASCADE,
  payment_date DATE NOT NULL DEFAULT CURRENT_DATE,
  amount       NUMERIC(10,2) NOT NULL CHECK (amount > 0),
  method       VARCHAR(20) NOT NULL
);

-- Views
CREATE OR REPLACE VIEW member_invoice_summary AS
SELECT
  i.invoice_id,
  i.member_id,
  i.issue_date,
  i.total_amount,
  COALESCE(SUM(p.amount), 0)              AS total_paid,
  i.total_amount - COALESCE(SUM(p.amount), 0) AS remaining,
  i.status
FROM invoice i
LEFT JOIN payment p
  ON i.invoice_id = p.invoice_id
GROUP BY
  i.invoice_id, i.member_id, i.issue_date, i.total_amount, i.status;

-- Trigger
CREATE OR REPLACE FUNCTION update_invoice_status_after_payment()
RETURNS TRIGGER AS $$
DECLARE
  total_paid NUMERIC(10,2);
  inv_total  NUMERIC(10,2);
  inv_status VARCHAR(20);
BEGIN
  -- Get invoice total and current status
  SELECT total_amount, status
    INTO inv_total, inv_status
  FROM invoice
  WHERE invoice_id = NEW.invoice_id;

  -- cancelled invoices
  IF inv_status = 'cancelled' THEN
    RETURN NEW;
  END IF;

  -- Sum all payments
  SELECT COALESCE(SUM(amount), 0)
    INTO total_paid
  FROM payment
  WHERE invoice_id = NEW.invoice_id;

  -- Set status based on how much is paid
  IF total_paid >= inv_total THEN
    UPDATE invoice
    SET status = 'paid'
    WHERE invoice_id = NEW.invoice_id;
  ELSE
    UPDATE invoice
    SET status = 'unpaid'
    WHERE invoice_id = NEW.invoice_id;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Indexes
CREATE INDEX idx_session_members_member_id
ON session_members (member_id);

CREATE INDEX idx_training_sessions_trainer_status_type_start
ON training_sessions (trainer_id, status, session_type, start_time);

CREATE INDEX idx_invoice_member_id
ON invoice (member_id);

CREATE INDEX idx_payment_invoice_id
ON payment (invoice_id);

CREATE INDEX idx_health_metric_member_date
ON health_metric (member_id, date DESC);