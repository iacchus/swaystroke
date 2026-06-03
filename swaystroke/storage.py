import json
import os
from .gesture import Gesture

class StorageManager:
    def __init__(self, file_path):
        self.file_path = file_path

    def save_gesture(self, gesture):
        gestures = self.load_all()
        
        max_id = 0
        for g in gestures:
            if getattr(g, "id", None) is not None:
                max_id = max(max_id, g.id)
                
        # retroactively assign IDs to old gestures
        for g in gestures:
            if getattr(g, "id", None) is None:
                max_id += 1
                g.id = max_id

        if getattr(gesture, "id", None) is None:
            max_id += 1
            gesture.id = max_id
        
        replaced = False
        for i, g in enumerate(gestures):
            if g.name == gesture.name:
                # If we're overwriting by name, preserve the old ID if the new one didn't have one explicitly set to something else? 
                # Actually, gesture.id is already assigned a new max_id above. Let's just keep the old ID for consistency.
                gesture.id = g.id
                gestures[i] = gesture
                replaced = True
                break
                
        if not replaced:
            gestures.append(gesture)
            
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        
        with open(self.file_path, 'w') as f:
            json.dump([g.to_dict() for g in gestures], f, indent=4)

    def delete_gesture(self, identifier):
        gestures = self.load_all()
        
        if isinstance(identifier, int) or (isinstance(identifier, str) and identifier.isdigit()):
            id_to_delete = int(identifier)
            filtered = [g for g in gestures if getattr(g, "id", None) != id_to_delete]
        else:
            filtered = [g for g in gestures if g.name != identifier]
        
        if len(filtered) == len(gestures):
            return False
            
        with open(self.file_path, 'w') as f:
            json.dump([g.to_dict() for g in filtered], f, indent=4)
            
        return True

    def load_all(self):
        if not os.path.exists(self.file_path):
            return []
        
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
                return [Gesture.from_dict(g) for g in data]
        except (json.JSONDecodeError, KeyError):
            return []
