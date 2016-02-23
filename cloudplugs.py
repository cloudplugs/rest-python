import requests
import json

from cp_rest import CP_HTTP_RESULT, CP_ERR_CODE
from cp_internals import CP_HTTP_METHOD

version = "1.0"


class CloudPlugs(object):
    CP_TIMEOUT = 60
    CP_URL = "https://api.cloudplugs.com/iot/"

    CP_OK = 0
    CP_FAIL = 1

    PLUG_AUTH_HEADER = "X-Plug-Auth"  ## CloudPlugs Header for auth/password
    PLUG_ID_HEADER = "X-Plug-Id"  ## CloudPlugs Header for device id
    PLUG_EMAIL_HEADER = "X-Plug-Email"  ## CloudPlugs Header for master email
    PLUG_MASTER_HEADER = "X-Plug-Master"  ## CloudPlugs Header for master auth/password

    PATH_DATA = "data"
    PATH_DEVICE = "device"
    PATH_CHANNEL = "channel"

    CTRL = "ctrl"
    HWID = "hwid"
    NAME = "name"
    MODEL = "model"
    PASS = "pass"
    PERM = "perm"
    PROPS = "props"
    DATA = "data"
    BEFORE = "before"
    AFTER = "after"
    OF = "of"
    OFFSET = "offset"
    LIMIT = "limit"
    AUTH = "auth"
    ID = "id"
    AT = "at"

    LOCATION = "location"
    LONGITUDE = "x"
    LATITUDE = "y"
    ACCURACY = "r"
    ALTITUDE = "z"
    TIMESTAMP = "t"
    MAX_LONGITUDE = 180.0
    MIN_LONGITUDE = -180.0
    MAX_LATITUDE = 90.0
    MIN_LATITUDE = -90.0

    CP_HTTP_STR = "http://"
    CP_HTTPS_STR = "https://"

    # Internal use
    _CP_ID = 'id'
    _CP_AUTH = 'auth'

    ##  Constructor
    #   @param self The object pointer
    def __init__(self):
        self.timeout = CloudPlugs.CP_TIMEOUT # timeout value for HTTP requests (in seconds)
        self.cp_id = None  # id is a built-in function, so using cp_id
        self.cp_auth = None  # use cp_... for consistency with cp_id
        self.cp_headers = {}  # id plug-related headers
        self.is_master = False
        self.base_url = CloudPlugs.CP_URL
        self.http_res = 0
        self.err = 0
        self.err_string = None
        self.result = None  # request class response/results
        self.session = requests.Session()

    ## Change the default base url
    #   @param self The object pointer
    #   @param url The new URL
    #   @return TRUE if the new base url is set correctly, FALSE otherwise.
    def set_base_url(self, url):

        if not url:
            return self.set_error(CP_ERR_CODE.CP_ERR_INVALID_PARAMETER)

        if url.startswith(CloudPlugs.CP_HTTP_STR) or \
                url.startswith(CloudPlugs.CP_HTTPS_STR):
            self.base_url = url
            if url[-1:] != '/':
                self.base_url += '/'
            return CloudPlugs.CP_OK

        else:
            return self.set_error(CP_ERR_CODE.CP_ERR_INVALID_PARAMETER)

    ##  Change the default timeout
    #   @param self The object pointer
    #   @param timeout The new timeout value in seconds
    #   @return TRUE if the new base url is set correctly,FALSE otherwise.
    def set_timeout(self, timeout):

        if timeout >= 0:
            if timeout:
                self.timeout = timeout
            else:
                self.timeout = CloudPlugs.CP_TIMEOUT
            return CloudPlugs.CP_OK

        return CloudPlugs.CP_FAIL

    ##  Get the current timeout.
    #   @param self The object pointer
    #   @return The current timeout in seconds.
    def get_timeout(self):

        return self.timeout

    ##  Set the session authentication credentials.
    #   @param self The object pointer
    #   @param cp_id: A string containing the @ref details_PLUG_ID or the master email
    #   @param cp_pass: A string containing the authentication code.
    #   @param is_master: True for using master authentication in the session; False for using regular authentication.
    #   @return TRUE if the authentication is set correctly, FALSE otherwise.
    def set_auth(self, cp_id, cp_pass, is_master):

        if not cp_id or not cp_pass:
            return self.set_error(CP_ERR_CODE.CP_ERR_INVALID_PARAMETER)

        if cp_id.find('@') != -1:
            self.cp_id = CloudPlugs.PLUG_EMAIL_HEADER + ': ' + cp_id
            self.cp_headers[CloudPlugs._CP_ID] = {CloudPlugs.PLUG_EMAIL_HEADER: cp_id}
        else:
            self.cp_id = CloudPlugs.PLUG_ID_HEADER + ': ' + cp_id
            self.cp_headers[CloudPlugs._CP_ID] = {CloudPlugs.PLUG_ID_HEADER: cp_id}

        if is_master:
            self.cp_auth = CloudPlugs.PLUG_MASTER_HEADER + ': ' + cp_pass
            self.cp_headers[CloudPlugs._CP_AUTH] = {CloudPlugs.PLUG_MASTER_HEADER: cp_pass}
        else:
            self.cp_auth = CloudPlugs.PLUG_AUTH_HEADER + ': ' + cp_pass
            self.cp_headers[CloudPlugs._CP_AUTH] = {CloudPlugs.PLUG_AUTH_HEADER: cp_pass}

        self.is_master = is_master
        if self.cp_id and self.cp_auth:
            return True
        else:
            return False

    ##  Get the authentication id (@ref details_PLUG_ID or email) of the session.
    #   @param self The object pointer
    #   @return The authenticatoin id on success, and None on failure.
    def get_auth_id(self):

        if not self.cp_id:
            return self.set_error(CP_ERR_CODE.CP_ERR_INVALID_PARAMETER)
        index = self.cp_id.find(' ')
        if index == -1:
            return None
        return self.cp_id[index + 1:]

    ##  Get the authentication password of the session.
    #   @param self The object pointer
    #   @return The authentication password on success, and None on failure.
    def get_auth_pass(self):

        if not self.cp_auth:
            return self.set_error(CP_ERR_CODE.CP_ERR_INVALID_PARAMETER)
        index = self.cp_auth.find(' ')
        if index == -1:
            return None
        return self.cp_auth[index + 1:]

    ##  Return the authentication mode in the session.
    #   @param self The object pointer
    #   @return True if using master authentication in the session. False if using regular authentication.
    def is_auth_master(self):

        return self.is_master

    ##  Request for removing any device (development, product or controller).  Response in placed in self.request.
    #   @param  self The object pointer
    #   @param  plugid: @ref details_PLUG_ID or [@ref details_PLUG_ID,...] or @ref details_PLUG_ID_CSV
    #           The plug-ids  of the device(s) to remove
    #   @return TRUE if the request succeeds, FALSE otherwise.
    def unenroll(self, plugid):

        if plugid:
            cp_id = plugid
        else:
            cp_id = self.get_plug_id()

        cp_id = '"' + cp_id + '"'
        return self.request_exec(True, CP_HTTP_METHOD.CP_HTTP_DELETE, CloudPlugs.PATH_DEVICE, None, None, cp_id)

    ##  Request for retrieving list a list of channels refer already published data matching some criteria.  Response is placed in self.request.
    #   @param  self The object pointer
    #   @param  channel_mask The channel mask.
    #   @param  query If not None, a dictionary that will be converted  to a query-string.
    #           The dictionary can have these values: \n
    #                   \b before: (optional) @ref details_TIMESTAMP or @ref details_OBJECT_ID	(OID of published data) \n
    #                   \b after: (optional) @ref details_TIMESTAMP or @ref details_OBJECT_ID	(OID of published data) \n
    #                   \b at: (optional) @ref details_TIMESTAMP_CSV \n
    #                   \b of: (optional) @ref details_PLUG_ID_CSV \n
    #                   \b offset: (optional) Number: positive integer (including 0) \n
    #                   \b limit: (optional) Number: positive integer (including 0) \n
    #   @return TRUE if the request succeeds, FALSE otherwise.
    def get_channel(self, channel_mask, query):

        url = CloudPlugs.PATH_CHANNEL
        if channel_mask:
            url += '/' + channel_mask

        return self.request_exec(True, CP_HTTP_METHOD.CP_HTTP_GET, url, None, query, None)

    ##  Request for retrieving a list of channels refer already published data matching some criteria (explicit parameters version).
    #   The response is placed in self.request.
    #   @param  self The object pointer
    #   @param  channel_mask The channel mask.
    #   @param  before: (optional) @ref details_TIMESTAMP or @ref details_OBJECT_ID	(OID of published data)
    #   @param  after: (optional) @ref details_TIMESTAMP or @ref details_OBJECT_ID (OID of published data)
    #   @param  at: (optional) @ref details_TIMESTAMP_CSV
    #   @param  of:  (optional) @ref details_PLUG_ID_CSV
    #   @param  offset: (optional) Number: positive integer (including 0)
    #   @param  limit: (optional) Number: positive integer (including 0)
    #   @return TRUE if the request succeeds, FALSE otherwise.
    def get_channel_ex(self, channel_mask, before, after, at, of, offset, limit):

        if not channel_mask:
            return self.set_error(CP_ERR_CODE.CP_ERR_INVALID_PARAMETER)

        url = CloudPlugs.PATH_CHANNEL
        if channel_mask:
            url += '/' + channel_mask

        body = {}
        if before:
            body[CloudPlugs.BEFORE] = before
        if after:
            body[CloudPlugs.AFTER] = after
        if at:
            body[CloudPlugs.AT] = at
        if of:
            body[CloudPlugs.OF] = of
        if offset:
            body[CloudPlugs.OFFSET] = offset
        if limit:
            body[CloudPlugs.LIMIT] = limit

        return self.request_exec(True, CP_HTTP_METHOD.CP_HTTP_GET, url, None, None, body)

    ##  Request for reading device's information and properties
    #   @param self The object pointer
    #   @param plugid If not None, then the @ref details_PLUG_ID of the device, otherwise the device referenced in the session.
    #   @return TRUE if the request succeeds, FALSE otherwise.
    def get_device(self, plugid):

        if plugid:
            cp_id = plugid
        else:
            cp_id = self.get_plug_id()
        url = CloudPlugs.PATH_DEVICE + '/' + cp_id

        return self.request_exec(True, CP_HTTP_METHOD.CP_HTTP_GET, url, None, None, None)

    ##  Request for modifying device and place the response in self.request.
    #   @param  self The object pointer
    #   @param  plugid The @ref details_PLUG_ID of the device.
    #   @param  value A dictionary that will be converted to json.  For  example: \n
    #                   \b perm: @ref details_PERM_FILTER (optional) it contains just the sharing filters to modify \n
    #                   \b name: String (optional) the device name \n
    #                   \b status: @ref details_STATUS (optional) \n
    #                   \b props:  Object       # optional, it contains just the properties to modify
    #   @return TRUE if the request succeeds, FALSE otherwise.
    def set_device(self, plugid, value):

        if plugid:
            cp_id = plugid
        else:
            cp_id = self.get_plug_id()
        url = CloudPlugs.PATH_DEVICE + '/' + cp_id

        return self.request_exec(True, CP_HTTP_METHOD.CP_HTTP_PATCH, url, None, None, value)

    ##  Request for reading the device properties and place the response in self.reuest.
    #   @param self The object pointer
    #   @param plugid If not None, then the @ref details_PLUG_ID of the device, otherwise the device referenced in the session.
    #   @param prop If None, then all properties value; otherwise the single property value..
    #   @return TRUE if the request succeeds, FALSE otherwise.
    def get_device_prop(self, plugid, prop):

        if plugid:
            cp_id = plugid
        else:
            cp_id = self.get_plug_id()

        url = CloudPlugs.PATH_DEVICE + '/' + cp_id + '/'
        if prop:
            url += prop

        return self.request_exec(True, CP_HTTP_METHOD.CP_HTTP_GET, url, None, None, None)

    ##  Request for writing or deleting device properties and places the response in self.request.
    #   @param  self The object pointer
    #   @param  plugid The @ref details_PLUG_ID of the device.
    #   @param  prop If None, then value must be a dictionary of properties and values;
    #           otherwise the single property value is written.
    #   @param  value A single value or a dictionary -  use None to delete one or all device properties.
    #   @return TRUE if the request succeeds, FALSE otherwise.
    def set_device_prop(self, plugid, prop, value):

        if plugid:
            cp_id = plugid
        else:
            cp_id = self.get_plug_id()

        url = CloudPlugs.PATH_DEVICE + '/' + cp_id + '/'
        if prop:
            url += prop

        # If 'value' is a dictionary,
        # request_exec() will convert it to json being sending it.
        # If it is an integer, it will be converted to a string
        # before it is sent.
        body = value

        return self.request_exec(True, CP_HTTP_METHOD.CP_HTTP_PATCH, url, None, None, body)

    ##  Request for deleting device property and places the response in self.request.
    #   @param  self The object pointer
    #   @param  plugid The @ref details_PLUG_ID of the device.
    #   @param  prop string the single property name to be removed.
    #   @return TRUE if the request succeeds, FALSE otherwise.
    def remove_device_prop(self, plugid, prop):

        if plugid:
            cp_id = plugid
        else:
            cp_id = self.get_plug_id()

        url = CloudPlugs.PATH_DEVICE + '/' + cp_id + '/' + prop

        return self.request_exec(True, CP_HTTP_METHOD.CP_HTTP_DELETE, url, None, None, None)

    ##  Request for writing or deleting device location and place the response in self.request
    #   @param  self The object pointer
    #   @param  plugid If not None, then the @ref details_PLUG_ID of the device, otherwise the device referenced in the session.
    #   @param  longitude   double
    #   @param  latitude    double
    #   @param  altitude    double (optional)
    #   @param  accuracy    double (optional)
    #   @param  timestamp   double (optional)
    #   @return TRUE if the request succeeds, FALSE otherwise.
    def set_device_location(self, plugid, longitude, latitude, altitude, accuracy, timestamp):

        body = {}
        body[CloudPlugs.LONGITUDE] = longitude
        body[CloudPlugs.LATITUDE] = latitude
        if accuracy >= 0:
            body[CloudPlugs.ACCURACY] = accuracy
        if altitude >= 0:
            body[CloudPlugs.ALTITUDE] = altitude
        if timestamp >= 0:
            body[CloudPlugs.TIMESTAMP] = timestamp

        if plugid:
            cp_id = plugid
        else:
            cp_id = self.get_plug_id()

        url = CloudPlugs.PATH_DEVICE + '/' + cp_id + '/' + CloudPlugs.LOCATION

        return self.request_exec(True, CP_HTTP_METHOD.CP_HTTP_PATCH, url, None, None, body)

    ##  Request for getting the device location property
    #   @param  self The object pointer
    #   @param  plugid If not None, then the @ref details_PLUG_ID of the device, otherwise the device referenced in the session.
    #   @return TRUE if the request succeeds, FALSE otherwise.
    def get_device_location(self, plugid):

        if plugid:
            cp_id = plugid
        else:
            cp_id = self.get_plug_id()

        url = CloudPlugs.PATH_DEVICE + '/' + cp_id + '/' + CloudPlugs.LOCATION

        return self.request_exec(True, CP_HTTP_METHOD.CP_HTTP_GET, url, None, None, None)

    def set_error(self, x):
        self.err = x
        return CloudPlugs.CP_FAIL

    ##  Request for publishing data and places the response in self.request.
    #   @param  self The object pointer
    #   @param  channel A optional @ref details_CHANNEL, if None data need to contain a couple "channel":"channel"
    #   @param  body body can be an array, a dictionary, a string, an integer, etc. which will be converted to
    #           json.  For example: \n
    #               {\n
    #               \b "id"        : @ref details_OBJECT_ID		(optional), OID of the published data to update\n
    #               \b "channel"   : @ref details_CHANNEL,	(optional), to override the channel in the url\n
    #               \b \b "data"   : JSON of data to publish ,\n
    #               "at"           : @ref details_TIMESTAMP,\n
    #               \b "of"        : @ref details_PLUG_ID, (optional), check if the X-Plug-Id is authorized for setting this field \n
    #               \b "expire_at" : @ref details_TIMESTAMP,	// (optional), expire date of this data entry\n
    #               \b "ttl"       : int	(optional), how many \b seconds this data entry will live (if "expire_at" is present, then this field is ignored)\n
    #                }
    #   @return TRUE if the request succeeds, FALSE otherwise.
    def publish_data(self, channel, body):


        # Should we check the validity of body?
        url = CloudPlugs.PATH_DATA
        if channel:
            url += '/' + channel

        return self.request_exec(True, CP_HTTP_METHOD.CP_HTTP_PUT, url, None, None, body)

    ##  Request for enrolling a prototype and place the response in self.request.
    #   @param  self     The object pointer
    #   @param  body    can be an array, a dictionary, a string, an integer, etc. which will be converted to
    #                   json.  For example: \n
    #                   {\n
    #                   \b "hwid"  : String @ref details_HWID (optional) if absent it will be set as a random unique string \n
    #                   \b "pass"  : String,       (optional) if absent set as the X-Plug-Master of the company \n
    #                   \b "name"  : String \n
    #                   \b "perm"  : @ref details_PERM_FILTER (optional) if absent permit all  \n
    #                   \b "props" : JSON/dict     (optional) to initialize the custom properties\n
    #                   }
    #   @return TRUE if the request succeeds, FALSE otherwise.
    def enroll_prototype(self, body):
        if not self.is_master:
            return self.set_error(CP_ERR_CODE.CP_ERR_INVALID_LOGIN)
        return self.request_exec(True, CP_HTTP_METHOD.CP_HTTP_POST, CloudPlugs.PATH_DEVICE, None, None, body)

    ##  Request for enrolling a prototype and place the response self.request (explicit parameters version).
    #   @param  self    The object pointer
    #   @param  hwid    String @ref details_HWID (optional) if absent it will be set as a random unique string
    #   @param  cp_pass String,       (optional) if absent set as the X-Plug-Master of the company
    #   @param  name    String,
    #   @param  perm    @ref details_PERM_FILTER (optional) if absent permit all
    #   @param  props   JSON/dict     (optional) to initialize the custom properties
    #   @return TRUE if the request succeeds, FALSE otherwise.
    def enroll_prototype_ex(self, hwid, cp_pass, name, perm, props):

        if not hwid and not name:
            return self.set_error(CP_ERR_CODE.CP_ERR_INVALID_PARAMETER)

        if not self.is_master:
            return self.set_error(CP_ERR_CODE.CP_ERR_INVALID_LOGIN)

        body = {}
        body[CloudPlugs.HWID] = hwid
        body[CloudPlugs.NAME] = name
        if perm:
            body[CloudPlugs.PERM] = perm
        if props:
            body[CloudPlugs.PROPS] = props
        if cp_pass:
            body[CloudPlugs.PASS] = cp_pass

        return self.request_exec(True, CP_HTTP_METHOD.CP_HTTP_POST, CloudPlugs.PATH_DEVICE, None, None, body)

    ##  Request for enrolling a production device and place the response in self.request.
    #   @param  self    The object pointer
    #   @param  body    A dictionary that will be converted to json.  For example: \n
    #                   {\n
    #                   \b "model" : @ref details_PLUG_ID the model of this device \n
    #                   \b "hwid"  : @ref details_HWID the serial number \n
    #                   \b "pass"  : String\n
    #                   \b "props" : JSON/dict     (optional) to initialize the custom properties \n
    #                   }
    #   @return TRUE if the request succeeds, FALSE otherwise.
    def enroll_product(self, body):

        if not body:
            return self.set_error(CP_ERR_CODE.CP_ERR_INVALID_PARAMETER)

        return self.request_exec(True, CP_HTTP_METHOD.CP_HTTP_POST, CloudPlugs.PATH_DEVICE, None, None, body)

    ##  Request for controlling an existing device and place the response in self.request (Auth is requested)
    #   @param  self    The object pointer
    #   @param  body    A dictionary that will be converted to json.  For example: \n
    #                   {\n
    #                   \b "model" : @ref details_PLUG_ID model id of the device to control \n
    #                   \b "ctrl"  : @ref details_HWID serial number  of the device to control \n
    #                   \b "pass"  : String\n
    #                   \b "hwid"  : String, (optional) @ref details_HWID unique string to identify this controller device \n
    #                   \b "name"  : String (optional) the name of this device \n
    #                   }
    #   @return TRUE if the request succeeds, FALSE otherwise.
    def control_device(self, body):

        if not body:
            return self.set_error(CP_ERR_CODE.CP_ERR_INVALID_PARAMETER)
        return self.request_exec(True, CP_HTTP_METHOD.CP_HTTP_PUT, CloudPlugs.PATH_DEVICE, None, None, body)

    ##  Request for  enrolling a new or already existent controller device and place the response in self.request.
    #   (No Auth requested)
    #   @param  self    The object pointer
    #   @param  body    A dictionary that will be converted to json.  For example: \n
    #                   {\n
    #                   \b "model" : @ref details_PLUG_ID model id of the device to control \n
    #                   \b "ctrl"  : @ref details_HWID serial number  of the device to control \n
    #                   \b "pass"  : String\n
    #                   \b "hwid"  : String, (optional) @ref details_HWID unique string to identify this controller device \n
    #                   \b "name"  : String (optional) the name of this device \n
    #                   }
    #   @return TRUE if the request succeeds, FALSE otherwise.
    def enroll_ctrl(self, body):

        if not body:
            return self.set_error(CP_ERR_CODE.CP_ERR_INVALID_PARAMETER)
        return self.request_exec(False, CP_HTTP_METHOD.CP_HTTP_PUT, CloudPlugs.PATH_DEVICE, None, None, body)

    ##  Request for retrieving already published data and places the response in self.request.
    #   The response is placed in self.request.
    #   @param  self The object pointer
    #   @param  channel_mask The @ref details_CHMASK
    #   @param  before  (optional) @ref details_TIMESTAMP or @ref details_OBJECT_ID	(OID of published data)
    #   @param  after   (optional) @ref details_TIMESTAMP or @ref details_OBJECT_ID	(OID of published data)
    #   @param  at      (optional) @ref details_TIMESTAMP_CSV
    #   @param  of      (optional) @ref details_PLUG_ID_CSV
    #   @param  offset  (optional) Number: positive integer (including 0)
    #   @param  limit   (optional) Number: positive integer (including 0)
    #   @return TRUE if the request succeeds, FALSE otherwise.
    def retrieve_data(self, channel_mask, before, after, at, of, offset, limit):

        if not channel_mask:
            return self.set_error(CP_ERR_CODE.CP_ERR_INVALID_PARAMETER)

        url = CloudPlugs.PATH_DATA + '/' + channel_mask

        query = {}
        if before:
            query[CloudPlugs.BEFORE] = before
        if after:
            query[CloudPlugs.AFTER] = after
        if at:
            query[CloudPlugs.AT] = at
        if of:
            query[CloudPlugs.OF] = of
        if offset:
            query[CloudPlugs.OFFSET] = offset
        if limit:
            query[CloudPlugs.LIMIT] = limit

        return self.request_exec(True, CP_HTTP_METHOD.CP_HTTP_GET, url, None, query, None)

    ##  Request for  uncontrolling a device and places the response self.request.
    #   @param  self The object pointer
    #   @param  plugid If None, then is the @ref details_PLUG_ID in the session.
    #   @param  plugid_controlled  If not None, then @ref details_PLUG_ID or [ @ref details_PLUG_ID, ... ] the device(s) to disassociate (default: all associated devices)
    #   @return TRUE if the request succeeds, FALSE otherwise.
    def uncontrol_device(self, plugid, plugid_controlled):

        if plugid:
            cp_id = plugid
        else:
            cp_id = self.get_plug_id()

        url = CloudPlugs.PATH_DEVICE + '/' + cp_id

        if not plugid_controlled or not list(plugid_controlled):
            return self.set_error(CP_ERR_CODE.CP_ERR_INVALID_PARAMETER)

        return self.request_exec(True, CP_HTTP_METHOD.CP_HTTP_DELETE, url, None, None, plugid_controlled)

    ##  Request  for removing published data
    #   @param  self    The object pointer
    #   @param  channel_mask    A channel mask
    #   @param  body    A dictionary that will be converted to json.  For example: \n
    #                   {\n
    #                   \b id       : (optional) @ref details_OBJECT_ID_CSV or  [@ref details_OBJECT_ID,...] \n
    #                   \b before   : (optional) @ref details_TIMESTAMP or @ref details_OBJECT_ID	(OID of published data) \n
    #                   \b after    : (optional) @ref details_TIMESTAMP or @ref details_OBJECT_ID	(OID of published data) \n
    #                   \b at       : (optional) @ref details_TIMESTAMP_CSV or [@ref details_TIMESTAMP,...] \n
    #                   \b of       : (optional) @ref details_PLUG_ID_CSV or [@ref details_PLUG_ID,...] \n
    #                   }\n
    #                   ( \b Note: at least one of the following param is required: id, before, after or at)
    #   @return TRUE if the request succeeds, FALSE otherwise.
    def remove_data(self, channel_mask, body):

        if not body or not channel_mask:
            return self.set_error(CP_ERR_CODE.CP_ERR_INVALID_PARAMETER)

        url = CloudPlugs.PATH_DATA + '/' + channel_mask
        return self.request_exec(True, CP_HTTP_METHOD.CP_HTTP_DELETE, url, None, None, body)

    ##  Request  for removing published data (explicit parameters version).
    #   ( \b Note: at least one of the following param is required: id, before, after or at)
    #   @param  self The object pointer
    #   @param  channel_mask    A @ref details_CHMASK
    #   @param  cp_id           (optional) @ref details_OBJECT_ID_CSV or  [@ref details_OBJECT_ID,...]
    #   @param  before          (optional) @ref details_TIMESTAMP or @ref details_OBJECT_ID	(OID of published data)
    #   @param  after           (optional) @ref details_TIMESTAMP or @ref details_OBJECT_ID	(OID of published data)
    #   @param  at              (optional) @ref details_TIMESTAMP_CSV or [@ref details_TIMESTAMP,...]
    #   @param  of              (optional) @ref details_PLUG_ID_CSV or [@ref details_PLUG_ID,...]
    #   @return TRUE if the request succeeds, FALSE otherwise.
    def remove_data_ex(self, channel_mask, cp_id, before, after, at, of):

        if not channel_mask or (not cp_id and not before and not after and not at):
            return self.set_error(CP_ERR_CODE.CP_ERR_INVALID_PARAMETER)

        url = CloudPlugs.PATH_DATA + '/' + channel_mask

        body = {}
        if cp_id:
            body[CloudPlugs.ID] = cp_id
        if before:
            body[CloudPlugs.BEFORE] = before
        if after:
            body[CloudPlugs.AFTER] = after
        if at:
            body[CloudPlugs.AT] = at
        if of:
            body[CloudPlugs.OF] = of


        return self.request_exec(True, CP_HTTP_METHOD.CP_HTTP_DELETE, url, None, None, body)

    ##  Execute a generic http request.The result of the request is placed in  self.result
    #   This method uses the python "Requests" library for preparing,
    #   sending, receiving and post-processing HTTP requests.
    #   See its documentation for more information about
    #   the arguments (headers, query, etc.) and the result: http://docs.python-requests.org/en/latest/
    #   @param  self            The object pointer
    #   @param  cp_auth         boolean, to Check if auth is present.
    #   @param  http_method     Indicates the desired action to be performed on the identified resource.
    #   @param  cp_path         Relative path of the requested resource
    #   @param  headers         If not None, is an dictionary with headers to send
    #   @param  query           If not None, a dictionary for the parameters to append with a '?' character.
    #   @param  body            If body is a dictionary or array, it is converted to a json string.
    #                           If body is an integer, it is converted to a string.
    #   @return TRUE if the request succeeds, FALSE otherwise.

    def request_exec(self, cp_auth, http_method, cp_path, headers, query, body):


        if cp_auth and not self.cp_auth:
            return self.set_error(CP_ERR_CODE.CP_ERR_INVALID_LOGIN)

        self.http_res = 0
        self.err = 0

        full_path = self.base_url + cp_path

        if headers:
            loc_headers = headers.copy()  # local copy of the headers
        else:
            loc_headers = {}
        if self.cp_id and self.cp_auth:
            loc_headers = dict(loc_headers.items() +
                               self.cp_headers[CloudPlugs._CP_ID].items() + \
                               self.cp_headers[CloudPlugs._CP_AUTH].items())
        else:
            loc_headers = None

        loc_headers['Content-type'] = 'application/json'

        ssl_verifypeer = False  # TODO

        if type(body) == dict or type(body) == type([]):
            body = json.dumps(body)
        elif type(body) == type(123):
            body = str(body)
        elif not body:
            body = ""
        else:
            # In case it isn't already a string, make it one:
            body = str(body)

        ssl_verify_peer = False

        try:
            req_start = requests.Request(http_method, full_path, params=query, headers=loc_headers, data=body)

            prepped = req_start.prepare()
            req = self.session.send(prepped, timeout=self.timeout, allow_redirects=True, verify=ssl_verify_peer)

        except requests.exceptions.RequestException as e:
            self.result = str(e)  # On error, returns text error string
            self.http_res = 0
            self.err = CP_ERR_CODE.CP_ERR_HTTP
            return CloudPlugs.CP_FAIL

        self.result = req  # Save the result
        self.http_res = req.status_code
        self.request = req

        if self.http_res == CP_HTTP_RESULT.CP_HTTP_OK or \
                        self.http_res == CP_HTTP_RESULT.CP_HTTP_CREATED:
            return CloudPlugs.CP_OK
        else:
            self.err = CP_ERR_CODE.CP_ERR_HTTP
            return CloudPlugs.CP_FAIL

    ##  Get The current @ref details_PLUG_ID
    #   @param  self            The object pointer
    #   @return Current @ref details_PLUG_ID of this session
    def get_plug_id(self):
        if not self.cp_id or self.cp_id.find('@') != -1:
            self.err = CP_ERR_CODE.CP_ERR_INVALID_LOGIN
            return ""

        # Skip over 'X-Plug-Id' and ': '
        return self.cp_id[len(CloudPlugs.PLUG_ID_HEADER) + 2:]

    ##  Return a human-readable string that describes the last error.
    #   @param  self    The object pointer
    #   @return A human-readable string that describes the last error.
    def get_last_err_string(self):

        if self.err == CP_ERR_CODE.CP_ERR_INTERNAL_ERROR:
            return "Internal Library Error"
        elif self.err == CP_ERR_CODE.CP_ERR_OUT_OF_MEMORY:
            return "Out of memory"
        elif self.err == CP_ERR_CODE.CP_ERR_INVALID_SESSION:
            return "Invalid session"
        elif self.err == CP_ERR_CODE.CP_ERR_QUERY_IS_NOT_AN_OBJECT:
            return "Query is not an object"
        elif self.err == CP_ERR_CODE.CP_ERR_QUERY_INVALID_TYPE:
            return "Query contain invalid type"
        elif self.err == CP_ERR_CODE.CP_ERR_HEADERS_MUST_BE_STRING:
            return "Header value must be a string"
        elif self.err == CP_ERR_CODE.CP_ERR_INVALID_PARAMETER:
            return "Invalid parameter"
        elif self.err == CP_ERR_CODE.CP_ERR_INVALID_LOGIN:
            return "Invalid login"
        elif self.err == CP_ERR_CODE.CP_ERR_JSON_PARSE:
            return "JSON parse error"
        elif self.err == CP_ERR_CODE.CP_ERR_JSON_ENCODE:
            return "JSON encode error"
        elif self.err == CP_ERR_CODE.CP_ERR_HTTP:
            return "HTTP error"
        return None

    ##  Returns the last error that occurred.
    #   @param  self            The object pointer
    #   @return code of the last error  occurred.
    def get_last_err_code(self):

        return self.err

    ##  Return a human-readable string that describes the last http code.
    #   @param  self            The object pointer
    #   @return a human-readable string that describes the last http code.
    def get_last_http_result_string(self):

        if self.http_res == CP_HTTP_RESULT.CP_HTTP_OK:
            return "Ok";
        elif self.http_res == CP_HTTP_RESULT.CP_HTTP_CREATED:
            return "Created"
        elif self.http_res == CP_HTTP_RESULT.CP_HTTP_MULTI_STATUS:
            return "Multi-Status"
        elif self.http_res == CP_HTTP_RESULT.CP_HTTP_BAD_REQUEST:
            return "Bad Request"
        elif self.http_res == CP_HTTP_RESULT.CP_HTTP_UNAUTHORIZED:
            return "Unauthorized"
        elif self.http_res == CP_HTTP_RESULT.CP_HTTP_PAYMENT_REQUIRED:
            return "Payment Required"
        elif self.http_res == CP_HTTP_RESULT.CP_HTTP_FORBIDDEN:
            return "Forbidden"
        elif self.http_res == CP_HTTP_RESULT.CP_HTTP_NOT_FOUND:
            return "Not found"
        elif self.http_res == CP_HTTP_RESULT.CP_HTTP_NOT_ALLOWED:
            return "Method Not Allowed"
        elif self.http_res == CP_HTTP_RESULT.CP_HTTP_NOT_ACCEPTABLE:
            return "Not Acceptable"
        elif self.http_res == CP_HTTP_RESULT.CP_HTTP_SERVER_ERROR:
            return "Internal Server Error"
        elif self.http_res == CP_HTTP_RESULT.CP_HTTP_NOT_IMPLEMENTED:
            return "Not Implemented"
        elif self.http_res == CP_HTTP_RESULT.CP_HTTP_BAD_GATEWAY:
            return "Bad Gateway"
        elif self.http_res == CP_HTTP_RESULT.CP_HTTP_SERVICE_UNAVAILABLE:
            return "Service Unavailable"
        else:
            return None
    ##  Return  the last http code.
    #   @param  self            The object pointer
    #   @return   the last http code.
    def get_last_http_result(self):

        return self.http_res
