"""
This file is part of CLIMADA.

Copyright (C) 2017 ETH Zurich, CLIMADA contributors listed in AUTHORS.

CLIMADA is free software: you can redistribute it and/or modify it under the
terms of the GNU Lesser General Public License as published by the Free
Software Foundation, version 3.

CLIMADA is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along
with CLIMADA. If not, see <https://www.gnu.org/licenses/>.

---

Define AgriculturalDrought (AD) class.
WORK IN PROGRESS
"""

__all__ = ['CropPotential']

import logging
import os
from os import listdir
from os.path import isfile, join
import xarray as xr
import numpy as np
from matplotlib import pyplot as plt
import cartopy
import shapely.geometry
from scipy import sparse
import scipy.stats
import h5py


from climada.hazard.base import Hazard
from climada.util import dates_times as dt
from climada.util.constants import DATA_DIR



LOGGER = logging.getLogger(__name__)

HAZ_TYPE = 'CP'
""" Hazard type acronym for Crop Potential """


AG_MODEL = ['gepic',
            'lpjml',
            'pepic'
            ]

CL_MODEL = ['gfdl-esm2m',
            'hadgem2-es',
            'ipsl-cm5a-lr',
            'miroc5'
            ]

SCENARIO = ['historical',
            'rcp60'
            ]

SOC = ['2005soc',
       'histsoc'
       ]

CO2 = ['co2',
       '2005co2'
       ]

CROP = ['whe',
        'mai',
        'soy',
        'ric'
       ]

IRR = ['noirr',
       'irr']


FN_STR_VAR = 'global_annual'

YEARCHUNKS = dict()
YEARCHUNKS[SCENARIO[0]] = dict()
YEARCHUNKS[SCENARIO[0]] = {'yearrange' : np.array([1976, 2005]), \
          'startyear' : 1861, 'endyear': 2005}
YEARCHUNKS[SCENARIO[1]] = dict()
YEARCHUNKS[SCENARIO[1]] = {'yearrange' : np.array([2006, 2099]), \
          'startyear' : 2006, 'endyear': 2099}

BBOX = np.array([-180, -85, 180, 85]) # [Lon min, lat min, lon max, lat max]

INT_DEF = 'Yearly Yield'

#default: deposit the input files in the directory: climada_python/data/ISIMIP/Input/Hazard
INPUT_DIR = DATA_DIR+'/ISIMIP/Input/Hazard'
OUTPUT_DIR = DATA_DIR+'/ISIMIP/Output/Hazard'

