import logging
import tornado.ioloop
from matplotlib import pyplot as plt
from socket import gethostname

from ._app import WebToolApp

__all__ = ['webtool', 'webfn']


def webtool(title, port, **funcs):
  logging.basicConfig(level=logging.INFO)
  app = WebToolApp(title, funcs)
  app.listen(port)
  print('Starting server at http://%s:%s/' % (gethostname(), port))
  tornado.ioloop.IOLoop.current().start()


def webfn(title, desc, **arg_descs):
  def decorate(f):
    def wrapper(state, **kwargs):
      plt.close('all')
      result = f(state, **kwargs)
      figures = [plt.figure(i) for i in plt.get_fignums()]
      return result, figures
    wrapper._webtool_args = (title, desc, arg_descs)
    wrapper.__name__ = f.__name__
    return wrapper
  return decorate
