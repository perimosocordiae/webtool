import argparse
import logging
import tornado.ioloop
from matplotlib import pyplot as plt
from socket import gethostname

from ._app import WebToolApp

__all__ = ['webtool', 'webfn']


def webtool(title='WebTool', port=8787, **funcs):
  logging.basicConfig(level=logging.INFO)
  app = WebToolApp(title, funcs)
  app.listen(port)
  print('Starting server at http://%s:%s/' % (gethostname(), port))
  tornado.ioloop.IOLoop.current().start()


def webfn(title, desc, **args):
  if not all(isinstance(a, webarg) for a in args.values()):
    raise ValueError('All keyword arguments to webfn() must be webarg objects.')

  def decorate(f):
    def wrapper(state, **kwargs):
      plt.close('all')
      result = f(state, **kwargs)
      figures = [plt.figure(i) for i in plt.get_fignums()]
      return result, figures
    wrapper._webtool_args = (title, desc, args)
    wrapper.__name__ = f.__name__
    return wrapper
  return decorate


class webarg(object):
  def __init__(self, desc, type=str, default=''):
    self.desc = desc
    self.type = type
    self.default = default

  def to_html(self, key):
    if self.type is int:
      attrs = 'type="number"'
    elif self.type is float:
      attrs = 'type="number" step="any"'
    elif self.type is open or isinstance(self.type, argparse.FileType):
      attrs = 'type="file"'
    else:
      attrs = 'type="text"'
    # NOTE: an f-string would be great here
    t = '<label><input {attrs} name="{key}" value="{default}"> {desc}</label>'
    return t.format(attrs=attrs, key=key, default=self.default, desc=self.desc)
