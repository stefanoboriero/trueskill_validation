# WELLA #
import tensorflow as tf
import numpy as np
from bipedal_walker import BipedalWalkerSuperEasy
from bipedal_walker import BipedalWalker
from bipedal_walker import BipedalWalkerHardcore


class BipedalWalkerWrapper:

    def __init__(self, hardcore=False, render=False, verbose=False):
        self.render = render
        self.verbose = verbose

    def create_env(self, hardcore=False, super_easy=False):
        # Create a BipedalWalker environmnet
        if hardcore:
            self.max_number_steps = 2000
            self.env = BipedalWalkerHardcore()
        elif super_easy:
            self.max_number_steps = 1600
            self.env = BipedalWalkerSuperEasy()
        else:
            self.max_number_steps = 1600
            self.env = BipedalWalker()

    def setup_simulation(self, render=False, verbose=False):
        # Setup variable for simulation
        self.n_step = 0
        self.render = render
        self.verbose = verbose

    def step(self, action):
        state, reward, done, info = self.env.step(action)
        self.n_step += 1
        # print(self.n_step)
        
        if(self.n_step == self.max_number_steps):
            done = True
        
        if self.render:
            self.env.render()

        return state, reward, done, info


    def reset_environment(self, render=False):
        self.render = render
        self.env.reset()
        self.n_step = 0



class BipedalWalkerAgent:

    def __init__(self):
        #self.base_path = '/home/stefano/Projects/gym_bipedal_walker_v2_solution/experiments/logs/bipedal_walker_hardcore/'
        self.base_path = './models/'
        self.sess = tf.Session()
        #self.load_model(0)
        self.observation_shape = (1,3,24)
        
        self.env_wrapper = BipedalWalkerWrapper(render=False)
        self.env_wrapper.setup_simulation(render=False)
        

    def build_model_path(self, model_number):
        self.model_number = model_number
        self.model_name = 'model-' + str(self.model_number) + '.ckpt'

        self.model_path = self.base_path + self.difficulty_path + self.model_name
        self.model_meta_path = self.model_path + '.meta'

    def load_model(self, id_number):
        self.build_model_path(id_number)
        saver = tf.train.import_meta_graph(self.model_meta_path)
        saver.restore(self.sess, self.model_path)
        # saver = tf.train.import_meta_graph('/home/stefano/Projects/gym_bipedal_walker_v2_solution/experiments/logs/bipedal_walker_easy/model-200000.ckpt.meta')
        # saver.restore(self.sess, '/home/stefano/Projects/gym_bipedal_walker_v2_solution/experiments/logs/bipedal_walker_easy/model-200000.ckpt')
        

        self.state_tensor = self.sess.graph.get_tensor_by_name('states0_ph:0')
        self.action_tensor = self.sess.graph.get_tensor_by_name('taking_action/model/dense_2/Tanh:0')
    
    def set_model_difficulty(self, path_string):
        self.difficulty_path = path_string + '/'

        
    def play(self, render=False):
        self.env_wrapper.reset_environment(render)
        self.reset()

        outcome = 0
        while True:
            feed_dict = {self.state_tensor: self.states}
            action = self.sess.run(self.action_tensor, feed_dict=feed_dict)[0]

            state, reward, done, info = self.env_wrapper.step(action)
            self.total_reward += reward
            # print(self.total_reward)
            self.rotate_observation_triplet(state)

            #if(self.total_reward == 300):
            #    print('TARGET REACHED')
            #    outcome = +1 # WIN
            #    break

            if done:
                if self.total_reward < 0:
                    outcome = -1 # LOSS    
                elif info['has_fallen']:
                        outcome = 0 # DRAW
                else:
                    if self.total_reward > 200:
                        outcome = +1 # WIN
                break
                
        return outcome, self.total_reward
    
    def set_environment_type(self, hardcore=False, super_easy=False):
        self.env_wrapper.create_env(hardcore=hardcore, super_easy=super_easy)

    def rotate_observation_triplet(self, new_observation):
        self.states[0][0] = self.states[0][1]
        self.states[0][1] = self.states[0][2]
        self.states[0][2] = new_observation

    def reset(self):
        self.states = np.zeros(self.observation_shape, dtype=np.float)
        initial_state = self.env_wrapper.step(np.array([0,0,0,0]))[0]

        self.states[0][0] = initial_state
        self.states[0][1] = initial_state
        self.states[0][2] = initial_state
        
        self.total_reward = 0.0



if __name__ == "__main__":
    agent = BipedalWalkerAgent()
    agent.set_model_difficulty('easy')
    agent.load_model(340000)
    agent.set_environment_type(hardcore=False, super_easy=True)
    total = 0.0
    for i in range(30):
        _, reward = agent.play(render=False)
        total += reward
        print(reward)
    print('#####################\n# Average Reward against easy: {}\n#####################'.format(total/30.0))

    agent.set_environment_type(hardcore=False, super_easy=False)
    total = 0.0
    for i in range(30):
        _, reward = agent.play(render=False)
        total += reward
        print(reward)
    print('#####################\n# Average Reward against medium: {}\n#####################'.format(total/30.0))

    
