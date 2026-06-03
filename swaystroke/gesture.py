import math

class Gesture:
    def __init__(self, points=None, name=None, command=None, app_id=None, app_class=None, id=None, action_type="command"):
        self.points = points or []
        self.name = name
        self.command = command
        self.app_id = app_id
        self.app_class = app_class
        self.id = id
        self.action_type = action_type

    def add_point(self, x, y):
        self.points.append((x, y))

    def normalize(self, num_points=32):
        """
        Simplistic normalization:
        1. Resample to fixed number of points.
        2. Scale to a 1x1 bounding box.
        3. Translate centroid to origin.
        """
        if len(self.points) < 2:
            return []

        # 1. Resample
        resampled = self._resample(self.points, num_points)
        
        # 2. Scale
        scaled = self._scale(resampled)
        
        # 3. Translate
        normalized = self._translate_to_origin(scaled)
        
        return normalized

    def _resample(self, points, n):
        I = self._path_length(points) / (n - 1)
        D = 0.0
        new_points = [points[0]]
        i = 1
        while i < len(points):
            d = self._distance(points[i-1], points[i])
            if (D + d) >= I:
                qx = points[i-1][0] + ((I - D) / d) * (points[i][0] - points[i-1][0])
                qy = points[i-1][1] + ((I - D) / d) * (points[i][1] - points[i-1][1])
                new_points.append((qx, qy))
                points.insert(i, (qx, qy))
                D = 0.0
            else:
                D += d
            i += 1
        
        # Ensure we have exactly n points (sometimes floating point errors)
        if len(new_points) == n - 1:
            new_points.append(points[-1])
        return new_points[:n]

    def _path_length(self, points):
        d = 0.0
        for i in range(1, len(points)):
            d += self._distance(points[i-1], points[i])
        return d

    def _distance(self, p1, p2):
        return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

    def _scale(self, points):
        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)
        
        width = max_x - min_x
        height = max_y - min_y
        
        # Avoid division by zero
        if width == 0: width = 1
        if height == 0: height = 1
        
        scale = max(width, height)
        
        return [((p[0] - min_x) / scale, (p[1] - min_y) / scale) for p in points]

    def _translate_to_origin(self, points):
        centroid_x = sum(p[0] for p in points) / len(points)
        centroid_y = sum(p[1] for p in points) / len(points)
        return [(p[0] - centroid_x, p[1] - centroid_y) for p in points]

    def to_dict(self):
        return {
            "id": getattr(self, "id", None),
            "name": self.name,
            "command": self.command,
            "points": self.points,
            "app_id": getattr(self, "app_id", None),
            "app_class": getattr(self, "app_class", None),
            "action_type": getattr(self, "action_type", "command")
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            points=[tuple(p) for p in data.get("points", [])], 
            name=data.get("name"),
            command=data.get("command"),
            app_id=data.get("app_id"),
            app_class=data.get("app_class"),
            id=data.get("id"),
            action_type=data.get("action_type", "command")
        )
