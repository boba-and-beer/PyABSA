# -*- coding: utf-8 -*-
# file: ram.py
# author: songyouwei <youwei0314@gmail.com>
# Copyright (C) 2018. All Rights Reserved.

import torch
import torch.nn as nn
import torch.nn.functional as F

from pyabsa.networks.dynamic_rnn import DynamicLSTM


class RAM_BERT(nn.Module):
    inputs = ['text_indices', 'aspect_indices', 'left_indices']

    def locationed_memory(self, memory, memory_len, left_len, aspect_len):
        batch_size = memory.shape[0]
        seq_len = memory.shape[1]
        memory_len = memory_len.cpu().numpy()
        left_len = left_len.cpu().numpy()
        aspect_len = aspect_len.cpu().numpy()
        weight = [[] for i in range(batch_size)]
        u = [[] for i in range(batch_size)]
        for i in range(batch_size):
            for idx in range(left_len[i]):
                weight[i].append(1 - (left_len[i] - idx) / memory_len[i])
                u[i].append(idx - left_len[i])
            for idx in range(left_len[i], left_len[i] + aspect_len[i]):
                weight[i].append(1)
                u[i].append(0)
            for idx in range(left_len[i] + aspect_len[i], memory_len[i]):
                weight[i].append(1 - (idx - left_len[i] - aspect_len[i] + 1) / memory_len[i])
                u[i].append(idx - left_len[i] - aspect_len[i] + 1)
            for idx in range(memory_len[i], seq_len):
                weight[i].append(1)
                u[i].append(0)
        u = torch.tensor(u, dtype=memory.dtype).to(self.config.device).unsqueeze(2)
        weight = torch.tensor(weight).to(self.config.device).unsqueeze(2)
        v = memory * weight
        memory = torch.cat([v, u], dim=2)
        return memory

    def __init__(self, bert, config):
        super(RAM_BERT, self).__init__()
        self.config = config
        self.embed = bert
        self.bi_lstm_context = DynamicLSTM(config.embed_dim, config.hidden_dim, num_layers=1, batch_first=True,
                                           bidirectional=True)
        self.att_linear = nn.Linear(config.hidden_dim * 2 + 1 + config.embed_dim * 2, 1)
        self.gru_cell = nn.GRUCell(config.hidden_dim * 2 + 1, config.embed_dim)
        self.dense = nn.Linear(config.embed_dim, config.output_dim)

    def forward(self, inputs):
        text_raw_indices, aspect_indices, text_left_indices = \
            inputs['text_indices'], inputs['aspect_indices'], inputs['left_indices']
        left_len = torch.sum(text_left_indices != 0, dim=-1)
        memory_len = torch.sum(text_raw_indices != 0, dim=-1)
        aspect_len = torch.sum(aspect_indices != 0, dim=-1)
        nonzeros_aspect = aspect_len.float()

        memory = self.embed(text_raw_indices)['last_hidden_state']
        memory, (_, _) = self.bi_lstm_context(memory, memory_len)
        memory = self.locationed_memory(memory, memory_len, left_len, aspect_len)
        memory = memory.float()
        aspect = self.embed(aspect_indices)['last_hidden_state']
        aspect = torch.sum(aspect, dim=1)
        aspect = torch.div(aspect, nonzeros_aspect.unsqueeze(-1))
        et = torch.zeros_like(aspect).to(self.config.device)

        batch_size = memory.size(0)
        seq_len = memory.size(1)
        if 'hops' not in self.config.args:
            self.config.hops = 3
        for _ in range(self.config.hops):
            g = self.att_linear(torch.cat([memory,
                                           torch.zeros(batch_size, seq_len, self.config.embed_dim).to(
                                               self.config.device) + et.unsqueeze(1),
                                           torch.zeros(batch_size, seq_len, self.config.embed_dim).to(
                                               self.config.device) + aspect.unsqueeze(1)],
                                          dim=-1))
            alpha = F.softmax(g, dim=1)
            i = torch.bmm(alpha.transpose(1, 2), memory).squeeze(1)
            et = self.gru_cell(i, et)
        out = self.dense(et)
        return {'logits': out}
