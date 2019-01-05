import numpy as np
import math
import trueskill
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
# player = (id, name, surname, mu, sigma, games_played, rank_updates)
# opponent = (id, player_id, level_id, mu, sigma)
###################################################

class TrueskillManager(object):
 
    def __init__(self, name, surname, baseline=False, verbose=False):
        self.db = DatabaseManager(baseline=baseline)
        self.update_ranking_rate = 3
        self.step = 0
        self.set_player_tuple(name, surname)
        self.set_changes = 0
        self.set_opponent_tuples(self.player.id)
        self.baseline = baseline
        self.verbose = verbose

    def set_player_tuple(self, name, surname):
        player_tuple = self.db.get_player_record(name, surname)
        # self.player_row = player_tuple
        self.player = PlayerRatingWrapper(player_tuple)

    def set_opponent_tuples(self, player_id):
        opponent_tuples = self.db.get_opponents(player_id)
        # self.opponent_rows = opponent_tuples
        # self.opponent_rows.sort(key=self.sort_fun)
        self.parameter_sets = [OpponentRatingWrapper(t) for t in opponent_tuples]
        self.parameter_sets.sort(key=self.sort_fun)

    def sort_fun(self, element):
        return element.level_id

    def choose_opponent(self):
        # Return the opponent with the best drawing probability
        # The drawing prob is given by quality_1vs1(r1,r2)
        games_played = self.player.games_played
        if not self.baseline:
            if self.player.rank_updates == 0:
                self.update_opponent_ranking()
        # player_rating = Rating(self.player_row[3], self.player_row[4])
        # opponent_ratings = [Rating(opp[3], opp[4]) for opp in self.opponent_rows]

        draw_probabilities = [quality_1vs1(self.player.rating, opp.rating) for opp in self.parameter_sets]
        sigmas = [opp.rating.sigma for opp in self.parameter_sets]
        if self.verbose:
            print('Draw probabilities: {}'.format(draw_probabilities))
            print('Sigmas: {}'.format(sigmas))

        new_opponent_index = np.argmax(draw_probabilities)
        
        if self.baseline:
            # Take greedy decision
            self.opponent_index = new_opponent_index
        else:
            try:
                if new_opponent_index != self.opponent_index:
                    delta_sigma = abs(sigmas[new_opponent_index] - sigmas[self.opponent_index])
                    delta_treshold = 0.5
                    # delta_sigma = sigmas[new_opponent_index] - sigmas[self.opponent_index]
                    # delta_treshold = 0.2 * self.set_changes
                    # delta_treshold = max(delta_treshold, 0.7)
                    if self.verbose:
                        print('Setting a treshold of {}'.format(delta_treshold))
                        print('Delta sigma: {}'.format(delta_sigma))
                    if delta_sigma > delta_treshold:
                        if self.verbose:
                            print('Changing set..')
                        self.set_changes += 1
                        self.opponent_index = new_opponent_index
            except Exception as e:
                # First time, we have to inizialize the variable
                self.opponent_index = new_opponent_index
        
        best_level = self.parameter_sets[self.opponent_index].level_id
        return best_level


    def are_close(self, p1, p2, treshold=0.1):
        if abs(p1 - p2) < treshold:
            return True
        return False

    def win_probability(self, player, opponent):
        delta_mu = player.mu - opponent.mu
        sum_sigma = player.sigma ** 2 + opponent.sigma ** 2
        ts = trueskill.global_env()
        BETA = ts.beta
        denom = math.sqrt(2 * (BETA * BETA) + sum_sigma)
        return ts.cdf(delta_mu / denom)

    def handle_game_outcome(self, outcome):
        # Updates Trueskill rankings
        opp = self.parameter_sets[self.opponent_index]

        p_rating, opp_rating = self.update_ratings(self.player.rating, opp.rating, outcome)
        
        self.parameter_sets[self.opponent_index].rating = opp_rating
        self.player.rating = p_rating
        self.player.games_played = self.player.games_played + 1
        
        if not self.baseline:
            games_played = self.player.games_played
            if games_played % 5**self.player.rank_updates == 0:
                self.update_opponent_ranking()
        self.update_database()
        return

    def update_ratings(self, r_1, r_2, outcome):
        r1_old = r_1
        r2_old = r_2
        
        if outcome == 1:
            r1_new, r2_new = rate_1vs1(r1_old, r2_old)
        elif outcome == -1:
            r2_new, r1_new = rate_1vs1(r2_old, r1_old)
        else:
            r1_new, r2_new = rate_1vs1(r1_old, r2_old, drawn=True)

        return r1_new, r2_new

    def update_opponent_ranking(self):
        # Fake games between opponents: we already know what the ordering should be
        if self.verbose:
            print('Updating rankings...')
        couples = []
        couples.append((0, 1)) # Easy vs Medium
        couples.append((1, 2)) # Medium vs Hard
        couples.append((0, 2)) # Easy vs Hard

        ratings = [opp.rating for opp in self.parameter_sets]

        for c in couples:
            winner = c[1]
            loser = c[0]
            r0, r1 = rate_1vs1(ratings[winner], ratings[loser])
            
            ratings[winner] = r0
            ratings[loser] = r1
            
            # self.opponent_rows[winner] = (self.opponent_rows[winner][0], self.opponent_rows[winner][1], self.opponent_rows[winner][2], ratings[winner].mu, ratings[winner].sigma)
            # self.opponent_rows[loser]= (self.opponent_rows[loser][0], self.opponent_rows[loser][1], self.opponent_rows[loser][2], ratings[loser].mu, ratings[loser].sigma)
        
            self.parameter_sets[winner].rating = r0
            self.parameter_sets[loser].rating = r1

        #self.player_row = (self.player_row[0], self.player_row[1], self.player_row[2], self.player_row[3], self.player_row[4], self.player_row[5], self.player_row[6]+1)
        self.player.rank_updates = self.player.rank_updates + 1
        self.update_database()
        return

    def update_database(self):
        # Updates the database with the current values of ratings
        #self.db.update_player_tuple(self.player_row[0], self.player_row[3], self.player_row[4], self.player_row[5], self.player_row[6])
        self.db.update_player_tuple(self.player.id, self.player.rating.mu, self.player.rating.sigma, self.player.games_played, self.player.rank_updates)

        for opp in self.parameter_sets:
            #self.db.update_robot_tuple(self.player_row[0], opp[2], opp[3], opp[4])
            self.db.update_robot_tuple(self.player.id, opp.level_id, opp.rating.mu, opp.rating.sigma)
        return

