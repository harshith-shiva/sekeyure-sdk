import numpy as np
import time
from listener import Listener
class FeatureExtractor:

    def __init__(self):
        pass  # no length needed at construction

    def extract(self, raw_strokes: dict) -> dict:
       
        N = raw_strokes['final_length']

        if N < 4:
            # Too short to build a meaningful vector
            return {"vector": None, "length": N, "reason": "too_short"}

        raw_strokes['events'] = sorted(raw_strokes['events'], key=lambda e: e["position"])

        hold = np.array([e["hold_time"] for e in raw_strokes['events']])

        dd, uu, ud = [], [], []
        for i in range(N - 1):
            dd.append(raw_strokes['events'][i+1]["keydown"] - raw_strokes['events'][i]["keydown"])
            uu.append(raw_strokes['events'][i+1]["keyup"]   - raw_strokes['events'][i]["keyup"])
            ud.append(raw_strokes['events'][i+1]["keydown"] - raw_strokes['events'][i]["keyup"])

        vector = np.concatenate([hold, dd, uu, ud])
        # print(hold)
        # print(dd)
        # print(uu)
        # print(vector)

        return {
            "vector": vector,
            "length": N,
            "reason": "ok"
        }
    


l=Listener()
print("Start typing...")
l.start()
time.sleep(5)
data=l.stop()
f=FeatureExtractor()
print(f.extract(data))

