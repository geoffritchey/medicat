import datetime
from dateutil import tz
import re
import Util
import json
# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


def get_current_students(session=Util.authenticated_session, today=datetime.datetime.now().strftime("%Y-%m-%d")):
    phone_regex = re.compile(r"[-() ]", re.IGNORECASE)
    print("GetCurrentStudents")
    print(today)
    '''
    Find current list of students
    '''
    students_uri = "{0}ds/campusnexus/StudentDegreePathways?$count=true" \
                   "&$expand=Program,StudentCourse($expand=Student($expand=Gender($select=Code))" \
                   ",Student($expand=EmploymentStatus)" \
                   ",Student($expand=College)" \
                   ",Student($select=Ssn,StudentNumber,LastName,FirstName,MiddleName,DateOfBirth,StreetAddress" \
                   ",StreetAddress2,City,State,PostalCode,WorkPhoneNumber,MobilePhoneNumber,PhoneNumber,EmailAddress," \
                   "DateOfBirth,MaritalStatusId,NickName))" \
                   "&$filter=StudentCourse/Term/EndDate ge {1}" \
                   "&$orderby=StudentCourse/Student/StudentNumber" \
                   "&$apply=groupby((StudentCourse/Student/StudentNumber))" \
                   "".format(Util.root_uri, today)

    r = session.get(students_uri)
    r.raise_for_status()
    print(students_uri)
    # print(r.text)
    result = json.loads(r.text)
    print(result)

    last_student = ''
    count = 0
    marital_statuses = [7, 2, 1, 3, 4, 5]
    for child in result.get("value"):
        student = child["StudentCourse"]["Student"]["StudentNumber"]
        if student != last_student:
            count = count + 1
            patient_control_id = ''
            college = child["Program"]["Name"]
            status = child["StudentCourse"]["Status"]
            if status is not None:
                if status == 'P':
                    status = 2
                else:
                    status = 1
            else:
                status = 0
            other_id = child["StudentCourse"]["Student"]["StudentNumber"]
            last_name = child["StudentCourse"]["Student"]["LastName"]
            first_name = child["StudentCourse"]["Student"]["FirstName"]
            middle_name = child["StudentCourse"]["Student"]["MiddleName"]
            sex = child["StudentCourse"]["Student"]["Gender"]["Code"]
            address = child["StudentCourse"]["Student"]["StreetAddress"]
            address_line_2 = child["StudentCourse"]["Student"]["StreetAddress2"]
            city = child["StudentCourse"]["Student"]["City"]
            state = child["StudentCourse"]["Student"]["State"]
            zip_code = child["StudentCourse"]["Student"]["PostalCode"]
            work_phone = child["StudentCourse"]["Student"]["WorkPhoneNumber"]
            home_phone = child["StudentCourse"]["Student"]["PhoneNumber"]
            cell_phone = child["StudentCourse"]["Student"]["MobilePhoneNumber"]
            date_of_birth = child["StudentCourse"]["Student"]["DateOfBirth"]
            if date_of_birth is None:
                date_of_birth = "01/01/1900"
            date_of_birth = datetime.datetime.strptime(date_of_birth, '%Y-%m-%dT%H:%M:%S')
            marital_status = child["StudentCourse"]["Student"]["MaritalStatusId"]
            if marital_status is None:
                marital_status = 0
            employment = 7
            employment_code = ''
            email_address = child["StudentCourse"]["Student"]["EmailAddress"]
            eligibility = 2
            inactive = 0
            nickname = child["StudentCourse"]["Student"]["NickName"]
            print(""
                  , f"{patient_control_id[:9] if patient_control_id is not None else ''}"
                  , f"{other_id[:20] if other_id is not None else ''}"
                  , f"{last_name[:30] if last_name is not None else ''}"
                  , f"{first_name[:20] if first_name is not None else ''}"
                  , f"{middle_name[:1] if middle_name is not None else ''}"
                  , f"{sex[:1] if sex is not None else ''}"
                  , f"{address[:40] if address is not None else ''}"
                  , f"{address_line_2[:40] if address_line_2 is not None else ''}"
                  , f"{city[:60] if city is not None else ''}"
                  , f"{state[:2] if state is not None else ''}"
                  , f"{zip_code[:20] if zip_code is not None else ''}"
                  , f"{phone_regex.sub('', home_phone)[:10] if home_phone is not None else ''}"
                  , f"{phone_regex.sub('', work_phone)[:10] if work_phone is not None else ''}"
                  , f"{phone_regex.sub('', cell_phone)[:10] if cell_phone is not None else ''}"
                  , f"{date_of_birth:%m/%d/%Y}"
                  , f"{marital_statuses[marital_status]}"
                  , f"{marital_statuses[marital_status]}"
                  , f"{employment}"
                  , f"{employment_code}"
                  , f"{email_address[:50] if email_address is not None else ''}"
                  , f"{eligibility if eligibility is not None else ''}"
                  , f"{inactive if inactive is not None else ''}"
                  , f"{status}"
                  , f"{college[:50] if college is not None else ''}"
                  , f"{nickname[:80] if nickname is not None else ''}"
                  , ""
                  , ""
                  , ""
                  , ""
                  , ""
                  , ""
                  , ""
                  , ""
                  , ""
                  , ""
                  , ""
                  , ""
                  , ""
                  , ""
                  , ""
                  , ""
                  , ""
                  , ""
                  , ""
                  , ""
                  , ""
                  , ""
                  , ""
                  , ""
                  , ""
                  , ""
                  , ""
                  , sep="|")
        last_student = student
    return count


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    get_current_students()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