class PlayerRatingWrapper(object):
    ID_IDX = 0
    NAME_IDX = 1
    SURNAME_IDX = 2
    MU_IDX = 3
    SIGMA_IDX = 4
    GAMES_PLAYED_IDX = 5
    RANK_UPDATES_IDX = 6

    def __init__(self, values):
        self.id = values[self.ID_IDX]
        self.name = values[self.NAME_IDX]
        self.surname = values[self.SURNAME_IDX]
        self.rating = Rating(values[self.MU_IDX], values[self.SIGMA_IDX])
        self.games_played = values[self.GAMES_PLAYED_IDX]
        self.rank_updates = values[self.RANK_UPDATES_IDX]


class OpponentRatingWrapper(object):
    ID_IDX = 0
    PLAYER_ID_IDX = 1
    LEVEL_ID_IDX = 2
    MU_IDX = 3
    SIGMA_IDX = 4

    def __init__(self, values):
        self.id = values[self.ID_IDX]
        self.player_id = values[self.PLAYER_ID_IDX]
        self.level_id = values[self.LEVEL_ID_IDX]
        self.rating = Rating(values[self.MU_IDX], values[self.SIGMA_IDX])


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






    # def choose_opponent(self):
    #     # Return the opponent with the best drawing probability
    #     # The drawing prob is given by quality_1vs1(r1,r2)
    #     games_played = self.player_row[5]
    #     if not self.baseline:
    #         if self.player_row[6] == 0:
    #             self.update_opponent_ranking()
    #     player_rating = Rating(self.player_row[3], self.player_row[4])
    #     opponent_ratings = [Rating(opp[3], opp[4]) for opp in self.opponent_rows]

    #     draw_probabilities = [quality_1vs1(player_rating, opp) for opp in opponent_ratings]
    #     sigmas = [opp.sigma for opp in opponent_ratings]

    #     new_opponent_index = np.argmax(draw_probabilities)
    #     try:
    #         if new_opponent_index != self.opponent_index:
    #             delta_sigma = abs(sigmas[new_opponent_index] - sigmas[self.opponent_index])
    #             # print('Delta sigma: {}'.format(delta_sigma))
    #             if delta_sigma > 0.5:
    #                 self.opponent_index = new_opponent_index
    #     except Exception as e:
    #         self.opponent_index = new_opponent_index
        

    #     # print(draw_probabilities)
    #     # print(sigmas)
        
    #     if self.baseline:
    #         self.opponent_index = np.argmax(draw_probabilities)
    #
    #     best_level = self.opponent_rows[self.opponent_index][2]
    #     return best_level