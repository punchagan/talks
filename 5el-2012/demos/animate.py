#!/usr/bin/env python
'''Module to make animations from simulations easier

@author: Pankaj
19 August, 2009
'''

from traits.etsconfig.etsconfig import ETSConfig
ETSConfig.toolkit = "wx"

# Major library imports
import wx
import numpy
from numpy import linspace, sin, cos, ceil, array, ma
import os

#from enthought.enable.example_support import DemoFrame, demo_main

# Enthought library imports
from enable.api import Window

from traits.api import File, Enum, Tuple, HasTraits, DelegatesTo,\
    Instance, Any
from traitsui.api import View, Item, FileEditor

from chaco.api import PlotGraphicsContext
from chaco.tools.api import SaveTool
from chaco.example_support import COLOR_PALETTE

# Chaco imports
from chaco.api import Plot, PlotLabel, create_line_plot,\
    add_default_axes, add_default_grids, ArrayPlotData, HPlotContainer,\
    VPlotContainer, QuiverPlot, LinearMapper, LogMapper, MultiArrayDataSource,\
    AbstractDataSource, DataRange1D
from chaco.tools.api import PanTool, ZoomTool, DragZoom, TraitsTool


def set_extended_trait(obj, ext_trait, value):
    '''set an extended trait of an object. only normal value extended trait
    names accepted. wildcard and list extended names will probably raise errors
    '''
    trait = obj
    traits_list = ext_trait.split('.')
    for trait_name in traits_list[: - 1]:
        trait = getattr(trait, trait_name)
    t = {traits_list[ - 1]:value}
    trait.trait_set(**t)

def set_extended_traits(obj, traits):
    '''set multiple extended traits from the key-value pairs in the `traits`
    dictionary argument
    '''
    for k, v in traits.iteritems():
        set_extended_trait(obj, k, v)

def isdict(d):
    return hasattr(d, 'iteritems')

class CustomPlot(Plot):
    '''a subclass of Plot to implement additional quiver plot type
    '''
    def __init__(self, *args, **kwargs):
        super(CustomPlot, self).__init__(*args, **kwargs)
        self.renderer_map['quiver'] = QuiverPlot
    
    def plot(self, *args, **kwargs):
        super(CustomPlot, self).plot(*args, **kwargs)
    
    def quiver_plot(self, data, type="quiver", name=None, index_scale="linear",
             value_scale="linear", **styles):
        ''' Adds a quiver plot using the given data and plot style.

        Parameters
        ==========
        data : tuple(string) of length 3
                Interpreted as (x_arr, y_arr, vector_Arr)

        name : string
            The name of the plot.  If None, then a default one is created
            (usually "plotNNN").
        index_scale : string
            The type of scale to use for the index axis. If not "linear", then
            a log scale is used.
        value_scale : string
            The type of scale to use for the value axis. If not "linear", then
            a log scale is used.
        styles : series of keyword arguments
            attributes and values that apply to one or more of the
            plot types requested, e.g.,'line_color' or 'line_width'.

        Examples
        ========
        ::
            quiver_plot(("x", "y", "v"))

        Returns
        =======
        [renderers] -> list of renderers created in response to this call to plot()
        '''
        
        if len(data) == 0:
            return

        if isinstance(data, basestring):
            data = (data,)

        self.index_scale = index_scale
        self.value_scale = value_scale

        plot_type = type
        if name is None:
            name = self._make_new_plot_name()
        plot_name = name
        if plot_type in ("quiver",):
            if not len(data) == 3:
                raise ValueError('quiver plot requires (x_arr, y_arr, vectors) data')
            index = self._get_or_create_datasource(data[0])
            if self.default_index is None:
                self.default_index = index
            self.index_range.add(index)
            value_name = data[1]
            vectors = self._get_or_create_datasource(data[2], cls=MultiArrayDataSource)

            new_plots = []
            simple_plot_types = ("quiver",)
             
            value = self._get_or_create_datasource(value_name)
            self.value_range.add(value)
            
            cls = self.renderer_map[plot_type]
            # handle auto-coloring request
            if styles.get("color") == "auto":
                self._auto_color_idx = \
                    (self._auto_color_idx + 1) % len(self.auto_colors)
                styles["color"] = self.auto_colors[self._auto_color_idx]


            if self.index_scale == "linear":
                imap = LinearMapper(range=self.index_range,
                            stretch_data=self.index_mapper.stretch_data)
            else:
                imap = LogMapper(range=self.index_range,
                            stretch_data=self.index_mapper.stretch_data)
            if self.value_scale == "linear":
                vmap = LinearMapper(range=self.value_range,
                            stretch_data=self.value_mapper.stretch_data)
            else:
                vmap = LogMapper(range=self.value_range,
                            stretch_data=self.value_mapper.stretch_data)
            plot = cls(index=index,
                       value=value,
                       vectors=vectors,
                       index_mapper=imap,
                       value_mapper=vmap,
                       **styles)
            self.add(plot)
            new_plots.append(plot)

            self.plots[name] = new_plots
        else:
            raise ValueError("Unknown plot type: " + plot_type)

        return self.plots[name]
    
    def _get_or_create_datasource(self, name, cls=None, args=[]):
        ''' Returns the data source associated with the given name, or creates
        it if it doesn't exist.
        '''
        if cls is None:
            return super(CustomPlot, self)._get_or_create_datasource(name)
        if name not in self.datasources:
            data = self.data.get_data(name)
            if type(data) in (list, tuple):
                data = array(data, *args)
            ds = cls(data)
            self.datasources[name] = ds
        return self.datasources[name]


