
def memoize(f):
  cache= {}
  def cf(*x):
    if x not in cache: cache[x] = f(*x)
    return cache[x]
  return cf

import sys
sys.modules[__name__] = memoize

