import argparse
import matplotlib
import os
import tornado.template

__all__ = ['ui_template']
_TPL = None


def ui_template():
  global _TPL
  if _TPL is None:
    head = _tpl_head()
    tpl = '<html><head>%s</head><body>%s</body></html>' % (head, _TPL_BODY)
    _TPL = tornado.template.Template(tpl)
    _TPL.namespace['arg_desc_to_input'] = arg_desc_to_input
  return _TPL


def arg_desc_to_input(key, arg_desc):
  '''Convert (desc, type, default) tuples into labeled <input> elements'''
  desc, t, default = arg_desc
  if issubclass(t, int):
    attrs = 'type="number"'
  elif issubclass(t, float):
    attrs = 'type="number" step="any"'
  elif t is open or isinstance(t, argparse.FileType):
    attrs = 'type="file"'
  else:
    attrs = 'type="text"'
  # NOTE: an f-string would be great here
  tpl = '<label><input {attrs} name="{key}" value="{default}"> {desc}</label>'
  return tpl.format(attrs=attrs, key=key, default=default, desc=desc)


def _tpl_head():
  mpl_js = sorted(os.listdir(os.path.join(matplotlib.__path__[0],
                                          'backends/web_backend/jquery/js')))
  mpl_css = ['css/page.css', 'css/fbm.css',
             'jquery/css/themes/base/jquery-ui.min.css']

  resource_html = []
  for path in mpl_css:
    x = '<link rel="stylesheet" href="_static/%s" type="text/css">' % path
    resource_html.append(x)
  for path in mpl_js:
    x = '<script src="_static/jquery/js/%s"></script>' % path
    resource_html.append(x)
  return '\n'.join(resource_html) + _TPL_HEAD


_TPL_HEAD = '''
<title>{{title}}</title>
<script src="mpl.js"></script>
<style>
fieldset { display:inline-block; }
.figure { display:inline-block; }
input[type="submit"] { width: 100%; }
</style>
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
      <p>{{arg_desc_to_input(key, arg_descs[key])}}</p>
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
        all_figures[fignum] = new mpl.figure(fignum, ws, savefig, $(this));
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
