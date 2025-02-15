# -*- coding: utf-8 -*-
# file: text_classification_augmentation.py
# time: 2021/8/5
# author: yangheng <hy345@exeter.ac.uk>
# github: https://github.com/yangheng95
# Copyright (C) 2021. All Rights Reserved.

from pyabsa.augmentation import auto_classification_augmentation

from pyabsa import TextClassification as TC

config = TC.TCConfigManager.get_tc_config_english()
config.model = TC.BERTTCModelList.BERT_MLP
config.num_epoch = 1
config.evaluate_begin = 0
config.max_seq_len = 80
config.dropout = 0.5
config.seed = {42}
config.log_step = -1
config.l2reg = 0.00001

SST2 = TC.TCDatasetList.SST2

auto_classification_augmentation(config=config, dataset=SST2, device='cuda')
