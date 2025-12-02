import psycopg2
from app.validators import get_valid_time_input, validate_time

def add_room(connection):
  room_name = input("Room name: ")
  capacity = input("Capacity: ")

  try:
    with connection.cursor() as cur:
      cur.execute(
        """
        INSERT INTO rooms (room_name, capacity)
        VALUES(%s, %s)
        RETURNING room_id
        """,
        (room_name, capacity),
      )
      room_id = cur.fetchone()[0]
    connection.commit()
    print(f"Added Room with ID: {room_id}")
  except psycopg2.Error as e:
    connection.rollback()
    print("Adding Room Failed, Error:", e)

def create_class(connection):
  trainer_id = input("Assign Trainer by ID: ")
  room_id = input("Select Room by ID: ")
  capacity = input("What is the max capacity of this class: ")
  start_time = get_valid_time_input("Start Time(HH:MM): ")
  end_time = get_valid_time_input("End Time (HH:MM): ")

  if not validate_time(start_time, end_time):
    return
  
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

  #Check requested slot is within trainer availability
  if start_time < avail_start or end_time > avail_end:
    print( "Requested time is outside trainer's availability.\n")
    return

  # Check for overlapping sessions for this trainer (any active session)
  try:
    with connection.cursor() as cur:
      cur.execute(
        """
        SELECT 1
        FROM training_sessions
        WHERE trainer_id = %s
          AND status = 'active'
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
  
  # Check if room is already used
  try:
    with connection.cursor() as cur:
      cur.execute(
        """
        SELECT isBooked
        FROM rooms
        WHERE room_id = %s
        """,
        (room_id,),
      )
      row = cur.fetchone()
      if row is None:
        print(f"Room ID {room_id} does not exist.")
        return
      isBooked = row[0]
  except psycopg2.Error as e:
    connection.rollback()
    print("Error checking trainer:", e)
    return
  
  if isBooked:
    print(f"Room ID {room_id} is already booked")
    return
  
  try:
    with connection.cursor() as cur:
      cur.execute(
        """
        INSERT INTO training_sessions (trainer_id, room_id, session_type, start_time, end_time, status, capacity)
        VALUES(%s, %s, %s, %s, %s, %s, %s)
        RETURNING session_id
        """,
        (trainer_id, room_id, 'group', start_time, end_time, 'active', capacity),
      )
      session_id = cur.fetchone()[0]

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
    print(f"Class Created with ID: {session_id}")
  except psycopg2.Error as e:
    connection.rollback()
    print("Failed Creating a class, Error:", e)

def create_invoice(connection):
  print("\n--------- Create Invoice --------")
  member_id = input("Enter Member ID to bill: ")
  amount = input("Enter total amount: ")

  # Check member exists
  try:
    with connection.cursor() as cur:
      cur.execute(
          "SELECT 1 FROM member WHERE member_id = %s",
          (member_id,),
      )
      row = cur.fetchone()
    if row is None:
      print(f"Member with ID {member_id} does not exist.")
      return
  except psycopg2.Error as e:
    print("Error checking member:", e)
    return

  # Create the invoice
  try:
    with connection.cursor() as cur:
      cur.execute(
        """
        INSERT INTO invoice (member_id, total_amount)
        VALUES (%s, %s)
        RETURNING invoice_id
        """,
        (member_id, amount),
      )
      invoice_id = cur.fetchone()[0]
    connection.commit()
    print(f"Invoice created: ID {invoice_id} for Member {member_id}, Amount(CAD): {amount}")
  except psycopg2.Error as e:
    connection.rollback()
    print("Creating invoice failed, Error:", e)

def record_payment(connection):
  print("\n--------- Record Payment --------")
  invoice_id = input("Enter Invoice ID: ").strip()
  amount_str = input("Enter payment amount: ").strip()
  method = input("Enter payment method (e.g., cash, card): ").strip()

  # Validate amount
  try:
    amount = float(amount_str)
  except ValueError:
    print("Amount must be a valid number.")
    return

  if amount <= 0:
    print("Amount must be greater than 0.")
    return

  #Check invoice exists and get its info
  try:
    with connection.cursor() as cur:
      cur.execute(
        """
        SELECT total_amount, status
        FROM invoice
        WHERE invoice_id = %s
        """,
        (invoice_id,),
      )
      row = cur.fetchone()
  except psycopg2.Error as e:
    print(f"Error fetching invoice {invoice_id}:", e)
    return

  if row is None:
    print(f"Invoice with ID {invoice_id} does not exist.")
    return

  total_amount, status = row

  if status == 'cancelled':
    print("Cannot record payment on a cancelled invoice.")
    return

  if status == 'paid':
    print("This invoice is already fully paid.")
    return

  #Check how much has already been paid
  try:
    with connection.cursor() as cur:
      cur.execute(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM payment
        WHERE invoice_id = %s
        """,
        (invoice_id,),
      )
      paid_so_far = cur.fetchone()[0]
  except psycopg2.Error as e:
    print("Error checking existing payments:", e)
    return

  remaining = float(total_amount) - float(paid_so_far)

  if amount > remaining:
    print(f"Cannot Process, payment exceeds remaining balance. Remaining: {remaining}")
    return

  #Insert payment and update invoice status if fully paid
  try:
    with connection.cursor() as cur:
      cur.execute(
        """
        INSERT INTO payment (invoice_id, amount, method)
        VALUES (%s, %s, %s)
        """,
        (invoice_id, amount, method),
      )

      # Recompute remaining after this payment
      new_remaining = remaining - amount
      if new_remaining == 0:
        cur.execute(
          """
          UPDATE invoice
          SET status = 'paid'
          WHERE invoice_id = %s
          """,
          (invoice_id,),
        )

    connection.commit()
    if new_remaining == 0:
      print(f"Payment recorded. Invoice {invoice_id} is now PAID.")
    else:
      print(
        f"Payment recorded. Remaining balance on invoice {invoice_id}: {new_remaining:.2f}"
      )

  except psycopg2.Error as e:
    connection.rollback()
    print("Recording payment failed, Error:", e)

