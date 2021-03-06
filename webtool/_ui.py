import glob
import matplotlib
import os
import tornado.template

__all__ = ['ui_template']
_TPL = None


def ui_template():
  global _TPL
  if _TPL is None:
    head = _tpl_head()
    tpl = '<!DOCTYPE html><html><head>%s</head><body>%s</body></html>' % (
        head, _TPL_BODY)
    _TPL = tornado.template.Template(tpl)
  return _TPL


def _tpl_head():
  mpl_dir = os.path.join(matplotlib.__path__[0],
                         'backends/web_backend')
  mpl_js = glob.glob(os.path.join(mpl_dir, 'js/mp*.js'))
  mpl_css = glob.glob(os.path.join(mpl_dir, 'css/*.css'))

  resource_html = []
  for abspath in mpl_css:
    if abspath.endswith('boilerplate.css'):
      continue
    path = abspath.replace(mpl_dir, '_static')
    x = '<link rel="stylesheet" href="%s" type="text/css">' % path
    resource_html.append(x)
  for abspath in mpl_js[::-1]:
    path = abspath.replace(mpl_dir, '_static')
    x = '<script src="%s"></script>' % path
    resource_html.append(x)
  return '\n'.join(resource_html) + _TPL_HEAD


_TPL_HEAD = '''
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{title}}</title>
<script src="mpl.js"></script>
<style>
fieldset { display:inline-block; }
.figure { display:inline-block; }
input[type="submit"] { width: 100%; }
</style>
<script src="https://code.jquery.com/jquery-1.12.4.min.js"></script>
'''

_TPL_BODY = '''
<h1>{{title}}</h1>
{% for name, func in funcs.items() %}
  {% set ftitle, fdesc, arg_descs = func._webtool_args %}
  <form name="{{name}}" action="/{{name}}" method="POST"
        enctype='multipart/form-data' onsubmit="return run(this);">
  <fieldset>
    <legend>{{ftitle}}</legend>
    <p>{{fdesc}}</p>
    {% for key in arg_descs %}
      <p>{% raw arg_descs[key].to_html(key) %}</p>
    {% end %}
    <input type="hidden" name="session.uid" value="{{uid}}">
    <input type="submit" value="Run">
  </fieldset></form>
  <div class="results"></div>
{% end %}
<script type="text/javascript">
var all_figures = {};
var websocket_type = mpl.get_websocket_type();
function savefig(figure, format) {
  window.open('/'+figure.id+'/download.'+format, '_blank');
}
function run(form) {
  if (!form.checkValidity()) return false;
  var f = $(form), res = f.next('.results'), data = new FormData(form);
  $.ajax({
    type: form.method, url: form.action, data: data, processData: false,
    contentType: false,
    error: function(e){
      res.html(e.responseText);
    },
    success: function(resp){
      res.html(resp);
      $('.figure', res).each(function(){
        var fignum = $(this).attr('id').slice(3);
        var ws = new websocket_type('ws://{{host}}/{{uid}}/'+fignum+'/ws');
        all_figures[fignum] = new mpl.figure(fignum, ws, savefig, this);
      });
    },
  });
  return false;
}
var keepalive = new websocket_type('ws://{{host}}/{{uid}}/0/ws');
keepalive.onclose = function(){
  // close all figures by replacing their canvases with static images
  $('.figure').each(function(){
    var img = new Image();
    img.src = $(this).find('.mpl-canvas')[0].toDataURL('image/png');
    $(this).html(img);
  });
  // throw away the dict of mpl.figure objects
  all_figures = {};
};
</script>'''
