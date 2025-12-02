from datetime import datetime

def get_valid_time_input(p):
  while True:
    time = input(p)
    try:
        if time == '0':
          return 0
        return datetime.strptime(time, "%H:%M").time()
    except ValueError:
        print("Invalid time format. Format should be in HH:MM. Try Again or type 0 to exit")

def validate_time(start_time, end_time):
  if start_time == 0 or end_time == 0:
    print(f"Exited.")
    return False
  
  if end_time <= start_time:
    print("End time must be AFTER start time.")
    return False

  return True