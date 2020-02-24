#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 24 15:10:35 2019

@author: molano

Economic choice task, based on

  Neurons in the orbitofrontal cortex encode economic value.
  C Padoa-Schioppa & JA Assad, Nature 2006.

  http://dx.doi.org/10.1038/nature04676

"""
from __future__ import division

import numpy as np
from neurogym.utils import tasktools
import neurogym as ngym
from gym import spaces


class EconomicDecisionMaking(ngym.PeriodEnv):
    metadata = {
        'description': '''Agents choose between two stimuli (A and B; where A
         is preferred) offered in different amounts.''',
        'paper_link': 'https://www.nature.com/articles/nature04676',
        'paper_name': '''Neurons in the orbitofrontal cortex encode
         economic value''',
        'timing': {
            'fixation': ('constant', 1500),
            'offer_on': ('uniform', [1000, 2000]),
            'decision': ('constant', 750)},
        'tags': ['perceptual', 'value-based']
    }

    def __init__(self, dt=100, rewards=None, timing=None):
        """
        Agents choose between two stimuli (A and B; where A is preferred)
        offered in different amounts.
        dt: Timestep duration. (def: 100 (ms), int)
        rewards:
            R_ABORTED: given when breaking fixation. (def: -0.1, float)
            R_CORRECT: rew associated to most valued juice. (def: .22, float)
        timing: Description and duration of periods forming a trial.
        """
        super().__init__(dt=dt, timing=timing)
        # Inputs
        self.inputs = tasktools.to_map('FIXATION', 'L-A', 'L-B', 'R-A',
                                       'R-B', 'N-L', 'N-R')

        # Actions
        self.actions = tasktools.to_map('FIXATE', 'CHOOSE-LEFT',
                                        'CHOOSE-RIGHT')

        # trial conditions
        self.B_to_A = 1/2.2
        self.juices = [('A', 'B'), ('B', 'A')]
        self.offers = [(0, 1), (1, 3), (1, 2), (1, 1), (2, 1),
                       (3, 1), (4, 1), (6, 1), (2, 0)]

        # Input noise
        sigma = np.sqrt(2*100*0.001)
        self.sigma_dt = sigma/np.sqrt(self.dt)

        # Rewards
        self.rewards = {'abort': -0.1, 'correct': +0.22}
        if rewards:
            self.rewards.update(rewards)

        self.R_B = self.B_to_A * self.rewards['correct']
        self.R_A = self.rewards['correct']
        self.abort = False
        # Increase initial policy -> baseline weights
        self.baseline_Win = 10

        self.action_space = spaces.Discrete(3)
        self.observation_space = spaces.Box(-np.inf, np.inf, shape=(7, ),
                                            dtype=np.float32)

    # Input scaling
    def scale(self, x):
        return x/5

    def new_trial(self, **kwargs):
        # ---------------------------------------------------------------------
        # Trial
        # ---------------------------------------------------------------------
        self.trial = {
            'juice': self.juices[self.rng.choice(len(self.juices))],
            'offer': self.offers[self.rng.choice(len(self.offers))]
        }
        self.trial.update(kwargs)

        juiceL, juiceR = self.trial['juice']
        nB, nA = self.trial['offer']

        if juiceL == 'A':
            nL, nR = nA, nB
        else:
            nL, nR = nB, nA

        # ---------------------------------------------------------------------
        # Periods
        # ---------------------------------------------------------------------
        self.add_period('fixation', after=0)
        self.add_period('offer_on', after='fixation')
        self.add_period('decision', after='offer_on', last_period=True)

        # ---------------------------------------------------------------------
        # Inputs
        # ---------------------------------------------------------------------
        self.set_ob([1]+[0]*6, 'fixation')
        ob = self.view_ob('offer_on')
        ob[:, 0] = 1
        ob[:, self.inputs['L-'+juiceL]] = 1
        ob[:, self.inputs['R-'+juiceR]] = 1
        ob[:, self.inputs['N-L']] = self.scale(nL)
        ob[:, self.inputs['N-R']] = self.scale(nR)
        ob[:, [self.inputs['N-L'], self.inputs['N-R']]] += \
            self.rng.randn(ob.shape[0], 2) * self.sigma_dt

    def _step(self, action):
        trial = self.trial

        new_trial = False

        obs = self.obs_now

        reward = 0
        if self.in_period('fixation') or self.in_period('offer_on'):
            if action != self.actions['FIXATE']:
                new_trial = self.abort
                reward = self.rewards['abort']
        elif self.in_period('decision'):
            if action in [self.actions['CHOOSE-LEFT'],
                          self.actions['CHOOSE-RIGHT']]:
                new_trial = True

                juiceL, juiceR = trial['juice']

                nB, nA = trial['offer']
                rA = nA * self.R_A
                rB = nB * self.R_B

                if juiceL == 'A':
                    rL, rR = rA, rB
                else:
                    rL, rR = rB, rA

                if action == self.actions['CHOOSE-LEFT']:
                    reward = rL
                    self.performance = rL > rR
                elif action == self.actions['CHOOSE-RIGHT']:
                    reward = rR
                    self.performance = rR > rL

        return obs, reward, False, {'new_trial': new_trial, 'gt': 0}