class AnimKeyControlTool(SaveTool):
    ''' This tool allows the user to press
    'Ctrl+s' to save a snapshot image of the plot component
    Also allows setting of custom `on_key_event` callbacks for key press events
    '''
    on_key_event = Any
    
    # This hack was done because calling self.configure_traits in normal_key_pressed
    # causes corruption in saved image and also the ui
    class FileName(HasTraits):
        filename = File("saved_plot.png")

    # The file that the image is saved in.  The format will be deduced from
    # the extension.
    filenameview = Instance(FileName, FileName())
    filename = DelegatesTo('filenameview')
    
    #-------------------------------------------------------------------------
    # PDF format options
    # This mirror the traits in PdfPlotGraphicsContext.
    #-------------------------------------------------------------------------

    pagesize = Enum("letter", "A4")
    dest_box = Tuple((0.5, 0.5, - 0.5, - 0.5))
    dest_box_units = Enum("inch", "cm", "mm", "pica")

    #-------------------------------------------------------------------------
    # Override default trait values inherited from BaseTool
    #-------------------------------------------------------------------------

    # This tool does not have a visual representation (overrides BaseTool).
    draw_mode = "none"

    # This tool is not visible (overrides BaseTool).
    visible = False
    
    def normal_key_pressed(self, event):
        ''' Handles a key-press when the tool is in the 'normal' state.
        
        Saves an image of the plot if the keys pressed are Control and S.
        '''
        if self.component is None:
            return
        
        if callable(self.on_key_event):
            self.on_key_event(event)
        
        if event.character == "s" and event.control_down:
            if self.filenameview.configure_traits(view=View(Item('filename',
                                    editor=FileEditor(entries=0,
                                        filter=['PNG file (*.png)|*.png',
                                                'GIF file (*.gif)|*.gif',
                                                'JPG file (*.jpg)|*.jpg',
                                                'JPEG file (*.jpeg)|*.jpeg',
                                                'PDF file (*.pdf)|*.pdf'])),
                                buttons=['OK', 'Cancel']), kind='modal'):
                if self.filename.endswith('.pdf'):
                    self._save_pdf()
                else:
                    self._save_raster()
                event.handled = True
        return
    
    def _save_raster(self):
        ''' Saves an image of the component.
        '''
        from chaco.api import PlotGraphicsContext
        gc = PlotGraphicsContext((int(self.component.outer_width), int(self.component.outer_height)))
        self.component.draw(gc, mode="normal")
        gc.save(self.filename)
        return

    def _save_pdf(self):
        ''' Save a pdf file of the component
        '''
        from chaco.pdf_graphics_context import PdfPlotGraphicsContext
        gc = PdfPlotGraphicsContext(filename=self.filename,
                pagesize=self.pagesize,
                dest_box=self.dest_box,
                dest_box_units=self.dest_box_units)
        gc.render_component(self.component, container_coords=True)
        gc.save()


