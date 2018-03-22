import numpy as np
from functools import reduce
from ..sprites.point import Point

class ClusterController:

    team = None
    team_bots = None
    game = None
    opponents = None
    opponent_cluster = None

    def __init__(self, game, team):
        self.game = game
        self.team = team


    def get_bots(self):

        if self.team == "a":
            self.team_bots = self.game.team_a
            self.opponents = self.game.team_b
        else:
            self.team_bots = self.game.team_b
            self.opponents = self.game.team_a

    def command(self):
        self.get_bots()
        opponent_locations = [opp.get_position() for opp in self.opponents]
        self.opponent_cluster = reduce(lambda x, y: x + y, opponent_locations) / len(opponent_locations)

        for bot in self.team_bots:

            visible_opponents = self.sees_enemy(bot)

            if len(visible_opponents) != 0:
                weakest_opponent = self.get_weakest(visible_opponents)
                bot.target = weakest_opponent
                bot.current_state = "Shoot"

            if bot.current_state == "Wait":
                self.go_to(bot,self.opponent_cluster)

    def go_to(self, bot, target):
        if bot.path_to_target is None:
            bot.target = target
            if isinstance(target, np.ndarray):
                bot.path_to_target = bot.pathfind(Point(target))
            else:
                bot.path_to_target = bot.pathfind(target)
        bot.current_state = "Go"

    def fire(self, bot, target):
        bot.target = target
        bot.current_state = "Shoot"

    def sees_enemy(self, bot1):
        targets = []

        for opponent in self.opponents:
            if bot1.is_target_visible(opponent):
               targets.append(opponent)

        return targets

    def get_weakest(self,opponents):
        return sorted(opponents,key=lambda x: x.health)[0]