class CropPotential(Hazard):
    """Contains events impacting the crop potential.

    Attributes:
        crop_type (str): crop type (e.g. whe for wheat)
        intensity_def (str): intensity defined as the Yearly Yield / Relative Yield / Percentile
    """

    def __init__(self, pool=None):
        """Empty constructor. """
        Hazard.__init__(self, HAZ_TYPE)
        if pool:
            self.pool = pool
            LOGGER.info('Using %s CPUs.', self.pool.ncpus)
        else:
            self.pool = None

        self.crop = CROP[0]
        self.intensity_def = INT_DEF

    def set_from_single_run(self, input_dir=None, bbox=BBOX, \
                            yearrange=(YEARCHUNKS[SCENARIO[0]])['yearrange'], \
                            ag_model=AG_MODEL[0], cl_model=CL_MODEL[0], \
                            scenario=SCENARIO[0], soc=SOC[0], co2=CO2[0], \
                            crop=CROP[0], irr=IRR[0], fn_str_var=FN_STR_VAR):

        """Wrapper to fill hazard from nc_dis file from ISIMIP
        Parameters:
            input_dir (string): path to input data directory
            bbox (list of four floats): bounding box:
                [lon min, lat min, lon max, lat max]
            yearrange (int tuple): year range for hazard set, f.i. (1976, 2005)
            ag_model (str): abbrev. agricultural model (only when input_dir is selected)
                f.i. 'gepic' etc.
            cl_model (str): abbrev. climate model (only when input_dir is selected)
                f.i. 'gfdl-esm2m' etc.
            scenario (str): climate change scenario (only when input_dir is selected)
                f.i. 'historical' or 'rcp60'
            soc (str): socio-economic trajectory (only when input_dir is selected)
                f.i. '2005soc' or 'histsoc'
            co2 (str): CO2 forcing scenario (only when input_dir is selected)
                f.i. 'co2' or '2005co2'
            crop (str): crop type (only when input_dir is selected)
                f.i. 'whe', 'mai', 'soy' or 'ric'
            irr (str): irrigation type (only when input_dir is selected)
                f.i 'noirr' or 'irr'
            fn_str_var (str): FileName STRing depending on VARiable and
                ISIMIP simuation round
        raises:
            NameError
        """

        if input_dir is not None:
            if not os.path.exists(input_dir):
                LOGGER.warning('Input directory %s does not exist', input_dir)
                raise NameError
        else:
            LOGGER.warning('Input directory %s not set', input_dir)
            raise NameError


        yearchunk = YEARCHUNKS[scenario]
        string = '%s_%s_ewembi_%s_%s_%s_yield-%s-%s_%s_%s_%s.nc'
        filename = os.path.join(input_dir, string % (ag_model, cl_model, scenario, soc, co2, crop, \
                                                 irr, fn_str_var, str(yearchunk['startyear']), \
                                                 str(yearchunk['endyear'])))

        #define idx of the nc-bands to be extracted and the corresponding event names / dates
        #corrected idx due to the bands in input starting with the idx = 1
        id_bands = np.arange(yearrange[0] - yearchunk['startyear']+1, \
                             yearrange[1] - yearchunk['startyear']+2).tolist()
        event_list = [str(n) for n in range(int(yearrange[0]), int(yearrange[1]+1))]
        date = [event_list[n]+'-01-01' for n, _ in enumerate(event_list)]

        #hazard setup
        self.set_raster([filename], band=id_bands, \
                        geometry=list([shapely.geometry.box(bbox[0], bbox[1], bbox[2], bbox[3])]))

        self.crop = (xr.open_dataset(filename, decode_times=False)).crop
        self.event_name = event_list
        self.frequency = np.ones(len(self.event_name))*(1/len(self.event_name))
        self.fraction = self.intensity.copy()
        self.fraction.data.fill(1.0)
        self.units = 't / y / ha'
        self.date = np.array(dt.str_to_date(date))
        self.centroids.set_meta_to_lat_lon()
        self.check()

        return self

    def calc_mean(self, yearrange=(YEARCHUNKS[SCENARIO[0]])['yearrange'], save=False, \
                  output_dir=OUTPUT_DIR):
        """ Calculates mean of the hazard for a given reference time period
            Parameter:
                yearrange (array): time period used to calculate the mean intensity
                default: 1976-2005

            Returns:
                hist_mean(array): contains mean value over the given reference
                time period for every centroid
        """
        time_array = np.array(self.event_name, dtype=int)
        idx_time = np.zeros(2, dtype=int)
        idx_time[0] = np.where(time_array == yearrange[0])[0]
        idx_time[1] = np.where(time_array == yearrange[1])[0]
        mean = np.mean(self.intensity[idx_time[0]:idx_time[1]], 0)
        hist_mean = np.nan_to_num(np.squeeze(np.asarray(mean)))

        if save:
            #generate output directories if they do not exist yet
            if not os.path.exists(output_dir):
                os.mkdir(output_dir)
            mean_dir = output_dir+'/Hist_mean/'
            if not os.path.exists(mean_dir):
                os.mkdir(mean_dir)
            #save mean_file
            mean_file = h5py.File(mean_dir+'hist_mean_'+self.crop+'_'+str(yearrange[0])+ \
                                  '-'+str(yearrange[1]), 'w')
            mean_file.create_dataset('mean', data=hist_mean)
            mean_file.create_dataset('lat', data=self.centroids.lat)
            mean_file.create_dataset('lon', data=self.centroids.lon)
            mean_file.close()

        return hist_mean


    def set_rel_yield_to_int(self, hist_mean):
        """ Sets relative yield to intensity (yearly yield / historic mean) per centroid

            Parameter:
                historic mean (array): historic mean per centroid

            Returns:
                hazard with modified intensity
        """
        #determine idx of the centroids with a mean yield !=0
        idx = np.where(hist_mean != 0)[0]

        #initialize new hazard_matrix
        hazard_matrix = np.empty(self.intensity.shape)
        hazard_matrix[:, :] = np.nan

        for event in range(len(self.event_id)):
            hazard_matrix[event, idx] = self.intensity[event, idx]/hist_mean[idx]

        self.intensity = sparse.csr_matrix(hazard_matrix)
        self.intensity_def = 'Relative Yield'
        self.units = ''
        self.intensity.max = np.nanmax(self.intensity.toarray())
        self.intensity.min = np.nanmin(self.intensity.toarray())

        return self

    def set_percentile_to_int(self, reference_intensity=None):
        """ Sets percentile to intensity

            Parameter:
                reference_intensity (AD): intensity to be used as reference (e.g. the historic
                                    intensity can be used in order to be able to directly compare
                                    historic and future projection data)

            Returns:
                hazard with modified intensity
        """
        hazard_matrix = np.zeros(self.intensity.shape)
        if reference_intensity is None:
            reference_intensity = self.intensity

        for centroid in range(self.intensity.shape[1]):
            array = (reference_intensity[:, centroid].toarray()).reshape(\
                    reference_intensity.shape[0])
            for event in range(self.intensity.shape[0]):
                value = self.intensity[event, centroid]
                hazard_matrix[event, centroid] = (scipy.stats.percentileofscore(array, value))/100

        self.intensity = sparse.csr_matrix(hazard_matrix)
        self.intensity_def = 'Percentile'
        self.units = ''

        return self

    def plot_intensity_cp(self, event, dif=0, axis=None, **kwargs):
        """ Plots intensity with predefined settings depending on the intensity definition

        Parameters:
            event (int or str): event_id or event_name
            dif (int): variable signilizing whether absolute values or the difference between
                future and historic are plotted (dif=0: his/fut values; dif=1: difference = fut-his)
            axis (geoaxes): axes to plot on
        """
        if dif == 0:
            if self.intensity_def == 'Yearly Yield':
                axes = self.plot_intensity(event=event, axis=axis, cmap='YlGn', vmin=0, vmax=10, \
                                           **kwargs)
            elif self.intensity_def == 'Relative Yield':
                axes = self.plot_intensity(event=event, axis=axis, cmap='RdBu', vmin=0, vmax=2, \
                                           **kwargs)
            elif self.intensity_def == 'Percentile':
                axes = self.plot_intensity(event=event, axis=axis, cmap='RdBu', vmin=0, vmax=1, \
                                           **kwargs)
        elif dif == 1:
            if self.intensity_def == 'Yearly Yield':
                axes = self.plot_intensity(event=event, axis=axis, cmap='RdBu', vmin=-2, vmax=2, \
                                           **kwargs)
            elif self.intensity_def == 'Relative Yield':
                axes = self.plot_intensity(event=event, axis=axis, cmap='RdBu', vmin=-0.5, \
                                           vmax=0.5, **kwargs)

        return axes

    def plot_time_series(self, years=None):
        """ Plots a time series of intensities (a series of sub plots)

        Returns:
            figure
        """

        if years is None:
            event_list = self.event_name
        else:
            event_list = [str(n) for n in range(years[0], years[1]+1)]

        self.centroids.set_meta_to_lat_lon()

        len_lat = abs(self.centroids.lat[0]-self.centroids.lat[-1])*(2.5/13.5)
        len_lon = abs(self.centroids.lon[0]-self.centroids.lon[-1])*(5/26)

        nr_subplots = len(event_list)

        if len_lon >= len_lat:
            colums = int(np.floor(np.sqrt(nr_subplots/(len_lon/len_lat))))
            rows = int(np.ceil(nr_subplots/colums))
        else:
            rows = int(np.floor(np.sqrt(nr_subplots/(len_lat/len_lon))))
            colums = int(np.ceil(nr_subplots/colums))

        fig, axes = plt.subplots(rows, colums, sharex=True, sharey=True, \
                                 figsize=(colums*len_lon, rows*len_lat), \
                                 subplot_kw=dict(projection=cartopy.crs.PlateCarree()))
        colum = 0
        row = 0

        for year in range(nr_subplots):
            axes.flat[year].set_extent([np.min(self.centroids.lon), np.max(self.centroids.lon), \
                      np.min(self.centroids.lat), np.max(self.centroids.lat)])

            if rows == 1:
                self.plot_intensity_cp(event=event_list[year], axis=axes[colum])
            elif colums == 1:
                self.plot_intensity_cp(event=event_list[year], axis=axes[row])
            else:
                self.plot_intensity_cp(event=event_list[year], axis=axes[row, colum])

            if colum <= colums-2:
                colum = colum + 1
            else:
                colum = 0
                row = row + 1

        return fig

    def plot_comparing_maps(self, his, fut, axes, nr_cli_models=1, model=1):
        """ Plots comparison maps of historic and future data and their difference fut-his

        Parameters:
            his (sparse matrix): historic mean annual yield or mean relative yield
            fut (sparse matrix): future mean annual yield or mean relative yield
            axes (Geoaxes): subplot axes that can be generated with ag_drought_util.setup_subplots
            nr_cli_models (int): number of climate models and respectively nr of rows within
                                    the subplot
            model (int): current model/row to plot

        Returns:
            geoaxes
        """
        dif = fut - his
        self.event_id = 0

        for subplot in range(3):

            if self.intensity_def == 'Yearly Yield':
                self.units = 't / y'
            elif self.intensity_def == 'Relative Yield':
                self.units = ''

            if subplot == 0:
                self.intensity = sparse.csr_matrix(his)
                dif_def = 0
            elif subplot == 1:
                self.intensity = sparse.csr_matrix(fut)
                dif_def = 0
            elif subplot == 2:
                self.intensity = sparse.csr_matrix(dif)
                dif_def = 1


            if nr_cli_models == 1:
                ax1 = self.plot_intensity_cp(event=0, dif=dif_def, axis=axes[subplot])
            else:
                ax1 = self.plot_intensity_cp(event=0, dif=dif_def, axis=axes[model, subplot])

            ax1.set_title('')

        if nr_cli_models == 1:
            cols = ['Historical', 'Future', 'Difference = Future - Historical']
            for ax0, col in zip(axes, cols):
                ax0.set_title(col, size='large')

        return axes


