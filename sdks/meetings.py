from logging import getLogger

from api.meeting_place.zeep_client import Zeep

logger = getLogger()


def get_schedule_params_form(zeep: Zeep):
    try:
        response = zeep.services["MeetingService"].getScheduleParamsForm(schedulerUserId=150)
    except Exception as err:
        logger.info("failed to get schedule params form")
        print(f"failed to schedule recurring meeting: {err}")
        return None
    logger.info("successfully got schedule params form")
    print(f"successfully got schedule params form")
    return response

def build_recurring_params(meeting_id: str,
                           password: str = None,
                           invitee_list_element=None,
                           invitee_element=None):
    invitee_kwargs = {
        "email": f"{meeting_id}@iaf.idf.il",
        "inviteGuest": False,
        "speakerAbility": "SPEAKERPLUS",
        "status": "TOBEADDED",
        "username": meeting_id,
    }
    invitee = invitee_element(**invitee_kwargs)
    invitees_list_args = [invitee]
    invitees_list = invitee_list_element(*invitees_list_args)

    schedule_params_form = {
        "dialableMtgId": meeting_id,
        "durationMin": 0,
        "entryAnnouncement": 'BEEP',
        "exitAnnouncement": 'BEEP',
        "meetingTemplateName": 'Meeting Center',
        "meetingType": 'REGULAR',
        "initialPartNum": 0,
        "schedulerUniqueId": 0,
        "whoCanAttend": "ANYONE",
        "outdialOnFirstCaller": True,
        'schedulerUserId': 'admin',
        "recurrenceType": "RT_CONTINUOUS",
        "videoEnabled": True
    }

    restricted_params = {}
    if password:
        restricted_params = {
            "password": password,
            "invitees": invitees_list
        }

    schedule_params_form.update(restricted_params)
    return schedule_params_form

def get_invitee_elements(zeep: Zeep):
    schedule_recurring_meeting = zeep.clients["MeetingService"].get_element("ns3:scheduleRecurringMeeting")
    recurring_params = schedule_recurring_meeting.type.elements[1][1]
    invitees_list_element = recurring_params.type.elements[17][1]
    invitee_element = invitees_list_element.type.elements[0][1]
    return invitees_list_element, invitee_element

# is the meeting name missing (ori)
def create_scheduled_meeting(zeep: Zeep, meeting_id: str, password: str = None) -> bool:
    invitee_list_element, invitee_element = get_invitee_elements(zeep)
    recurring_params = build_recurring_params(meeting_id, password, invitee_list_element, invitee_element)
    try:
        response = zeep.services["MeetingService"].scheduleRecurringMeeting(requesterUserId="admin",
                                                                            recurringParams=recurring_params,
                                                                            tryBeforeBuy=True)
        # response = zeep.services["MeetingService"].rescheduleMeeting(requesterUserId="admin",
        #                                                                     scheduleParams=recurring_params,
        #                                                                     tryBeforeBuy=True)
        logger.info(f"successfully scheduled recurring meeting {meeting_id}")
        return True
    except Exception as err:
        logger.info(f"failed to schedule recurring meeting {meeting_id}: {err}")
        return False

def create_scheduled_meeting_for_preconf(zeep: Zeep, meeting_id: str, meeting_subject: str = None, password: str = None) -> bool:
    invitee_list_element, invitee_element = get_invitee_elements(zeep)
    recurring_params = build_recurring_params(meeting_id, meeting_subject, password, invitee_list_element, invitee_element)
    try:
        response = zeep.services["MeetingService"].scheduleRecurringMeeting(requesterUserId="admin",
                                                                            recurringParams=recurring_params,
                                                                            tryBeforeBuy=True)
        logger.info(f"successfully scheduled recurring meeting {meeting_id}")
        return True
    except Exception as err:
        logger.info(f"failed to schedule recurring meeting {meeting_id}: {err}")
        return False

def build_preconf_params(meeting_id: str, preconf_subject: str = None, invitees_list=None):
    invitees = {}
    invitees = {'Invitee': []}
    for invitee in invitees_list:
        element = {
            "email": f"{invitee}@iaf.idf.il",
            "inviteGuest": False,
            "speakerAbility": "SPEAKERPLUS",
            "status": "TOBEADDED",
            "username": invitee
            }
        invitees['Invitee'].append(element)


    schedule_params_form = {
        "subject": preconf_subject,
        "dialableMtgId": meeting_id,
        "durationMin": 0,
        "entryAnnouncement": 'BEEP',
        "exitAnnouncement": 'BEEP',
        "meetingTemplateName": 'Meeting Center',
        "meetingType": 'REGULAR',
        "initialPartNum": 0,
        "schedulerUniqueId": 0,
        "whoCanAttend": "ANYONE",
        "outdialOnFirstCaller": True,
        'schedulerUserId': 'admin',
        "recurrenceType": "RT_CONTINUOUS",
        "videoEnabled": True,
        "invitees": invitees
    }
    return schedule_params_form

