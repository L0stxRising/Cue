import sys
import json
import urllib.request
import urllib.error
import os
import time

# url = "https://openrouter.ai/api/v1/auth/key"
# timeout_val = 10

def main():
    if len(sys.argv)>1:
        k=sys.argv[1].strip()
    else:
        sys.exit(1)

    # r=urllib.request.Request(url)
    r=urllib.request.Request("https://openrouter.ai/api/v1/auth/key")
    r.add_header("Authorization",f"Bearer {k}")
    r.add_header("User-Agent","Mozilla/5.0")
    try:
        rsp=urllib.request.urlopen(r,timeout=10)
        d=rsp.read()
        json.loads(d.decode("utf-8"))
        print("VALID")
        sys.exit(0)
    except urllib.error.HTTPError as e:
        if e.code==401:
            print("INVALID")
        else:
            print(f"ERROR:{e.code}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR:{e}")
        sys.exit(1)

if __name__=="__main__":
    main()