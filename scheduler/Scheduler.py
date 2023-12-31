from model.Vaccine import Vaccine
from model.Caregiver import Caregiver
from model.Patient import Patient
from util.Util import Util
from db.ConnectionManager import ConnectionManager
import pymssql
import datetime


'''
objects to keep track of the currently logged-in user
Note: it is always true that at most one of currentCaregiver and currentPatient is not null
        since only one user can be logged-in at a time
'''
current_patient = None

current_caregiver = None


def create_patient(tokens):
    if len(tokens) != 3:
        print("Failed to create user.")
        return

    username = tokens[1]
    password = tokens[2]

    if username_exists_patient(username):
        print("Username taken, try again!")
        return
    
    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    patient = Patient(username, salt=salt, hash=hash)

    try:
        patient.save_to_db()
    except pymssql.Error as e:
        print("Failed to create user.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Failed to create user.")
        print(e)
        return
    print("Created user ", username)


def create_caregiver(tokens):
    # create_caregiver <username> <password>
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Failed to create user.")
        return

    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists_caregiver(username):
        print("Username taken, try again!")
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the caregiver
    caregiver = Caregiver(username, salt=salt, hash=hash)

    # save to caregiver information to our database
    try:
        caregiver.save_to_db()
    except pymssql.Error as e:
        print("Failed to create user.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Failed to create user.")
        print(e)
        return
    print("Created user ", username)


def username_exists_caregiver(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Caregivers WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when checking username")
        print("Error:", e)
    finally:
        cm.close_connection()
    return False


def username_exists_patient(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Patients WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when checking username")
        print("Error:", e)
    finally:
        cm.close_connection()
    return False


def login_patient(tokens):
    global current_patient
    if current_caregiver is not None or current_patient is not None:
        print("User already logged in.")
        return

    if len(tokens) != 3:
        print("Login failed.")
        return

    username = tokens[1]
    password = tokens[2]

    patient = None
    try:
        patient = Patient(username, password=password).get()
    except pymssql.Error as e:
        print("Login failed.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Login failed.")
        print("Error:", e)
        return

    if patient is None:
        print("Login failed.")
    else:
        print("Logged in as: " + username)
        current_patient = patient


def login_caregiver(tokens):
    # login_caregiver <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_caregiver
    if current_caregiver is not None or current_patient is not None:
        print("User already logged in.")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Login failed.")
        return

    username = tokens[1]
    password = tokens[2]

    caregiver = None
    try:
        caregiver = Caregiver(username, password=password).get()
    except pymssql.Error as e:
        print("Login failed.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Login failed.")
        print("Error:", e)
        return

    # check if the login was successful
    if caregiver is None:
        print("Login failed.")
    else:
        print("Logged in as: " + username)
        current_caregiver = caregiver


def search_caregiver_schedule(tokens):
    # Check if an user has loged in
    global current_caregiver, current_patient
    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return
    # Check if the length for the tokens is 2 
    if len(tokens) != 2:
        print("Please try again!")
        return
    # read the date 
    date = tokens[1]
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    
    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict=True)

    get_avaiable_caregiver = "SELECT Username FROM Availabilities WHERE Time = %s"
    get_vaccines = "SELECT Name, Doses FROM Vaccines"

    try:
        d = datetime.datetime(year, month, day)
        cursor.execute(get_avaiable_caregiver, d)
        print("Available Caregivers:")
        for row in cursor:
            print(str(row['Username']))
        print()
        print("Remaining Vaccines:")
        cursor.execute(get_vaccines)
        for row in cursor:
           print(str(row['Name']) + ' ' + str(row['Doses']))
    except pymssql.Error:
        print("Please try again!")
        quit()
    except ValueError:
        print("Please try again!")
        return
    except Exception:
        print("Please try again!")
        return
    finally:
        cm.close_connection()


def reserve(tokens):
    # check if a patient has loged in 
    global current_caregiver, current_patient
    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return
    if current_patient is None:
        print("Please login as a patient!")
        return
    
    # check if the length for tokens is exactly 3
    if len(tokens) != 3:
        print("Please try again!")
        return
    
    date = tokens[1]
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])

    vaccine = tokens[2]

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict=True)

    get_caregiver = "SELECT TOP 1 Username FROM Availabilities WHERE Time = %s"
    get_doses = "SELECT Doses FROM Vaccines WHERE Name = %s"
    make_appointment = "INSERT INTO Appointment VALUES (%s, %s, %s, %s)"
    update_availability = "DELETE FROM Availabilities WHERE Time = %s AND Username = %s"
    update_doses = "UPDATE Vaccines SET Doses = %s WHERE Name = %s"
    appointment_id = "SELECT AppID FROM Appointment WHERE Time = %s AND Patient = %s"
    try:
        d = datetime.datetime(year, month, day)
        cursor.execute(get_caregiver, d)
        for row in cursor:
            caregiver = row["Username"]
        if not caregiver:
            print("No caregiver is available!")
            return
        cursor.execute(get_doses, vaccine)
        for row in cursor:
            doses = row["Doses"]
        if doses == 0:
            print("Not enough available doses!")
            return
        cursor.execute(make_appointment, (current_patient.get_username(), d, vaccine, caregiver))
        cursor.execute(update_doses, (doses - 1, vaccine))
        cursor.execute(appointment_id, (d, current_patient.get_username()))
        for row in cursor:
            appid = row["AppID"]
        print("Appointment ID: " + str(appid) + ", Caregiver username: "+ caregiver)
        cursor.execute(update_availability, (d, caregiver))
        conn.commit()
    except pymssql.Error:
        print("Please try again!")
        quit()
    except ValueError:
        print("Please try again!")
        return
    except Exception:
        print("Please try again!")
        return
    finally:
        cm.close_connection()


