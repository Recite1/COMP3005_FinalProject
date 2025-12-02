import psycopg2
from datetime import datetime
from app.validators import get_valid_time_input, validate_time

def register_trainer(connection):
    print("\n---------Trainer Registration--------")
    full_name = input("Full name: ")
    phone = input("Phone#: ")
    availability_start = get_valid_time_input("Availability start time (HH:MM): ")
    availability_end   = get_valid_time_input("Availability end time   (HH:MM): ")

    if not validate_time(availability_start, availability_end):
      print("Registration cancelled.")
      return

    try:
      with connection.cursor() as cur:
        cur.execute(
          """
          INSERT INTO trainer (full_name, phone, availability_start, availability_end)
          VALUES (%s, %s, %s, %s)
          RETURNING trainer_id
          """,
          (full_name, phone, availability_start, availability_end),
        )
        trainer_id = cur.fetchone()[0]
      connection.commit()
      print(f"Trainer registered successfully with ID: {trainer_id}\n")
    except psycopg2.Error as e:
      connection.rollback()
      print("Registering Trainer Failed, Error:", e)

def login_trainer(connection):
  trainer_id = input("Enter your trainer ID: ")

  try:
    with connection.cursor() as cur:
      cur.execute(
        """
        SELECT * FROM trainer WHERE trainer_id = %s
        """,
        (trainer_id,),
      )
      row = cur.fetchone()
  except psycopg2.Error as e:
    connection.rollback()
    print(f"Retreiving Info For Trainer:{trainer_id} Failed, Error:", e)
    return None

  if row is None:
      print("***Trainer ID not found***")
      return None
  return row[0]

def view_sessions(connection, trainer_id):
  print("\n------------ Your Upcoming Sessions ----------")
  try:
    with connection.cursor() as cur:
      cur.execute(
        """
        SELECT ts.session_id, ts.start_time, ts.end_time, ts.status, r.room_name, ts.session_type
        FROM training_sessions ts JOIN rooms r
          ON ts.room_id = r.room_id
        WHERE ts.trainer_id = %s AND ts.status = 'active' AND ts.session_type = 'personal'
        ORDER BY ts.start_time
        """,
        (trainer_id,),
      )

      rows = cur.fetchall()
    if not rows:
      print("you don't have any sessions scheduled")
      return

    for session_id, start_time, end_time, status, room_name, session_type in rows:
        print(f"{session_id} | {start_time}-{end_time} | room_name: {room_name} | {session_type} |{status}")

  except psycopg2.Error as e:
    connection.rollback()
    print(f"Error fetching sessions for trainer {trainer_id}:", e)

def view_classes(connection, trainer_id):
  print("\n------------ Your Upcoming Classes ----------")
  try:
    with connection.cursor() as cur:
      cur.execute(
        """
        SELECT session_id, start_time, end_time, status, r.room_name
        FROM training_sessions ts JOIN rooms r
          ON ts.room_id = r.room_id
        WHERE trainer_id = %s AND status = 'active' AND session_type = 'group'
        ORDER BY start_time
        """,
        (trainer_id,),
      )

      rows = cur.fetchall()
    if not rows:
      print("you don't have any classes scheduled")
      return

    for session_id, start_time, end_time, status, room_name in rows:
        print(f"{session_id} | {start_time}-{end_time} | Room_name: {room_name} | {status}")

  except psycopg2.Error as e:
    connection.rollback()
    print(f"Error fetching sessions for trainer {trainer_id}:", e)

def member_lookup(connection, trainer_id):
  print("\n------------ Member Lookup ----------")

  try:
    with connection.cursor() as cur:
      cur.execute(
        """
        SELECT DISTINCT m.member_id, m.full_name
        FROM session_members sm JOIN training_sessions ts
          ON sm.session_id = ts.session_id
        JOIN member m
          ON sm.member_id = m.member_id
        WHERE ts.trainer_id = %s AND ts.status = 'active'
        ORDER BY m.member_id
        """,
        (trainer_id,),
      )
      rows = cur.fetchall()
  except psycopg2.Error as e:
    connection.rollback()
    print(f"Error looking up members for trainer {trainer_id}:", e)
    return

  if not rows:
      print("You don't have any members assigned to your sessions.")
      return

  print("Members in your sessions:")
  for member_id, full_name in rows:
      print(f"- ID: {member_id} | Name: {full_name}")

  format_ids = {str(member_id) : full_name for member_id, full_name in rows}
  selected_member_id = input("Enter the member ID you wanna lookup: ")
  if selected_member_id not in format_ids:
    print("You don't have access to this member ID")
    return 
  
  view_member(connection, trainer_id, selected_member_id , format_ids[selected_member_id])

def view_member(connection, trainer_id, member_id, member_name):
  print(f"\n------------ Member Profile (ID: {member_id}) ----------")

  try:
    with connection.cursor() as cur:
      # Basic member profile
      cur.execute(
        """
        SELECT member_id, weight, target_date
        FROM fitness_goal
        WHERE member_id = %s
        """,
        (member_id,),
      )
      fitness_goal = cur.fetchone()

      cur.execute(
        """
        SELECT member_id, height, weight, heart_rate, date
        FROM health_metric
        WHERE member_id = %s
        """,
        (member_id,),
      )
      health_metric = cur.fetchall()
  except psycopg2.Error as e:
    connection.rollback()
    print("Error fetching member details:", e)
    return
  
  if not fitness_goal:
    print("This member has not assigned any fitness goal")
  else:
    member_id, weigtht, target_date = fitness_goal
    print(f"Current Fitness Goal for {member_name}({member_id}) | weigtht(lbs): {weigtht} | target_date: {target_date}")

  if not health_metric:
      print("This member has not assigned any health metrics")
  else: 
    for member_id, height, weigtht, heart_rate, date in health_metric: 
      print(f"Health Metrics for {member_name}({member_id}) | height(cm): {height} | weigtht(lbs): {weigtht} | heart_rate: {heart_rate} | date: {date}")

def set_availability(connection, trainer_id):
  print("\n--------- Set Trainer Availability --------")

  start_time = get_valid_time_input("Availability start time (HH:MM): ")
  end_time   = get_valid_time_input("Availability end time   (HH:MM): ")

  if not validate_time(start_time, end_time):
      print("Set Availability cancelled.")
      return

  try:
    with connection.cursor() as cur:
      cur.execute(
        """
        UPDATE trainer
        SET availability_start = %s,
            availability_end   = %s
        WHERE trainer_id = %s
        """,
        (start_time, end_time, trainer_id),
      )

      if cur.rowcount == 0:
        print(f"No trainer found with ID {trainer_id}.")
        connection.rollback()
        return

    connection.commit()
    print(f"Availability updated: {start_time} - {end_time}")

  except psycopg2.Error as e:
    connection.rollback()
    print("Updating availability failed, Error:", e)

  





