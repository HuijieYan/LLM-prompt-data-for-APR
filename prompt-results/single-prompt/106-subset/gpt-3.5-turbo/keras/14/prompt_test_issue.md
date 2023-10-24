You need to fix a bug in a python code snippet.

The buggy source code is following, and you should follow all specifications in comment if there exists comment:

def sparse_top_k_categorical_accuracy(y_true, y_pred, k=5):
    return K.mean(K.in_top_k(y_pred, K.cast(K.max(y_true, axis=-1), 'int32'), k),
                  axis=-1)



The test source code is following:

@pytest.mark.skipif((K.backend() == 'cntk'),
                    reason='CNTK backend does not support top_k yet')
@pytest.mark.parametrize('y_pred, y_true', [
    # Test correctness if the shape of y_true is (num_samples, 1)
    (np.array([[0.3, 0.2, 0.1], [0.1, 0.2, 0.7]]), np.array([[1], [0]])),
    # Test correctness if the shape of y_true is (num_samples,)
    (np.array([[0.3, 0.2, 0.1], [0.1, 0.2, 0.7]]), np.array([1, 0])),
])
def test_sparse_top_k_categorical_accuracy(y_pred, y_true):
    y_pred = K.variable(y_pred)
    y_true = K.variable(y_true)
    success_result = K.eval(
        metrics.sparse_top_k_categorical_accuracy(y_true, y_pred, k=3))

    assert success_result == 1
    partial_result = K.eval(
        metrics.sparse_top_k_categorical_accuracy(y_true, y_pred, k=2))
    assert partial_result == 0.5
    failure_result = K.eval(
        metrics.sparse_top_k_categorical_accuracy(y_true, y_pred, k=1))
    assert failure_result == 0



The raised issue description for this bug is:
fix sparse categorical acc

Summary
sparse categorical acc should have the same result as categorical acc.
For example, with 3 classes, given sparse_true_label = [0, 1, 1], it's equivalent in categorical labels is dense_true_label = [[1, 0, 0], [0, 1, 0], [0, 1, 0]]. With the same predictions

pred = [[0.7, 0.2, 0.1], 
[0.1, 0.1, 0.8], 
[0.2, 0.6, 0.2]]
They should produce the same acc which is [1, 0 ,1]

Not sure why max is used, but it should directly compare with y_true
Added unit test to test correctness
Related Issues
PR Overview
 This PR requires new unit tests [y] (make sure tests are included)
 This PR requires to update the documentation [n] (make sure the docs are up-to-date)
 This PR is backwards compatible [y]
 This PR changes the current API [n] (all API changes need to be approved by fchollet)
The raised issue description for this bug is:
metrics=['accuracy'] seems to be calculated differently if one uses tf.data inputs instead of numpy arrays for keras model

Please go to Stack Overflow for help and support:

https://stackoverflow.com/questions/tagged/tensorflow

If you open a GitHub issue, here is our policy:

It must be a bug, a feature request, or a significant problem with documentation (for small docs fixes please send a PR instead).
The form below must be filled out.
It shouldn't be a TensorBoard issue. Those go here.
Here's why we have that policy: TensorFlow developers respond to issues. We want to focus on work that benefits the whole community, e.g., fixing bugs and adding features. Support only helps individuals. GitHub also notifies thousands of people when issues are filed. We want them to see you communicating an interesting problem, rather than being redirected to Stack Overflow.

System information
Have I written custom code (as opposed to using a stock example script provided in TensorFlow): YES
OS Platform and Distribution (e.g., Linux Ubuntu 16.04): Windows 10
Mobile device:na
TensorFlow installed from (source or binary): binary
TensorFlow version (use command below):1.11.0-dev20180907
Python version:3.6.3
Bazel version (if compiling from source):na
GCC/Compiler version (if compiling from source):na
CUDA/cuDNN version:na
GPU model and memory:na
Exact command to reproduce:na
You can collect some of this information using our environment capture script:

https://github.com/tensorflow/tensorflow/tree/master/tools/tf_env_collect.sh

You can obtain the TensorFlow version with

python -c "import tensorflow as tf; print(tf.GIT_VERSION, tf.VERSION)"

Describe the problem
Describe the problem clearly here. Be sure to convey here why it's a bug in TensorFlow or a feature request.

Given the same piece of code for loading mnist data and training a keras model in tensorflow, the metric "accuracy" given as argument to keras_model.compile(metrics=[...]) generates very different values (order of 0.10 versus order of 0.90) depending on if you use numpy arrays or tf.data datasets as training inputs. Note that the values of the loss in each case are very close. I suspect that "accuracy" is being calculated differently depending on the type of input (numpy or tf.data), or that it is being calculated wrong in one of the cases.
In particular, as an example, using numpy arrays as input, one can get the pair loss: 0.2086 - acc: 0.9389 in one of the steps, while the same loss in with tf.data gives the pair loss: 0.2086 - acc: 0.1024.

Source code / logs
Include any logs or source code that would be helpful to diagnose the problem. If including tracebacks, please include the full traceback. Large logs and files should be attached. Try to provide a reproducible test case that is the bare minimum necessary to generate the problem.

The code below as it is can be run and training with tf.data datasets will be performed. If you comment the block between #Train with tf.data datasets and ######################## and uncomment the block between #Train with numpy arrays and ########################, training with numpy arrays as inputs will be performed.

import tensorflow as tf
import numpy as np

np.random.seed(1)
tf.set_random_seed(1)
BATCH_SIZE = 32

#Import mnist dataset as numpy arrays
(x_train, y_train), (_, _) = tf.keras.datasets.mnist.load_data()#Import
x_train = x_train / 255.0 #normalizing
y_train = y_train.astype(dtype='float32')
x_train = x_train.astype(dtype='float32')

x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1]*x_train.shape[2]))#Reshaping the 2D picture

##############################################################################################
#THIS BLOCK CREATES A DATASET FROM THE NUMPY ARRAYS. IT WILL BE USED FOR THE CASE OF TF.DATA DATASET INPUTS
tfdata_dataset_train = tf.data.Dataset.from_tensor_slices((x_train, y_train))
tfdata_dataset_train = tfdata_dataset_train.batch(BATCH_SIZE).repeat()
##############################################################################################

#Create model
keras_model = tf.keras.models.Sequential([
    tf.keras.layers.Dense(512, activation=tf.nn.relu),
    tf.keras.layers.Dropout(0.2, seed=1),
    tf.keras.layers.Dense(10, activation=tf.nn.softmax)
])

#Compile the model
keras_model.compile(optimizer=tf.keras.optimizers.Adam(),
                    loss=tf.keras.losses.sparse_categorical_crossentropy,
                    metrics=['accuracy'])

#Train with numpy arrays
#keras_training_history = keras_model.fit(x_train,
#                y_train,
#                epochs=1
#                )
########################

#Train with tf.data datasets
keras_training_history = keras_model.fit(tfdata_dataset_train,
                epochs=1,
                steps_per_epoch=60000//BATCH_SIZE
                )
########################
The raised issue description for this bug is:
Fix bug in tf.keras.metrics.sparse_categorical_accuracy

Fix #22190

For the input of tf.keras.metrics.sparse_categorical_accuracy, the shape of y_true can be (num_samples, 1) or (num_samples,), see #22190 for detail. The existing code assume the shape of y_true is (num_samples, 1), always reduce in the last dimension which leads the incorrect output. Actually we should check the shape of y_true and squeeze if applicable.
Meanwhile, I also fix sparse_top_k_categorical_accuracy which has the same issue.