def create_scheduled_preconf(zeep: Zeep, preconf_id: str, preconf_subject: str = None, invitees: list = None) -> bool:
    # sets the recurring params for the preconf
    recurring_params = build_preconf_params(meeting_id=preconf_id, preconf_subject=preconf_subject, invitees_list=invitees)
    # try to create the preconf with the specified parameters
    try:
        response = zeep.services["MeetingService"].scheduleRecurringMeeting(requesterUserId="admin",
                                                                            recurringParams=recurring_params,
                                                                            tryBeforeBuy=True)
        logger.info(f"successfully scheduled recurring meeting {preconf_id}")
        return True
    except Exception as err:
        logger.info(f"failed to schedule recurring meeting {preconf_id}: {err}")
        return False

# Added by Ori
def delete_schedule_meeting(zeep: Zeep, meeting_id: str):
    # cancelMeeting
    print("Hello from ori's bedika")
    test = zeep.services["MeetingService"].findMeetingList(uniqueMeetingId=meeting_id).cancelMeeting
    print(f"Meeting ID: {meeting_id} test: {test}")
    return test

def get_all_meetings_short_info(zeep: Zeep) -> list:
    return zeep.services["MeetingService"].findMeetingList(filter={"dialableMeetingId": ""})

def get_meeting_state(zeep: Zeep, meeting_id: str) -> dict:
    return zeep.services["MeetingService"].getMeetingState(uniqueMeetingId=meeting_id)

def get_meeting_info(zeep: Zeep, uid=None):
     return zeep.services["MeetingService"].getMeetingInfo(requesterUserId="admin", uniqueMeetingId=uid)

def reschedule_meeting(zeep: Zeep, uid=None, schedule_params=None):
     return zeep.services["MeetingService"].rescheduleMeeting(requesterUserId="admin", uniqueMeetingId=uid, scheduleParams=schedule_params)

def end_meeting(zeep: Zeep, uid=None):
    return zeep.services["MeetingService"].endMeeting(requesterUserId="admin", uniqueMeetingId=uid)

def remove_invitees(zeep: Zeep, uid=None, invitees_list=None):
    return zeep.services["MeetingService"].removeInvitees(requesterUserId="admin", uniqueMeetingId=uid, inviteesList=invitees_list)

def eject_meeting_participants(zeep: Zeep, meeting_uuid: int, participant_ids: list[int]):
    return zeep.services["MeetingService"].ejectParticipants(uniqueMeetingId=meeting_uuid,
                                                             listOfParticipantIds=participant_ids)

def get_meeting(zeep: Zeep, meeting_id: int):
    meetings = zeep.services["MeetingService"].findMeetingList(filter={"dialableMeetingId": meeting_id})
    return meetings
# def get_invitees(client: Zeep, meeting_id: int):
#     meeting_state = client.service_meeting.findMeetingWithInviteesList(filter={"dialableMeetingId": meeting_id})
#     all_invitees = []
#     for user in meeting_state[0]["invitees"]["_raw_elements"]:
#         if (user[5].text != None):
#             all_invitees.append({"Participant Number": user[5].text})
#     return all_invitees

def get_meeting_uuid(short_meeting_info):
    for info in short_meeting_info["_raw_elements"]:
        if info.tag == '{http://beans.webservices.meetingplace.cisco.com}uniqueMeetingId':
            return info.text
    return None

def get_meetings_with_invitees(zeep: Zeep, meeting_id: int):
    meetings = zeep.services["MeetingService"].findMeetingWithInviteesList(filter={"dialableMeetingId": meeting_id})
    # print(meetings)
    return meetings

def get_meeting_participants_num(meeting_state):
    return meeting_state["participantCount"]

def get_meeting_participant_ids(meeting_state):
    participants = meeting_state["participants"]
    participant_ids = []
    for participant in participants["ParticipantState"]:
        for info in participant["_raw_elements"]:
            if info.tag == '{http://beans.meeting.businesslayer.meetingplace.cisco.com}participantId':
                participant_ids.append(info.text)
                continue
    return participant_ids
