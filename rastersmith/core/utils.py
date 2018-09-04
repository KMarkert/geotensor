
# import dependency
from __future__ import print_function,division

import math
import warnings
from itertools import groupby
import numpy as np
import xarray as xr
from scipy import interpolate


# warnings.simplefilter("always")

def meters2dd(inPt,scale=30):
    """Function to convert meters to decimal degrees based on the approximation
    given by: https://en.wikipedia.org/wiki/Geographic_coordinate_system

    Args:
        inPt (list or array): A Y,X point provided in geographic coordinates
        in that order.

    Keywords:
        scale (int): Resolution of the raster value to covert into decimal
        degrees, must be in meters.

    Returns:
        list: List of Y,X resolution values converted from meters to decimal degrees

    """

    lat = inPt[0] # get latitude value

    radLat = math.radians(lat) # convert degree latitude to radians

    a = 6378137 # radius of Earth in meters

    ba = 0.99664719 # constant of b/a

    ss = math.atan(ba*math.tan(radLat)) # calculate the reduced latitude

    # factor to convert meters to decimal degrees for X axis
    xfct = (math.pi/180)*a*math.cos(ss)

    # factor to convert meters to decimal degrees for Y axis
    yfct = (111132.92-559.82*math.cos(2*radLat)+1.175*math.cos(4*radLat)-
              0.0023*math.cos(6*radLat))

    # get decimal degree resolution
    ydd = scale / yfct
    xdd = scale / xfct

    # return list of converted resolution values
    return [ydd,xdd]

def dd2meters(inPt,scale=0.1):
    """Function to convert decimal degrees to meters based on the approximation
        given by: https://en.wikipedia.org/wiki/Geographic_coordinate_system

        Args:
        inPt (list or array): A Y,X point provided in geographic coordinates
        in that order.

        Keywords:
        scale (int): Resolution of the raster value to covert into meters,
        must be in decimal degrees.

        Returns:
        list: List of Y,X resolution values converted from meters to decimal degrees

        """

    lat = inPt[0] # get latitude value

    radLat = math.radians(lat) # convert degree latitude to radians

    a = 6378137 # radius of Earth in meters

    ba = 0.99664719 # constant of b/a

    ss = math.atan(ba*math.tan(radLat)) # calculate the reduced latitude

    # factor to convert meters to decimal degrees for X axis
    xfct = (math.pi/180)*a*math.cos(ss)

    # factor to convert meters to decimal degrees for Y axis
    yfct = (111132.92-559.82*math.cos(2*radLat)+1.175*math.cos(4*radLat)-
            0.0023*math.cos(6*radLat))

    # get meter resolution
    y_meters = scale * yfct
    x_meters = scale * xfct

    # return list of converted resolution values
    return [y_meters,x_meters]


def projectRaster(rasterobj, grid,resampleMethod='nearest'):

    rasterLons = rasterobj.coords['lon'].values
    rasterLats = rasterobj.coords['lat'].values


    xSelect = (rasterLons>grid.west) & (rasterLons<grid.east)
    ySelect = (rasterLats>grid.south) & (rasterLats<grid.north)
    spatialSelect = ySelect & xSelect

    idx = np.where(spatialSelect == True)

    # Format geolocation coordinates for regridding
    pts = np.zeros((idx[0].size,2))
    pts[:,0] = rasterLons[idx].ravel()
    pts[:,1] = rasterLats[idx].ravel()

    arr = raster.values
    bandKeys = raster.coords['band']

    newDims = (grid.dims[0],grid.dims[1],arr.shape[2],arr.shape[3],arr.shape[4])
    print(newDims)

    out = np.full(newDims,np.nan)
    quality = np.ones(grid.dims,dtype=np.bool)

    for i in range(newDims[3]):
        if bandKeys[i] != 'mask':
            iMethod = resampleMethod
        else:
            iMethod = 'nearest'
        # Regrid data to common grid
        interp = interpolate.griddata(pts,
                    arr[idx[0],idx[1],0,i,0].ravel(),
                    (grid.xx,grid.yy), method=iMethod,
                 )
        interp.astype(np.float)[np.where(interp<-1)] = np.nan
        out[:,:,0,i,0] = interp

        quality = quality & (interp>=0)

    out[:,:,0,-1,0] = out[:,:,0,-1,0].astype(np.bool) & quality

    coords = {'y': range(grid.dims[0]),
              'x': range(grid.dims[1]),
              'z': range(arr.shape[2]),
              'lat':(['y','x'],grid.yy),
              'lon':(['y','x'],grid.xx),
              'band':raster.coords['band'],
              'time':raster.coords['time']}

    dims = ['y','x','z','band','time']

    attrs = raster.attrs

    outDa = xr.DataArray(out,coords=coords,dims=dims,attrs=attrs,name=raster.name)

    return outDa


def test():
    # main level program for testing
    inPt = [-1,0] # -1 degrees latitude, 0 degrees longitue
    outMeters = meters2dd(inPt,100)
    outDD = dd2meters(inPt,1)

    # print results
    print('Output decimal degrees: {0}\nOutput meters: {1}'.format(outMeters,outDD))

    return


# Execute the main level program if run as standalone
if __name__ == "__main__":
    test()