class PlotFrame(wx.Frame):
    ''' The main window (wx.Frame) of the animate tool
    press 'p' to toggle play-pause of the animation
    press 'Ctrl+b' to break the process to debug (pdb.set_trace())
    '''
    
    def __init__ (self, func, structure, delay, total_time, time_factor=1.0,
            title='Plot', post_init=lambda plotframe:None,
            on_plot=lambda plotframe:None, post_finish=lambda plotframe:None,
            obj=None, *args, **kw):
        wx.Frame.__init__(*(self,) + (None,) + args, title=title, **kw)
        self.cont = True
        self.func = func
        self.structure = structure
        self.time = 0.0
        self.delay = delay
        self.total_time = total_time
        self.time_factor = time_factor
        self.title = title
        self.post_init = post_init
        self.on_plot = on_plot
        self.post_finish = post_finish
        self.obj = obj
        
        self.SetAutoLayout(True)
        
        # Create the subclass's window
        self.enable_win = self._create_window()
        
        # Listen for the Activate event so we can restore keyboard focus.
        wx.EVT_ACTIVATE(self, self._on_activate)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.enable_win.control, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Show(True)
        
        return
    
    def _on_activate(self, event):
        if self.enable_win is not None and self.enable_win.control is not None:
            self.enable_win.control.SetFocus()
    
    def save_plot(self, filename=None):
        ''' Saves an image of the component.
        '''
        if filename is None:
            filename = 'plots/plot%05d.jpg' %(round(self.time/self.delay*self.time_factor))
        d = os.path.dirname(filename)
        if d != '' and not os.path.exists(d):
            os.makedirs(os.path.dirname(filename))
        gc = PlotGraphicsContext((int(self.component.outer_width),
                    int(self.component.outer_height)))
        self.component.draw(gc, mode="normal")
        gc.save(filename)
    
    def set_aspect_ratio(self, plot, ar=1.0):
        plot.aspect_ratio = ar
        plot.x_mapper.stretch_data = False
        plot.y_mapper.stretch_data = False
        plot.request_redraw()
        pass
    
    def set_plotdata(self, data):
        for i, x in enumerate(data):
            self.pd.set_data('x%d' % (i), x)
    
    def gen_plots(self):
        self.pd = ArrayPlotData()
        self.num_plots = [[len(j) for j in i] for i in self.structure]
        self.num_cols = [len(i) for i in self.structure]
        self.num_rows = len(self.structure)
        
        self.plot_props = [[{} for j in xrange(self.num_cols[i])] for i in xrange(self.num_rows)]
        self.renderer_props = [[[{'color':'auto'} for k in xrange(self.num_plots[i][j])]
                        for j in xrange(self.num_cols[i])] for i in xrange(self.num_rows)]
        
        for i in xrange(self.num_rows):
            for j in xrange(self.num_cols[i]):
                if isdict(self.structure[i][j][-1]):
                    self.plot_props[i][j].update(self.structure[i][j][-1])
                    self.num_plots[i][j] -= 1
                for k in xrange(self.num_plots[i][j]):
                    if len(self.structure[i][j][k])>1:
                        self.renderer_props[i][j][k].update(self.structure[i][j][k][1])
                    self.renderer_props[i][j][k]['data'] = self.structure[i][j][k][0]
        data = self.func()
        if data is not None:
            self.set_plotdata(data)
        
        self.plots = []
        self.containers = []
        self.component = self.container = VPlotContainer(padding_top=30,
                    use_backbuffer=True, stack_order='top_to_bottom')
        self.title_label = PlotLabel("Plot",
                                        component=self.container,
                                        overlay_position="top")
        #self.title = "Plot"
        self.container.overlays.append(self.title_label)
        self.container.tools.append(AnimKeyControlTool(component=self.container,
                    on_key_event=self.on_key_event))
        self.container.tools.append(TraitsTool(component=self.container))
        
        for i in xrange(self.num_rows):
            container = HPlotContainer(use_backbuffer=True)
            self.container.add(container)
            self.containers.append(container)
            for ij in xrange(self.num_cols[i]):
                plot = CustomPlot(self.pd)
                for j in xrange(self.num_plots[i][ij]):
                    p = ['plot']
                    if self.renderer_props[i][ij][j].has_key('plot'):
                        p = [self.renderer_props[i][ij][j]['plot']] + p
                        self.renderer_props[i][ij][j]['plot']
                        del self.renderer_props[i][ij][j]['plot']
                    pt = getattr(plot, '_'.join(p))
                    renderers = pt(**self.renderer_props[i][ij][j])
                    
                plot.padding = 60
                plot.padding_right = 10
                plot.padding_top = 10
                
                plot.tools.append(PanTool(component=plot))
                plot.tools.append(DragZoom(component=plot, drag_button='right',
                        maintain_aspect_ratio=False))
                plot.tools.append(TraitsTool(component=plot))
                plot.overlays.append(ZoomTool(component=plot))
                set_extended_traits(plot, self.plot_props[i][ij])
                container.add(plot)
                self.plots.append(plot)
        if callable(self.post_init):
            self.post_init(self)
        else:
            for f in self.post_init:
                f(self)
        
    def _create_window(self):
        self.gen_plots()
        # Set the timer to generate events to us
        timerId = wx.NewId()
        self.timer = wx.Timer(self, timerId)
        self.Bind(wx.EVT_TIMER, self.onTimer, id=timerId)
        self.timer.Start(self.delay*1000, wx.TIMER_ONE_SHOT)
        return Window(self, - 1, component=self.container)
    
    def on_key_event(self, event):
        if event.character == 'p':
            #print 'toggle play-pause'
            self.cont = not self.cont
            if self.cont:
                self.onTimer(event)
        elif event.character == "b" and event.control_down:
            try:
                from IPython.core.debugger import Tracer
                Tracer()()
            except ImportError:
                import pdb
                obj = self.obj
                pdb.set_trace()
    
    def onTimer(self, event):
        data = self.func()
        self.set_plotdata(data)
        self.time += self.delay/self.time_factor
        #print self.time/1000
        #self.container.title = 'Time = ' + str(self.time/1000)
        self.SetTitle(self.title + ' : Time = ' + str(self.time))
        self.title_label.text = 'Time = ' + str(self.time)
        self.container.request_redraw()
        for plot in self.plots:
            plot.request_redraw()
        if callable(self.on_plot):
            self.on_plot(self)
        else:
            for f in self.on_plot:
                f(self)
        if self.cont and (0 >= self.total_time or self.time <= self.total_time):
            self.timer.Start(self.delay*1000, wx.TIMER_ONE_SHOT)
        elif self.time > self.total_time:
            if callable(self.post_finish):
                self.post_finish(self)
            else:
                for f in self.post_finish:
                    f(self)
        return

