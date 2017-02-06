# webtool
Hassle-free web interface generator for Python code.

## Usage
```python
from webtool import webtool, webfn, webarg

@webfn('My function', 'This is a description.',
       foo=webarg('This is an argument.', type=int, default=4),
       bar=webarg('Another arg.'))
def any_python_function(state, foo='4', bar=''):
  # state is a dict that persists for the whole webtool session
  state['called'] = state.get('called', 0) + 1
  # the returned string will be displayed as HTML below the argument form
  return '<b>Any HTML</b> output goes <i>here</i>.'

if __name__ == '__main__':
  webtool(title='Usage Example', port=8787, f=any_python_function)
```

Matplotlib figures are supported as well.
Create figures as normal in a `webfn`-decorated function,
and they will appear as interactive WebAgg plots.

## Installation

WebTool isn't on PyPI yet, but you can install from GitHub:

    pip install git+https://github.com/perimosocordiae/webtool.git

Alternatively, clone this repo and run `setup.py install`.

