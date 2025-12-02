INSERT INTO member (full_name, date_of_birth, phone, gender) VALUES
  ('Alice Smith',   '1995-03-14', '555-111-1111', 'F'),
  ('Bob Johnson',   '1990-07-02', '555-222-2222', 'M'),
  ('Charlie Wong',  '1988-11-20', '555-333-3333', 'M'),
  ('Diana Carter',  '1998-05-09', '555-444-4444', 'F');

INSERT INTO trainer (full_name, phone, availability_start, availability_end) VALUES
  ('John Trainer',   '555-555-1111', '08:00:00', '16:00:00'),
  ('Emily Coach',    '555-555-2222', '12:00:00', '20:00:00'),
  ('Michael Strong', '555-555-3333', '06:00:00', '14:00:00');

INSERT INTO rooms (room_name, capacity, isBooked) VALUES
  ('Studio A', 15, FALSE),
  ('Studio B', 20, FALSE),
  ('PT Room 1',  2, FALSE);

INSERT INTO equipment (room_id, type, status) VALUES
  (1, 'Treadmill',      0),
  (1, 'Exercise Bike',  0),
  (2, 'Rowing Machine', 1),
  (2, 'Bench Press',    0),
  (3, 'Dumbbells Set',  0),
  (3, 'Smith Machine',  2);

INSERT INTO fitness_goal (member_id, weight, target_date) VALUES
  (1, 130.0, '2025-06-30'),  
  (2, 180.0, '2025-07-31'),  
  (3, 160.0, '2025-08-15');  

INSERT INTO health_metric (member_id, height, weight, heart_rate, date) VALUES
  (1, 165.0, 140.0, 72, '2025-11-25 10:00:00'),
  (1, 165.0, 138.5, 70, '2025-11-28 09:30:00'),
  (2, 178.0, 190.0, 80, '2025-11-26 14:15:00'),
  (3, 172.0, 170.0, 76, '2025-11-27 18:45:00'),
  (4, 160.0, 120.0, 68, '2025-11-28 08:10:00');

INSERT INTO training_sessions
  (trainer_id, room_id, session_type, start_time, end_time, status, capacity)
VALUES
  -- Personal sessions 
  (1, 3, 'personal', '09:00:00', '09:30:00', 'active',    1), 
  (1, 3, 'personal', '10:00:00', '10:30:00', 'cancelled', 1), 
  (2, 3, 'personal', '13:00:00', '13:45:00', 'active',    1), 

  -- Group classes
  (1, 1, 'group', '11:00:00', '12:00:00', 'active',   10),   
  (2, 2, 'group', '18:00:00', '19:00:00', 'full',     15),    
  (3, 1, 'group', '07:00:00', '08:00:00', 'active',   12);    

-- Personal sessions
INSERT INTO session_members (session_id, member_id) VALUES
  (1, 1),  
  (3, 2);  

-- Group sessions
INSERT INTO session_members (session_id, member_id) VALUES
  (4, 1),  
  (4, 2),  
  (4, 3),  
  (5, 2), 
  (6, 3), 
  (6, 4);  

INSERT INTO invoice (member_id, issue_date, total_amount, status) VALUES
  (1, '2025-11-20', 100.00, 'unpaid'),   
  (1, '2025-11-25',  60.00, 'unpaid'),   
  (2, '2025-11-22', 150.00, 'unpaid'),   
  (3, '2025-11-23',  80.00, 'cancelled'); 

INSERT INTO payment (invoice_id, payment_date, amount, method) VALUES
  (1, '2025-11-21', 50.00, 'card'),
  (2, '2025-11-26', 60.00, 'cash'),
  (3, '2025-11-23', 100.00, 'card'),
  (3, '2025-11-24',  50.00, 'card');
