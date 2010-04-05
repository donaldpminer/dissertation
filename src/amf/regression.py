# regression.py contains the definititon of a pluggable regression algorithm.
#  Also, this file has a bunch of 'built-in' regression methods that can be used
#  as either examples or straight from the box.

import copy
import misc
import sys 
import scipy.optimize
import random

# This is the basic Interface that other regression objects should inherit from
class Regression(object):
   name = None

   def train(self, data):
      raise NotImplementedError, "'train' method not implemented."

   def predict(self, configuration):
      raise NotImplementedError, "'predict' method not implemented."


class kNN(Regression):
   name = "kNN"

   def __init__(self, k):
      self.k = k
      self.__data__ = None
      self.ind = None
      self.dep = None

   def train(self, data):
      # kNN just stores the data...
      self.__data__ = copy.deepcopy(data)

      self.ind = len(self.__data__[0][0])

   def predict(self, configuration):
      nn = self.__find_knn__(configuration)      

      # average each value in each column of the dependent variable data

      avg = sum(n[1] for n in nn)/float(len(nn)) 

      return avg

   # Finds the k nearest neighbors and returns them
   def __find_knn__(self, configuration):
      distances = [ (misc.distance(configuration, entry[0]), idx) for idx, entry in enumerate(self.__data__) ]
      distances.sort()
      
      return tuple( self.__data__[idx] for distance, idx in distances[:self.k] )


def __tricubic__(p1, p2, window):
   """
   Weighs points close to eachother close to 1.
   Weighs points close to the window distance close to 0.
   Weighs points past the window distance to 0.
   """

   z = misc.distance(p1,p2)

   weight = (1 - abs(z/float(window))**3)**3

   return weight if abs(z) < window else 0.0

class LOESS(Regression):
   name = "LOESS"

   def __init__(self, window, iterations):
      self.window = window
      self.__data__ = None
      self.cur_data = None
      self.iterations = iterations

   def train(self, data):
      self.__data__ = copy.deepcopy(data)
      self.yhats = misc.get_col(self.__data__, 1)

      for i in range(self.iterations):
         self.__smooth__()

   def predict(self, configuration, smoothing = False):
         sum_weights = 0.0
         weighted_sum = 0.0

         for (other_xs, other_y), other_yhat in misc.xzip(self.__data__, self.yhats):
            ydist = 1.0 + (abs(other_y - other_yhat) if smoothing else 0.0)
            weight = __tricubic__(configuration, other_xs, self.window) / ydist


            sum_weights += weight

            weighted_sum += weight * other_y

         if sum_weights == 0.0:
            sys.stderr.write("WARNING: No other instances found to have weights for point %s\n" % repr(configuration))
            return 0.0

         return weighted_sum / sum_weights

   def __smooth__(self):
      new_yhats = []

      for xs, y in self.__data__:
         new_yhats.append(self.predict(xs, True))

      self.yhats = new_yhats




class NLR(Regression):
   name = "NLR"

   def __init__(self, model, initial_guess):
      """
      model - a function that takes two parameters:
         v : the list of parameters
         x : the configuration
      """
      self.model = model

      self.error = lambda v, x, y: (self.model(v, x) - y)

      self.initial = initial_guess

      self.ind = None

   def train(self, data):
      self.ind = len(data[0][0])

      x_arrays = []
      for idx in range(self.ind):
         x_arrays.append( scipy.array(misc.get_col(misc.get_col(data, 0), idx)) )

      y_array = scipy.array(misc.get_col(data, 1))

      v, success = scipy.optimize.leastsq( self.error, self.initial, args=tuple(x_arrays + [y_array]) )

      print 'success?', success
      print 'v=', v

      self.opt = v

   def predict(self, configuration):
      return self.model(self.opt, configuration)


# This class is intended to test the evaulation -- RANDOM should do very poorly!
class Random(Regression):
   name = "RANDOM"
   def __init__(self, mi, ma):
      self.gen = lambda : random.random() * (ma - mi) + mi

   def train(self, data):
      pass

   def predict(self, configuration):
      return self.gen()



