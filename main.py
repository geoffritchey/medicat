import datetime
from dateutil import tz
import re
import Util
import json
import logging
import pysftp
import sys

logging.basicConfig(format='%(message)s')
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
# log.setLevel(logging.DEBUG)

# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

def get_current_students(session=Util.authenticated_session, today=datetime.datetime.now().strftime("%Y-%m-%d")):
    phone_regex = re.compile(r"[-() _]")
    newline_regex = re.compile("\r|\n")
    log.debug(today)
    all_id_numbers = ''
    '''
    Find current list of students
    '''
    students_uri = "{0}ds/campusnexus/StudentCourses?$count=true" \
                   "&$expand=Student($expand=Gender($select=Code))" \
                   ",Student($expand=EmploymentStatus)" \
                   ",Student($expand=College)" \
                   ",Student($select=Id,Ssn,StudentNumber,LastName,FirstName,MiddleName,DateOfBirth,StreetAddress" \
                   ",StreetAddress2,City,State,PostalCode,WorkPhoneNumber,MobilePhoneNumber,PhoneNumber,EmailAddress," \
                   "DateOfBirth,MaritalStatusId,NickName)" \
                   "&$filter=Term/EndDate ge {1} and Term/StartDate le {1} " \
                   "&$select=Status,Student,StudentEnrollmentPeriodId" \
                   "&$orderby=Student/StudentNumber" \
                   "&$apply=groupby((Student/StudentNumber))" \
                   "".format(Util.root_uri, today)

    r = session.get(students_uri)
    r.raise_for_status()
    log.debug(students_uri)
    # log.debug(r.text)
    result = json.loads(r.text)
    log.debug(result)

    # start period list as a set to get distinct values
    # then convert it to a list for easy of use
    period_list = set()
    for child in result.get("value"):
        period_list.add(child["StudentEnrollmentPeriodId"])

    period_list = list(period_list)

    id_program_map = {}
    block_size = 200
    for i in range(0, len(period_list), block_size):
        all_id_numbers = " or ".join([(lambda x: "Id eq " + str(x))(x) for x in period_list[i:i+block_size]])
        enrollment_periods_uri = "{0}ds/campusnexus/StudentEnrollmentPeriods?$count=true" \
                                 "&$select=ProgramVersionName,Id" \
                                 "&$filter={1}" \
                                 "".format(Util.root_uri, all_id_numbers)
        result_period_list = session.get(enrollment_periods_uri)
        result_period_list.raise_for_status()
        log.debug(enrollment_periods_uri)
        result_period_list = json.loads(result_period_list.text)
        log.debug(f"List: {result_period_list}")
        for child in result_period_list.get("value"):
            id = child["Id"]
            program_version_name = child["ProgramVersionName"]
            id_program_map[id] = program_version_name

    last_student = ''
    count = 0
    log.debug("count = %s", result.get("@odata.count"))
    marital_statuses = [7, 2, 1, 3, 4, 5, 5]
    for child in result.get("value"):
        student = child["Student"]["StudentNumber"]
        # results are sorted by student id; duplicates can be eliminated here
        if student == last_student:
            do_body = False
        else:
            do_body = True
        last_student = student
        if do_body:
            count = count + 1
            patient_control_id = child["Student"]["Id"]
            status = child["Status"]
            if status is not None:
                if status == 'P':
                    status = 2
                else:
                    status = 1
            else:
                status = 0
            other_id = child["Student"]["StudentNumber"]
            last_name = child["Student"]["LastName"]
            first_name = child["Student"]["FirstName"]
            middle_name = child["Student"]["MiddleName"]
            sex = child["Student"]["Gender"]["Code"]
            address = child["Student"]["StreetAddress"]
            address_line_2 = child["Student"]["StreetAddress2"]
            city = child["Student"]["City"]
            state = child["Student"]["State"]
            zip_code = child["Student"]["PostalCode"]
            work_phone = child["Student"]["WorkPhoneNumber"]
            home_phone = child["Student"]["PhoneNumber"]
            cell_phone = child["Student"]["MobilePhoneNumber"]
            date_of_birth = child["Student"]["DateOfBirth"]
            if date_of_birth is None:
                date_of_birth = "01/01/1900"
            date_of_birth = datetime.datetime.strptime(date_of_birth, '%Y-%m-%dT%H:%M:%S')
            marital_status = child["Student"]["MaritalStatusId"]
            if marital_status is None:
                marital_status = 0
            employment = 7
            employment_code = ''
            email_address = child["Student"]["EmailAddress"]
            eligibility = 2
            inactive = 0
            nickname = child["Student"]["NickName"]

            try:
                enrollment_id = child["StudentEnrollmentPeriodId"]
                college = id_program_map[enrollment_id]
            except KeyError as e:
                college = "Unknown"
                log.debug(f"control: {patient_control_id}")
                log.debug(f"other_id: {other_id}")
                log.debug(f"enrollment_id: {enrollment_id}")
                log.debug(f"name: {first_name} {last_name}")

            print(f"{patient_control_id if patient_control_id is not None else ''}"
                  , f"{other_id[:20] if other_id is not None else ''}"
                  , f"{last_name.strip()[:30] if last_name is not None else ''}"
                  , f"{first_name.strip()[:20] if first_name is not None else ''}"
                  , f"{middle_name[:1] if middle_name is not None else ''}"
                  , f"{sex[:1] if sex is not None else 'N'}"
                  , f"{newline_regex.sub('', address.strip())[:40] if address is not None else ''}"
                  , f"{newline_regex.sub('', address_line_2.strip())[:40] if address_line_2 is not None else ''}"
                  , f"{city.strip()[:60] if city is not None else ''}"
                  , f"{state.strip()[:2] if state is not None else ''}"
                  , f"{zip_code.strip()[:20] if zip_code is not None else ''}"
                  , f"{phone_regex.sub('', home_phone)[:10] if home_phone is not None else ''}"
                  , f"{phone_regex.sub('', work_phone)[:10] if work_phone is not None else ''}"
                  , f"{phone_regex.sub('', cell_phone)[:10] if cell_phone is not None else ''}"
                  , f"{date_of_birth:%m/%d/%Y}"
                  , f"{marital_statuses[marital_status]}"
                  , f"{employment}"
                  , f"{employment_code}"
                  , f"{newline_regex.sub('', email_address.strip())[:50] if email_address is not None else ''}"
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
                  , ""
                  , ""
                  , sep="|")
    return count


def ftp():
    with pysftp.Connection('ftp.medicatconnect.com', username=Util.sftp_username, password=Util.sftp_password) as sftp:
        sftp.put('Medicat-Import.txt')


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    original_stdout = sys.stdout
    with open("Medicat-Import.txt", 'w') as f:
        sys.stdout = f
        get_current_students()
        sys.stdout = original_stdout
    ftp()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