def save_plot(plotframe):
    '''convenience function which can be passed on as on_plot to animate to 
    save each frame of the plot'''
    plotframe.save_plot()

def make_video(plotframe=None, file_pattern='plots/plot*.jpg',
            outfile='plot.avi', fps=10, opts=''):
    '''convenience function which can be passed on as post_finish to animate to 
    make a video from saved images if `save_plot` is added as on_plot
    requires `mencoder` program'''
    if plotframe is not None and outfile == 'plot.avi':
        outfile = 'plot_%s.avi' %plotframe.title
    os.system('mencoder "mf://%s" -mf fps=%f -o "%s" -ovc lavc %s' %(file_pattern,float(fps),outfile,opts))

def make_video2(plotframe=None, file_pattern='plots/plot%05d.jpg',
            outfile='plot.mp4', fps=10, opts=''):
    '''convenience function which can be passed on as post_finish to animate to 
    make a video from saved images if `save_plot` is added as on_plot
    requires `ffmpeg` program, use `make_video` for better default quality'''
    if plotframe is not None and outfile == 'plot.mp4':
        outfile = 'plot_%s.mp4' %plotframe.title
    os.system('ffmpeg -r %f -i %s %s %s' %(float(fps),file_pattern,outfile,opts))

def anim_close(plotframe):
    '''convenience function which can be passed on as post_finish to animate to
    close the plot window after the animation time is finished so that
    plot/video generation can be automated without waiting for the user to
    close the animate window'''
    plotframe.Close()


