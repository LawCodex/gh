#!/usr/bin/env python3
"""Ghana: list items of the legislation collections of the Parliament of Ghana institutional
repository (DSpace 7 REST API, https://repository.parliament.gh) and their PDF bitstreams.
Writes ../../_raw/gh/items.json."""
import json
import os
import sys
import time

import requests

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(os.path.dirname(REPO), "_raw", "gh")
API = "https://repository.parliament.gh/server/api/"
S = requests.Session()
S.headers["User-Agent"] = "LawCodex/1.0 (+https://github.com/LawCodex)"

# collection uuid -> (category directory, label)
COLLECTIONS = {
    "71b5e7e6-9552-4bf5-a796-c3b9268f40da": ("acts", "Acts - First Republic"),
    "49c250c2-e4d0-471f-ad21-c2542e1b12c0": ("acts", "Acts - Second Republic"),
    "0778dbe0-79f7-4508-adfb-376216cf7008": ("acts", "Acts - Third Republic"),
    "613930c4-a86b-45bc-b456-c1e85a0a60a3": ("acts", "Acts - 4th Republic, 1st and 2nd Parliament"),
    "3e6101cf-fe5b-495b-a504-6dcda4b23750": ("acts", "Acts - 4th Republic, 3rd and 4th Parliament"),
    "99f2baa0-c45a-4b70-88d4-43e0ed8123ba": ("acts", "Acts - 4th Republic, 5th and 6th Parliament"),
    "c851655c-89c7-4d13-bd29-9c8b35fcfe34": ("acts", "Acts - 4th Republic, 7th and 8th Parliament"),
    "f4c5ff3f-ae94-4bec-ace2-f975fffed92f": ("acts", "Acts - 4th Republic, 9th and 10th Parliament"),
    "2e7b5a77-7576-4c25-9ec8-4f0cb2ec9c3f": ("decrees/nlcd", "National Liberation Council Decrees"),
    "0da04983-8631-4d01-a115-1527b0f7a4bb": ("decrees/nrcd", "National Redemption Council Decrees"),
    "70f5a27c-a099-4802-8205-25f096fdabe0": ("decrees/smcd", "Supreme Military Council Decrees"),
    "32c61b4e-77f0-4057-9006-4592a83544c6": ("decrees/afrcd", "Armed Forces Revolutionary Council Decrees"),
    "93cd509c-8819-48b7-bdd5-e4d5799ba446": ("decrees/pndcl", "Provisional National Defence Council (AFRC sub-community)"),
    "f3c4da60-6d43-44cd-8938-ca64838ac9c9": ("decrees/pndcl", "Provisional National Defence Council Laws"),
    "435da901-c42d-4b2b-9a00-93000399fd67": ("constitutional-instruments", "Constitutional Instruments - First Republic"),
    "3b98891f-f1d2-4ba8-b707-885790b6090f": ("constitutional-instruments", "Constitutional Instruments - First and Second Republic"),
    "acb36742-a65e-4e6f-be6e-47846c52882c": ("constitutional-instruments", "Constitutional Instruments - Third Republic"),
    "8c2fdd67-5fe4-4ca6-85bd-3cf380cdadf3": ("constitutional-instruments", "Constitutional Instruments - 1st and 2nd Parliament"),
    "556e3091-8264-4f38-9447-d370c25d348b": ("constitutional-instruments", "Constitutional Instruments - 3rd and 4th Parliament"),
    "9e82e130-ed67-474d-9eda-6da08633a32a": ("constitutional-instruments", "Constitutional Instruments - 5th and 6th Parliament"),
    "104670d2-0733-4f59-b2bf-0a2286bab388": ("constitutional-instruments", "Constitutional Instruments - 7th and 8th Parliament"),
}
OPTIONAL = {
    "7dac0d07-5002-491e-ac9f-6da528c6407d": ("legislative-instruments", "Legislative Instruments - Third Republic"),
    "1e11065b-40a5-4bff-bb02-e5fa5a93f995": ("legislative-instruments", "Legislative Instruments - 1st and 2nd Parliament"),
    "e6b0ba1c-90d2-4613-883a-272138c4ed9d": ("legislative-instruments", "Legislative Instruments - 3rd and 4th Parliament"),
    "9f8417e7-c81c-43c7-919d-068054d13f61": ("legislative-instruments", "Legislative Instruments - 5th and 6th Parliament"),
    "2a523dc3-27d4-405c-917d-c8d1533c56b1": ("legislative-instruments", "Legislative Instruments - 7th and 8th Parliament"),
}


def get(url, tries=6):
    for i in range(tries):
        try:
            time.sleep(0.5)
            r = S.get(url, timeout=180)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # truncated responses happen on this server
            print("  retry", i + 1, url, e, flush=True)
            time.sleep(5 * (i + 1))
    raise SystemExit("failed: " + url)


def meta(it):
    return {k: [x["value"] for x in v] for k, v in it.get("metadata", {}).items()}


def main():
    os.makedirs(RAW, exist_ok=True)
    out_path = os.path.join(RAW, "items.json")
    items = json.load(open(out_path)) if os.path.exists(out_path) else {}
    cols = dict(COLLECTIONS)
    if "--with-li" in sys.argv:
        cols.update(OPTIONAL)
    for cid, (cat, label) in cols.items():
        page = 0
        while True:
            d = get(API + "discover/search/objects?scope=%s&dsoType=ITEM&size=40&page=%d" % (cid, page))
            sr = d["_embedded"]["searchResult"]
            objs = sr["_embedded"]["objects"]
            for o in objs:
                it = o["_embedded"]["indexableObject"]
                if it["uuid"] in items and items[it["uuid"]].get("bitstreams") is not None:
                    continue
                items[it["uuid"]] = {"uuid": it["uuid"], "name": it.get("name"), "handle": it.get("handle"),
                                     "collection": cid, "category": cat, "collection_label": label,
                                     "metadata": meta(it), "bitstreams": None}
            print(label, "page", page, "/", sr["page"]["totalPages"], "total", sr["page"]["totalElements"], flush=True)
            page += 1
            if page >= sr["page"]["totalPages"]:
                break
        json.dump(items, open(out_path, "w"), indent=1)
    # bitstreams
    n = 0
    for uid, it in items.items():
        if it.get("bitstreams") is not None:
            continue
        d = get(API + "core/items/%s?embed=bundles/bitstreams" % uid)
        bs = []
        for b in d["_embedded"]["bundles"]["_embedded"]["bundles"]:
            if b["name"] != "ORIGINAL":
                continue
            for x in b["_embedded"]["bitstreams"]["_embedded"]["bitstreams"]:
                bs.append({"uuid": x["uuid"], "name": x["name"], "size": x.get("sizeBytes"),
                           "checksum": (x.get("checkSum") or {}).get("value")})
        it["bitstreams"] = bs
        n += 1
        if n % 50 == 0:
            json.dump(items, open(out_path, "w"), indent=1)
            print("bitstreams", n, flush=True)
    json.dump(items, open(out_path, "w"), indent=1)
    print("items", len(items))


if __name__ == "__main__":
    main()
