# -*- coding: utf-8 -*-
# file: bert_classification_inference.py
# time: 2021/8/5
# author: yangheng <yangheng@m.scnu.edu.cn>
# github: https://github.com/yangheng95
# Copyright (C) 2021. All Rights Reserved.

import os

import findfile
from pyabsa import TextAdversarialDefense as TAD, DatasetItem

os.environ['PYTHONIOENCODING'] = 'UTF8'

dataset = 'SST2TextFooler'
inference_sets = DatasetItem(dataset, findfile.find_cwd_files([dataset, '.org', '.inference']))

text_classifier = TAD.TADTextClassifier('tadbert_SST2TextFooler_cls_acc_94.18_cls_f1_94.16_adv_det_acc_90.69_adv_det_f1_90.65_adv_training_acc_92.67_adv_training_f1_92.67',
                                        auto_device=True,  # Use CUDA if available
                                        )

# inference_sets = DatasetItem(dataset)
results = text_classifier.batch_predict(target_file=inference_sets,
                                        print_result=False,
                                        save_result=False,
                                        ignore_error=False,
                                        )