def upload_availability(tokens):
    #  upload_availability <date>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please try again!")
        return

    date = tokens[1]
    # assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    try:
        d = datetime.datetime(year, month, day)
        current_caregiver.upload_availability(d)
    except pymssql.Error as e:
        print("Upload Availability Failed")
        print("Db-Error:", e)
        quit()
    except ValueError:
        print("Please enter a valid date!")
        return
    except Exception as e:
        print("Error occurred when uploading availability")
        print("Error:", e)
        return
    print("Availability uploaded!")


def cancel(tokens):
    # Check if an user has loged in
    global current_caregiver, current_patient
    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return
    
    # check if the length for tokens is exactly 2 
    if len(tokens) != 2:
        print("Please try again!")
        return
    
    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict=True)
    
    appid = tokens[1]
    search_appointment = "SELECT * FROM Appointment WHERE AppID = %s"
    get_doses = "SELECT Doses FROM Vaccines WHERE Name = %s"
    cancel_appointment = "DELETE FROM Appointment WHERE AppID = %s"
    update_availability = "INSERT INTO Availabilities VALUES (%s, %s)"
    update_doses = "UPDATE Vaccines SET Doses = %s WHERE Name = %s"

    try:
        cursor.execute(search_appointment, appid)
        if current_patient is not None: 
            for row in cursor:
                if row["Patient"] != current_patient.get_username():
                    print("The appointment ID does not match your name!")
                    return
                else:
                    caregiver = row["Caregiver"]
                    time = row["Time"]
                    vaccine = row["VaccName"]
            cursor.execute(cancel_appointment, appid)
            cursor.execute(get_doses, vaccine)
            for row in cursor:
                doses = row["Doses"]
            cursor.execute(update_doses, (doses + 1, vaccine))
            cursor.execute(update_availability, (time, caregiver))
            conn.commit()
            print("You have successfully canceled your appointment with " + str(caregiver))
        else:
            for row in cursor:
                if row["Caregiver"] != current_caregiver.get_username():
                    print("The appointment ID does not match your name!")
                    return
                else:
                    patient = row["Patient"]
                    time = row["Time"]
            cursor.execute(cancel_appointment, appid)
            cursor.execute(update_availability, (time, current_caregiver.get_username()))
            conn.commit()
            print("You have successfully canceled your appointment for " + str(patient))
    except pymssql.Error:
        print("Please try again!")
        quit()
    except ValueError:
        print("Please try again!")
        return
    except Exception:
        print("Please try again!")
        return
    finally:
        cm.close_connection()

def add_doses(tokens):
    #  add_doses <vaccine> <number>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    #  check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    vaccine_name = tokens[1]
    doses = int(tokens[2])
    vaccine = None
    try:
        vaccine = Vaccine(vaccine_name, doses).get()
    except pymssql.Error as e:
        print("Error occurred when adding doses")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when adding doses")
        print("Error:", e)
        return

    # if the vaccine is not found in the database, add a new (vaccine, doses) entry.
    # else, update the existing entry by adding the new doses
    if vaccine is None:
        vaccine = Vaccine(vaccine_name, doses)
        try:
            vaccine.save_to_db()
        except pymssql.Error as e:
            print("Error occurred when adding doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when adding doses")
            print("Error:", e)
            return
    else:
        # if the vaccine is not null, meaning that the vaccine already exists in our table
        try:
            vaccine.increase_available_doses(doses)
        except pymssql.Error as e:
            print("Error occurred when adding doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when adding doses")
            print("Error:", e)
            return
    print("Doses updated!")


