#!/usr/bin/env python
import webtool
from matplotlib import pyplot as plt


@webtool.webfn('Demo Function', 'This is a demo of webtool.',
               f=('File parameter', open, None),
               i=('Int parameter', int, 42),
               x=('Float parameter', float, 3.14159),
               s=('String parameter', str, 'default'))
def demo(state, **kwargs):
  count = state.get('count', 0)
  count += 1
  state['count'] = count

  m = float(kwargs['x'])
  b = int(kwargs['i'])
  fig, ax = plt.subplots()
  ax.plot([m*x+b for x in range(-5, 6)])

  fig, ax = plt.subplots()
  ax.plot([m*x**2+b for x in range(-5, 6)])

  plist = ['<li>%s = %r</li>' % kv for kv in kwargs.items()]
  return 'Called %d times.<br>Params:<ul>%s</ul>' % (count, '\n'.join(plist))

webtool.webtool('Demo', 8787, demo=demo)
