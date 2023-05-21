import re
import hashlib
import json
import pandas as pd
from datetime import datetime

# Function to check if a phone number is valid
def is_valid_mobile(phone_number):
    # Remove any non-digit characters from the phone number
    cleaned_number = re.sub(r'\D', '', phone_number)

    # Check if the cleaned number meets the length requirement
    if len(cleaned_number) == 10:
        # Check if the number falls within the valid range
        if 6000000000 <= int(cleaned_number) <= 9999999999:
            return True

    return False

# Function to generate SHA256 hash for a phone number
def generate_hash(phone_number):
    # Remove any non-digit characters from the phone number
    cleaned_number = re.sub(r'\D', '', phone_number)

    # Prefix the number with '+91' or '91' if it's a valid number
    if is_valid_mobile(cleaned_number):
        cleaned_number = '91' + cleaned_number[-10:]

    # Generate SHA256 hash
    sha256_hash = hashlib.sha256(cleaned_number.encode()).hexdigest()

    return sha256_hash if is_valid_mobile(phone_number) else None

# Function to calculate age based on date of birth
def calculate_age(dob):
    if dob is None:
        return None
        

    dob_date = datetime.fromisoformat(dob.replace('Z', '+00:00')).date()
    today = datetime.now().date()
    age = today.year - dob_date.year

    if today.month < dob_date.month or (today.month == dob_date.month and today.day < dob_date.day):
        age -= 1

    return age

# Read the JSON file
with open('DataEngineeringQ2.json') as f:
    data = json.load(f)

# Extract the required columns
columns = ['appointmentId', 'phoneNumber', 'patientDetails.firstName', 'patientDetails.lastName',
           'patientDetails.gender', 'patientDetails.birthDate']

records = []
for item in data:
    record = {}
    for col in columns:
        keys = col.split('.')
        temp = item
        for key in keys:
            if isinstance(temp, dict) and key in temp:
                temp = temp[key]
            else:
                temp = None
                break
        record[col] = temp
    records.append(record)

# Transform the 'gender' column
for record in records:
    gender = record['patientDetails.gender']
    if gender == 'M':
        record['patientDetails.gender'] = 'male'
    elif gender == 'F':
        record['patientDetails.gender'] = 'female'
    else:
        record['patientDetails.gender'] = 'others'

# Rename the 'birthDate' column as 'DOB'
for record in records:
    record['DOB'] = record.pop('patientDetails.birthDate')

# Create the 'fullName' derived column
for record in records:
    firstName = record['patientDetails.firstName']
    lastName = record['patientDetails.lastName']
    record['fullName'] = f"{firstName} {lastName}"

# Create the 'phoneNumberHash' column
for record in records:
    phoneNumber = record['phoneNumber']
    record['phoneNumberHash'] = generate_hash(phoneNumber)

# Create the 'Age' column
for record in records:
    dob = record['DOB']
    record['Age'] = calculate_age(dob)

# Extract the medicine names and count the active medicines for each appointmentId
medicines_data = {}
for item in data:
    appointment_id = item['appointmentId']
    medicines = item['consultationData']['medicines']
    active_medicines = [medicine['medicineName'] for medicine in medicines if medicine['isActive']]
    medicines_data[appointment_id] = {
        'noOfMedicines': len(medicines),
        'noOfActiveMedicines': len(active_medicines),
        'noOfInactiveMedicines': len(medicines) - len(active_medicines),
        'medicineNames': ', '.join(active_medicines)
    }
for record in records:
    appointment_id = record['appointmentId']
    if appointment_id in medicines_data:
        aggregated_data = medicines_data[appointment_id]
        record.update(aggregated_data)
        record['Age'] = record['Age']  # Add 'Age' column
        record['gender'] = record['patientDetails.gender']  # Add 'gender' column
    else:
        record['noOfMedicines'] = None
        record['noOfActiveMedicines'] = None
        record['noOfInactiveMedicines'] = None
        record['medicineNames'] = None
        record['Age'] = None  # Add 'Age' column with None value
        record['gender'] = None  # Add 'gender' column with None value

# Create a DataFrame from the records
#
df = pd.DataFrame(records)
with open('aggregated_data.json', 'w') as f:
    json.dump(aggregated_data, f, indent=4)



#to create a csv file
df.to_csv('output.csv', index=False, sep='—')

import matplotlib.pyplot as plt

# Count the number of appointments for each gender
gender_counts = df['patientDetails.gender'].value_counts()

# Plot the pie chart
plt.figure(figsize=(8, 6))
plt.pie(gender_counts, labels=gender_counts.index, autopct='%1.1f%%')
plt.title('Number of Appointments by Gender')
plt.axis('equal')
plt.show()