def init_full_hazard_set(input_dir=INPUT_DIR, output_dir=OUTPUT_DIR, bbox=BBOX, \
                         yearrange=(YEARCHUNKS[SCENARIO[0]])['yearrange']):
    """ Generates hazard set for all files contained in the input directory and saves them
    as hdf5 files in the output directory

        Parameter:
        input_dir (string): path to input data directory
        output_dir (string): path to output data directory
        bbox (list of four floats): bounding box:
            [lon min, lat min, lon max, lat max]
        yearrange (int tuple): year range for hazard set, f.i. (2001, 2005)

    """
    filenames = [f for f in listdir(input_dir) if (isfile(join(input_dir, f))) if not \
                 f.startswith('.')]

    #generate output directories if they do not exist yet
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    mean_dir = output_dir+'/Hist_mean/'
    if not os.path.exists(mean_dir):
        os.mkdir(mean_dir)

    #generate lists of splitted historical filenames (in order to differentiate betweeen
    #the used ag_model, cl_model, crop, etc.); list of the future scenarios; list
    #of all crop-irr combinations
    items = list()
    crop_list = list()
    scenario_list = list()
    for i, _ in enumerate(filenames):
        item = filenames[i].split('_')
        if item[3] == 'historical':
            items.append(item)
        elif item[3] not in scenario_list:
            scenario_list.append(item[3])
        crop_irr = ((item[6]).split('-'))[1]+'-'+((item[6]).split('-'))[2]
        if crop_irr not in crop_list:
            crop_list.append(crop_irr)

    #generate hazard using the first file to determine the size of the historic mean
    #file structure: ag_model _ cl_model _ scenario _ soc _ co2 _
    #   yield-crop-irr _ fn_str_var _ startyear _ endyear . nc
    #e.g. gepic_gfdl-esm2m_ewembi_historical_2005soc_co2_yield-whe-noirr_
    #   global_annual_1861_2005.nc
    cp_zero = CropPotential()
    cp_zero.set_from_single_run(input_dir=input_dir, bbox=bbox, yearrange=yearrange, \
                                ag_model=(items[0])[0], cl_model=(items[0])[1], \
                                scenario=(items[0])[3], soc=(items[0])[4], co2=(items[0])[5],\
                                crop=(((items[0])[6]).split('-'))[1], \
                                irr=(((items[0])[6]).split('-'))[2])
    hist_mean = cp_zero.calc_mean()
    cp_zero.set_rel_yield_to_int(hist_mean)

    #initiate the historic mean for each combination of crop and irrigation type
    hist_mean_per_crop = dict()
    for i, _ in enumerate(crop_list):
        hist_mean_per_crop[i] = dict()
        hist_mean_per_crop[crop_list[i]] = {'value': np.zeros([int(len( \
                          filenames)/len(crop_list)), len(hist_mean)]), 'idx' : 0}

    #calculate hazard as relative yield for all historic files and related future scenarios
    #and save them as hdf5 file in the output directory
    for i, _ in enumerate(items):
        #historic file
        crop_irr = (((items[i])[6]).split('-'))[1]+'-'+(((items[i])[6]).split('-'))[2]

        cp_his = CropPotential()
        cp_his.set_from_single_run(input_dir=input_dir, bbox=bbox, yearrange=yearrange, \
                                    ag_model=(items[i])[0], cl_model=(items[i])[1], \
                                    scenario=(items[i])[3], soc=(items[i])[4], \
                                    co2=(items[i])[5], crop=(((items[i])[6]).split('-'))[1],\
                                    irr=(((items[i])[6]).split('-'))[2])
        hist_mean = cp_his.calc_mean()
        cp_his.set_rel_yield_to_int(hist_mean)
        ((hist_mean_per_crop[crop_irr])['value'])[( \
        hist_mean_per_crop[crop_irr])['idx'], :] = hist_mean
        (hist_mean_per_crop[crop_irr])['idx'] = (hist_mean_per_crop[crop_irr])['idx']+1

        filename = 'haz'+'_'+(items[i])[0]+'_'+(items[i])[1]+'_'+(items[i])[3]+'_'+\
        (items[i])[4]+'_'+(items[i])[5]+'_'+crop_irr+'_'+str(yearrange[0])+'-'+str(yearrange[1])

        cp_his.write_hdf5(output_dir+'/'+filename)

        #compute the relative yield for all future scenarios with the corresponding historic mean
        for j, _ in enumerate(scenario_list):
            yearrange_fut = np.array([(YEARCHUNKS[scenario_list[j]])['startyear'], \
                                      (YEARCHUNKS[scenario_list[j]])['endyear']])
            cp_fut = CropPotential()
            cp_fut.set_from_single_run(input_dir=input_dir, bbox=bbox, yearrange=yearrange_fut, \
                                        ag_model=(items[i])[0], cl_model=(items[i])[1], \
                                        scenario=scenario_list[j], soc=(items[i])[4],\
                                        co2=(items[i])[5], crop=(((items[i])[6]).split('-'))[1], \
                                        irr=(((items[i])[6]).split('-'))[2])
            cp_fut.set_rel_yield_to_int(hist_mean)
            filename = 'haz'+'_'+(items[i])[0]+'_'+(items[i])[1]+'_'+scenario_list[j]+'_'+ \
            (items[i])[4]+'_'+(items[i])[5]+'_'+ \
            crop_irr+'_'+str(yearrange_fut[0])+'-'+str(yearrange_fut[1])

            cp_fut.write_hdf5(output_dir+'/'+filename)

    #calculate mean for each crop-irrigation combination and save as hdf5 in output_dir
    for i, _ in enumerate(crop_list):
        mean = np.mean((hist_mean_per_crop[crop_list[i]])['value'], 0)
        mean_file = h5py.File(mean_dir+'hist_mean_'+crop_list[i]+'_'+str(yearrange[0])+ \
                              '-'+str(yearrange[1]), 'w')
        mean_file.create_dataset('mean', data=mean)
        mean_file.create_dataset('lat', data=cp_his.centroids.lat)
        mean_file.create_dataset('lon', data=cp_his.centroids.lon)
        mean_file.close()
        #save historic mean as netcdf (saves mean, lat and lon as arrays)
#        mean_file = xr.Dataset({'mean': mean, 'lat': cp_his.centroids.lat, \
#                                'lon': cp_his.centroids.lon})
#        mean_file.to_netcdf(mean_dir+'hist_mean_'+crop_list[i]+'.nc')