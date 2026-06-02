import json
import os
from .gesture import Gesture

class StorageManager:
    def __init__(self, file_path):
        self.file_path = file_path

    def save_gesture(self, gesture):
        gestures = self.load_all()
        
        replaced = False
        for i, g in enumerate(gestures):
            if g.name == gesture.name:
                gestures[i] = gesture
                replaced = True
                break
                
        if not replaced:
            gestures.append(gesture)
        
        with open(self.file_path, 'w') as f:
            json.dump([g.to_dict() for g in gestures], f, indent=4)

    def load_all(self):
        if not os.path.exists(self.file_path):
            return []
        
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
                return [Gesture.from_dict(g) for g in data]
        except (json.JSONDecodeError, KeyError):
            return []