def show_appointments(tokens):
    # Check if an user has loged in
    global current_caregiver, current_patient
    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return
    
    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict=True)

    caregiver_app = "SELECT AppID, VaccName, Time, Patient FROM Appointment WHERE \
        Caregiver = %s ORDER BY AppID"
    patient_app = "SELECT AppID, VaccName, Time, Caregiver FROM Appointment WHERE \
        Patient = %s ORDER BY AppID"
    
    try:
        if current_caregiver is not None:
            cursor.execute(caregiver_app, current_caregiver.get_username())
            for row in cursor:
                print(str(row["AppID"]) + ' ' + str(row["VaccName"]) + ' ' + \
                    str(row["Time"]) + ' ' + str(row["Patient"]))

        if current_patient is not None:
            cursor.execute(patient_app, current_patient.get_username())
            for row in cursor:
                print(str(row["AppID"]) + ' ' + str(row["VaccName"]) + ' ' + \
                    str(row["Time"]) + ' ' + str(row["Caregiver"]))
    except pymssql.Error:
        print("Please try again!")
        quit()
    except ValueError:
        print("Please try again!")
        return
    except Exception:
        print("Please try again!")
        return
    finally:
        cm.close_connection()


def logout(tokens):
    global current_patient, current_caregiver
    if current_caregiver is None and current_patient is None:
        print("Please login first.")
        return

    try:
        current_caregiver = None
        current_patient = None
    except Exception as e:
            print("Please try again!")
            return

    print("Successfully logged out!")


def start():
    stop = False
    while not stop:
        print()
        print(" *** Please enter one of the following commands *** ")
        print("> create_patient <username> <password>")  # //TODO: implement create_patient (Part 1)
        print("> create_caregiver <username> <password>")
        print("> login_patient <username> <password>")  #// TODO: implement login_patient (Part 1)
        print("> login_caregiver <username> <password>")
        print("> search_caregiver_schedule <date>")  #// TODO: implement search_caregiver_schedule (Part 2)
        print("> reserve <date> <vaccine>") #// TODO: implement reserve (Part 2)
        print("> upload_availability <date>")
        print("> cancel <appointment_id>") #// TODO: implement cancel (extra credit)
        print("> add_doses <vaccine> <number>")
        print("> show_appointments")  #// TODO: implement show_appointments (Part 2)
        print("> logout") #// TODO: implement logout (Part 2)
        print("> Quit")
        print()
        response = ""
        print("> Enter: ", end='')

        try:
            response = str(input())
        except ValueError:
            print("Type in a valid argument")
            break

        response = response.lower()
        tokens = response.split(" ")
        if len(tokens) == 0:
            ValueError("Try Again")
            continue
        operation = tokens[0]
        if operation == "create_patient":
            create_patient(tokens)
        elif operation == "create_caregiver":
            create_caregiver(tokens)
        elif operation == "login_patient":
            login_patient(tokens)
        elif operation == "login_caregiver":
            login_caregiver(tokens)
        elif operation == "search_caregiver_schedule":
            search_caregiver_schedule(tokens)
        elif operation == "reserve":
            reserve(tokens)
        elif operation == "upload_availability":
            upload_availability(tokens)
        elif operation == "cancel":
            cancel(tokens)
        elif operation == "add_doses":
            add_doses(tokens)
        elif operation == "show_appointments":
            show_appointments(tokens)
        elif operation == "logout":
            logout(tokens)
        elif operation == "quit":
            print("Thank you for using the scheduler, Goodbye!")
            stop = True
        else:
            print("Invalid Argument")


if __name__ == "__main__":
    '''
    // pre-define the three types of authorized vaccines
    // note: it's a poor practice to hard-code these values, but we will do this ]
    // for the simplicity of this assignment
    // and then construct a map of vaccineName -> vaccineObject
    '''

    # start command line
    print()
    print("Welcome to the COVID-19 Vaccine Reservation Scheduling Application!")

    start()
