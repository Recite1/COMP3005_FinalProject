import psycopg2
import random
from datetime import datetime
from validators import get_valid_time_input, validate_time

# ---------- MEMBER FUNCTIONS ----------
def register_member(connection):
    print("\n---------Member Registration--------")
    full_name = input("Full name: ")
    dob = None
    while dob is None:
      dob_str = input("Date of birth (YYYY-MM-DD): ")
      try:
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
      except ValueError:
        print("Invalid date format. Try again.")
    gender = input("Gender: ")
    phone = input("Phone: ")

    try:
      with connection.cursor() as cur:
        cur.execute(
          """
          INSERT INTO member (full_name, date_of_birth, gender, phone)
          VALUES (%s, %s, %s, %s)
          RETURNING member_id
          """,
          (full_name, dob, gender, phone),
        )
        member_id = cur.fetchone()[0]
      connection.commit()
      print(f"Member registered successfully, Your Member ID is {member_id}")
    except psycopg2.Error as e:
      connection.rollback()
      print("Registering Members Failed, Error:", e)

def login_member(connection):
  member_id = input("Enter your member ID: ")

  try:
    with connection.cursor() as cur:
      cur.execute(
        """
        SELECT * FROM member WHERE member_id = %s
        """,
        (member_id,),
      )
      row = cur.fetchone()
  except psycopg2.Error as e:
    print(f"Retreiving Info For Member:{member_id} Failed, Error:", e)
    return None

  if row is None:
        print("***Member ID not found***")
        return None

  return row[0]

def update_profile(connection, member_id):
  print("\n--------- Update Member Profile--------")
  full_name = input("Full name: ")
  dob = None
  while dob is None:
    dob_str = input("Date of birth (YYYY-MM-DD): ")
    try:
      dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
    except ValueError:
      print("Invalid date format. Try again.")
  gender = input("Gender: ")
  phone = input("Phone: ")

  try:
    with connection.cursor() as cur:
      cur.execute(
        """
        UPDATE member
        SET full_name     = %s,
            date_of_birth = %s,
            gender        = %s,
            phone         = %s
        WHERE member_id   = %s;
        """,
        (full_name, dob, gender, phone, member_id),
      )
    connection.commit()
    print(f"Profile Updated for Member ID {member_id}")
  except psycopg2.Error as e:
    connection.rollback()
    print("Profile Update Failed, Error:", e)

def update_goal(connection, member_id):
  print("\n--------- Update Goal--------")
  weight = input("Weight in lbs: ")
  target = None

  while target is None:
    target_str = input("Target Date (YYYY-MM-DD): ")
    try:
      target = datetime.strptime(target_str, "%Y-%m-%d").date()
    except ValueError:
      print("Invalid date format. Try again.")

  try:
    with connection.cursor() as cur:
      cur.execute(
        """
        UPDATE fitness_goal
        SET weight        = %s,
            target_date   = %s
        WHERE member_id   = %s;
        """,
        (weight , target, member_id),
      )
      if cur.rowcount == 0:
        cur.execute(
            """
            INSERT INTO fitness_goal (member_id, weight, target_date)
            VALUES (%s, %s, %s)
            """,
            (member_id, weight, target),
        )
    connection.commit()
    print(f"Goal Updated for: {member_id}")
  except psycopg2.Error as e:
    connection.rollback()
    print("Goal Update Failed, Error:", e)

def add_metric(connection, member_id):
  print("\n--------- Add Metric--------")
  height = input("Your Current Height in cm: ")
  weight = input("Your Current Weight in lbs: ")
  heart_rate = input("Your Heart Rate: ")

  try:
    with connection.cursor() as cur:
      cur.execute(
        """
        INSERT INTO health_metric (member_id, height, weight, heart_rate )
        VALUES (%s, %s, %s, %s)
        """,
        (member_id, height, weight, heart_rate),
      )
    connection.commit()
    print(f"Metric Added For Member ID {member_id}")
  except psycopg2.Error as e:
    connection.rollback()
    print("Metric Failed, Error:", e)


