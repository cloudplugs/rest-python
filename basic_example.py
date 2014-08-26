import sys
import time
import json
import random

from cloudplugs import CloudPlugs


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
    
    ##Edit next line with your authentication data
    cps.set_auth("dev-5359d2857b97bb8946b2584f", "password", True)

    channel = "temperature"
    value = random.randint(0, 100)
    data = {'data': value}
    cp_res = cps.publish_data(channel, data)
    jdebug("PUBLISHED DATA OID", cp_res, cps)
    
    del cps

if __name__ == '__main__':
    main()
