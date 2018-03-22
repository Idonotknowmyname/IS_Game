import numpy as np
from functools import reduce

class ClusterController:

    team = None
    team_bots = None
    game = None
    opponent_positions = None
    opponent_cluster = None

    def __init__(self, game, team):
        self.game = game
        self.team = team


    def get_bots(self):

        if self.team == "a":
            self.team_bots = self.game.team_a
            self.opponent_positions = [opp.get_position() for opp in self.game.team_b]
        else:
            self.team_bots = self.game.team_b
            self.opponent_positions = [opp.get_position() for opp in self.game.team_a]

    def command(self):
        self.get_bots()
        self.opponent_cluster = reduce(lambda x, y: x + y, self.opponent_positions) / len(self.opponent_positions)

        for bot in self.team_bots:



            if bot.current_state == "Wait":
                self.go_to(bot,self.opponent_cluster)

    def go_to(self, bot, target):
        bot.target = target
        bot.path_to_target = bot.pathfind()
        bot.current_state = "Go"

    def fire(self, bot, target):
        bot.target = target
        bot.current_state = "Shoot"

    def sees_enemy(self, bot1):

        targets = []

        for opponent in self.opponent_positions:
            if bot1.is_target_visible(opponent):
               targets.append(opponent)

        return targets
