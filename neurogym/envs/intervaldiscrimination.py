from __future__ import division

import numpy as np
from gym import spaces

import neurogym as ngym


# TODO: Getting duration is not intuitive, not clear to people
class IntervalDiscrimination(ngym.PeriodEnv):
    r"""Agents have to report which of two stimuli presented
    sequentially is longer.
    """
    metadata = {
        'paper_link': 'https://www.sciencedirect.com/science/article/pii/' +
        'S0896627309004887',
        'paper_name': """Feature- and Order-Based Timing Representations
         in the Frontal Cortex""",
        'tags': ['timing', 'working memory', 'delayed response',
                 'two-alternative', 'supervised']
    }

    def __init__(self, dt=80, rewards=None, timing=None):
        super().__init__(dt=dt)
        # Rewards
        self.rewards = {'abort': -0.1, 'correct': +1., 'fail': 0.}
        if rewards:
            self.rewards.update(rewards)

        self.timing = {
            'fixation': ('constant', 300),
            'stim1': ('uniform', (300, 600)),
            'delay1': ('choice', [800, 1500]),
            'stim2': ('uniform', (300, 600)),
            'delay2': ('constant', 500),
            'decision': ('constant', 300)}
        if timing:
            self.timing.update(timing)

        self.abort = False

        self.action_space = spaces.Discrete(3)
        self.act_dict = {'fixation': 0, 'choice1': 1, 'choice2': 2}
        self.observation_space = spaces.Box(-np.inf, np.inf, shape=(3,),
                                            dtype=np.float32)
        self.ob_dict = {'fixation': 0, 'stim1': 1, 'stim2': 2}

    def new_trial(self, **kwargs):
        duration1 = self.sample_time('stim1')
        duration2 = self.sample_time('stim2')
        ground_truth = 1 if duration1 > duration2 else 2

        periods = ['fixation', 'stim1', 'delay1', 'stim2', 'delay2', 'decision']
        durations = [None, duration1, None, duration2, None, None]
        self.add_period(periods, duration=durations, after=0, last_period=True)

        self.add_ob(1, where='fixation')
        self.add_ob(1, 'stim1', where='stim1')
        self.add_ob(1, 'stim2', where='stim2')
        self.set_ob(0, 'decision')

        self.set_groundtruth(ground_truth, 'decision')

    def _step(self, action):
        # ---------------------------------------------------------------------
        # Reward and inputs
        # ---------------------------------------------------------------------
        new_trial = False
        # rewards
        reward = 0
        gt = self.gt_now
        # observations
        if self.in_period('fixation'):
            if action != 0:  # action = 0 means fixating
                new_trial = self.abort
                reward = self.rewards['abort']
        elif self.in_period('decision'):
            if action != 0:
                new_trial = True
                if action == gt:
                    reward = self.rewards['correct']
                    self.performance = 1
                else:
                    reward = self.rewards['fail']

        return self.ob_now, reward, False, {'new_trial': new_trial, 'gt': gt}


if __name__ == '__main__':
    from neurogym.tests import test_run
    env = IntervalDiscrimination()
    test_run(env)
    ngym.utils.plot_env(env, def_act=0)
