# trueskill_validation

This repository hosts code and results to evaluate an approach to difficulty level balancing using Microsoft TrueSkill ranking system

## Approach
Standard TrueSkill is used to rank different players playing the same game. It models each player as a gaussian where the mean represents the skill of the player and the variance the uncertainty of the skill estimate: such representation is called Rating. After each game, the ratings of the two opponents are updated based on their initial values and the outcome of the game. To make the game more engaging, we want to select the difficulty level that maximizes the draw probability of the game.  
In our approach players are not competing against each other but rather are competing against a difficulty level. Thus we have to redefine what a game is and what is the outcome of such game. From our perspective a game is a competition between a player and a difficulty level for a given game. The winner is the player if it can solve the game, the difficulty level otherwise: depending on the game, it could be defined also a draw condition where the winner is not determined. We then treat difficulty levels as players, thus with an associated Rating.  
If we just run basic TrueSkill with this settings, we see that it performs poorly: sometimes the chosen difficulty level oscillates and sometimes it converges to the wrong one. The main problem is that difficulty players never play against each other, so their relative ranking is not reliable.  
We try to exploit the fact that we know what the relative ranking between levels should be to stabilize the dynamics of the skills estimation evolution. To do so, we simulate games between difficulty levels for which we know the outcome since they have a ranking by definition (easy < medium < hard). These games are used to update difficulty level Ratings in order to make them stable. We do so at a decreasing rate, as the ranking is going to converge. This approach performed better in both chosen difficulty level and convergence time

## Validation
In order to study and validate our approach, we tested it on a simulated game

### Selected environment
The environment we chose is the BipedalWalker environment from openai gym https://gym.openai.com/envs/BipedalWalker-v2/. It already has defined two difficulty level: the basic one with some small hills and valleys, and the hardcore one with stairs and steps. We added another level as the easiest where the ground is completly flat. We defined a player win situation if it reaches the end of the field, a draw situation if it covers enough terrain but doesn't make it to the end, and a loss situation if it stumbles early.

### Model generation
We need to have agents with a different skill set in order to evaluate in a proper manner our approach. To do so, we trained a bunch of reinforcement learning agent to solve the environment at different difficulty levels, starting from the assumption that an agent trained on the medium level is not going to be able to solve the hard one. To do so we tweaked the approach used by https://github.com/parilo/gym_bipedal_walker_v2_solution. We saved a model each 100000 training steps on the assumption that agents that have been trained longer are more skilled. We saved them in the /models folder using the naming convention /difficulty_trained_on/save_trained_id (i.e. the model 200000 under the easy folder is the one trained for 200000 steps on the easy difficulty level).

### Ground truth evaluation
To have a ground truth to evaluate our approach, for each model we run 50 games for each level and collected the rewards and outcomes (win, draw, loss). Resulting plots can be found in the /img/ground_truth folder. You'll find 3 folders: one containing the plotting for models trained on the easy environment, containing the plotting for models trained on the medium environment, containing the plotting for models trained on the hard environment. 

### Plotting
To have a visual comprehension of everything, we condensed several plots into one that summurizes the outcome of the approach. The final plot will present the evolution of the skill estimation for both the basic baseline (on the bottom left) and for our approach (top left) as well as the difficulty level chosen at each time step. On the right side it will present, for each difficulty level, the win, draw and loss probabilities, following the same color code of the left side plots.  
Those plots can be found under the /img/cumulative_plots/with_baseline folder
