#!/usr/bin/env python

import ase,copy
from ase.io import read,write
from sys import argv
import numpy as np
from scipy.interpolate import UnivariateSpline
import cube_tools
import pdb

class trajectory():
    def __init__(self,fname = None,cube = False, nInterp = 10):
        self.xyz = []
        self.cube = cube
        self.xyz_data = True
        if fname != None:
            if cube:
                try:
                    self.cube_trajectory = [ cube_tools.cube(fin) for fin in fname]
                    [self.xyz.append(np.array(self.cube_trajectory[ind].atomsXYZ)) for ind in xrange(len(self.cube_trajectory))]
                except IOError as e:
                    print "File used as input: %s" % fname
                    print "File error ({0}): {1}".format(e.errno, e.strerror)
                    self.terminate_code()
            else:
                self.ase_trajectory = [read(fin) for fin in fname]
                [self.xyz.append(self.ase_trajectory[ind].positions) for ind in xrange(len(self.ase_trajectory))]
        else:
            print "Idiot"
        self.nInterp = nInterp 
        self.distance = np.linspace(0,100,len(self.xyz))
        self.new_axis = np.linspace(0,100,self.nInterp)
        return None

    def combine_cubes(self):
        self.cubes_combined = np.zeros((self.cube_trajectory[0].NX,self.cube_trajectory[0].NY,self.cube_trajectory[0].NZ,len(self.cube_trajectory))) 
        for x in xrange(self.cube_trajectory[0].NX):
            for y in xrange(self.cube_trajectory[0].NY):
                for z in xrange(self.cube_trajectory[0].NZ):
                     for ind,cube in enumerate(self.cube_trajectory):
                         self.cubes_combined[x][y][z][ind] = cube.data[x][y][z]
        return None 

    def interpolate_xyz(self):
        self.xyz_interpolated = [[],[],[]]
        for axis in xrange(3):
            for atom in xrange(len(self.xyz[0])):
                self.xyz_interpolated[axis].append(self.interpolate_points([i[:,axis][atom] for i in self.xyz]))
        self.xyz_interpolated = np.array(self.xyz_interpolated)
        return None 
    
    def interpolate_cube(self):
        self.combine_cubes()
        self.cube_interpolated = np.zeros((np.shape(self.cubes_combined)[0],np.shape(self.cubes_combined)[1],np.shape(self.cubes_combined)[2],self.nInterp)) 
        for x in xrange(np.shape(self.cubes_combined)[0]):
            for y in xrange(np.shape(self.cubes_combined)[1]):
                for z in xrange(np.shape(self.cubes_combined)[2]):
                    self.cube_interpolated[x][y][z] = self.interpolate_points(self.cubes_combined[x][y][z])
        return  None

    def interpolate_points(self,points):
        spl = UnivariateSpline(self.distance,points,k=2)
        y_new = spl(self.new_axis)
        return y_new
    
    def interpolate_all(self):
        if self.cube:
            self.interpolate_cube()
        if self.xyz_data:
            self.interpolate_xyz()
        return None
                    
    
    def write_interpolated(self):
        if self.cube:
            for frame in xrange(self.nInterp):
                for x in xrange(self.cube_trajectory[0].NX):
                    for y in xrange(self.cube_trajectory[0].NY):
                        for z in xrange(self.cube_trajectory[0].NZ):
                            self.cube_trajectory[0].data[x][y][z] = self.cube_interpolated[x][y][z][frame]
                self.cube_trajectory[0].atomsXYZ[:,0] = self.xyz_interpolated[0][:,frame] 
                self.cube_trajectory[0].atomsXYZ[:,1] = self.xyz_interpolated[1][:,frame] 
                self.cube_trajectory[0].atomsXYZ[:,2] = self.xyz_interpolated[2][:,frame] 
                self.cube_trajectory[0].write_cube('cube_linterp%03d.cube' % frame)
#        elif self.xyz_data:
#            for frame in xrange(self.nInterp):
#                self.ase_trajectory[0].atomsXYZ[:,0] = self.xyz_interpolated[0][:,frame] 
#                self.ase_trajectory[0].atomsXYZ[:,1] = self.xyz_interpolated[1][:,frame] 
#                self.ase_trajectory[0].atomsXYZ[:,2] = self.xyz_interpolated[2][:,frame] 
#                write('cube_linterp%03d.cube' % frame, self.ase_trajectory[0])
        return None


def main():
    nInterp = argv[1]
    finp = argv[2:]
    interpolated_trajectory = trajectory(finp,cube=True)
    interpolated_trajectory.interpolate_all()
    interpolated_trajectory.write_interpolated()
#    all_cubes = combine_cubes(trajectory)
#    distance = get_norm(trajectory)
#    interpolated_cubes = interpolate_all(all_cubes,nInterp)
#    xyz = interpolate_trajectory(distance,trajectory,nInterp)
#    trajectory = write_trajectory(trajectory,xyz)
#    if True:
#        write_cubes(trajectory,interpolated_cubes,xyz,nInterp)
#    return None 

if __name__ == '__main__':
    main()
