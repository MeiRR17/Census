import getpass
import sys
from sys import exit

from requests import Session
from requests.auth import HTTPBasicAuth
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
from zeep import Client, Settings
from zeep.cache import SqliteCache
from zeep.exceptions import Fault
from zeep.transports import Transport
import csv
import datetime
import time
import calendar
import inspect


disable_warnings(InsecureRequestWarning)

username = ""
password = ""
ip_address = ""

wsdl = "api/cucm/schema/current/AXLAPI.wsdl"
binding = "{http://www.cisco.com/AXLAPIService/}AXLAPIBinding"

############## THIS PAGE INCLUDE FUNCTIONS FOR THE CUCM EXTRACTOR APP AND MORE ###################################
class ZeepSingle(object):
    def __set_vars(self, ip_address,username,password): # I DID THIS BECAUSE IF WE REALLY WANT TO CHANGE THE ZEEP SINGLE SERVER CONNECTION WE CAN USE THIS FUNCTION AND CALL get_service
        self.ip_address = ip_address
        self.username = username
        self.password = password
        self.service = None
        self.static_init = False
        self.vars_changed = True

    def __init__(self,ip_address,username,password):
        # if ZeepSingle.static_init: return
        # ZeepSingle.static_init = True
        self.__set_vars(ip_address,username,password)
        self.service = self.create_service()
        print("connecting to",self.ip_address)

    def create_service(self):
        service_url = "https://{}:8443/axl/".format(self.ip_address)

        session = Session()
        session.verify = False
        session.auth = HTTPBasicAuth(self.username, self.password)

        settings = Settings(strict=False)

        transport = Transport(cache=SqliteCache(), session=session, timeout=20)
        client = Client(wsdl=wsdl, transport=transport, settings=settings)
        service = client.create_service(binding, service_url)
        
        return service
    
    ## creating user
    def create_user(self, user_id):
        try:
            user_data = {
                'firstName' : user_id,
                'lastName' : user_id,
                'userid' : user_id,
                'password' : "123456",
                'pin' : "123456",
                'userLocale' : "Hebrew Israel",
                'digestCredentials' : "123456", 
                'presenceGroupName': {
                '_value_1': 'Standard Presence group'
                }
            }
            self.service.addUser(user_data)
            return "User Created"
        except:
            print("User Exists")
            return "User Exists"
    
    ##create profile
    def create_profile(self, profile_id, name):
        # print(name)
        try:
            resp = self.service.getPhone(name=name, returnedTags=
                {
                    'product':"",
                    'model':"",
                    'protocol': "",
                    'protocolSide': "",
                    'userLocale': "",
                    'phoneTemplateName':""  
                })["return"]["phone"]

            # phone_button_template = resp['phoneTemplateName']
            # print(phone_button_template)

            profile_data = {
                    'name': profile_id,
                    'description': profile_id,
                    'product': resp['product'],
                    'model': resp['model'],
                    'class': 'Device Profile',
                    'protocol': resp['protocol'],
                    'protocolSide': resp['protocolSide'],
                    'userLocale': resp['userLocale'],
                    'softkeyTemplateName': {'_value_1': 'Standard User'}, ### need to change to standart sapir
                    'phoneTemplateName': resp['phoneTemplateName']
                     
            }
            
            self.service.addDeviceProfile(profile_data)
            return "Profile Created"
        except:
            print("Profile Exists")
            return "Profile Exists"

    ###assosiate the profile to the user        
    def associate_user(self, user_id, profile_id):
        try:
            res = self.service.getUser(userid=user_id, returnedTags={"phoneProfiles" : ""})
            user = res['return']['user']

            user['phoneProfiles'] = {'profileName': [
                                                        {
                                                        '_value_1': profile_id  
                                                        }
                                                    ]   
                    }

            res = self.service.updateUser(userid=user_id, phoneProfiles = user['phoneProfiles'])
            print("USERsd")
            return "User Associated"
        except:
            print("User Not Associated")
            return "User Not Associated"

    #### copying from mac to profile
    def copy_mac_lines_to_profile(self, profile_id, name):
        try:
            resp_mac = self.service.getPhone(
                    name=name,
                    returnedTags={
                        "lines": {
                            "line": {
                                "index": "",
                                "label": "",
                                "display": "",
                                "dirn": {"pattern": ""},
                            }
                        }
                    },
                )["return"]["phone"]["lines"]

            self.service.updateDeviceProfile(name=profile_id,lines=resp_mac)
            print("Success to copy lines")
            return "Success"

        except:
            print("FAILED TO COPY LINES")
            return "Failed"

    def copy_mac_blfs_to_profile(self, profile_id, name):
        try:
            resp_mac = self.service.getPhone(
                    name=name,
                    returnedTags={
                        "busyLampFields":{"busyLampField":{"blfDest":"","label":"","blfDirn":"","routePartition":"","associatedBlfSdFeatures":"","index":""}},
                        "speeddials": {"speeddial":{"dirn":"","label":"","index":""}}
                    }
                )["return"]["phone"]

            mac_sd = resp_mac['speeddials']
            mac_blfs = resp_mac['busyLampFields']
            # print(mac_sd)
            self.service.updateDeviceProfile(name=profile_id, busyLampFields=mac_blfs, speeddials=mac_sd)
            print("Success to copy blfs")
            return "Success"
           
        except:
            print("FAILED TO COPY BLFS")
            return "Failed to copy blfs"
        # service.addProfile(profile_data)

    def copy_mac_settings_to_profile(self, profile, mac):
        status0 = self.create_profile(profile_id=profile, name=mac)
        status1=self.copy_mac_lines_to_profile(profile, mac)
        status2 = self.copy_mac_blfs_to_profile(profile, mac)
        return {"PROFILE": profile, "MAC":mac, "LINES STATUS": status1, "BLFS STATUS": status2, "PROFILE STATUS": status0}

    # ------------------------------------------------------------------

    ##copying from profile to mac
    def copy_profile_lines_to_mac(self, profile_id, name):
        try:
            resp_profile = self.service.getDeviceProfile(
                    name=profile_id,
                    returnedTags={
                        'lines':{
                            "line": {
                                "index": "",
                                "label": "",
                                "display": "",
                                "dirn": {"pattern": ""},
                            }
                        }
                    },
                )["return"]['deviceProfile']['lines']

            # print(resp_profile)
            self.service.updatePhone(name=name,lines=resp_profile)
            return "Success"
        except Exception as e:
            print(e)
            return "Failed"

    def copy_profile_blfs_to_mac(self, profile_id, name):
        try:
            resp_profile = self.service.getDeviceProfile(
                    name=profile_id,
                    returnedTags={
                        "busyLampFields":{"busyLampField":{"blfDest":"","label":"","blfDirn":"","routePartition":"","associatedBlfSdFeatures":"","index":""}},
                        "speeddials": {"speeddial":{"dirn":"","label":"","index":""}},
                        "phoneTemplateName":""
                    }
                )["return"]['deviceProfile']

            profile_sd = resp_profile['speeddials']
            profile_blfs = resp_profile['busyLampFields']
            profile_template = resp_profile['phoneTemplateName']
            # print(profile_template)
            self.service.updatePhone(name=name, busyLampFields=profile_blfs, speeddials=profile_sd, phoneTemplateName=profile_template)
            return "Success"
        except Exception as e:
            print(e)
            return "Failed"

    def copy_profile_settings_to_mac(self, profile, mac):
        # print(1)
        status1 = self.copy_profile_lines_to_mac(profile, mac)
        status2 = self.copy_profile_blfs_to_mac(profile, mac)
        return {"PROFILE": profile, "MAC":mac, "LINES STATUS": status1, "BLFS STATUS": status2}

    def get_service(self):
        if not self.service or self.vars_changed:
            self.service = self.create_service()
            self.vars_changed = False
        return self.service  

    def get_phone_displays(self, name):
        print(self.service.getCCMVersion())

    def get_enduser_devices(self, device_name):

        sql_query = f"""
        SELECT eu.userid
        FROM enduser eu
        INNER JOIN enduserdevicemap eudm ON eu.pkid = eudm.fkenduser
        INNER JOIN device d ON eudm.fkdevice = d.pkid
        WHERE d.name = '{device_name}'
        """

        user_ids = []

        try:
            resp = self.service.executeSQLQuery(sql=sql_query)

            if 'return' in resp and resp['return'] is not None:
                rows = resp['return']['row']

                for row in rows:
                    user_ids.append(row[0].text if hasattr(row[0], 'text') else row[0])
            
            else:
                print("No users found!")
            
            return user_ids
        except Exception as e:
            print(f"SQLQuery error:{e}")
        
    def get_profile_by_uuid_displays(self, service, uuid):
        if not uuid:
            displays = {
                "index": line.index,
                "dirn": line.dirn.pattern,
                "label": line.label,
                "display": line.display,
                "name": resp.name
            }
            return displays

        try:
            resp = service.getDeviceProfile(
                uuid=uuid,
                returnedTags={
                    "name":"",
                    "lines": {
                        "line": {
                            "index": "",
                            "label": "",
                            "display": "",
                            "dirn": {"pattern": ""},
                        }
                    }
                },
            )["return"]["deviceProfile"]
        
            line = resp["lines"]["line"]

            for l in line:
                if l.index == 1:
                    line = l
                    break

            displays = {
                "index": line.index,
                "dirn": line.dirn.pattern,
                "label": line.label,
                "display": line.display,
                "name": resp.name
            }

            return displays

        except Fault as f:
            print(f.message)
            return None
    
    def get_phone_details(self,mac=None):
        # print(11)
        first_line = True   
        mac = mac
        # print(self.service.getCCMVersion()) 
        displays = {}
        try:
            resp = self.service.getPhone(
                name=mac,
                returnedTags={
                    "currentProfileName" :{"uuid":""},
                    "lines": {
                        "line": {
                            "index": "",
                            "label": "",
                            "display": "",
                            "dirn": {"pattern": ""},
                        }
                    },
                    "loginUserId": ""
                },
            )["return"]["phone"]

            if not resp:
                displays = {
                    "index": None,
                    "dirn": None,
                    "label": None,
                    "display": None,
                    "profile": None,
                }
                return displays

            if resp["lines"]:

                line = resp["lines"]["line"][0]

                displays = {
                "index": line.index,
                "dirn": line.dirn.pattern,
                "label": line.label,
                "display": line.display,
                "profile": resp.currentProfileName.uuid
                }
            else:
                displays = {
                    "index": None,
                    "dirn": None,
                    "label": None,
                    "display": None,
                    "profile": resp.currentProfileName.uuid
                }

        except Fault as f:
            print(f.message)
            displays = {
                "index": None,
                "dirn": None,
                "label": None,
                "display": None,
                "profile": None,
                } 

        profile = {"name":"","dirn":""}
    
        phone = displays

        if phone['profile']:
            profile = self.get_profile_by_uuid_displays(self.service, phone['profile'])
            login_id = resp['loginUserId']

        else:
            login_id = None
            profile['name'] = None
            profile['dirn'] = None


        ##### adding the user assosiated
       

        associated_user_ids = self.get_enduser_devices(mac)
        associated_user_ids.extend(['None','None']) # to add more fields
        associated_user_ids = associated_user_ids[:2]
        
        to_add = (mac, phone['dirn'], phone['label'], profile['name'], profile['dirn'], login_id, associated_user_ids[0], associated_user_ids[1])
        list_to_add = list(to_add)

        for i in range(1, len(list_to_add)):
            if not list_to_add[i]:
                list_to_add[i] = "None"

        dic_to_add = {
            "MAC":list_to_add[0],
            "DN mac":list_to_add[1],
            "Name of dn on mac":list_to_add[2],
            "Profile Name":list_to_add[3],
            "Profile DN":list_to_add[4],
            "Connected User Id": list_to_add[5],
            "User Id - 1": list_to_add[6],
            "User Id - 2": list_to_add[7]
        }
        
        return dic_to_add

    def get_dn_details(self, user_input="", condition='Contains', categories=['']):
        sql_request = """SELECT d.name AS device_name, d.tkmodel AS device_model,
                                                    dn.dnorpattern AS device_number,
                                                    d.description AS device_description
                                                    
                                                    FROM device AS d JOIN 
                                                    devicenumplanmap AS dnpm ON dnpm.fkdevice = d.pkid
                                                    JOIN numplan AS dn ON dn.pkid = dnpm.fknumplan
                                                    WHERE dn.dnorpattern LIKE """  
        if condition == 'Begins With':
            sql_request = sql_request + "'" + user_input + "%'"
        elif condition == 'Contains':
            sql_request = sql_request + "'%" + user_input + "%'"
        elif condition == 'Ends With':
            sql_request = sql_request + "'%" + user_input + "'"    

        devices_found = self.service.executeSQLQuery(sql_request)
        # print(devices_found)

        # extracts the device name, model, number, description, line lables
        results = None
        for field in devices_found['return']['row']:
            try:
                temp_dict = {}
                temp_dict['device_name'] = field[0].text
                # temp_dict['device_model'] = field[1].text
                temp_dict['device_number'] = field[2].text
                temp_dict['device_description'] = field[3].text
                temp_dict['device_alerting_name'] = self.extract_data_by_dn(field[2].text)
                results = temp_dict
                break # writes only about the first dn
            except Exception as e:
                temp_dict = {}
                temp_dict['device_name'] = "none"
                # temp_dict['device_model'] = field[1].text
                temp_dict['device_number'] = user_input
                temp_dict['device_description'] = "error"
                temp_dict['device_alerting_name'] = "error"
                results = temp_dict
                print(e)
                break
        # print(results)

        return results

    def extract_data_by_dn(self, dn):
        resp_dn = self.service.listLine(
                {
                    'pattern':dn
                    },
                returnedTags={
                    'alertingName':''
                }
            )["return"]["line"][0]["alertingName"]
        print(resp_dn,dn)
        return resp_dn

    ##function to login to profile 
    def do_device_login(self, user_id, profile_name, device_name):

        try:
            resp = self.service.doDeviceLogin(deviceName=device_name, loginDuration=0, profileName=profile_name,userId=user_id)
            
            if resp:
                return {"USER":user_id,"PROFILE":profile_name,"MAC":device_name, "STATUS":"Success"}
            else:
                raise Exception()

        except Exception as e:
            print(e)
            return {"USER":user_id,"PROFILE":profile_name,"MAC":device_name, "STATUS":"Failed"}

    ##function to logut from a device
    def do_device_logout(self, device_name):

        try:
            resp = self.service.doDeviceLogout(deviceName=device_name)

            if resp:
                  return {"MAC":device_name, "STATUS":"Success"}
            else:
                raise Exception()
        except:
            return {"MAC":device_name, "STATUS":"Failed"}
 
    def create_user_and_profile_from_mac(self,profile_id, mac,user_id):
        status1=self.create_user(user_id)
        status2 = self.create_profile(profile_id=profile_id, name=mac)
        status3 = self.copy_mac_lines_to_profile(profile_id= profile_id, name = mac)
        status10=self.copy_mac_blfs_to_profile(profile_id=profile_id, name = mac)
        status4 = self.associate_user(user_id = user_id , profile_id = profile_id)
       
        return {"PROFILE": profile_id, "MAC":mac, "USER":user_id, "USER STATUS":status1, "PROFILE STATUS":status2, "COPY SETTINGS STATUS":status3 ,"ASSOCIATE USER STATUS":status4 }
 
    def close_session(self):
        self.client.transport.session.close()
    
    ###### updated functions noam##############
    def get_service(self):
        if not self.service or self.vars_changed:
            self.service = self.create_service()
            self.vars_changed = False
        return self.service
    
    def sql_get_blfs(self, dn):
        all_blfs = []
        blf_query = "select np.dnorpattern as dn, blf.label, d.name AS device_name, blf.blfdestination from blfspeeddial as blf inner join devicenumplanmap dnpm on blf.fkdevice=dnpm.fkdevice inner join numplan np on dnpm.fknumplan=np.pkid inner join device as d ON d.pkid = dnpm.fkdevice where blfdestination like '{}'".format(dn)
        speeddial_query = "select np.dnorpattern as dn, sd.label, d.name AS device_name, sd.speeddialnumber from speeddial as sd inner join devicenumplanmap dnpm on sd.fkdevice = dnpm.fkdevice inner join numplan np on dnpm.fknumplan = np.pkid inner join device as d ON d.pkid = dnpm.fkdevice where speeddialnumber like '{}'".format(dn)
        query = blf_query + " union " + speeddial_query
        resp = self.service.executeSQLQuery(query)

        try:
            rows = resp['return']['row']
            for row in rows:
                label = row[1].text
                dn = row[0].text
                device = row[2].text
                destination = row[3].text
                temp = {}
                temp['dn'] = dn
                temp['label'] = label
                temp['device_name'] = device
                temp['destination'] = destination
                # temp = {"label":label,"dn":dn}
                # all_blfs.append(temp)

                all_blfs.append(temp)

            # print(all_blfs)
            return all_blfs
        except:
            return ""
    
    def sql_get_devices(self, dn):
        try:
            all_dns = []
            blf_query = "select np.dnorpattern as dn, d.name AS device_name from devicenumplanmap as dnpm inner join numplan as np on dnpm.fknumplan=np.pkid inner join device as d ON d.pkid = dnpm.fkdevice where np.dnorpattern like '{}'".format(dn)

            query = blf_query 
            resp = self.service.executeSQLQuery(query)

            rows = resp['return']['row']
            for row in rows:
                dn = row[0].text
                device = row[1].text
                temp = {}
                temp['dn'] = dn
                temp['device_name'] = device

                all_dns.append(temp)
            
            return all_dns
        except:
            return None

    def update_blf(service, dst_num, new_name):
        sql = r"update blfspeeddial set label = '{}' where blfdestination = {}".format(new_name, dst_num)
        print("SQL: {}".format(sql))
        sql_response = service.executeSQLUpdate(sql)
        print(sql_response)
    
    #ADDD 30.10.24 OSHER&DABASH
    #TODO: add result status of the update functions
    def get_device_details(self, mac):
            resp_mac = self.service.getPhone(
                    name=mac,
                    returnedTags={
                        "lines": {
                            "line": {
                                "index": "",
                                "label": "",
                                "display": "",
                                "dirn": {"pattern": ""},
                                "uuid":"",
                            }
                        },
                        "busyLampFields":{"busyLampField":{"blfDest":"","label":"","blfDirn":"","routePartition":"","associatedBlfSdFeatures":"","index":""}},
                        "speeddials": {"speeddial":{"dirn":"","label":"","index":""}},
                        "phoneTemplateName":""
                    }
                )["return"]["phone"]

            mac_lines = resp_mac['lines']
            mac_sd = resp_mac['speeddials']
            mac_blfs = resp_mac['busyLampFields']
            mac_template_uuid = resp_mac['phoneTemplateName']

            result ={}
            result['lines'] = mac_lines
            result['speeddials'] = mac_sd
            result['busyLampFields'] = mac_blfs
            result['phone_template_uuid'] = mac_template_uuid
            return result

    def update_device(self, device, old_blf, new_blf,new_name):
        original_data = self.get_device_details(mac=device)
        original_data_blfs = []
        original_data_sd = []
        try:
            original_data_blfs = original_data['busyLampFields']['busyLampField']
            for data_set in original_data_blfs:
                if data_set['blfDest'] == old_blf:
                    data_set['blfDest'] = new_blf
                    #print(new_name)
                    data_set['label'] = new_name
        except:
            pass
        # edits the speed dials
        try:
            original_data_sd = original_data['speeddials']['speeddial']
            for data_set in original_data_sd:
                if data_set['dirn'] == old_blf:
                    data_set['dirn'] = new_blf
                    data_set['label'] = new_name
        except:
            pass
        # print(original_data_blfs) 
        resp_device = self.service.updatePhone(
                    name=device,
                    busyLampFields=
                    {
                        'busyLampField':original_data_blfs
                    },
                    speeddials=
                    {
                        'speeddial':original_data_sd
                    }
                )
        return True

    def get_buttons_positions(self, template_id):
        resp = self.service.getPhoneButtonTemplate(uuid=template_id)
        return resp

    def update_buttons(self, template_id, new_buttons):
        self.service.updatePhoneButtonTemplate(uuid=template_id, buttons=new_buttons)

    def convert_nln_to_blf(self, mac, nln=None, new_blf=None):
        mac_details = self.get_device_details(mac=mac)
        mac_buttons_template_id = mac_details['phone_template_uuid']['uuid']
        resp = service.get_buttons_positions(template_id=mac_buttons_template_id)
        mac_buttons = resp['return']['phoneButtonTemplate']['buttons']
        new_buttons = {
                'button': [
                    {
                        'feature': 'Line',
                        'label': 'Line 2',
                        'buttonNumber': 2,
                    }
                ]
            } 
        self.update_buttons(mac_buttons_template_id, new_buttons)

    def get_line(self, uuid):
        response = self.service.getLine(uuid=uuid)
        return response

    def get_line_devices(self, uuid):
        response = self.service.getLine(
                uuid=uuid,
                returnedTags={
                    'associatedDevices':""
                })
        return response['return']['line']['associatedDevices']['device']

    def update_line_dn(self, unique_id, new_dn):
        response = self.service.updateLine(uuid=unique_id, newPattern=new_dn)
        return response

    def find_lines(self, line):
        lines_found = self.service.listLine(
            searchCriteria=line,
            returnedTags={
                            'uuid':"",
                            'pattern':""
                        })
        try:
            temp = {}
            for line_element in lines_found['return']['line']:
                pattern = line_element['pattern']
                uuid = line_element['uuid']
                temp[pattern] = uuid
            # print(lines_found['return']['line'])
            return temp
        except:
            return "error with"+line

    def open_nln_data(file_name):
        with open(file_name,'r',newline='',encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile,delimiter=',')
            reading_header = True
            output_data = []
            for row in reader:
                temp = {}
                temp['calling_number_device_name_cucm'] = row[2]
                if reading_header == False:
                    if row[2] != 'not found in the cucm':
                        output_data.append(row[2])
                reading_header = False

            return output_data

    def save_to_csv(data, file_name):
        # print(data)
        with open(file_name, mode='w', newline='', encoding='utf-8-sig') as file:
            writer = csv.DictWriter(file, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data) 
    
    def get_mac_kitzorim(self, uuid):
        resp_mac = self.service.getPhone(
            name=uuid,
            returnedTags={
                "busyLampFields":{"busyLampField":{"blfDest":"","label":"","blfDirn":"","routePartition":"","associatedBlfSdFeatures":"","index":""}},
                "speeddials": {"speeddial":{"dirn":"","label":"","index":""}},
                "phoneTemplateName":""
            }
        )["return"]["phone"]

        mac_sd = resp_mac['speeddials']
        mac_blfs = resp_mac['busyLampFields']

        result={}
        #result['speeddials'] = mac_sd
        result['busyLampFields'] = mac_blfs
        return result    

    def get_mac_kitzorim_sd(self,uuid):
        resp_mac = self.service.getPhone(
            name=uuid,
            returnedTags={
                "busyLampFields":{"busyLampField":{"blfDest":"","label":"","blfDirn":"","routePartition":"","associatedBlfSdFeatures":"","index":""}},
                "speeddials": {"speeddial":{"dirn":"","label":"","index":""}},
                "phoneTemplateName":""
            }
        )["return"]["phone"]

        mac_sd = resp_mac['speeddials']
        mac_blfs = resp_mac['busyLampFields']

        result={}
        result['speeddials'] = mac_sd
        #result['busyLampFields'] = mac_blfs
        return result

    def update_line_alerting_name(self, unique_id, new_alerting_name,mac):
        result = self.get_device_details(mac=mac)
        result_uuid = result["lines"]["line"][0]["dirn"]["uuid"]
        response = self.service.updateLine(uuid=result_uuid, alertingName=new_alerting_name)
        return response

    def update_line_display_name_and_label(self, name="", new_display_name="", new_label_name="",line=""):
        try:
            if name != "":
                result = self.get_device_details(mac=name)
                result_uuid = result["lines"]["line"][0]["dirn"]["uuid"]
                result_partition = result["lines"]["line"][0]["dirn"]["routePartitionName"]
                result_number = result["lines"]["line"][0]["dirn"]["pattern"]
                if new_display_name != "" and new_label_name != "":
                    response = self.service.updatePhone(
                                            name=name, 
                                            lines={
                                            'line':[{
                                                'index':1,
                                                'label':new_label_name,
                                                'display':new_display_name,
                                                'dirn':{
                                                    'pattern': result_number,
                                                    'routePartitionName':result_partition,
                                                    'uuid': result_uuid
                                                }
                                                }]
                                            })
            
            if response:
                return {"MAC":name,"Line":line, "STATUS":"Success"}
        except Exception as e:
            print(e)
            return {"MAC":name,"Line":line, "STATUS":"Failed"}      