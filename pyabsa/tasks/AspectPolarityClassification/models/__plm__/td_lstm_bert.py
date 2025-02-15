# -*- coding: utf-8 -*-
# file: td_lstm.py
# author: songyouwei <youwei0314@gmail.com>
# Copyright (C) 2018. All Rights Reserved.

import torch
import torch.nn as nn

from pyabsa.networks.dynamic_rnn import DynamicLSTM


class TD_LSTM_BERT(nn.Module):
    inputs = ['left_with_aspect_indices', 'right_with_aspect_indices']

    def __init__(self, bert, config):
        super(TD_LSTM_BERT, self).__init__()
        self.embed = bert
        self.lstm_l = DynamicLSTM(config.embed_dim, config.hidden_dim, num_layers=1, batch_first=True)
        self.lstm_r = DynamicLSTM(config.embed_dim, config.hidden_dim, num_layers=1, batch_first=True)
        self.dense = nn.Linear(config.hidden_dim * 2, config.output_dim)

    def forward(self, inputs):
        x_l, x_r = inputs['left_with_aspect_indices'], inputs['right_with_aspect_indices']
        x_l_len, x_r_len = torch.sum(x_l != 0, dim=-1), torch.sum(x_r != 0, dim=-1)
        x_l, x_r = self.embed(x_l)['last_hidden_state'], self.embed(x_r)['last_hidden_state']
        _, (h_n_l, _) = self.lstm_l(x_l, x_l_len)
        _, (h_n_r, _) = self.lstm_r(x_r, x_r_len)
        h_n = torch.cat((h_n_l[0], h_n_r[0]), dim=-1)
        out = self.dense(h_n)
        return {'logits': out}
