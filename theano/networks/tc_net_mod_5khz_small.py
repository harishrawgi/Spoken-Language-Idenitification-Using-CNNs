import random
import numpy as np

import theano
import theano.tensor as T

import lasagne
from lasagne import layers
from lasagne.nonlinearities import rectify, softmax, sigmoid, tanh

import PIL.Image as Image
from base_network import BaseNetwork

floatX = theano.config.floatX


class Network(BaseNetwork):
    
    def __init__(self, train_list_raw, test_list_raw, png_folder, batch_size, dropout, l2, mode, batch_norm, **kwargs):
        
        print "==> not used params in DMN class:", kwargs.keys()
        self.train_list_raw = train_list_raw
        self.test_list_raw = test_list_raw
        self.png_folder = png_folder
        self.batch_size = batch_size
        self.dropout = dropout
        self.l2 = l2
        self.mode = mode
        self.batch_norm = batch_norm
        
        self.input_var = T.tensor4('input_var')
        self.answer_var = T.ivector('answer_var')
        
        print "==> building network"
        example = np.random.uniform(size=(self.batch_size, 1, 128, 858), low=0.0, high=1.0).astype(np.float32) #########
        answer = np.random.randint(low=0, high=176, size=(self.batch_size,)) #########
       
        network = layers.InputLayer(shape=(None, 1, 128, 858), input_var=self.input_var)
        print layers.get_output(network).eval({self.input_var:example}).shape
        
        # CONV-RELU-POOL 1
        network = layers.Conv2DLayer(incoming=network, num_filters=16, filter_size=(7, 7), 
                                     stride=1, nonlinearity=rectify)
        print layers.get_output(network).eval({self.input_var:example}).shape
        network = layers.MaxPool2DLayer(incoming=network, pool_size=(3, 3), stride=2, pad=2)
        print layers.get_output(network).eval({self.input_var:example}).shape
        if (self.batch_norm):
            network = layers.BatchNormLayer(incoming=network)
        
        # CONV-RELU-POOL 2
        network = layers.Conv2DLayer(incoming=network, num_filters=32, filter_size=(5, 5), 
                                     stride=1, nonlinearity=rectify)
        print layers.get_output(network).eval({self.input_var:example}).shape
        network = layers.MaxPool2DLayer(incoming=network, pool_size=(3, 3), stride=2, pad=2)
        print layers.get_output(network).eval({self.input_var:example}).shape
        if (self.batch_norm):
            network = layers.BatchNormLayer(incoming=network)

        
        # CONV-RELU-POOL 3
        network = layers.Conv2DLayer(incoming=network, num_filters=32, filter_size=(3, 3), 
                                     stride=1, nonlinearity=rectify)
        print layers.get_output(network).eval({self.input_var:example}).shape
        network = layers.MaxPool2DLayer(incoming=network, pool_size=(3, 3), stride=2, pad=2)
        print layers.get_output(network).eval({self.input_var:example}).shape
        if (self.batch_norm):
            network = layers.BatchNormLayer(incoming=network)
        
        # CONV-RELU-POOL 4
        network = layers.Conv2DLayer(incoming=network, num_filters=64, filter_size=(3, 3), 
                                     stride=1, nonlinearity=rectify)
        print layers.get_output(network).eval({self.input_var:example}).shape
        network = layers.MaxPool2DLayer(incoming=network, pool_size=(3, 3), stride=2, pad=2)
        print layers.get_output(network).eval({self.input_var:example}).shape
        if (self.batch_norm):
            network = layers.BatchNormLayer(incoming=network)
        
        # CONV-RELU-POOL 5
        network = layers.Conv2DLayer(incoming=network, num_filters=64, filter_size=(3, 3), 
                                     stride=1, nonlinearity=rectify)
        print layers.get_output(network).eval({self.input_var:example}).shape
        network = layers.MaxPool2DLayer(incoming=network, pool_size=(3, 3), stride=2, pad=2)
        print layers.get_output(network).eval({self.input_var:example}).shape
        if (self.batch_norm):
            network = layers.BatchNormLayer(incoming=network)

        
        # DENSE 1
        network = layers.DenseLayer(incoming=network, num_units=256, nonlinearity=rectify)
        if (self.batch_norm):
            network = layers.BatchNormLayer(incoming=network)
        if (self.dropout > 0):
            network = layers.dropout(network, self.dropout)
        print layers.get_output(network).eval({self.input_var:example}).shape

                
        # Last layer: classification
        network = layers.DenseLayer(incoming=network, num_units=176, nonlinearity=softmax)
        print layers.get_output(network).eval({self.input_var:example}).shape
        

        self.params = layers.get_all_params(network, trainable=True)
        self.prediction = layers.get_output(network)
        self.test_prediction = layers.get_output(network, deterministic=True)
        
        print "==> param shapes", [x.eval().shape for x in self.params]
        
        def get_loss(prediction):
            loss_ce = lasagne.objectives.categorical_crossentropy(prediction, self.answer_var).mean()
            if (self.l2 > 0):
                loss_l2 = self.l2 * lasagne.regularization.regularize_network_params(network, 
                                                                        lasagne.regularization.l2)
            else:
                loss_l2 = 0
            return loss_ce + loss_l2
    
        self.loss = get_loss(self.prediction)
        self.test_loss = get_loss(self.test_prediction)
        
        #updates = lasagne.updates.adadelta(self.loss, self.params)
        updates = lasagne.updates.momentum(self.loss, self.params, learning_rate=0.003)
        
        if self.mode == 'train':
            print "==> compiling train_fn"
            self.train_fn = theano.function(inputs=[self.input_var, self.answer_var], 
                                            outputs=[self.prediction, self.loss],
                                            updates=updates)
        
        print "==> compiling test_fn"
        # deterministic version
        #self.test_fn = theano.function(inputs=[self.input_var, self.answer_var],
        #                               outputs=[self.test_prediction, self.test_loss])
    
        # non deterministic version, as train_fn
        self.test_fn = theano.function(inputs=[self.input_var, self.answer_var],
                                       outputs=[self.prediction, self.loss])
    
    
    def say_name(self):
        return "tc_net_mod_5khz_small"
    

    def read_batch(self, data_raw, batch_index):

        start_index = batch_index * self.batch_size
        end_index = start_index + self.batch_size
        
        data = np.zeros((self.batch_size, 1, 128, 858), dtype=np.float32)
        answers = []
        
        for i in range(start_index, end_index):
            answers.append(int(data_raw[i].split(',')[1]))
            name = data_raw[i].split(',')[0]
            path = self.png_folder + name + ".png"
            im = Image.open(path)
            data[i - start_index, 0, :, :] = np.array(im).astype(np.float32)[:128, :] / 256.0

        answers = np.array(answers, dtype=np.int32)
        return data, answers
    
    