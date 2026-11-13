"""Read-only proof that VediSMM links exactly the new SOVETSKIY VK group.

Never fall back to the SHAM or SKRBL accounts.
"""
import os
import requests

VK_GROUP_ID="243244760"
BASE="https://vedismm.ru/api/v1"


def find_account(token, session=requests):
    if not isinstance(token,str) or not token.strip():
        raise RuntimeError("VEDISMM_TOKEN not configured")
    reply=session.get(BASE+"/accounts",
        headers={"Authorization":"Bearer "+token.strip()},timeout=35)
    reply.raise_for_status()
    entries=reply.json().get("data")
    if not isinstance(entries,list):
        raise RuntimeError("VediSMM account listing unavailable")
    matched=[a for a in entries if a.get("network")=="vk" and
             str(a.get("external_id","")).lstrip("-")==VK_GROUP_ID]
    if len(matched)!=1:
        raise RuntimeError("SOVETSKIY VK 243244760 is NOT linked to this VediSMM token")
    item=matched[0]
    if str(item.get("status","")).lower()!="active":
        raise RuntimeError("SOVETSKIY account is not active in VediSMM")
    account_id=int(item.get("id") or 0)
    if account_id<=0:
        raise RuntimeError("VediSMM SOVETSKIY account id is invalid")
    return account_id


if __name__=="__main__":
    token=os.getenv("VEDISMM_TOKEN","")
    result=find_account(token)
    print("SOVETSKIY_ACCOUNT_CONNECTED=YES")
    print("SOVETSKIY_VK_GROUP=243244760")
    print("SOVETSKIY_VEDISMM_ACCOUNT_ID=",result)
    print("Other VK groups are never used as substitutes.")
