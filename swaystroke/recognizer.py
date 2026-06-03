import math
from .config import MATCH_THRESHOLD

class Recognizer:
    def __init__(self, templates=None):
        self.templates = templates or []

    def recognize(self, gesture):
        if not self.templates:
            return None, 0.0

        normalized_target = gesture.normalize()
        if not normalized_target:
            return None, 0.0

        best_match = None
        best_score = 0.0

        for template in self.templates:
            normalized_template = template.normalize()
            score_fwd = self._compare(normalized_target, normalized_template)
            score_rev = self._compare(normalized_target, list(reversed(normalized_template)))
            score = max(score_fwd, score_rev)
            
            if score > best_score:
                best_score = score
                best_match = template

        if best_score >= MATCH_THRESHOLD:
            return best_match, best_score
        
        return None, best_score

    def _compare(self, pts1, pts2):
        """
        Calculates similarity between two normalized point sets.
        Returns a value between 0.0 and 1.0.
        """
        if len(pts1) != len(pts2):
            return 0.0

        total_dist = 0.0
        for p1, p2 in zip(pts1, pts2):
            total_dist += math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
        
        # Average distance
        avg_dist = total_dist / len(pts1)
        
        # Convert to a score where 1.0 is perfect match.
        # Max distance in a 1x1 box translated to origin is roughly sqrt(2).
        # We can use a simpler heuristic.
        score = max(0.0, 1.0 - avg_dist)
        return score
