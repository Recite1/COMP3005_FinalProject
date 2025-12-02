# COMP3005 Final Project (AnthonyLin 101250297)

**Language:** Python
**Library:** psycopg2
**DB:** PostgreSQL  

**Yotube Video Link: ** https://www.youtube.com/watch?v=GgsHWR2Avl8
---
## SETPUP INSTRUCTIONS
## 1. Create and populate the database

Set up PostgreSQL and create a database

Use the schema DDL.sql to create your tables in PostgreSQL

Load the table with the SQL command in DML.sql

## 2. App configuration
In your python enviroment make sure to install psycopg2 with `pip install psycopg2` 

In the get_connection() function in app.py make sure to change the values with your actual host, dbname, user, password and port

## 3. Report
This project implements a Fitness Club Management System using a PostgreSQL relational database and also uses the command-line as the user interface.

## Core Features For Each Role

### Member

- **Register & Login**
  - Insert into `member` table 
  - login checks existence by the `member_id`
- **Profile Management**
  - Allow the user to update profile information like `full_name`, `phone`
- **Fitness Goal & Health Metrics**
  - Insert metrics into `health_metric`, this is stored historically
  - Allow the user to add a `fitness_goal`, each record is unique with `member_id`
- **Personal Sessions**
  - List trainers and their availability
  - Book a session:
    - Ensure no overlapping with trainer
    - Random room is selected
  - Reschedule/cancel only their own active sessions
- **Group Classes**
  - View active group sessions and join if
    - session not full
    - member not already enrolled
- **Dashboard**
  - `member` info
  - latest `health_metric`
  - `fitness_goal`
  - active sessions with trainer and room
  - invoices and payments via `member_invoice_summary`

### Trainer

- **Register Trainer**
  - Insert into `trainer` with availability
- **Set Availability**
  - Update `availability_start` and `availability_end`
- **View Sessions**
  - List personal and group sessions where `trainer_id` matches
- **Member Lookup**
  - Get members from sessions they have classes with and show
    - member profile
    - fitness goal

### Admin

- **Rooms & Equipment**
  - Add rooms
  - Log/update equipment in `equipment` and status field (e.g., 0 = operational, 1 = needs maintenance, 2 = out of order).
- **Create Group Classes**
  - Select trainer, room, capacity, time window.
  - Enforce trainer availability and no overlap using the same time-overlap query.
  - Insert into `training_sessions` with `session_type = 'group'`.
- **Billing**
  - Create invoices in `invoice`.
  - Record payments into `payment`.
  - Trigger automatically updates `invoice.status` based on total payments.