def animate(func, structure, delay=0.1, total_time=0.0, time_factor=1.0,
            size=(800, 600), title='Plot', post_init=lambda plotframe: None,
            on_plot=lambda plotframe: None, post_finish=lambda plotframe: None,
            obj=None):
    '''function to animate the values returned by a function
   
    func : function which returns a tuple of data arrays which are used to plot
        the data is sequentially named as x0,x1,x2 and so on
    structure :
        it is a complex sequence describing all the plots and their properties
        it is structured as follows
        `structure` is a sequence of `row`s of multiple vertical subplots
        `row` is a sequence of horizontal `subplots`
        `subplot` is an actual plot which may have many `renderer`s (sequence
            of `renderer`s) such as line, scatter, contour plots etc
            It may also have an optional dictionary at the end of the sequence
                to set extended traits of the Plot instance;
                ex: title, x_axis.title, y_axis.title etc
                Check enthought.chaco.plot.Plot for available traits
        `renderer` is a size 2 sequence:
            first element is a tuple of the names of the data to plot,
                such as ('x1','x3') etc
            second element is a dictionary supplying extra arguments to be
                passed to plot(); ex: type = ['scatter','line',...] color, etc
                Check enthought.chaco.plot.Plot.plot() for more details
                It can also have a key 'plot' which is the plot function used
                    to plot, can be any of ['img','quiver','contour','candle']
    delay: time interval in seconds after which the func is to be called
    total_time: time at which to stop the animation
            animation will stop when total_time > self.time / time_factor
            total_time <= 0 will continue indefinitely
    time_factor: time to display as title (displayed_time=time/time_factor)
    size and title: size and title of the plot window frame
    post_init, on_plot, post_finish: function (or a sequence of functions)
        accepting a single argument of plotframe called on various events;
            on initialization of the plots, on every iteration of plot and on
                finishing the animation respectively
        they can be used for various customizations such as setting window size,
        saving plots, changing plot properties, making video of plots etc
    obj: any object passed on which can be used for debugging and is available
        as local variable obj and also as self.obj in the last frame when
        debugged in pdb using keystroke 'ctrl+b'
    
    In the plot window:
        left click drag allows you to pan the plot
        right click drag allows you to zoom the plot
        pressing 'z' key allows dragging to select a rectangular region to zoom
        pressing 'p' key will toggle animation play-pause
        pressing 'Ctrl+s' will open a dialog to save a rendering of the plot
        pressing 'ESC' will reset the zoom level of the plot
        double clicking on some parts of the plot allows editing them in a gui,
            (axis titles, grids, ticks etc)
        if the window becomes unresponsive, pause the animation for a while
    '''
    app = wx.GetApp()
    if app is None:
        app = wx.PySimpleApp()
    frame = PlotFrame(func, structure, delay, total_time, time_factor,
            size=size, title=title, post_init=post_init, on_plot=on_plot,
            post_finish=post_finish, obj=obj)
    app.SetTopWindow(frame)
    app.MainLoop()


if __name__ == '__main__':

    # The animate function
    # This example plot does following
    # 3 rows of plots
    # 1st row has 2 columns of plots
    # 2nd row has 2 columns of plots
    # 3rd subplot has 1 contour plot
    x = linspace(-10, 10, 101)
    i = 0.0
    
    # the function which returns the data for each iteration
    def get_data():
        global i
        i += 0.1
        x3 = x+i + sin(x + i)[:,None]
        #print x3.shape
        s = x3.shape
        return x, sin(x + i), x+i, x3, array([cos(x+i),sin(x+i)]).T
    
    # same get_data function can be used with different `structure`s to
    # generate completely different plots
    structure = ([[[('x0', 'x1'), {'type':'scatter'}], [('x0', 'x0'), {'type':'line'}]],
                  [[('x1', 'x0'), {'type':'scatter'}], {'title':'Plot Title','legend.visible':True}] ],
                 [[[('x0', 'x1'), {'type':'scatter'}]], [[('x1', 'x2'), {'type':'line'}]]],
                 [[['x3', {'plot':'contour','type':'poly'}], ['x3', {'plot':'contour','type':'line'}]] ],
                )
    
    structure2 = ([[[('x1', 'x2', 'x4'), {'plot':'quiver'}], [('x0', 'x1'), {'type':'line'}]],
                   [[('x1', 'x0'), {'type':'scatter','marker_size':2,'color':'red'}],
                    {'orientation':'v','x_axis.title':'X','y_axis.title':'Y'}] ],
                  [[['x3', {'plot':'contour','type':'poly'}], ['x3', {'plot':'contour','type':'line'}],
                    {'title':'Contour Plot'}] ],
                 )
    
    structure3 = ([[['x3', {'plot':'contour','type':'poly'}], ['x3', {'plot':'contour','type':'line'}],
                    {'title':'Contour Plot'}],
                   [[('x1', 'x0'), {'type':'scatter','marker_size':2,'color':'red'}],
                    {'orientation':'v','x_axis.title':'X','y_axis.title':'Y'}] ],
                  [[[('x3'), {'plot':'img','interpolation':'bicubic'}], {'title':'Image Plot'}], ],
                    
                 )
    
    animate(func=get_data, structure=structure)
    
    animate(func=get_data, structure=structure2)
    
    animate(func=get_data, structure=structure3)
    
    
# example encoding commands for generating video from images
# mencoder "mf://plots/plot*.jpg" -mf fps=10 -o plot.avi -ovc lavc
# ffmpeg -r 10 -i plots/plot%05d.jpg plot.mp4
# ffmpeg -r 10 -i plots/plot%05d.jpg -f webm plot.webm
# ffmpeg -r 10 -i plots/plot%05d.jpg plot.ogv

