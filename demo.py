#!/usr/bin/env python
from matplotlib import pyplot as plt
from webtool import webtool, webfn, webarg


@webfn('Demo Function', 'This is a demo of WebTool functionality.',
       f=webarg('File parameter', type=open),
       i=webarg('Int parameter', type=int, default=42),
       x=webarg('Float parameter', type=float, default=3.14159),
       s=webarg('String parameter', default='default'))
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

if __name__ == '__main__':
  webtool(title='Demo', port=8787, demo=demo)