def add_equipment(connection):
  print("\n--------- Add Equipment --------")
  room_id = input("Room ID: ")
  eq_type = input("Equipment type: ")

  try:
    with connection.cursor() as cur:
      cur.execute(
        """
        SELECT *
        FROM rooms
        WHERE room_id = %s
        """,
        (room_id,),
      )
      row = cur.fetchone()
      if row is None:
        print(f"Room ID {room_id} does not exist.")
        return
      
      cur.execute(
        """
        INSERT INTO equipment (room_id, type, status)
        VALUES (%s, %s, %s)
        RETURNING equipment_id
        """,
        (room_id, eq_type, 0),
      )
      equipment_id = cur.fetchone()[0]
    connection.commit()
    print(f"Equipment added with ID {equipment_id}")
  except psycopg2.Error as e:
    connection.rollback()
    print("Adding equipment failed:", e)

def update_equipment_issues(connection):
  list_equipment(connection)
  print("\n--------- Log Equipment Issue --------")
  equipment_id = input("Enter equipment ID: ").strip()

  # 1) Check that equipment exists
  try:
    with connection.cursor() as cur:
      cur.execute(
        """
        SELECT type, status
        FROM equipment
        WHERE equipment_id = %s
        """,
        (equipment_id,),
      )
      row = cur.fetchone()
  except psycopg2.Error as e:
    print(f"Error fetching equipment {equipment_id}:", e)
    return

  if row is None:
    print(f"Equipment with ID {equipment_id} does not exist.")
    return

  print("\nSet new status code for this equipment")
  print("  0 = operational")
  print("  1 = needs maintenance")
  print("  2 = out of order")

  status_str = input("Enter new status code: ")
  try:
    new_status = int(status_str)
  except ValueError:
    print("Status must be an integer.")
    return

  # 2) Update equipment status
  try:
    with connection.cursor() as cur:
      cur.execute(
        """
        UPDATE equipment
        SET status = %s
        WHERE equipment_id = %s
        """,
        (new_status, equipment_id),
      )
    connection.commit()
    print(f"Equipment {equipment_id} status updated to {new_status}.")
  except psycopg2.Error as e:
    connection.rollback()
    print("Updating equipment status failed, Error:", e)

def list_equipment(connection):
  print("\n--------- Equipment ----------")
  try:
    with connection.cursor() as cur:
      cur.execute(
        """
        SELECT equipment_id, room_id, type, status
        FROM equipment
        ORDER BY equipment_id
        """
      )
      rows = cur.fetchall()
  except psycopg2.Error as e:
    print("Error fetching equipment:", e)
    return

  if not rows:
    print("No equipment found.")
    return

  for eq_id, room_id, eq_type, status in rows:
    if status == 0:
      status = "Operational"
    elif status == 1:
      status = "needs maintenance"
    elif status == 2:
      status = "out of order"
    else:
      status = "N/A"

    print(f"- ID {eq_id} | Room {room_id} | {eq_type} | Status: {status}")