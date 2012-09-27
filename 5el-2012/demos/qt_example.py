"""
Example of how to directly embed Chaco into Qt widgets.

The actual plot being created is drawn from the basic/line_plot1.py code.
"""

# FIXME: does not run from ipython-qtconsole (ok under python).

from traits.etsconfig.etsconfig import ETSConfig
ETSConfig.toolkit = "qt4"

import sys
from numpy import linspace, sin, cos
from scipy.special import jn
from pyface.qt import QtGui, QtCore

from enable.api import Window

from chaco.api import ArrayPlotData, Plot
from chaco.tools.api import PanTool, ZoomTool, TraitsTool

windows = []

def create_chaco_plot(parent, data, args, type=''):
    #x = linspace(-2.0, 10.0, 100)
    #pd = ArrayPlotData(index = x)
    #for i in range(5):
    #    pd.set_data("y" + str(i), jn(i,x))
    #if not type:
    #    type = ['plot']
    #else:
    #    type = [type, 'plot']
    # Create some line plots of some of the data
    plot = Plot(data, title="Line Plot", padding=50, border_visible=True)
    plot.legend.visible = True
    #plot_fn = getattr(plot, '_'.join(type))
    if type:
        renderers = plot.plot(args, plot=type)
    else:
        renderers = plot.plot(args)
    #plot.plot(("index", "y3"), name="j_3", color="blue")

    # Attach some tools to the plot
    plot.tools.append(PanTool(plot))
    zoom = ZoomTool(component=plot, tool_mode="box", always_on=False)
    plot.overlays.append(zoom)
    plot.tools.append(TraitsTool(component=plot))

    # This Window object bridges the Enable and Qt4 worlds, and handles events
    # and drawing.  We can create whatever hierarchy of nested containers we
    # want, as long as the top-level item gets set as the .component attribute
    # of a Window.
    return Window(parent, -1, component = plot)

def add_plot(main_window, plot_window):
    dw = QtGui.QDockWidget(plot_window.component.title, main_window)
    print plot_window.component.title, plot_window.control
    windows.append(plot_window)
    dw.setWidget(plot_window.control)
    #dw.setWidget(QtGui.QPushButton('text'))
    main_window.addDockWidget(QtCore.Qt.TopDockWidgetArea, dw)

def create_data():
    x = linspace(0, 10, 101)
    y = sin(x)
    z = cos(x)
    data = ArrayPlotData(x=x, y=y, z=z)
    return data

def main():
    app = QtGui.QApplication.instance()
    main_window = QtGui.QMainWindow()
    main_window.resize(500,500)
    
    data = create_data()
    #for args, type in [(('x','y'), ''), (('y','z'),'scatter')]:
    #add_plot(main_window, create_chaco_plot(main_window, data, ('x','y'), 'scatter'))

    ew = create_chaco_plot(main_window, data, ('z','y'))
    dw = QtGui.QDockWidget(ew.component.title, main_window)
    print ew.component.title, ew.control
    #windows.append(ew)
    #ew.control.setParent(dw)
    dw.setWidget(ew.control)
    #dw.setWidget(QtGui.QPushButton('text'))
    #ew.control.show()
    main_window.addDockWidget(QtCore.Qt.TopDockWidgetArea, dw)

    # The .control attribute references a QWidget that gives Chaco events
    # and that Chaco paints into.
    main_window.setCentralWidget(create_chaco_plot(main_window, data, ('z','y'), 'scatter').control)
    #main_window.setCentralWidget(QtGui.QPushButton())
    main_window.show()
    app.exec_()

if __name__ == "__main__":
    main()

