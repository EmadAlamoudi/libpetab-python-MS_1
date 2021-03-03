import numpy as np
import pandas as pd

from typing import Dict, List, Optional, Tuple, Union
from matplotlib import pyplot as plt

from .plotting import Figure, SinglePlot, BarPlot, LinePlot, ScatterPlot
from ..problem import Problem
from ..C import *

# for typehints
IdsList = List[str]
NumList = List[int]


class Plotter:
    def __init__(self,
                 exp_conditions: Union[str, pd.DataFrame],
                 exp_data: Union[str, pd.DataFrame],
                 sim_data: Optional[Union[str, pd.DataFrame]] = None,
                 vis_spec: Optional[Union[str, pd.DataFrame]] = None,
                 dataset_id_list: Optional[List[IdsList]] = None,
                 sim_cond_id_list: Optional[List[IdsList]] = None,
                 sim_cond_num_list: Optional[List[NumList]] = None,
                 observable_id_list: Optional[List[IdsList]] = None,
                 observable_num_list: Optional[List[NumList]] = None,
                 plotted_noise: Optional[str] = MEAN_AND_SD):
        self.conditions_df = None
        self.measurements_df = None
        self.simulation_df = None
        self.vis_spec_df = None  # pd dataframe
        self.check_and_extend_dfs()

        # data_to_plot

        self.figure = Figure(self.vis_spec_df)

    def check_and_extend_dfs(self):
        # check_ex_exp_columns for measurements_df
        # check_ex_exp_columns for simulation_df
        # extend vis_spec
        pass

    def create_figure(self, num_subplots) -> Figure:
        pass

    def generate_plot(self):
        if plots_to_file:
            # TODO save plot
            pass
        else:
            pass

        pass


