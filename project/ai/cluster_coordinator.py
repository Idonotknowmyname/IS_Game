from ..ai.cluster_controller import ClusterController

from functools import reduce

import numpy as np

class ClusterCoordinator(ClusterController):

    def command(self):
        self.get_bots()

        opponent_locations = [opp.get_position() for opp in self.opponents]
        self.opponent_cluster = reduce(lambda x, y: x + y, opponent_locations) / len(opponent_locations)

        team_locations = [bot.get_position() for bot in self.team_bots]
        self.team_centroid = reduce(lambda x, y: x + y, team_locations) / len(team_locations)

        for bot in self.team_bots:

            visible_opponents = self.sees_enemy(bot)

            if len(visible_opponents) != 0 and bot.current_state == "Wait":
                weakest_opponent = self.get_weakest(visible_opponents)
                bot.target = weakest_opponent
                bot.current_state = "Shoot"

            if bot.current_state == "Wait":

                goal = None

                while goal is None or self.game.grid[bot.get_grid_node(goal)]:
                    rand_vec = np.random.rand(2) * 2 - 1
                    rand_vec = rand_vec / np.linalg.norm(rand_vec) * 80
                    goal = self.team_centroid + rand_vec

                self.go_to(bot,goal)

