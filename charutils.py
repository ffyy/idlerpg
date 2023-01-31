import json
import os

def saveToDisk(content):
    try:
        os.mkdir("chars")
    except Exception:
        pass

    f = open(os.path.join("chars", content + ".txt"), "a")
    f.write(content)
    f.close()