def book_training(connection, member_id):
  print("\n--------- Book A Personal Training Session --------")

  # List all trainers and their availability
  try:
    with connection.cursor() as cur:
      cur.execute(
        """
        SELECT trainer_id, full_name, availability_start, availability_end
        FROM trainer
        ORDER BY trainer_id
        """
      )
      trainers = cur.fetchall()
  except psycopg2.Error as e:
    connection.rollback()
    print("Error fetching trainers:", e)
    return

  if not trainers:
    print("No trainers are available")
    return

  print("\nAvailable Trainers:")
  for t_id, name, a_start, a_end in trainers:
    start_str = a_start.strftime("%H:%M")
    end_str = a_end.strftime("%H:%M")
    print(f"- ID {t_id} | {name} | Availability: {start_str} - {end_str}")

  trainer_id = input("Enter Your Trainer's ID: ")

  # Check if trainer exists
  try:
    with connection.cursor() as cur:
      cur.execute(
        """
        SELECT availability_start, availability_end
        FROM trainer
        WHERE trainer_id = %s
        """,
        (trainer_id,),
      )
      row = cur.fetchone()
  except psycopg2.Error as e:
    connection.rollback()
    print("Error checking trainer:", e)
    return
  
  if row is None:
      print(f"Trainer with ID {trainer_id} does not exist.")
      return
  avail_start, avail_end = row

  start_time = get_valid_time_input("Enter start time (HH:MM): ")
  end_time = get_valid_time_input("Enter end time (HH:MM): ")

  if not validate_time(start_time, end_time):
    print("Exited Booking.")
    return
  
  #Check requested slot is within trainer availability
  if start_time < avail_start or end_time > avail_end:
    print( "Requested time is outside trainer's availability.\n")
    return

  # Check trainer does not already have a session that overlaps
  try:
    with connection.cursor() as cur:
      cur.execute(
        """
        SELECT 1
        FROM training_sessions
        WHERE trainer_id = %s
          AND status = 'active'
          AND session_type = 'personal'
          AND NOT (end_time <= %s OR start_time >= %s)
        """,
        (trainer_id, start_time, end_time),
      )
      conflict = cur.fetchone()
  except psycopg2.Error as e:
    connection.rollback()
    print("Error checking for overlapping sessions:", e)
    return

  if conflict:
    print("This trainer already has a session that overlaps this time.")
    return

  #Find an available room, create session, add member
  try:
    with connection.cursor() as cur:
      cur.execute(
        """
        SELECT room_id, room_name
        FROM rooms
        WHERE isBooked = FALSE
        """
      )
      rooms_available = cur.fetchall()

      if not rooms_available:
        print("No rooms are available at this time.")
        return

      room_id, room_name = random.choice(rooms_available)

      cur.execute(
        """
        INSERT INTO training_sessions (trainer_id, room_id,session_type, start_time, end_time, capacity)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING session_id
        """,
        (trainer_id, room_id,'personal', start_time, end_time, 1),
      )
      session_id = cur.fetchone()[0]

      #Add member to session
      cur.execute(
        """
        INSERT INTO session_members (session_id, member_id)
        VALUES (%s, %s)
        """,
        (session_id, member_id),
      )

      # Mark room as booked
      cur.execute(
        """
        UPDATE rooms
        SET isBooked = TRUE
        WHERE room_id = %s
        """,
        (room_id,),
      )
      
    connection.commit()
    print(f"Session Booked ID: {session_id} | Room: {room_name} (RoomID: {room_id})")
    
  except psycopg2.Error as e:
    connection.rollback()
    print("Booking Session Failed, Error:", e)

def reschedule_training(connection, member_id):
  print("\n--------- Reschedule Training Session --------")
  format_rows = get_training_sessions(connection, member_id)
  if not format_rows: 
    return

  session_id = input("Enter Session ID you wanna reschedule: ")

  if session_id not in format_rows:
    print("You don't have access to this session ID")
    return 

  # Get trainer availability for this session
  try:
    with connection.cursor() as cur:
      cur.execute(
        """
        SELECT t.availability_start, t.availability_end
        FROM training_sessions ts
        JOIN trainer t
          ON ts.trainer_id = t.trainer_id
        WHERE ts.session_id = %s
        """,
        (session_id,),
      )
      row = cur.fetchone()
  except psycopg2.Error as e:
    print("Error fetching trainer availability for this session:", e)
    return

  if row is None:
    print("Could not find trainer or session for this ID.")
    return
  
  avail_start, avail_end = row

  start_time = get_valid_time_input("New start time: ")
  end_time = get_valid_time_input("New end time: ")

  if not validate_time(start_time, end_time):
    print("Exited rescheduling.")
    return

  if start_time < avail_start or end_time > avail_end:
    print( "Requested time is outside trainer's availability.\n" )
    return

  #Check for overlapping sessions for this trainer, excluding this session
  try:
    with connection.cursor() as cur:
      cur.execute(
        """
        SELECT 1
        FROM training_sessions ts
        WHERE ts.trainer_id = (
          SELECT trainer_id
          FROM training_sessions
          WHERE session_id = %s
        )
          AND ts.status = 'active'
          AND ts.session_id <> %s
          AND NOT (ts.end_time <= %s OR ts.start_time >= %s)
        """,
        (session_id, session_id, start_time, end_time),
      )
      conflict = cur.fetchone()
  except psycopg2.Error as e:
    connection.rollback()
    print("Error checking for overlapping sessions while rescheduling:", e)
    return

  if conflict:
    print("This new time overlaps with another session for this trainer.")
    return
  
  #Update the session times
  try:
    with connection.cursor() as cur:
      cur.execute(
        """
        UPDATE training_sessions 
        SET start_time = %s, end_time = %s 
        WHERE session_id = %s
        """,
        (start_time, end_time, session_id),
      )
    connection.commit()
    print(f"Session Rescheduled: {session_id}")
    
  except psycopg2.Error as e:
    connection.rollback()
    print("Rescheduling Session Failed, Error:", e)

