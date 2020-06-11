#miniClassifier (for poor mans laptop)

import tensorflow as tf
import meta
import numpy as np

tf.compat.v1.reset_default_graph()

class miniClassifier():
    def __init__(self, X, Y, totalClasses = 2, preOutput = 300):
        self.learn_rate = 0.0001
        self.Img = X
        self.Label = Y
        self.totalClasses = totalClasses
        self.preOutputSize = preOutput
        
        self.save_path = None
        self.sess = None

        self.input = tf.compat.v1.placeholder(dtype = tf.float32, shape = (None,self.Img.shape[1],self.Img.shape[2],self.Img.shape[3]))
        self.output = tf.compat.v1.placeholder(dtype = tf.float32, shape = (None,self.Label.shape[1]))

    def set_learning_rate(self,lr):
        if(lr >0 and lr <1):
            self.learn_rate = lr
            
    def conv_layer(self, inFeed, tfFilter, bias,padding_type, name):
        #VALID -> ensures shrinking
        #SAME -> ensures same dimension
        convolve = tf.nn.conv2d(inFeed ,tfFilter, strides = (1,1,1,1), padding = padding_type)
        biased = tf.nn.bias_add(convolve, bias)
        return tf.nn.leaky_relu(biased, alpha = 0.3, name = name)
    
    def max_pooling(self,inFeed,name):
        return tf.nn.max_pool(inFeed, ksize = [1,2,2,1], strides = [1,2,2,1], padding = "SAME", name = name)
    
    def avg_pooling(self,inFeed,name):
        return tf.nn.avg_pool(inFeed, ksize = [1,2,2,1], strides = [1,2,2,1] ,padding = "SAME", name = name)
        
    def flatten(self, layer):        
        ln = len(layer.shape)
        totalNeurons = 1
        for i in range(1,ln):
            totalNeurons*=layer.shape[i].value
        return tf.reshape(layer,[-1,totalNeurons])
    
    def fullcon(self, layer, name, inputNeurons, outputNeurons, keep_prob = 0.3 ):
        W = tf.Variable(name = name, shape = (inputNeurons,outputNeurons), dtype = tf.float32, initial_value = tf.random.normal((inputNeurons,outputNeurons), mean = 0.0, stddev = 1, dtype = tf.float32))
        b = tf.Variable(name = name, shape = (outputNeurons,), dtype = tf.float32, initial_value = tf.random.normal((outputNeurons,), mean = 0.0, stddev = 1, dtype = tf.float32))

        self.weights[name] = W
        self.biases[name] = b        
        fc = tf.nn.bias_add(tf.matmul(layer,W),b)
        dropped = tf.nn.dropout(fc, keep_prob = keep_prob, name = name)
        return dropped

    def build(self):        
        weights = {
            'w1_1': tf.Variable(initial_value = tf.truncated_normal_initializer(mean = 0.0, stddev = 1, dtype = tf.float32)([3,3,3,5]),dtype = tf.float32,shape = [3,3,3,5], name = 'w1_1'),
            'w2_1': tf.Variable(initial_value = tf.truncated_normal_initializer(mean = 0.0, stddev = 1, dtype = tf.float32)([3,3,5,10]),dtype = tf.float32,shape = [3,3,5,10], name = 'w2_1'),
            'w3_1': tf.Variable(initial_value = tf.truncated_normal_initializer(mean = 0.0, stddev = 1, dtype = tf.float32)([3,3,10,2]),dtype = tf.float32,shape = [3,3,10,2], name = 'w3_1'),
            }

        biases = {
            'b1_1': tf.Variable(initial_value = tf.random.normal(shape = (5,), mean = 0.0, stddev = 1, dtype = tf.float32), dtype = tf.float32,shape = (5,), name = 'b1_1'),
            'b2_1': tf.Variable(initial_value = tf.random.normal(shape = (10,), mean = 0.0, stddev = 1, dtype = tf.float32), dtype = tf.float32,shape = (10,), name = 'b2_1'),
            'b3_1': tf.Variable(initial_value = tf.random.normal(shape = (2,), mean = 0.0, stddev = 1, dtype = tf.float32), dtype = tf.float32,shape = (2,), name = 'b3_1'),            
            }

        self.weights = weights; self.biases = biases;

        self.conv1_1 = self.conv_layer(self.input,weights["w1_1"],biases["b1_1"],'VALID', 'conv1_1')
        self.pool1 = self.avg_pooling(self.conv1_1,"avg_pool1")

        self.conv2_1 = self.conv_layer(self.pool1, weights["w2_1"], biases["b2_1"],'VALID', 'conv2_1')
        self.pool2 = self.avg_pooling(self.conv2_1,"avg_pool2")

        self.conv3_1 = self.conv_layer(self.pool2, weights["w3_1"], biases["b3_1"],'VALID', 'conv3_1')        
        self.pool3 = self.avg_pooling(self.conv3_1,"max_pool3")

        self.pool4 = self.max_pooling(self.pool3,"max_pool3")
        
        self.flat = self.flatten(self.pool4)
        self.fc1 = self.fullcon(self.flat,"fc1",self.flat.shape[1].value,self.preOutputSize,keep_prob = 0.3)
        self.relu1 = tf.nn.relu(self.fc1)

        self.fc2 = self.fullcon(self.relu1,"fc2",self.preOutputSize,self.preOutputSize//2 , keep_prob = 0.8)
        self.sig1 = tf.nn.sigmoid(self.fc2 , name = "context_layer")
        self.fc3 = self.fullcon(self.sig1,"fc3",self.preOutputSize//2,self.totalClasses,keep_prob = 1.0)
        self.classifierOutput = tf.nn.softmax(self.fc3,name = "result")

        return self.classifierOutput

    def optimize(self,logits):        
        entropy_loss = tf.clip_by_value(tf.nn.softmax_cross_entropy_with_logits_v2(labels = self.output, logits = logits),clip_value_min = -1000, clip_value_max = 1000)
        cost = tf.reduce_mean(entropy_loss)
        optimizer = tf.train.AdamOptimizer(learning_rate = self.learn_rate).minimize(cost)
        
        correct_pred = tf.equal(tf.argmax(logits,1),tf.argmax(self.output,1))
        acc = tf.reduce_mean(tf.cast(correct_pred,tf.float32))

        return cost,optimizer,acc

    def train_init(self):
        #run train_init before moving over to compile
        self.classifier = self.build()
        self.cost, self.optimizer, self.accuracy = self.optimize(self.classifier)
        
        init = tf.global_variables_initializer()
        self.sess = tf.Session()
        self.sess.run(init)
        print("Initialization done\n")
        
    def compile(self,iters = 150,batches = None):
        startingLoss = np.inf
        currentLoss = np.inf
        for it in range(iters):
            if(batches == None):
                batch_x = self.Img
                batch_y = self.Label
                currentLoss = self.run_compute(batch_x,batch_y)                
            else:
                intermid_sum = 0
                for batch_pointer in range(len(self.Img)//batches):                    
                    batch_x = self.Img[batch_pointer*batches:min((batch_pointer+1)*batches,len(self.Img))]
                    batch_y = self.Label[batch_pointer*batches:min((batch_pointer+1)*batches,len(self.Label))]
                    intermid_sum += self.run_compute(batch_x,batch_y)
                currentLoss /= batches
            self.oneshot_save(startingLoss,currentLoss)
            if(it % 20 == 0):
                    self.learn_rate = self.learn_rate / (1+ 0.1*it)
                    
    def run_compute(self,feed_x,feed_y):
        opt = self.sess.run(self.optimizer,feed_dict={self.input: feed_x, self.output: feed_y})
        loss,acc = self.sess.run([self.cost, self.accuracy],feed_dict={self.input: feed_x, self.output: feed_y})
        print("Loss= {:.5f} , Training Acc = {:.5f}".format(loss,acc))
        return loss

    def oneshot_save(self, lowestLoss, currentLoss):        
        if (lowestLoss >= currentLoss -0.1) :
            return lowestLoss    
        else:
            self.save_model(self)
            return currentLoss

    def save_model(self,_path = "/tmp/model.ckpt"):
        saver = tf.train.Saver()
        self.save_path = saver.save(self.sess, _path)

    def load_model(self,_path = "/tmp/model.ckpt"):
        Layers = {}
        conv1_1 = tf.get_variable('conv1_1',shape = [3,3,3,5])
        conv2_1 = tf.get_variable('conv2_1',shape = [3,3,5,10])
        #context = tf.get_variable('context_layer',shape = [])
        
        #get_variable to be utilized before trying to attempt below portion#
        saver = tf.train.Saver()
        saver.restore(self.sess, "/tmp/model.ckpt")
        
#classifier = miniClassifier(meta.joinedData,meta.labelsOneHot)
