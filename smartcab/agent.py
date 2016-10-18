import pdb
import random
from environment import Agent, Environment, TrafficLight
from planner import RoutePlanner
from simulator import Simulator
import operator

class LearningAgent(Agent):
    """An agent that learns to drive in the smartcab world."""

    def __init__(self, env, trials=1):
        super(LearningAgent, self).__init__(env)  # sets self.env = env, state = None, next_waypoint = None, and a default color
        self.color = 'red'  # override color
        self.planner = RoutePlanner(self.env, self)  # simple route planner to get next_waypoint
        # TODO: Initialize any additional variables here
        self.Q = {}
        self.default_Q = 1

        # q-learning parameters
        self.alpha = 0.8
        self.gamma = 0.2
        self.epsilon = 0.05

        # statistics
        self.success = 0
        self.attempts = 0
        self.trials = trials
        self.penalties = 0
        self.moves = 0
        self.net_reward = 0

    def reset(self, destination=None):
        self.planner.route_to(destination)
        # TODO: Prepare for a new trip; reset any variables here, if required
        self.prev_state = None
        self.prev_action = None
        self.prev_reward = None

    def update(self, t):
        # Gather inputs
        self.next_waypoint = self.planner.next_waypoint()  # from route planner, also displayed by simulator
        inputs = self.env.sense(self)
        deadline = self.env.get_deadline(self)

        # TODO: Update state
        self.state = inputs
        self.state['next_waypoint'] = self.next_waypoint
        self.state = tuple(sorted(inputs.items()))
        
        # TODO: Select action according to your policy
        Q, action = self.select_Q_action(self.state)

        # Execute action and get reward
        reward = self.env.act(self, action)


        # TODO: Learn policy based on state, action, reward
        if self.prev_state != None:
            if (self.prev_state, self.prev_action) not in self.Q:
                self.Q[(self.prev_state, self.prev_action)] = self.default_Q
            self.Q[(self.prev_state,self.prev_action)] = (1 - self.alpha) * self.Q[(self.prev_state,self.prev_action)] + self.alpha * (self.prev_reward + self.gamma * self.select_Q_action(self.state)[0])

        self.prev_state = self.state
        self.prev_action = action
        self.prev_reward = reward

        # Additional statistics
        self.net_reward += reward
        self.moves += 1
        if reward < 0:
            self.penalties += 1

        add_total = False
        if deadline == 0:
            add_total = True
        if reward >= 10:
            self.success += 1
            add_total = True
        if add_total:
            self.attempts += 1
            print self.stats()
        self.env.status_text += ' ' + self.stats()

        print "LearningAgent.update(): deadline = {}, inputs = {}, action = {}, reward = {}".format(deadline, inputs, action, reward)  # [debug]

    def stats(self):
        """Get additional stats"""
        if self.attempts == 0:
            success_rate = 0
        else:
            success_rate = round(float(self.success)/float(self.attempts), 2)
        penalty_rate = round(float(self.penalties)/float(self.moves), 2)
        return "success_rate: {}/{} ({})\npenalty_rate: {}/{} ({})\nnet_reward: {}".format(
                self.success, self.attempts, success_rate, self.penalties, self.moves, penalty_rate, self.net_reward)

    def select_Q_action(self, state):
        """Select max Q and action based on given state."""
        best_action = random.choice(Environment.valid_actions)
        if random.random() < self.epsilon:
            max_Q = self.get_Q_value(state, best_action)
        else:
            max_Q = float('-inf')
            for action in Environment.valid_actions:
                Q = self.get_Q_value(state, action)
                if Q > max_Q:
                    max_Q = Q
                    best_action = action
                elif Q == max_Q:
                    if random.random() < 0.5:
                        best_action = action
        return (max_Q, best_action)


    def get_Q_value(self, state, action):
        """Get Q value given state and action."""
        return self.Q.get((state, action), self.default_Q)

def run():
    """Run the agent for a finite number of trials."""

    # Set up environment and agent
    e = Environment()  # create environment (also adds some dummy traffic)
    a = e.create_agent(LearningAgent)  # create agent
    e.set_primary_agent(a, enforce_deadline=True)  # specify agent to track
    # NOTE: You can set enforce_deadline=False while debugging to allow longer trials

    # Now simulate it
    sim = Simulator(e, update_delay=0, display=False)  # create simulator (uses pygame when display=True, if available)
    # NOTE: To speed up simulation, reduce update_delay and/or set display=False

    sim.run(n_trials=100)  # run for a specified number of trials
    # NOTE: To quit midway, press Esc or close pygame window, or hit Ctrl+C on the command-line


if __name__ == '__main__':
    run()
