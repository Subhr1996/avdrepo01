    def can_move(self, dice):
        if self.finished:
            return False
        if self.pos == -1:
            return dice == 6
        remaining = 57 - self.pos  # steps to home (58 = center, but 52+5=57 is last home col)
        return dice <= remaining + 1