def cancel_training(connection, member_id):
  format_rows = get_training_sessions(connection, member_id)
  if not format_rows: 
    return
  
  session_id = input("Enter Session ID you wanna cancel: ")

  if session_id not in format_rows:
    print("You don't have access to this session ID")
    return 
  
  try:
    with connection.cursor() as cur:
      cur.execute(
        """
        UPDATE training_sessions SET status = %s WHERE session_id = %s
        RETURNING room_id
        """,
        ('cancelled', session_id),
      )

      row = cur.fetchone()
      if row is None:
          room_id = None
      else:
          room_id = row[0]
      # Mark room as unbooked
      cur.execute(
        """
        UPDATE rooms
        SET isBooked = FALSE
        WHERE room_id = %s
        """,
        (room_id,),
      )
    connection.commit()
    print(f"Session Cancelled: {session_id}")
    
  except psycopg2.Error as e:
    connection.rollback()
    print("Canceling Session Failed, Error:", e)

def join_group(connection, member_id):
  print("\n--------- Join A Group Session --------")

  try:
    with connection.cursor() as cur:
      cur.execute(
        """
          SELECT session_id, start_time, end_time, status, capacity
          FROM training_sessions
          WHERE status = %s AND session_type = %s
        """,
        ('active', 'group'),
      )
      rows = cur.fetchall()
  except psycopg2.Error as e:
    connection.rollback()
    print("Error getting group classes", e)
    return

  if not rows:
    print("No Group Class Scheduled.")
    return

  format_rows = {str(r[0]) for r in rows}

  print("Group Classes Available: ")
  for ses_id, start_time, end_time, status, capacity in rows:
    print(f" {ses_id} | {start_time}-{end_time} | {status} | Max:{capacity}")

  session_id = input("Enter Session ID you want to join: ")

  if session_id not in format_rows:
    print("That session ID is not in the available list.")
    return

  try:
    with connection.cursor() as cur:
      # Check if user already in this session
      cur.execute(
        """
          SELECT 1
          FROM session_members
          WHERE session_id = %s AND member_id = %s
        """,
        (session_id, member_id),
      )
      already = cur.fetchone()
      if already:
        print("You have already joined this class.")
        return

      # Optional: check capacity
      cur.execute(
        """
          SELECT capacity
          FROM training_sessions
          WHERE session_id = %s
        """,
        (session_id,),
      )
      row = cur.fetchone()
      if row is None:
        print("Session no longer exists.")
        return
      capacity = row[0]

      cur.execute(
        """
          SELECT COUNT(*) 
          FROM session_members
          WHERE session_id = %s
        """,
        (session_id,),
      )
      current_count = cur.fetchone()[0]
      if current_count >= capacity:
        print("This class is already full.")
        return

      # Insert membership
      cur.execute(
        """
        INSERT INTO session_members (session_id, member_id) 
        VALUES (%s, %s)
        """,
        (session_id, member_id),
      )

    connection.commit()
    print(f"Successfully Added Member:{member_id} into Session: {session_id}")

  except psycopg2.Error as e:
    connection.rollback()
    print("Inserting Member Into Session Failed, Error:", e)

#Helper funtion
def get_training_sessions(connection, member_id):
  try:
    with connection.cursor() as cur:
      cur.execute(
          """
            SELECT session_members.session_id, ts.start_time, ts.end_time, ts.status, ts.room_id, r.room_name
            FROM session_members JOIN training_sessions ts
              ON session_members.session_id = ts.session_id
            JOIN rooms r
              ON ts.room_id = r.room_id
            WHERE session_members.member_id = %s AND ts.status = %s AND ts.session_type = 'personal'
          """,
          (member_id, 'active'),
      )
      rows = cur.fetchall()
    if not rows:  # empty list means no bookings
      print("You don't have any bookings scheduled.")
      return

    print("Your Active Bookings: ")
    for session_id, start_time, end_time, status, room_id, room_name in rows:
      if room_id is None:
        room_id = "TBD"
      print(f"{session_id} | {start_time}-{end_time} | {room_id}-{room_name} | {status}")

    format_rows = {str(r[0]) for r in rows}
    return format_rows
  except psycopg2.Error as e:
    connection.rollback()
    print(f"Error checking sessions for member: {member_id}", e)
    return
  