class MPLPlotter(Plotter):
    """
    matplotlib wrapper
    """
    def __init__(self):
        super().__init__()

    def generate_lineplot(self, ax):
        # it should be possible to plot data or simulation or both

        # set xScale
        if plot_spec[X_SCALE] == LIN:
            ax.set_xscale("linear")
        elif plot_spec[X_SCALE] == LOG10:
            ax.set_xscale("log")
        elif plot_spec[X_SCALE] == LOG:
            ax.set_xscale("log", basex=np.e)
        # equidistant
        elif plot_spec[X_SCALE] == 'order':
            ax.set_xscale("linear")
            # check if conditions are monotone decreasing or increasing
            if np.all(np.diff(conditions) < 0):             # monot. decreasing
                xlabel = conditions[::-1]                   # reversing
                conditions = range(len(conditions))[::-1]   # reversing
                ax.set_xticks(range(len(conditions)), xlabel)
            elif np.all(np.diff(conditions) > 0):
                xlabel = conditions
                conditions = range(len(conditions))
                ax.set_xticks(range(len(conditions)), xlabel)
            else:
                raise ValueError('Error: x-conditions do not coincide, '
                                 'some are mon. increasing, some monotonically'
                                 ' decreasing')

        # add xOffset
        conditions = conditions + plot_spec[X_OFFSET]

        # plotting all measurement data
        label_base = plot_spec[LEGEND_ENTRY]
        if plot_spec[PLOT_TYPE_DATA] == REPLICATE:
            p = ax.plot(
                conditions[conditions.index.values],
                ms.repl[ms.repl.index.values], 'x',
                label=label_base
            )

        # construct errorbar-plots: noise specified above
        else:
            # sort index for the case that indices of conditions and
            # measurements differ if indep_var='time', conditions is a numpy
            # array, for indep_var=observable its a Series
            if isinstance(conditions, np.ndarray):
                conditions.sort()
            elif isinstance(conditions, pd.core.series.Series):
                conditions.sort_index(inplace=True)
            else:
                raise ValueError('Strange: conditions object is neither numpy'
                                 ' nor series...')
            ms.sort_index(inplace=True)
            # sorts according to ascending order of conditions
            scond, smean, snoise = \
                zip(*sorted(zip(conditions, ms['mean'], ms[noise_col])))
            p = ax.errorbar(
                scond, smean, snoise,
                linestyle='-.', marker='.', label=label_base
            )
        # construct simulation plot
        colors = p[0].get_color()
        if plot_sim:
            xs, ys = zip(*sorted(zip(conditions, ms['sim'])))
            ax.plot(
                xs, ys, linestyle='-', marker='o',
                label=label_base + " simulation", color=colors
            )

    def generate_barplot(self, ax):
        x_name = plot_spec[LEGEND_ENTRY]

        if plot_sim:
            bar_kwargs = {
                'align': 'edge',
                'width': -1/3,
            }
        else:
            bar_kwargs = {
                'align': 'center',
                'width': 2/3,
            }

        p = ax.bar(x_name, ms['mean'], yerr=ms[noise_col],
                   color=sns.color_palette()[0], **bar_kwargs)

        if plot_sim:
            colors = p[0].get_facecolor()
            bar_kwargs['width'] = -bar_kwargs['width']
            ax.bar(x_name, ms['sim'], color='white',
                   edgecolor=colors, **bar_kwargs)

    def generate_scatterplot(self, ax):
        if not plot_sim:
            raise NotImplementedError('Scatter plots do not work without'
                                      ' simulation data')
        ax.scatter(ms['mean'], ms['sim'],
                   label=plot_spec[LEGEND_ENTRY])
        ax = square_plot_equal_ranges(ax)

    def generate_subplot(self,
                         ax,
                         subplot: SinglePlot):
        #subplot should already have a plot_vis_spec information
        # plot_lowlevel

        # set yScale
        if subplot.vis_spec.yScale == LIN:
            ax.set_yscale("linear")
        elif subplot.vis_spec.yScale == LOG10:
            ax.set_yscale("log")
        elif subplot.vis_spec.yScale == LOG:
            ax.set_yscale("log", basey=np.e)

        # add yOffset
        ms.loc[:, 'mean'] = ms['mean'] + subplot.vis_spec.yOffset
        ms.loc[:, 'repl'] = ms['repl'] + subplot.vis_spec.yOffset
        if plot_sim: # TODO: different df for that
            ms.loc[:, 'sim'] = ms['sim'] + subplot.vis_spec.yOffset

        # set type of noise
        if subplot.vis_spec.plotTypeData == MEAN_AND_SD:
            noise_col = 'sd'
        elif subplot.vis_spec.plotTypeData == MEAN_AND_SEM:
            noise_col = 'sem'
        elif subplot.vis_spec.plotTypeData == PROVIDED:
            noise_col = 'noise_model'

        if isinstance(subplot, BarPlot):
            self.generate_barplot(subplot)
        elif isinstance(subplot, ScatterPlot):
            self.generate_scatterplot(subplot)
        else:
            self.generate_lineplot(subplot)

        # show 'e' as basis not 2.7... in natural log scale cases
        def ticks(y, _):
            return r'$e^{{{:.0f}}}$'.format(np.log(y))

        if subplot.vis_spec.xScale == LOG:
            ax.xaxis.set_major_formatter(mtick.FuncFormatter(ticks))
        if subplot.vis_spec.yScale == LOG:
            ax.yaxis.set_major_formatter(mtick.FuncFormatter(ticks))

        if not isinstance(subplot, BarPlot):
            ax.legend()
        ax.set_title(subplot.vis_spec.plotName)
        ax.relim()
        ax.autoscale_view()

        return ax

    def generate_plot(self):
        # Set Options for plots
        # possible options: see: plt.rcParams.keys()
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.titlesize'] = 10
        plt.rcParams['figure.figsize'] = [20, 10]
        plt.rcParams['errorbar.capsize'] = 2

        # Set Colormap
        # sns.set(style="ticks", palette="colorblind") ?

        # compute, how many rows and columns we need for the subplots
        num_row = int(np.round(np.sqrt(self.figure.num_subplots)))
        num_col = int(np.ceil(self.figure.num_subplots / num_row))

        fig, axes = plt.subplots(num_row, num_col, squeeze=False)

        for ax in axes.flat[self.figure.num_subplots:]:
            ax.remove()

        axes = dict(zip(uni_plot_ids, axes.flat))

        for idx, subplot in enumerate(self.figure.subplots):
            self.generate_subplot(axes[idx], subplot)


class SeabornPlotter(Plotter):
    """
    seaborn wrapper
    """
    def __init__(self):
        super().__init__()

    def generate_plot(self):
        pass
