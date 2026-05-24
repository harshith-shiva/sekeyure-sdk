from pynput import keyboard
import time

class Listener:

    def __init__(self):
        self.events=[]
        self.position=0
        self.downs={}
        self.ups=[]
        self.holds=[]
        self.backspacepositions=[]
        self.listener=None

    def start(self):
        self.events=[]
        self.position=0
        self.listener=keyboard.Listener(on_press=self.onpress,on_release=self.onrelease)
        self.listener.start()

    def stop(self):
        if self.listener:
            self.listener.stop()
        
        print({
            "events": self.events,
            "final_length": self.position,
            "backspace_count": len(self.backspacepositions)
        })
    
    def onpress(self, key):
        ts = time.perf_counter()

        if key == keyboard.Key.backspace:
            if self.position > 0:
                self.backspacepositions.append(self.position)
                self.position -= 1
                self.events = [e for e in self.events
                               if e["position"] != self.position]
            return

        if isinstance(key, keyboard.Key):
            return

        self.downs[self.position] = ts
        self.position += 1

    def onrelease(self, key):
        ts = time.perf_counter()

        if isinstance(key, keyboard.Key):
            return

        pos = self.position - 1
        if pos in self.downs:
            down_ts = self.downs.pop(pos)
            self.events.append({
                "position": pos,
                "keydown":  down_ts,
                "keyup":    ts,
                "hold_time": ts - down_ts
            })




l=Listener()
print("Start typing...")
l.start()
time.sleep(8)
l.stop()
