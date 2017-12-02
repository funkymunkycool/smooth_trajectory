#!/usr/bin/env python

import ase,copy,argparse
from ase.io import read,write
from sys import argv
import numpy as np
from scipy.interpolate import UnivariateSpline
from argparse import RawTextHelpFormatter
import cube_tools

class trajectory():
    def __init__(self,fname = None,cube = False, nInterp = 10):
        self.xyz = []
        self.cube = cube
        self.xyz_file = False 
        self.cube_file = False 
        if fname[0][-3:] == 'xyz':
            self.xyz_file = True
        if fname[0][-4:] == 'cube':
            self.cube_file = True
        if fname != None:
            if self.cube_file:
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
        self.interpolate_xyz()
        return None
                    
    
    def write_interpolated(self):
        if self.cube_file:
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
            else:
                for frame in xrange(self.nInterp):
                    self.cube_trajectory[0].atomsXYZ[:,0] = self.xyz_interpolated[0][:,frame] 
                    self.cube_trajectory[0].atomsXYZ[:,1] = self.xyz_interpolated[1][:,frame] 
                    self.cube_trajectory[0].atomsXYZ[:,2] = self.xyz_interpolated[2][:,frame] 
                    self.cube_trajectory[0].write_cube('cube_linterp%03d.cube' % frame)
        if self.xyz_file:
            for frame in xrange(self.nInterp):
                self.ase_trajectory[0].positions[:,0] = self.xyz_interpolated[0][:,frame] 
                self.ase_trajectory[0].positions[:,1] = self.xyz_interpolated[1][:,frame] 
                self.ase_trajectory[0].positions[:,2] = self.xyz_interpolated[2][:,frame] 
                write('linterp%03d.xyz' % frame, self.ase_trajectory[0])
        return None


def main():
    parser = argparse.ArgumentParser(description="Interpolate between images in a trajectory.  \nWorks with .xyz and .cube files. \nPass the files as arguments in the order in which they appear in the trajectory. \nThe default is to interpolate so that the trajectory becomes 10 images. This behaviour can be controlled by command line options.\nCommand line option required to interpolate cube data\nMinimum of 3 files required as input to be able to interpolate!",formatter_class=RawTextHelpFormatter)

    parser.add_argument("Files",help="Files used in program",nargs = '+')
    parser.add_argument("-c","--cube",help="Interpolate cube data. May take a few minutes.",action = "store_true")
    parser.add_argument("-n","--ninterp",help="Total number of images to interpolate to. This includes the files that are passed as arguments",nargs=1,type=int)


    if len(argv) <= 2:
        parser.print_help()

    args = parser.parse_args()

    if len(args.Files) < 3:
        print 'Minimum of 3 images required to interpolate. Exiting now'
        exit()

    if args.cube:
        if args.Files: 
            if args.ninterp:
                interpolated_trajectory = trajectory(args.Files,nInterp = int(args.ninterp[0]),cube=True)
                interpolated_trajectory.interpolate_all()
                interpolated_trajectory.write_interpolated()
            else:
                interpolated_trajectory = trajectory(args.Files,cube=True)
                interpolated_trajectory.interpolate_all()
                interpolated_trajectory.write_interpolated()
    elif args.ninterp: 
        interpolated_trajectory = trajectory(args.Files, nInterp = int(args.ninterp[0]))
        interpolated_trajectory.interpolate_all()
        interpolated_trajectory.write_interpolated()
    else:
        interpolated_trajectory = trajectory(args.Files)
        interpolated_trajectory.interpolate_all()
        interpolated_trajectory.write_interpolated()
                

if __name__ == '__main__':
    main()
