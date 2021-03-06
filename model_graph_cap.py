# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 07:18:29 2019

@author: limingfan
"""


import tensorflow as tf

from zoo_capsules import capsule_layer

from Zeras.model_baseboard import ModelBaseboard

class ModelCAP(ModelBaseboard):
    """
    """
    def __init__(self, settings):
        """
        """
        super(ModelCAP, self).__init__(settings)

        # input/output tensors
        self.pb_input_names = {"input_x": "input_x:0"}
        self.pb_output_names = {"logits": "vs_gpu/score/logits:0"}
        self.pb_save_names = ["vs_gpu/score/logits"]
        #
        self.debug_tensor_names = ["vs_gpu/score/logits:0",
                                   "vs_gpu/score/logits:0"]
    #
    def build_placeholder(self):
        """
        """         
        input_x = tf.placeholder(tf.int32, [None, None], name='input_x')
        input_y = tf.placeholder(tf.int64, [None], name='input_y')
        
        #        
        print(input_x)
        print(input_y)
        #
        input_tensors = {"input_x": input_x}
        label_tensors = {"input_y": input_y}
        #
        return input_tensors, label_tensors

    def build_inference(self, input_tensors):
        """
        """
        settings = self.settings        
        input_x = input_tensors["input_x"]
        #
        keep_prob = tf.get_variable("keep_prob", shape=[], dtype=tf.float32, trainable=False)
        #   
        with tf.device('/cpu:0'):
            emb_mat = tf.get_variable('embedding',
                                      [settings.vocab.size(), settings.vocab.emb_dim],
                                      initializer=tf.constant_initializer(settings.vocab.embeddings),
                                      trainable = settings.emb_tune,
                                      dtype=tf.float32)
            seq_emb = tf.nn.embedding_lookup(emb_mat, input_x)
            
            seq_mask = tf.cast(tf.cast(input_x, dtype = tf.bool), dtype = tf.int32)
    
        with tf.variable_scope("feat"):
            
            seq_e = seq_emb
            
            B = tf.shape(seq_e)[0]
        
            #
            num_caps = 3
            cap_dim = 64
            num_iter = 3
            
            caps_initial_state = tf.get_variable('caps_state', shape = (num_caps, cap_dim),
                                                 initializer = tf.truncated_normal_initializer() )
            caps_initial_state = tf.tile(tf.expand_dims(caps_initial_state, 0), [B, 1, 1])
            
            mask_t = tf.cast(seq_mask, dtype=tf.float32)    
            cap_d = capsule_layer(seq_e, mask_t, num_caps, cap_dim, num_iter = num_iter,
                                  keep_prob = keep_prob, caps_initial_state = caps_initial_state,
                                  scope="capsules")
            cap_d = tf.nn.relu(cap_d)
            #
            feat = tf.reshape(cap_d, [-1, num_caps * cap_dim])
            #
    
        with tf.name_scope("score"):
            #
            fc = tf.nn.dropout(feat, keep_prob)
            fc = tf.layers.dense(fc, 128, name='fc1')            
            fc = tf.nn.relu(fc)
            
            fc = tf.nn.dropout(fc, keep_prob)
            logits = tf.layers.dense(fc, settings.num_classes, name='fc2')
    
            normed_logits = tf.nn.softmax(logits, name='logits')
        
        #
        print(normed_logits)
        #
        output_tensors = {"normed_logits": normed_logits,
                          "logits": logits }
        #   
        return output_tensors
    
    def build_loss_and_metric(self, output_tensors, label_tensors):
        """
        """
        settings = self.settings
        
        logits = output_tensors["logits"]
        input_y = label_tensors["input_y"]         
        
        y_pred_cls = tf.argmax(logits, 1, name='pred_cls')
        
        with tf.name_scope("loss"):
            #
            cross_entropy = tf.nn.sparse_softmax_cross_entropy_with_logits(logits = logits,
                                                                           labels = input_y)
            loss = tf.reduce_mean(cross_entropy, name = 'loss')
    
        with tf.name_scope("accuracy"):
            #
            correct_pred = tf.equal(input_y, y_pred_cls)
            acc = tf.reduce_mean(tf.cast(correct_pred, tf.float32), name = 'metric')
            
        #
        print(loss)
        print(acc)
        #
        loss_and_metric = {"loss_model": loss,
                           "metric": acc}
        #
        return loss_and_metric
        #
        
