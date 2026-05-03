from logging import getLogger
from typing import Tuple, Any

from zeep.exceptions import Fault

from api.meeting_place.zeep_client import Zeep

logger = getLogger()

TEMPLATE_ID_CREATE_USER = 3


def build_user(user_id=None, user_fields=None):
    if user_fields == None:
        user_fields = user_id
    user_params = {
        "FAllowGuestViewIsDefault": True,
        "FAllowInternetAccessIsDefault": True,
        "FAutoStartRecordIsDefault": True,
        "FCanHostAudioVideoIsDefault": True,
        "FCanHostWebEx": False,
        "FCanHostWebExIsDefault": True,
        "FDisableRollCallIsDefault": True,
        "FRsvnAllowGuestViewIsDefault": True,
        "FRsvnlessAllowInternetAccIsDefault": True,
        "FSchedHomeSiteOnly": False,
        "VLanguageIsDefault": True,
        "alternatePhone": "",
        "attendModeIsDefault": True,
        "attendPasswdRequiredIsDefault": True,
        "attendPreference": 1,
        "billCode": "",
        "billCodeIsDefault": True,
        "canChangeMtgIDIsDefault": True,
        "canOutdialIsDefault": True,
        "canRecordMeetingsIsDefault": True,
        "contactIDIsDefault": True,
        "contactNameStr": "",
        "defNotPriorityIsDefault": True,
        "defaultEmailFormatIsDefault": True,
        "email": f"{user_fields}@iad.idf.il",
        "emailAdd1": "",
        "emailTypeIsDefault": True,
        "firstName": "autoanswerdevice",
        "firstSearchMethod": 1,
        "flexPromptMaskEndOfMtgIsDefault": True,
        "flexPromptMaskMtgExtendPromptIsDefault": True,
        "forcePasswordChange": False,
        "forcePinChange": False,
        "fourthSearchMethod": 4,
        "isActiveIsDefault": True,
        "isAssignedVideoTypesDefault": True,
        "isSiteDefault": False,
        "isfSchedHomeSiteOnlyDefault": False,
        "lastName": user_fields,
        "maxVUIODsPerMtgIsDefault": True,
        "maximumMeetingLength": 3,
        "maximumMeetingLengthIsDefault": True,
        "meetingCategoryIsDefault": True,
        "meetingRestrictionIsDefault": True,
        "mtgEntryModeIsDefault": True,
        "mtgNoteRestrictionIsDefault": True,
        "namedDisconnectIsDefault": True,
        "namedIntroductionIsDefault": True,
        "outdialPhone": user_id,
        "pagerNum": "",
        "pagerType": 1,
        "pagerTypeIsDefault": False,
        "password": user_fields,
        "passwordRequiredIsDefault": True,
        "passwordRequiredOnODIsDefault": True,
        "profileId": user_fields,
        "profilePassword": user_id,
        "receiveNotMaskIsDefault": True,
        "screenedIntroductionIsDefault": True,
        "secondSearchMethod": 2,
        "sendInviteListWithNotIsDefault": True,
        "sendMtgPwdWithNotIsDefault": True,
        "sendNotAboutMtgChngsIsDefault": True,
        "sendNotAboutMtgsIsDefault": True,
        "thirdSearchMethod": 3,
        "timeZoneIsDefault": True,
        "typeOfUser": "END_USER",
        "uniqueGroupId": 0,
        "useReservationless": -1,
        "userId": user_fields,
        "whoSkipsPasswordIsDefault": True
    }
    return user_params


def create_user(zeep=None, user_id=None, user_fields=None):
    user = build_user(user_id, user_fields)
    try:
        response = zeep.services["UserService"].addUserProfileFromTemplate(userInfo=user,
                                                                           templateId=TEMPLATE_ID_CREATE_USER)
        logger.info(f"successfully created user {user_id}")
        return True, response
    except Exception as err:
        logger.info(f"failed to create user {user_id}: {err}")
        if isinstance(err, Fault):
            if 'is already being used' in err.message:
                return True, err
        else:
            return False, err

def get_user(zeep: Zeep, user_id: str):
    response = zeep.services["UserService"].findUserProfileList(filter={"matchType":"BEGINSWITH", "userId": user_id})
    # logger.info(response)
    # print(response)
    try:
        return response
    except:
        return None



def get_user_id(zeep: Zeep, user_id: str):
    response = zeep.services["UserService"].getUniqueUserId(userId=user_id)
    logger.info(response)
    print(response)
