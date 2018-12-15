
import sqlite3

class Dumper(object):

    def __init__(self):
        self.db_path = './data/trueskillDB.db'
        
    def get_player(self, name, surname):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        values = (name, surname,)
        cur.execute('SELECT * FROM players WHERE name=? AND surname=?', values)
        players = cur.fetchall()
        conn.close()
        return players
        

    def get_all_players(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute('SELECT * FROM players')
        players = cur.fetchall()
        conn.close()
        return players

    def get_opponents(self, player_id):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute('SELECT * FROM robots WHERE player_id=?', (player_id,))
        opponents = cur.fetchall()
        conn.close()
        return opponents
    
    def print_ranking(self, player, opponents):
        print(player)
        print('#########################')
        print('{} {}\n\tmu:{}\n\tsigma:{}\n\tgames_played:{}\n\trank_update{}'.format(player[1], player[2], player[3], player[4], player[5], player[6]))
        for o in opponents:
            print('level:{}\n    mu:{}\n    sigma:{}'.format(o[2], o[3], o[4]))
        print('#########################')

    def dump(self, name=None, surname=None, verbose=True):
        out = None
        if name == None:
            players = self.get_all_players()
        else:
            players = self.get_player(name, surname)
            out = []

        for p in players:
            opps = self.get_opponents(p[0])
            if verbose:
                self.print_ranking(p, opps)
        if out != None:
            for o in opps:
                out.append(o)
            out.append(players[0])
        return out
        

if __name__ == "__main__":
    dumper = Dumper()
    dumper.dump()