def view_dashboard(connection, member_id):
  print("\n========= Member Dashboard =========")
  try:
    with connection.cursor() as cur:
      #Basic member info
      cur.execute(
        """
        SELECT full_name, date_of_birth, phone, gender
        FROM member
        WHERE member_id = %s
        """,
        (member_id,),
      )
      member_row = cur.fetchone()

      if member_row is None:
        print(f"Member with ID {member_id} does not exist.")
        return

      full_name, dob, phone, gender = member_row

      #Latest health metric
      cur.execute(
        """
        SELECT height, weight, heart_rate, date
        FROM health_metric
        WHERE member_id = %s
        ORDER BY date DESC
        LIMIT 1
        """,
        (member_id,),
      )
      metric_row = cur.fetchone()

      #Latest fitness goal
      cur.execute(
        """
        SELECT weight, target_date
        FROM fitness_goal
        WHERE member_id = %s
        """,
        (member_id,),
      )
      goal_row = cur.fetchone()

      # 4) Active sessions (personal + group)
      cur.execute(
        """
        SELECT ts.session_id,
               ts.session_type,
               ts.start_time,
               ts.end_time,
               ts.status,
               r.room_name,
               t.full_name
        FROM session_members sm
        JOIN training_sessions ts
          ON sm.session_id = ts.session_id
        LEFT JOIN rooms r
          ON ts.room_id = r.room_id
        JOIN trainer t
          ON ts.trainer_id = t.trainer_id
        WHERE sm.member_id = %s
          AND ts.status = 'active'
        ORDER BY ts.start_time
        """,
        (member_id,),
      )
      sessions = cur.fetchall()

      #Invoices + payments summary
      cur.execute(
        """
        SELECT invoice_id,
              issue_date,
              total_amount,
              total_paid,
              remaining,
              status
        FROM member_invoice_summary
        WHERE member_id = %s
        ORDER BY issue_date DESC
        """,
        (member_id,),
      )
      invoices = cur.fetchall()

  except psycopg2.Error as e:
    print("Error loading dashboard:", e)
    return

  # ---- Print section: Profile ----
  print(f"\nMember: {full_name} (ID: {member_id})")
  print(f"Date of Birth: {dob}")
  print(f"Gender: {gender}")
  print(f"Phone: {phone}")

  # ---- Latest Health Metric ----
  print("\n--- Latest Health Metric ---")
  if metric_row is None:
    print("No health metrics recorded yet.")
  else:
    height, weight, heart_rate, metric_date = metric_row
    print(f"Recorded on: {metric_date}")
    print(f"Height: {height} cm")
    print(f"Weight: {weight} lbs")
    print(f"Heart Rate: {heart_rate} bpm")

  # Fitness Goal
  print("\n--- Fitness Goal ---")
  if goal_row is None:
    print("No fitness goal set yet.")
  else:
    goal_weight, target_date = goal_row
    print(f"Target Weight: {goal_weight}")
    print(f"Target Date: {target_date}")

  # Active Sessions
  print("\n--- Active Sessions ---")
  if not sessions:
    print("No active training sessions booked.")
  else:
    for session_id, session_type, start_time, end_time, status, room_name, trainer_name in sessions:
      room_label = room_name if room_name is not None else "No room assigned"
      print(
        f"- Session ID {session_id} | {session_type} | "
        f"{start_time}-{end_time} | Room: {room_label} | Trainer: {trainer_name} | Status: {status}"
      )

  #Invoices / Payments
  print("\n--- Billing ---")
  if not invoices:
    print("No invoices on file.")
  else:
    overall_outstanding = 0.0
    for invoice_id, issue_date, total_amount, total_paid , remaining, status in invoices:
      remaining = float(total_amount) - float(total_paid)
      if status != 'cancelled' and remaining > 0:
        overall_outstanding += remaining
      print(
        f"- Invoice {invoice_id} | Date: {issue_date} | "
        f"Total: {total_amount} | Paid: {total_paid} | Status: {status} | Remaining: {remaining:.2f}"
      )

    print(f"\nTotal Outstanding Balance: {overall_outstanding:.2f}")
