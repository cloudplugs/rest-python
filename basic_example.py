import sys
import time
import json
import random

from cloudplugs import CloudPlugs

## Edit the next lines with your authentication data
AUTH_PLUGID = "dev-xxxxxxxxxxxxxxxxxx" # The device plug ID or your CloudPlugs account id if AUTH_MASTER is True
AUTH_PASS = "your-password" # The device connection password or your CloudPlugs account password if AUTH_MASTER is True
AUTH_MASTER = True

def jdebug(tag, cp_res, cps):
    try:
        json_str = json.dumps(cps.result.json(), sort_keys=True, indent=4)
    except:
        json_str = "<JSON not returned>"
            
    if cp_res:
        print "%s: [ERROR-> %s] [HTTP_RES %d] %s" % (tag, cps.get_last_err_string(), cps.get_last_http_result(), json_str)
    else:
        print '%s: %s' % (tag, json_str)

def main():
    cps = CloudPlugs()

    cps.set_auth(AUTH_PLUGID, AUTH_PASS, AUTH_MASTER)

    channel = "temperature"
    value = random.randint(0, 100)
    data = {'data': value}
    cp_res = cps.publish_data(channel, data)
    jdebug("PUBLISHED DATA OID", cp_res, cps)

    del cps

if __name__ == '__main__':
    main()
