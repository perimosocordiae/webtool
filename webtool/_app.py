import io
import json
import logging
import tornado.ioloop
import tornado.template
import tornado.web
import tornado.websocket
from matplotlib.backends.backend_webagg_core import (
    FigureManagerWebAgg, new_figure_manager_given_figure)

from ._ui import ui_template


class WebToolApp(tornado.web.Application):
  def __init__(self, title, funcs, **kwargs):
    routes = [
        (r'/', FrontendHandler, dict(title=title, funcs=funcs)),
        # (r'/assets/(.*)', tornado.web.StaticFileHandler, dict(path=...)),
        (r'/([0-9]+)/download.([a-z0-9.]+)', DownloadHandler),
        (r'/([0-9a-f]+)/([0-9]+)/ws', WebSocketHandler),
        (r'/mpl.js', MplJsHandler),
        (r'/_static/(.*)', tornado.web.StaticFileHandler,
         dict(path=FigureManagerWebAgg.get_static_file_path())),
    ]
    for name in funcs:
      f = funcs[name]
      if not hasattr(f, '_webtool_args'):
        raise ValueError('Function %s must be decorated with @webtool.webfn')
      routes.append(('/'+name, BackendHandler, dict(func=funcs[name])))
    tornado.web.Application.__init__(self, routes, **kwargs)

    # keep track of per-session state, maps from string uid -> dict
    self.sessions = {}
    # keep track of active figures, including a fake one for the keepalive
    # maps from fignum -> managers
    self.fig_managers = {'0': MockFigureManager()}

  def new_session(self):
    session_state = {}
    uid = format(id(session_state), 'x')
    self.sessions[uid] = session_state
    return uid

  def end_session(self, session_id):
    del self.sessions[session_id]

  def add_figure(self, fig):
    # take care to prevent a fignum of zero, which is special to us
    fignum = id(fig) * 10 + 1
    manager = new_figure_manager_given_figure(fignum, fig)
    self.fig_managers[str(fignum)] = manager
    return fignum


class FrontendHandler(tornado.web.RequestHandler):
  def initialize(self, **tpl_vars):
    self.tpl_vars = tpl_vars

  def get(self):
    uid = self.application.new_session()
    tpl = ui_template()
    self.write(tpl.generate(uid=uid, host=self.request.host, **self.tpl_vars))


class BackendHandler(tornado.web.RequestHandler):
  def initialize(self, func):
    self.func = func

  def post(self):
    kwargs = {k: self.get_argument(k) for k in self.request.arguments}
    uid = kwargs.pop('session.uid')
    state = self.application.sessions[uid]
    for key, files in self.request.files.items():
      f, = files  # only one file per key
      kwargs[key] = io.BytesIO(f['body'])

    logging.info('Running [%s] in session %s: %r', self.func.__name__, uid,
                 kwargs)
    try:
      result, figures = self.func(state, **kwargs)
    except IOError as e:
      logging.exception('User function failed.')
      self.set_status(400)
      self.finish('Error: %s' % e.strerror)
    except Exception as e:
      logging.exception('User function failed.')
      self.set_status(400)
      self.finish('Error: %s' % e.message)
    else:
      self.write(result)
      for fig in figures:
        fignum = self.application.add_figure(fig)
        self.write('\n<div id="fig%s" class="figure"></div>' % fignum)


class MplJsHandler(tornado.web.RequestHandler):
  def get(self):
    self.set_header('Content-Type', 'application/javascript')
    self.write(FigureManagerWebAgg.get_javascript())


class DownloadHandler(tornado.web.RequestHandler):
  def get(self, fignum, fmt):
    mimetypes = {
        'ps': 'application/postscript',
        'eps': 'application/postscript',
        'pdf': 'application/pdf',
        'svg': 'image/svg+xml',
        'png': 'image/png',
        'jpeg': 'image/jpeg',
        'tif': 'image/tiff',
        'emf': 'application/emf'
    }
    self.set_header('Content-Type', mimetypes.get(fmt, 'binary'))
    buff = io.BytesIO()
    self.application.fig_managers[fignum].canvas.print_figure(buff, format=fmt)
    self.write(buff.getvalue())


class WebSocketHandler(tornado.websocket.WebSocketHandler):
  supports_binary = True

  def open(self, uid, fignum):
    self.uid = uid
    self.fignum = fignum
    self.application.fig_managers[fignum].add_web_socket(self)
    if hasattr(self, 'set_nodelay'):
      self.set_nodelay(True)

  def on_close(self):
    app = self.application
    logging.info('Closing websocket %s for figure %s', self.uid, self.fignum)
    app.fig_managers[self.fignum].remove_web_socket(self)
    if self.fignum == '0':
      # keep-alive died, so this whole session is over
      app.end_session(self.uid)
    else:
      # our figure is dead, delete it
      del app.fig_managers[self.fignum]

  def on_message(self, message):
    message = json.loads(message)
    if message['type'] == 'supports_binary':
      self.supports_binary = message['value']
    else:
      self.application.fig_managers[self.fignum].handle_json(message)

  def send_json(self, content):
    self.write_message(json.dumps(content))

  def send_binary(self, blob):
    if self.supports_binary:
      self.write_message(blob, binary=True)
    else:
      payload = blob.encode('base64').replace('\n', '')
      self.write_message("data:image/png;base64," + payload)


class MockFigureManager(object):
  def __init__(self):
    self.web_sockets = set()

  def add_web_socket(self, ws):
    self.web_sockets.add(ws)

  def remove_web_socket(self, ws):
    self.web_sockets.remove(ws)
