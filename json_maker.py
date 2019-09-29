import json

output = []
data = {"name": "events", "automatedExpansion": True }



with open ("events.txt") as f:
    objects = f.read().splitlines()
    print(len(objects))
    for obj in objects:
        #print(output)
        obj = obj.replace(')', '')
        obj = obj.replace('(', '')
        output.append({"value": obj, "synonyms": [obj]})
    with open("events.json", "w+") as f:
        data["entries"] = output
        json.dump(data, f, ensure_ascii=False)