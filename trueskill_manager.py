import numpy as np
from trueskill import Rating
from trueskill import rate_1vs1
from trueskill import quality_1vs1
from database_utils import DatabaseManager

###############################
# IMPORTS FOR TESTING PURPOSES
###############################
from bipedal_walker_wrapper import BipedalWalkerAgent

###################################################
# TUPLES FORMAT:
# player = (id, name, surname, mu, sigma)
# opponent = (id, player_id, level_id, mu, sigma)
###################################################

class TrueskillManager(object):

    def __init__(self, name, surname):
        self.db = DatabaseManager()
        self.update_ranking_rate = 3
        self.step = 0
        self.set_player_tuple(name, surname)
        self.set_opponent_tuples(self.player_row[0])

    def set_player_tuple(self, name, surname):
        self.player_row = self.db.get_player_record(name, surname)

    def set_opponent_tuples(self, player_id):
        self.opponent_rows = self.db.get_opponents(player_id)
        self.opponent_rows.sort(key=self.sort_fun)

    def sort_fun(self, element):
        return element[2]

    def choose_opponent(self):
        # Return the opponent with the best drawing probability
        # The drawing prob is given by quality_1vs1(r1,r2)
        games_played = self.player_row[5]
        if self.player_row[6] == 0:
            self.update_opponent_ranking()
        player_rating = Rating(self.player_row[3], self.player_row[4])
        opponent_ratings = [Rating(opp[3], opp[4]) for opp in self.opponent_rows]

        draw_probabilities = [quality_1vs1(player_rating, opp) for opp in opponent_ratings]
        self.opponent_index = np.argmax(draw_probabilities)

        best_level = self.opponent_rows[self.opponent_index][2]
        return best_level

    def handle_game_outcome(self, outcome):
        # Updates Trueskill rankings
        opp = self.opponent_rows[self.opponent_index]

        p_rating, opp_rating = self.update_ratings(self.player_row, opp, outcome)

        self.opponent_rows[self.opponent_index] = (self.opponent_rows[self.opponent_index][0], self.opponent_rows[self.opponent_index][1], self.opponent_rows[self.opponent_index][2], opp_rating.mu, opp_rating.sigma)
        
        self.player_row = (self.player_row[0], self.player_row[1], self.player_row[2], p_rating.mu, p_rating.sigma, self.player_row[5] + 1, self.player_row[6])
        
        games_played = self.player_row[5]
        if games_played % 5**self.player_row[6] == 0:
            self.update_opponent_ranking()
        self.update_database()

        return

    def update_ratings(self, tuple_1, tuple_2, outcome):
        r1_old = Rating(tuple_1[3], tuple_1[4])
        r2_old = Rating(tuple_2[3], tuple_2[4])
        
        if outcome == 1:
            r1_new, r2_new = rate_1vs1(r1_old, r2_old)
        elif outcome == -1:
            r2_new, r1_new = rate_1vs1(r2_old, r1_old)
        else:
            r1_new, r2_new = rate_1vs1(r1_old, r2_old, drawn=True)

        return r1_new, r2_new

    def update_opponent_ranking(self):
        # Fake games between opponents: we already know what the ordering should be
        couples = []
        couples.append((0, 1)) # Easy vs Medium
        couples.append((1, 2)) # Medium vs Hard
        couples.append((0, 2)) # Easy vs Hard

        ratings = [Rating(opp[3], opp[4]) for opp in self.opponent_rows]

        for c in couples:
            winner = c[1]
            loser = c[0]
            #r0, r1 = self.update_ratings(self.opponent_rows[winner], self.opponent_rows[loser], +1)
            r0, r1 = rate_1vs1(ratings[winner], ratings[loser])
            
            ratings[winner] = r0
            ratings[loser] = r1
            
            self.opponent_rows[winner] = (self.opponent_rows[winner][0], self.opponent_rows[winner][1], self.opponent_rows[winner][2], ratings[winner].mu, ratings[winner].sigma)
            self.opponent_rows[loser]= (self.opponent_rows[loser][0], self.opponent_rows[loser][1], self.opponent_rows[loser][2], ratings[loser].mu, ratings[loser].sigma)
        
        self.player_row = (self.player_row[0], self.player_row[1], self.player_row[2], self.player_row[3], self.player_row[4], self.player_row[5], self.player_row[6]+1)
        self.update_database()
        return

    def update_database(self):
        # Updates the database with the current values of ratings
        self.db.update_player_tuple(self.player_row[0], self.player_row[3], self.player_row[4], self.player_row[5], self.player_row[6])

        for opp in self.opponent_rows:
            self.db.update_robot_tuple(self.player_row[0], opp[2], opp[3], opp[4])
        return


def set_env(agent, level_id):
    if level_id == 0:
        # Set super_easy environment
        agent.set_environment_type(hardcore=False, super_easy=True)
    elif level_id == 1:
        agent.set_environment_type(hardcore=False, super_easy=False)
    elif level_id == 2:
        agent.set_environment_type(hardcore=True, super_easy=False)

if __name__ == "__main__":
    t_manager = TrueskillManager()

    # level_id = t_manager.choose_opponent()
    # agent = BipedalWalkerAgent()
    t_manager.update_opponent_ranking()
    # for i in range(10):
    #     print('Playing against level: {}'.format(level_id))
    #     set_env(agent, level_id)
    #     outcome, reward = agent.play()
    #     print('Outcome: {}'.format(outcome))
    #     t_manager.handle_game_outcome(outcome)
    #     level_id = t_manager.choose_opponent()
