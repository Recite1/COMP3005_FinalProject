from member import register_member, login_member, update_profile, update_goal, add_metric, book_training, reschedule_training,cancel_training, join_group, view_dashboard
from trainer import register_trainer, login_trainer, view_sessions, view_classes, member_lookup, set_availability
from admin import add_room, create_class, create_invoice, record_payment, add_equipment, list_equipment, update_equipment_issues
from database import get_connection, remove_connection 
   
def main():
    connection = get_connection()

    while True:
        print("\n === Health and Fitness Club Management System ===")
        print("1) Register as Member")
        print("2) Register as Trainer")
        print("3) Login as Member")
        print("4) Login as Trainer")
        print("5) Access Administrative Panel")
        print("0) Exit")
        choice = input("Enter: ")

        if choice == '1':
          register_member(connection)
        elif choice == '2':
          register_trainer(connection)
        elif choice == '3':
          member_id = login_member(connection)
          if member_id is not None:
            member_menu(connection, member_id)
        elif choice == '4':
          trainer_id = login_trainer(connection)
          if trainer_id is not None:
            trainer_menu(connection, trainer_id)
        elif choice == '5':
          admin_menu(connection)
        elif choice == '0':
           break
      
    remove_connection(connection)
    
def member_menu(connection, member_id):
    while True:
        print("\n=== Member Menu ===")
        print("1) View Dashboard")
        print("2) Update Profile")
        print("3) Update Goal")
        print("4) Add health metric")
        print("5) Book Training Session")
        print("6) Reschedule Training Session")
        print("7) Cancel Training Session")
        print("8) Join A Group Training Class")
        print("0) Back to main menu")
        choice = input("Enter: ")

        if choice == '1':
          view_dashboard(connection, member_id)
        elif choice == '2':
          update_profile(connection, member_id)
        elif choice == '3':
          update_goal(connection, member_id)
        elif choice == '4':
          add_metric(connection, member_id)
        elif choice == '5':
          book_training(connection, member_id)
        elif choice == '6':
          reschedule_training(connection, member_id)
        elif choice == '7':
          cancel_training(connection, member_id)
        elif choice == '8':
          join_group(connection, member_id)
        elif choice == '0':
          break


def trainer_menu(connection, trainer_id):
    while True:
        print("\n=== Trainer Menu ===")
        print("1) Set availability")
        print("2) View Upcoming Personal Sessions")
        print("3) View Upcoming Classes")
        print("4) Member lookup")
        print("0) Back to main menu")
        choice = input("Enter: ")

        if choice == '1':
          set_availability(connection, trainer_id)
        elif choice == '2':
          view_sessions(connection, trainer_id)
        elif choice == '3':
          view_classes(connection, trainer_id)
        elif choice == '4':
          member_lookup(connection, trainer_id)
        elif choice == '0':
          break


def admin_menu(connection):
    while True:
        print("\n=== Admin Menu ===")
        print("1) Add room ")
        print("2) Create fitness class")
        print("3) Add Equipment")
        print("4) List Equipment")
        print("5) Update equipment issues")
        print("6) Create invoice")
        print("7) Record payment")
        print("0) Back to main menu")
        choice = input("Enter: ")

        if choice == '1':
          add_room(connection)
        elif choice == '2':
          create_class(connection)
        elif choice == '3':
          add_equipment(connection)
        elif choice == '4':
          list_equipment(connection)
        elif choice == '5':
          update_equipment_issues(connection)
        elif choice == '6':
          create_invoice(connection)
        elif choice == '7':
          record_payment(connection)
        elif choice == '0':
          break
           
           


if __name__ == "__main__":
    main()