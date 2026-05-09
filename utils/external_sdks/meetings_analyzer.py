import time
from functools import partial

import pandas as pd
from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtCore import Slot
from PySide6.QtGui import QFont, QScreen
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QDialog, QLabel, QComboBox, QTabWidget, QApplication

from api.cms.cms_client import CMS
from api.meeting_place.meeting_place import get_all_meetings_short_info, get_meeting, create_scheduled_meeting, create_scheduled_preconf, get_meetings_with_invitees, get_meeting_info, reschedule_meeting, remove_invitees, end_meeting
from api.meeting_place.users import get_user, create_user
from ui.libs import CustomPyside
from api.conf_reader.log_conf import logger
from ui.libs import CustomPyside
from ui.utils.create_meeting import create_restricted_meeting
from api.meeting_place.meeting_place_client import Zeep, servers_config, get_zeeper
from ui.pages.meeting_place_menu.windows.debug_page import DebuggerPage

# need to organize the creation of zeep connections
# need to handle non existent case searches
# need to fix the password error
class MeetingsAnalyzer(QDialog):
    def __init__(self, parent=None, debug_page=None):
        super().__init__()
        self.set_window_size()

        # creating the apis
        self.zeeper = get_zeeper() # api for the meeting place
        self.cms_client = CMS(host="https://180.200.226.161:8443/", username="admin", password="zaq12wsx")

        # general variables
        self.debug_page = DebuggerPage()
        self.current_server = ""
        self.display_data = []
        self.thread_manager = QThreadPool()
        self.ongoing_operation = False
        self.parent = parent
        
        self.export_data = []
        # setting the layout
        meetings_analyzer_layout = QVBoxLayout()
        meetings_analyzer_layout.setSpacing(20)
        meetings_analyzer_layout.setAlignment(Qt.AlignTop)

        # adding the main label
        top_row_layout = QHBoxLayout()
        top_row_widget = QWidget()
        main_label = CustomPyside.set_label_font("Meetings Place Analyzer", 20)
        main_label.setObjectName("widget_label")
        top_row_layout.addWidget(main_label)

        # -------------------------------------------------------------------------------------
        # creating the combobox layout
        combo_box_layout = QHBoxLayout()
        combo_box_widget = QWidget()

        # adding the server combobox label
        self.combo_box_label = CustomPyside.set_label_font("Server In Usage : ", 13)
        self.combo_box_label.setObjectName("widget_label")

        self.apm_combo_box = QComboBox()
        options = []
        for name, properties in servers_config.items():# adding the appearance mode combo box with the meeting place servers
            option = f"{name} {properties['ip']}"
            self.apm_combo_box.addItem(option)
            options.append(option)
        self.zeeper.initialize_zeep(options[0])
        self.apm_combo_box.currentIndexChanged.connect(partial(self.set_zeep))

        combo_box_layout.addWidget(self.combo_box_label)
        combo_box_layout.addWidget(self.apm_combo_box)
        combo_box_layout.setAlignment(Qt.AlignRight)
        combo_box_widget.setLayout(combo_box_layout)
        top_row_layout.addWidget(combo_box_widget)
        # -------------------------------------------------------------------------------------

        # meetings_analyzer_layout.addWidget(main_label)
        top_row_widget.setLayout(top_row_layout)
        meetings_analyzer_layout.addWidget(top_row_widget)

        # adding the operations history search bar
        # self.categories = ["User Association", "Name Change", "DN Change", "Certificate Download"]
        self.categories = {"Meeting ID": "Meeting ID", "Password": "Password", "Meeting State": "Meeting State", "Unique Meeting ID": "Unique Meeting ID"}
        self.search_bar = CustomPyside.SearchBar(search_categories=self.categories)
        self.search_bar.search_button.clicked.connect(partial(self.show_results))
        meetings_analyzer_layout.addWidget(self.search_bar)

        # adding the meetings label 
        meetings_label = CustomPyside.set_label_font("Meetings Table", 17)
        meetings_label.setObjectName("widget_label")
        meetings_analyzer_layout.addWidget(meetings_label)

        # adding the meetings table 
        meeting_window = MeetingWindow(parent=self)
        add_meeting_window = AddMeetings(parent=self)
        self.table = CustomPyside.SmartTable(dialog_window=meeting_window, tool_bar_actions=True,
                                             add_data_window=add_meeting_window)
        meetings_analyzer_layout.addWidget(self.table)

        # connecting the search bar to the table 
        self.search_bar.append_table(self.table)
        self.setLayout(meetings_analyzer_layout)

        # -------------------------------------------------------------------------------------
        self.bottom_buttons = QWidget()
        self.bottom_buttons_layouts = QHBoxLayout()

        self.csv_button = QPushButton("Export To CSV")
        self.csv_button.setObjectName("action_button")
        self.csv_button.clicked.connect(self.save_to_csv)
        self.bottom_buttons_layouts.addWidget(self.csv_button)

        self.bottom_buttons.setLayout(self.bottom_buttons_layouts)
        meetings_analyzer_layout.addWidget(self.bottom_buttons)
        # -------------------------------------------------------------------------------------
    
    def display_element(self):
        self.exec()
    
    @Slot()
    def req_func(self):
        if self.ongoing_operation == False:
            self.ongoing_operation = True
            # self.thread_manager.start(self.loading_indiation)
            self.thread_manager.start(self.show_results)
            # self.search_bar.thread_manager.start(self.show_results)

    def show_results(self):
        self.current_server = self.apm_combo_box.currentText()
        print(self.current_server)
        
        if "cms" not in self.current_server:
            self.search_bar.search_button.setEnabled(False)
            data_base = []

            self.table.set_elements(data=[{"Message": "Searching....."}])
            self.table.display_elements()
            zeep = self.zeeper.get_current_zeep()
            self.debug_page.debug_box.add_line_space()
            self.debug_page.debug_box.add_line(f"using zeep: {zeep}")
            # logger.info(f"using zeep: {zeep}")
            meetings = get_all_meetings_short_info(zeep)

            for mm in meetings:
                # print(mm)
                data_base.append({'Meeting ID': mm["dialableMeetingId"], 'Password': mm["_raw_elements"][6].text,
                                'Meeting State': mm["_raw_elements"][10].text, "Unique Meeting ID": mm["_raw_elements"][14].text})

            search_type = self.search_bar.search_headers[self.search_bar.dropdown_type_menu.currentIndex()]
            search_condition = self.search_bar.dropdown_condition_menu.currentText()
            search_input = self.search_bar.search_input.text()
            # print(search_type,search_condition,search_input) # for debugging

            self.display_data = self.filter_data(main_data=data_base, search_condition=search_condition,
                                                search_type=search_type, search_input=search_input).to_dict('records')
            # print(desired_meetings.to_dict('records')[0])
            self.table.set_elements(data=self.display_data)
            self.table.display_elements()

            self.search_bar.search_button.setEnabled(True)
            self.ongoing_operation = False

        elif "cms" in self.current_server:
            self.search_bar.search_button.setEnabled(False)
            data_base = []
        
            self.table.set_elements(data=[{"Message": "Searching....."}])
            self.table.display_elements()
            self.debug_page.debug_box.add_line_space()
            self.debug_page.debug_box.add_line(f"using cms client: {self.cms_client}")

            search_input = self.search_bar.search_input.text()
            meetings = self.cms_client.get_cospaces(search_filter=str("filter="+search_input))
            # print(meetings)
            self.display_data = meetings
            self.table.set_elements(data=self.display_data)
            self.table.display_elements()

            self.search_bar.search_button.setEnabled(True)
            self.ongoing_operation = False

    def export_csv_file(self):
        CustomPyside.save_to_csv(parent=self,data=self.export_data)
      
    def filter_data(self, main_data, search_condition, search_type, search_input):
        data_frame = pd.DataFrame(main_data)  # converts data to pandas frame
        filtered_data_frame = []

        if search_condition == 'Begins With':
            try:
                filtered_data_frame = data_frame[data_frame[search_type].str.startswith(search_input)]
            except:
                filtered_data_frame = pd.DataFrame([{'Messege': "not found"}])

        elif search_condition == 'Contains':
            try:
                filtered_data_frame = data_frame[data_frame[search_type].str.contains(search_input)]
            except:
                filtered_data_frame = pd.DataFrame([{'Messege': "not found"}])

        elif search_condition == 'Ends With':
            try:
                filtered_data_frame = data_frame[data_frame[search_type].str.endswith(search_input)]
            except:
                filtered_data_frame = pd.DataFrame([{'Messege': "not found"}])

        return filtered_data_frame

    def count_meetings_participants(self):
        self.run_button.setEnabled(False)
        zeep = self.zeeper.get_current_zeep()

        meetings = zeep.services["MeetingService"].findMeetingList(filter={"dialableMeetingId": ""})
        chosen_meetings = []
        total_meetings = len(meetings)
        count = 0

        for mm in meetings:
            # print(mm)
            uuid = mm["_raw_elements"][6].text
            state = zeep.services["MeetingService"].getMeetingState(uniqueMeetingId=uuid)
            num_participants = state["participantCount"]
            meeting_id = mm["dialableMeetingId"]
            count += 1
            self.table.set_elements(data=[{"Messege": "Loading Meeting " + str(
                meeting_id) + " need to load more " + str(total_meetings - count) + " meetings"}])
            self.table.display_elements()

            if num_participants != 0:
                self.display_data.append(
                    {"Meeting ID": meeting_id, "Unique ID": uuid, "Participants": num_participants})
            time.sleep(0.1)

        print("--------------Relevant Meetings---------------------")
        self.table.set_elements(data=self.display_data)
        self.table.display_elements()
        self.run_button.setEnabled(True)
        self.ongoing_operation = False

    def save_to_csv(self):
        self.debug_page.debug_box.add_line_space()
        self.debug_page.debug_box.add_line(f"trying to save....")
        CustomPyside.save_to_csv2(parent=self, data=self.display_data, filename="Meetings.csv")

    def set_zeep(self, index: int):
        server = self.apm_combo_box.currentText()
        self.zeeper.initialize_zeep(server)
        self.table.clear_table()
        self.debug_page.debug_box.add_line_space()
        self.debug_page.debug_box.add_line(f"changed zeep to {server}")
        # logger.info(f"changed zeep to {server}")

    def set_window_size(self):
        self.screen_geometry = QScreen.availableGeometry(QApplication.primaryScreen()) # Get the screen geometry
        self.screen_width = self.screen_geometry.width()
        self.screen_height = self.screen_geometry.height()
        self.main_window_width = (self.screen_width // 5) * 3 # sets the width to 2/3 of the scrren width
        self.main_window_height = (self.screen_height // 6) * 4 # sets the height to 3/4 of the scrren height
        self.center_x = self.screen_geometry.width() // 2
        self. center_y = self.screen_geometry.height() // 2
        self.move(self.center_x - self.main_window_width // 2, self.center_y - self.main_window_height // 2) # moves window to the center
        self.resize(self.main_window_width, self.main_window_height)
# need to check a case for when you add a password and for when you remove
# need to remvoe the bridge meeting when there is no password 
class MeetingWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__()
        self.zeeper = get_zeeper()

        # general variables 
        self.parent = parent
        self.uid = None
        self.opened_meeting = None
        self.selected_element = None
        self.remove_invitees = []
        self.original_invitees = []
        self.current_meeting_uid = ""
        self.current_password = ""

        # setting the layout
        dialog_layout = QVBoxLayout()
        dialog_layout.setAlignment(Qt.AlignTop)
        main_font_size = 20
        secondary_font_size = 17
        third_font_size = 12

        font = QFont()
        font.setPointSize(main_font_size)

        main_label = QLabel("Meeting Settings")
        main_label.setObjectName("widget_label")
        main_label.setFont(font)
        dialog_layout.addWidget(main_label)

        font.setPointSize(third_font_size)
        self.meeting_id_label = QLabel("Meeting ID : " + "None")
        self.meeting_id_label.setObjectName("widget_label")
        self.meeting_id_label.setFont(font)
        dialog_layout.addWidget(self.meeting_id_label)

        self.meeting_status = QLabel("Meeting Status : " + "None")
        self.meeting_status.setObjectName("widget_label")
        self.meeting_status.setFont(font)
        dialog_layout.addWidget(self.meeting_status)

        self.meeting_password = QLabel("Meeting Password : ")
        self.meeting_password.setObjectName("widget_label")
        self.meeting_password.setFont(font)
        dialog_layout.addWidget(self.meeting_password)

        self.meeting_password_field = CustomPyside.RoundedTextLine("")
        dialog_layout.addWidget(self.meeting_password_field)

        dialog_layout.addSpacing(15)
        self.invitees_table_lable = QLabel("Invitees Table")
        self.invitees_table_lable.setObjectName("widget_label")
        self.invitees_table_lable.setFont(font)
        dialog_layout.addWidget(self.invitees_table_lable)

        self.invitees_table = CustomPyside.SmartTable(dialog_window=None, editable_lines=True, tool_bar_actions=True,
                                                          add_default_action=True, remove_default_action=True)
        self.invitees_table.add_data.triggered.connect(self.add_empty_space)
        # self.invitees_table.remove_data.triggered.connect(self.remove_space)
        self.invitees_table.table_widget.cellClicked.connect(partial(self.selected_item, self.invitees_table.table_widget))
        dialog_layout.addWidget(self.invitees_table)

        self.end_meeting_button = QPushButton("End Meeting")
        # self.update_button.clicked.connect(self.save_changes)
        self.end_meeting_button.setObjectName("action_button")
        dialog_layout.addWidget(self.end_meeting_button)

        self.update_button = QPushButton("Update")
        self.update_button.clicked.connect(self.save_changes)
        self.update_button.setObjectName("action_button")
        dialog_layout.addWidget(self.update_button)

        self.setLayout(dialog_layout)

    def save_changes(self):
        if "cms" not in self.parent.current_server:
            meeting_info_state = get_meeting_info(zeep=get_zeeper().get_current_zeep(), uid=self.uid)
            meeting_id = meeting_info_state["_raw_elements"][9].text

            if meeting_id[0:3] == "777": # settings for mm meetings 

                # print("trying to update a MM meeting")
                self.parent.debug_page.debug_box.add_line_space()
                self.parent.debug_page.debug_box.add_line(f"trying to update a MM meeting")
                

                wanted_password = self.meeting_password_field.text()
                password_requirement = meeting_info_state["_raw_elements"][51].text
                current_password = meeting_info_state["_raw_elements"][50].text
                # self.parent.debug_page.debug_box.add_line_space()
                self.parent.debug_page.debug_box.add_line("wanted password "+str(wanted_password))
                # self.parent.debug_page.debug_box.add_line_space()
                self.parent.debug_page.debug_box.add_line("password requirement "+str(password_requirement))
                # self.parent.debug_page.debug_box.add_line_space()
                self.parent.debug_page.debug_box.add_line("current password "+str(current_password))
                # print("wanted password", wanted_password)
                # print("password requirement", password_requirement)
                # print("current password", current_password)

                if wanted_password == current_password:
                    # self.parent.debug_page.debug_box.add_line_space()
                    self.parent.debug_page.debug_box.add_line("password is the same, aborting the change")
                    # print("password is the same, aborting the change")
                    return

                if wanted_password != None and current_password != None: # >>> no need to create a user and a bridge meeting
                    schedule_params_forms = {}
                    # schedule_params_forms["description"] = meeting_info_state["_raw_elements"][7].text # V
                    schedule_params_forms["dialableMtgId"] = meeting_info_state["_raw_elements"][9].text # V
                    schedule_params_forms["durationMin"] = meeting_info_state["_raw_elements"][10].text # V
                    schedule_params_forms["entryAnnouncement"] = meeting_info_state["_raw_elements"][12].text # V
                    schedule_params_forms["exitAnnouncement"] = meeting_info_state["_raw_elements"][13].text # V
                    # schedule_params_forms["invitees"] = meeting_info_state["_raw_elements"][18].text # <<-------
                    schedule_params_forms["meetingTemplateId"] = meeting_info_state["_raw_elements"][35].text # V
                    schedule_params_forms["meetingTemplateName"] = meeting_info_state["_raw_elements"][36].text # V
                    schedule_params_forms["meetingType"] = meeting_info_state["_raw_elements"][37].text # V
                    schedule_params_forms["initialPartNum"] = 0
                    schedule_params_forms["schedulerUniqueId"] = 0
                    schedule_params_forms["password"] = self.meeting_password_field.text()
                    schedule_params_forms["whoCanAttend"] = meeting_info_state["_raw_elements"][91].text # V
                    schedule_params_forms["outdialOnFirstCaller"] = meeting_info_state["_raw_elements"][43].text
                    reschedule_meeting(zeep=get_zeeper().get_current_zeep(), uid=self.uid, schedule_params=schedule_params_forms)
                    # print(schedule_params_forms)
                    # self.parent.debug_page.debug_box.add_line_space()
                    self.parent.debug_page.debug_box.add_line("finished updating to desired password")
                    # print("finished updating to desired password")

                if wanted_password != None and current_password == None: # >>> need to create a user and a bridge meeting , need to update user to add a route pattern and a vtp
                    response = get_meeting(zeep=get_zeeper().get_current_zeep(), meeting_id=meeting_id)
                    if response == None:
                            create_scheduled_meeting(zeep=get_zeeper().get_current_zeep(), meeting_id=f"9{meeting_id}")
                    user_response = get_user(zeep=get_zeeper().get_current_zeep(), user_id=meeting_id)
                    if user_response == None:
                        response = create_user(zeep=get_zeeper().get_current_zeep(), user_id=meeting_id)

                    schedule_params_forms = {}
                    # schedule_params_forms["description"] = meeting_info_state["_raw_elements"][7].text # V
                    schedule_params_forms["dialableMtgId"] = meeting_info_state["_raw_elements"][9].text # V
                    schedule_params_forms["durationMin"] = meeting_info_state["_raw_elements"][10].text # V
                    schedule_params_forms["entryAnnouncement"] = meeting_info_state["_raw_elements"][12].text # V
                    schedule_params_forms["exitAnnouncement"] = meeting_info_state["_raw_elements"][13].text # V

                    invitees = {}
                    invitees = {'Invitee': []}
                    element = {
                        "email": f"{meeting_id}@iaf.idf.il",
                        "inviteGuest": False,
                        "speakerAbility": "SPEAKERPLUS",
                        "status": "TOBEADDED",
                        "username": meeting_id
                        }
                    invitees['Invitee'].append(element)
                
                    schedule_params_forms["invitees"] = invitees
                    schedule_params_forms["meetingTemplateId"] = meeting_info_state["_raw_elements"][35].text # V
                    schedule_params_forms["meetingTemplateName"] = meeting_info_state["_raw_elements"][36].text # V
                    schedule_params_forms["meetingType"] = meeting_info_state["_raw_elements"][37].text # V
                    schedule_params_forms["initialPartNum"] = 0
                    schedule_params_forms["schedulerUniqueId"] = 0
                    schedule_params_forms["password"] = self.meeting_password_field.text()
                    schedule_params_forms["whoCanAttend"] = meeting_info_state["_raw_elements"][91].text # V
                    schedule_params_forms["outdialOnFirstCaller"] = meeting_info_state["_raw_elements"][43].text
                    reschedule_meeting(zeep=get_zeeper().get_current_zeep(), uid=self.uid, schedule_params=schedule_params_forms)
                    # print(reschedule_meeting(zeep=get_zeeper().get_current_zeep(), uid=self.uid, schedule_params=schedule_params_forms))
                    # print(schedule_params_forms)
                    # self.parent.debug_page.debug_box.add_line_space()
                    self.parent.debug_page.debug_box.add_line("finished updating to desired password")
                    # print("finished updating to desired password")

                if wanted_password == None and current_password != None: # >>> need to remove the bridge meeting from the invitees list , need to update user to remove route pattern
                    schedule_params_forms = {}
                    # schedule_params_forms["description"] = meeting_info_state["_raw_elements"][7].text # V
                    schedule_params_forms["dialableMtgId"] = meeting_info_state["_raw_elements"][9].text # V
                    schedule_params_forms["durationMin"] = meeting_info_state["_raw_elements"][10].text # V
                    schedule_params_forms["entryAnnouncement"] = meeting_info_state["_raw_elements"][12].text # V
                    schedule_params_forms["exitAnnouncement"] = meeting_info_state["_raw_elements"][13].text # V

                    invitees = {}
                    invitees = {'Invitee': []}
                
                    schedule_params_forms["invitees"] = invitees
                    schedule_params_forms["meetingTemplateId"] = meeting_info_state["_raw_elements"][35].text # V
                    schedule_params_forms["meetingTemplateName"] = meeting_info_state["_raw_elements"][36].text # V
                    schedule_params_forms["meetingType"] = meeting_info_state["_raw_elements"][37].text # V
                    schedule_params_forms["initialPartNum"] = 0
                    schedule_params_forms["schedulerUniqueId"] = 0
                    schedule_params_forms["password"] = self.meeting_password_field.text()
                    schedule_params_forms["whoCanAttend"] = meeting_info_state["_raw_elements"][91].text # V
                    schedule_params_forms["outdialOnFirstCaller"] = meeting_info_state["_raw_elements"][43].text
                    reschedule_meeting(zeep=get_zeeper().get_current_zeep(), uid=self.uid, schedule_params=schedule_params_forms)
                    # print(reschedule_meeting(zeep=get_zeeper().get_current_zeep(), uid=self.uid, schedule_params=schedule_params_forms))
                    # print(schedule_params_forms)
                    # self.parent.debug_page.debug_box.add_line_space()
                    self.parent.debug_page.debug_box.add_line("finished updating to desired password")
                    # print("finished updating to desired password")

            if meeting_id[0:2] == "57": # settings for blast dial meteings

                # self.parent.debug_page.debug_box.add_line_space()
                self.parent.debug_page.debug_box.add_line("trying to update a Blast Dial meeting")
                # print("trying to update a Blast Dial meeting")

                # section for removing participants
                if len(self.remove_invitees) != 0:
                    remove_invitees_params = {'Invitee': []}
                    for invitee in self.remove_invitees:
                        element = {
                            "email": f"{invitee}@iaf.idf.il",
                            "inviteGuest": False,
                            "speakerAbility": "SPEAKERPLUS",
                            "status": "TOBEADDED",
                            "username": invitee
                            }
                        remove_invitees_params['Invitee'].append(element)

                    # self.parent.debug_page.debug_box.add_line_space()
                    self.parent.debug_page.debug_box.add_line("invitees to remove "+str(remove_invitees_params))
                    # print("invitees to remove", remove_invitees_params)
                    end_meeting(zeep=get_zeeper().get_current_zeep(), uid=self.uid)
                    # time.sleep(2000)
                    remove_invitees(zeep=get_zeeper().get_current_zeep(), uid=self.uid, invitees_list=remove_invitees_params)

                    new_invitees = []
                    for invitee in self.invitees_table.get_table_data():
                        if invitee['Participant Number'] not in remove_invitees:
                            new_invitees.append(invitee['Participant Number'])

                    # self.parent.debug_page.debug_box.add_line_space()
                    self.parent.debug_page.debug_box.add_line("new invitees "+str(new_invitees))
                    # print("new invitees", new_invitees)
                    # new_invitees_params = {'Invitee': []}
                    # for invitee in self.new_invitees:
                    #     element = {
                    #         "email": f"{invitee}@iaf.idf.il",
                    #         "inviteGuest": False,
                    #         "speakerAbility": "SPEAKERPLUS",
                    #         "status": "TOBEADDED",
                    #         "username": invitee
                    #         }
                    #     new_invitees_params['Invitee'].append(element)
                    
                    create_scheduled_preconf(zeep=get_zeeper().get_current_zeep(), preconf_id=self.opened_meeting, preconf_subject="preconf_subject", invitees=new_invitees)

                # -------------------- section for adding invitees --------------------
                original_invitees_filter = []
                for invitee in self.original_invitees:
                    original_invitees_filter.append(invitee['Participant Number'])

                add_invitees = []
                for element in self.invitees_table.get_table_data():
                    if element['Participant Number'] not in original_invitees_filter:
                        add_invitees.append(element['Participant Number'])

                # self.parent.debug_page.debug_box.add_line_space()
                self.parent.debug_page.debug_box.add_line("invitees to add "+str(add_invitees))
                # print("invitees to add", add_invitees)
                if len(add_invitees) != 0:
                    invitees = {'Invitee': []}
                    for invitee in add_invitees:
                        element = {
                            "email": f"{invitee}@iaf.idf.il",
                            "inviteGuest": False,
                            "speakerAbility": "SPEAKERPLUS",
                            "status": "TOBEADDED",
                            "username": invitee
                            }
                        invitees['Invitee'].append(element)

                    # print(invitees)

                    schedule_params_forms = {}
                    # schedule_params_forms["description"] = meeting_info_state["_raw_elements"][7].text # V
                    schedule_params_forms["dialableMtgId"] = meeting_info_state["_raw_elements"][9].text # V
                    schedule_params_forms["durationMin"] = meeting_info_state["_raw_elements"][10].text # V
                    schedule_params_forms["entryAnnouncement"] = meeting_info_state["_raw_elements"][12].text # V
                    schedule_params_forms["exitAnnouncement"] = meeting_info_state["_raw_elements"][13].text # V
                    schedule_params_forms["invitees"] = invitees # <<-------
                    schedule_params_forms["meetingTemplateId"] = meeting_info_state["_raw_elements"][35].text # V
                    schedule_params_forms["meetingTemplateName"] = meeting_info_state["_raw_elements"][36].text # V
                    schedule_params_forms["meetingType"] = meeting_info_state["_raw_elements"][37].text # V
                    schedule_params_forms["initialPartNum"] = 0
                    schedule_params_forms["schedulerUniqueId"] = 0
                    # schedule_params_forms["password"] = self.meeting_password_field.text()
                    schedule_params_forms["whoCanAttend"] = meeting_info_state["_raw_elements"][91].text # V
                    schedule_params_forms["outdialOnFirstCaller"] = meeting_info_state["_raw_elements"][43].text
                    reschedule_meeting(zeep=get_zeeper().get_current_zeep(), uid=self.uid, schedule_params=schedule_params_forms)
                    # print(schedule_params_forms)
                    # self.parent.debug_page.debug_box.add_line_space()
                    self.parent.debug_page.debug_box.add_line("finished updating to desired password")
                    # print("finished updating to desired password")
        
        if "cms" in self.parent.current_server:
            new_password = self.meeting_password_field.text()
            if new_password == self.current_password:
                self.parent.debug_page.debug_box.add_line_space()
                self.parent.debug_page.debug_box.add_line("nothing to change , requested password is the same as the setted one")
                self.close()
            else:
                resp = self.parent.cms_client.update_password(meeting_id=self.current_meeting_uid, new_password=new_password)
                if resp == "success":
                    self.parent.debug_page.debug_box.add_line_space()
                    self.parent.debug_page.debug_box.add_line("changed the password from - "+self.current_password+" to - "+new_password)
                else:
                    self.parent.debug_page.debug_box.add_line_space()
                    self.parent.debug_page.debug_box.add_line("failed to change the password")
                self.close()
        
        self.close()

    def display_element(self, table_widget, row, col):#TODO:Need to clear the window each time
        # cleaning the window
        self.clean_window()

        # general variables settings
        self.selected_element = None
        self.remove_invitees = []

        selected_row = [table_widget.item(row, col).text() for col in range(table_widget.columnCount())]

        if "cms" not in self.parent.current_server:
            self.invitees_table_lable.show()
            self.invitees_table.show()
            self.end_meeting_button.show()

            self.opened_meeting = selected_row[0]
            self.uid = selected_row[3]
            self.meeting_id_label.setText("Meeting ID : " + selected_row[0])
            # self.meeting_password.setText("Password : " + selected_row[1])
            self.meeting_password_field.setText(selected_row[1])
            self.meeting_status.setText("Status : " + selected_row[2])

            all_meetings = []
            try:
                meetings = get_meetings_with_invitees(get_zeeper().get_current_zeep(), selected_row[0])
                for meeting in meetings:
                    if meeting['_raw_elements'][11].text == "IN_SESSION":
                        all_meetings.append(meeting)
            except:
                self.parent.debug_page.debug_box.add_line_space()
                self.parent.debug_page.debug_box.add_line("meeting - "+str(mm)+" was not found")
                # print("meeting -",mm,"was not found")

            if len(all_meetings) > 0:
                preconf_invitees = self.get_invitees(all_meetings[0])
                self.invitees_table.set_elements(data=preconf_invitees)
                self.invitees_table.display_elements()
                if len(preconf_invitees) > 0:
                    self.original_invitees = self.invitees_table.get_table_data()

        if "cms" in self.parent.current_server:
            self.invitees_table_lable.hide()
            self.invitees_table.hide()
            self.end_meeting_button.hide()

            # print(selected_row)
            self.current_meeting_uid = selected_row[0]
            self.meeting_id_label.setText("Meeting ID : " + selected_row[2])
            self.meeting_status.setText("Status : Available")

            meeting_details = self.parent.cms_client.get_meeting_details(meeting_id=selected_row[0])
            self.current_password = str(meeting_details[0]['password'])
            self.meeting_password_field.setText(self.current_password)

        self.exec()

    def clean_window(self):
        self.meeting_id_label.setText("Meeting ID : ")
        self.meeting_password_field.setText("")
        self.meeting_status.setText("Status : ")
        self.invitees_table.clear_table()

    def get_invitees(self, meeting):
        all_invitees = []
        for user in meeting["_raw_elements"][1]:
            # print(user[3].text)
            if user[5].text is not None and user[3].text != "false": # checks if invitee is not a guest and that he has a number
                all_invitees.append({"Participant Number": user[5].text})
        # print(all_invitees)
        return all_invitees

    def get_participants(self, participants):
        all_participants = []

        if len(participants) > 0:
            for par in participants["_raw_elements"]:
                par_number = par[5].text
                all_participants.append({'Participant Number': par_number})
            return all_participants
        return

    def add_empty_space(self):
        # print(self.opened_meeting)
        if self.opened_meeting[0:2] == "57":
            previous_data = self.invitees_table.get_table_data()
            empty_space = {}
            for header in self.invitees_table.data[0]:
                empty_space[header] = ""
            previous_data.append(empty_space)
            new_data = previous_data
            self.invitees_table.set_elements(data=new_data)
            self.invitees_table.display_elements()
        else:
            self.parent.debug_page.debug_box.add_line_space()
            self.parent.debug_page.debug_box.add_line("not a blast dial meeting")
            # print("not a blast dial meeting")

    def remove_space(self):
        if self.selected_element != None:
            if self.opened_meeting[0:2] == "57":
                previous_data = self.invitees_table.get_table_data()
                new_data = []
                self.parent.debug_page.debug_box.add_line_space()
                self.parent.debug_page.debug_box.add_line("all data - "+str(previous_data))
                # print("all data - ", previous_data)
                self.parent.debug_page.debug_box.add_line_space()
                self.parent.debug_page.debug_box.add_line("selected item for removel - "+str(self.selected_element))
                # print("selected item for removel - ", self.selected_element)
                self.remove_invitees.append(self.selected_element)
                for data_key in previous_data:
                    if data_key['Participant Number'] != self.selected_element:
                        new_data.append({'Participant Number':data_key['Participant Number']})
                try:
                    self.invitees_table.set_elements(new_data)
                    self.invitees_table.display_elements()
                except:
                    self.parent.debug_page.debug_box.add_line_space()
                    self.parent.debug_page.debug_box.add_line("was not able to update the table")
                    # print("was not able to update the table")
            else:
                self.parent.debug_page.debug_box.add_line_space()
                self.parent.debug_page.debug_box.add_line("not a blast dial meeting")
                # print("not a blast dial meeting")
        else:
            self.parent.debug_page.debug_box.add_line_space()
            self.parent.debug_page.debug_box.add_line("no element was selected")
            # print("no element was selected")

    def selected_item(self, table_widget, row, col):
        selected_row = [table_widget.item(row, col).text() for col in range(table_widget.columnCount())]
        self.selected_element = selected_row[0]
        # print(self.selected_element)

class AddMeetings(QDialog):
    def __init__(self, parent=None):
        super().__init__()

        # general variables
        self.parent = parent
        self.zeeper = get_zeeper()

        # setting the layout
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignTop)

        # adding the main label
        main_label = CustomPyside.set_label_font("Add Meetings", 20)
        main_label.setObjectName("widget_label")
        layout.addWidget(main_label)

        # adding the tab widget
        self.tab_widget = QTabWidget()
        self.add_mm_widget = AddMM()
        self.add_preconf_meetings = AddPreconf()
        self.tab_widget.addTab(self.add_mm_widget, "Add MM Meetings")
        self.tab_widget.addTab(self.add_preconf_meetings, "Add Preconf Meetings")
        layout.addWidget(self.tab_widget)

        # setting the layout
        self.setLayout(layout)

    def display_element(self):
        if "cms" not in self.parent.current_server:
            self.add_mm_widget.reset(filter=[{'Meeting ID': '', 'Meeting Password': '', 'Meeting Name': ''}])
            self.add_preconf_meetings.reset(filter=[{'Participants': ''}])
            self.exec()
        elif "cms" in self.parent.current_server:
            return

class AddMM(QDialog):
    def __init__(self, parent=None):
        super().__init__()

        # general variables
        self.zeeper = get_zeeper()
        self.display_data = [{"Meeting ID": "", "Meeting Password": "", "Meeting Name": ""}]
        self.thread_manager = QThreadPool()

        # setting the layout
        add_meetings_layout = QVBoxLayout()
        add_meetings_layout.setSpacing(20)
        add_meetings_layout.setAlignment(Qt.AlignTop)

        # -------------------------------------------------------------------------------------

        # adding the meetings table
        self.meetings_table = CustomPyside.SmartTable(dialog_window=None, editable_lines=True, tool_bar_actions=True,
                                                      add_default_action=True)
        self.meetings_table.add_data.triggered.connect(self.add_empty_space)
        self.meetings_table.set_elements(data=self.display_data)
        self.meetings_table.display_elements()
        add_meetings_layout.addWidget(self.meetings_table)

        # adding the add meetings button
        self.create_meetings_button = QPushButton("Create Meetings")
        self.create_meetings_button.setObjectName("action_button")
        self.create_meetings_button.clicked.connect(self.create_meetings)
        add_meetings_layout.addWidget(self.create_meetings_button)

        # setting the layout
        self.setLayout(add_meetings_layout)

    # @Slot()
    def req_func(self):
        self.thread_manager.start(self.create_meetings)
        pass

    def create_meetings(self):
        print("Trying To Create Meetings")
        zeep = self.zeeper.get_current_zeep()
        meetings_to_create = self.meetings_table.get_table_data()
        for meeting in meetings_to_create:
            meeting_id = meeting["Meeting ID"]
            password = meeting["Meeting Password"]
            try:
                if meeting_id == "":
                    continue
                # print(meeting_id)
                # print(password)
                create_restricted_meeting(zeep, meeting_id, password, invitees=[])
                # delete_restricted_meeting(zeep, meeting_id)
            except Exception as err:
                print("Failed To Create Meeting :", meeting_id)
                logger.info(f"failed to create meeting : {err}")
                continue

        # create_restricted_meeting(zeep, meeting_id, password, invitees)

    def add_empty_space(self):
        previous_data = self.meetings_table.get_table_data()
        empty_space = {}
        for header in self.meetings_table.data[0]:
            empty_space[header] = ""
        previous_data.append(empty_space)
        new_data = previous_data
        self.meetings_table.set_elements(data=new_data)
        self.meetings_table.display_elements()

    def display_element(self):
        self.exec()

    def reset(self, filter=[{"field 1":""}]):
        # print(filter)
        self.meetings_table.set_elements(data=filter)
        self.meetings_table.display_elements()

class AddPreconf(QDialog):
    def __init__(self, parent=None):
        super().__init__()

        # general variables
        self.zeeper = get_zeeper()
        self.display_data = [{"Participants": ""}]
        main_font_size = 20
        secondary_font_size = 17
        third_font_size = 12
        font = QFont()

        # setting the layout
        add_preconf_layout = QVBoxLayout()
        add_preconf_layout.setSpacing(20)
        add_preconf_layout.setAlignment(Qt.AlignTop)

        # -------------------------------------------------------------------------------------
        # adding the preconf number
        font.setPointSize(third_font_size)
        meeting_id_label = QLabel("Preconf Number")
        meeting_id_label.setObjectName("widget_label")
        meeting_id_label.setFont(font)
        add_preconf_layout.addWidget(meeting_id_label)
        self.meeting_id_field = CustomPyside.RoundedTextLine("")
        add_preconf_layout.addWidget(self.meeting_id_field)

        # adding the preconf subject
        preconf_subject_label = QLabel("Preconf Subject")
        preconf_subject_label.setObjectName("widget_label")
        preconf_subject_label.setFont(font)
        add_preconf_layout.addWidget(preconf_subject_label)
        self.preconf_subject_field = CustomPyside.RoundedTextLine("Meeting Place Preconf")
        add_preconf_layout.addWidget(self.preconf_subject_field)

        # adding the meetings table
        self.meetings_table = CustomPyside.SmartTable(dialog_window=None, editable_lines=True, tool_bar_actions=True,
                                                      add_default_action=True)
        self.meetings_table.add_data.triggered.connect(self.add_empty_space)
        self.meetings_table.set_elements(data=self.display_data)
        self.meetings_table.display_elements()
        add_preconf_layout.addWidget(self.meetings_table)

        # adding the add meetings button
        self.create_meetings_button = QPushButton("Create Meetings")
        self.create_meetings_button.setObjectName("action_button")
        self.create_meetings_button.clicked.connect(self.create_meetings)
        add_preconf_layout.addWidget(self.create_meetings_button)

        # setting the layout
        self.setLayout(add_preconf_layout)

    # @Slot()
    def req_func(self):
        self.thread_manager.start(self.create_meetings)
        pass

    def create_meetings(self):
        zeep = self.zeeper.get_current_zeep()
        print("Trying To Create The Preconf")

        preconf_id = self.meeting_id_field.text()
        preconf_subject = self.preconf_subject_field.text()

        preconf_users = []
        preconf_mm = []

        participants = self.meetings_table.get_table_data()
        for participant in participants:
            for element in participant:
                if participant[element][0:3] == "777":
                    preconf_mm.append(participant[element])
                else:
                    preconf_users.append(participant[element])
        
        print("preconf id",preconf_id) 
        print("preconf subject",preconf_subject)
        print("users",preconf_users)
        print("meetings",preconf_mm)
        
        # creates the preconf with the specified details
        self.create_preconf(zeep=zeep, preconf_id=preconf_id, preconf_subject=preconf_subject, preconf_users=preconf_users, preconf_mm=preconf_mm)

    def create_preconf(self, zeep, preconf_id, preconf_subject, preconf_users, preconf_mm): 
        # summerize all the users that need to be in the server
        all_users = preconf_users
        for mm in preconf_mm:
            # checks if the mm exists and if not it creates it ( without password as it should be )
            if self.check_mm(mm=mm) != "invalid meeting":
                # adds the mm to the list of users
                all_users.append(mm)
        
        # checks if all the invitees are in the server and if not it creates them 
        all_users = self.check_invitees(zeep=zeep, invitees_list=all_users)
        # # creates the preconf meeting
        create_scheduled_preconf(zeep=zeep, preconf_id=preconf_id, preconf_subject=preconf_subject, invitees=all_users)

    # need to check more cases
    def check_mm(self, mm=None):
        zeep = get_zeeper().get_current_zeep()
        original_ip = get_zeeper().current_ip
        print(zeep,original_ip)
        if len(mm) == 7:
            if mm[0:4] == "573" or mm[0:4] == "573":
                print("trying to search in zrifin main")
                if get_zeeper().current_ip != "180.100.216.104":
                    zeep = get_zeeper().initialize_zeep("zrifin-777[1/6]XXX-meetings")
                response = get_meeting(zeep=get_zeeper().get_current_zeep(), meeting_id=mm)
                if response == None:
                    create_scheduled_meeting(zeep=get_zeeper().get_current_zeep(), meeting_id=mm) # a password is never given for a mm in a preconf as it should be

            elif mm[0:4] == "575" or mm[0:4] == "575":
                print("trying to search in kirya main")
                if get_zeeper().current_ip != "180.200.216.105":
                    zeep = get_zeeper().initialize_zeep("kirya-main-777[7/9]XXX-meetings")
                response = get_meeting(zeep=get_zeeper().get_current_zeep(), meeting_id=mm)
                if response == None:
                    create_scheduled_meeting(zeep=get_zeeper().get_current_zeep(), meeting_id=mm) # a password is never given for a mm in a preconf as it should be

            elif mm[0:4] == "573":
                print("trying to search in kirya backup")
                if get_zeeper().current_ip != "180.100.216.105":
                    zeep = get_zeeper().initialize_zeep("kirya-7773XXX-meetings")
                response = get_meeting(zeep=get_zeeper().get_current_zeep(), meeting_id=mm)
                if response == None:
                    create_scheduled_meeting(zeep=get_zeeper().get_current_zeep(), meeting_id=mm) # a password is never given for a mm in a preconf as it should be
                    
            elif mm[0:4] == "575":
                print("not going to search in cms")

            if original_ip == "180.100.216.104":
                zeep = get_zeeper().initialize_zeep("zrifin-777[1/6]XXX-meetings")
            if original_ip == "180.200.216.105":
                zeep = get_zeeper().initialize_zeep("kirya-main-777[7/9]XXX-meetings")
            if original_ip == "180.100.216.105":
                zeep = get_zeeper().initialize_zeep("kirya-7773XXX-meetings")
            if original_ip == "180.200.226.104":
                zeep = get_zeeper().initialize_zeep("lab")

            return "meeting was in standard"
        else:
            return "invalid meeting"

    def check_invitees(self, zeep=None, invitees_list=None):
        print("all invitees", invitees_list)
        checked_invitees = []
        # the invitee number is the real number to dial out to
        for invitee in invitees_list:
            user_response = get_user(zeep=zeep, user_id=invitee)
            user_found = False
            if user_response == None:
                response = create_user(zeep=zeep, user_id=invitee)
                checked_invitees.append(invitee)
            else:
                # print(user_response)
                for user in user_response:
                    if user['outdialPhone'] == invitee and user['firstName'] == "autoanswerdevice":
                        checked_invitees.append(user['userId'])
                        user_found = True
                        # print(user)
                        break
                if user_found == False:
                    print("there was no user for the invitee",invitee,"that was with a good outdial number")
                    try:
                        response = create_user(zeep=zeep, user_id=invitee, user_fields=invitee+"a"+invitee) # user_id = outdial
                        if response != None:
                            checked_invitees.append(invitee+"a"+invitee)
                            print("created user for",invitee)
                    except Exception as err:
                        print("there was an error to create the user",invitee,err)
        
        print("invitees :",checked_invitees) # prints the invitees by their user_name tha have the correct outdial
        return checked_invitees

    # --------------------------------GUI FUNCTIONS--------------------------------
    def add_empty_space(self):
        previous_data = self.meetings_table.get_table_data()
        empty_space = {}
        for header in self.meetings_table.data[0]:
            empty_space[header] = ""
        previous_data.append(empty_space)
        new_data = previous_data
        self.meetings_table.set_elements(data=new_data)
        self.meetings_table.display_elements()

    def display_element(self):
        self.exec()

    def reset(self, filter=[{"field 1":""}]):
        self.meeting_id_field.setText("")
        # print(filter)
        self.meetings_table.set_elements(data=filter)
        self.meetings_table.display_elements()