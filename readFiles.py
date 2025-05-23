#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr  9 12:00:47 2025

@author: ariviere

To read files generated by StabFEM.

"""

import numpy as np
# import subprocess
from matplotlib.tri import Triangulation


def ffreadmesh(filename):
    with open(filename, 'r') as f:
        header = f.readline()[:-1]
        nv, nt, ne = np.array(header.split(' '), dtype = int)
        
        vertex = np.zeros([nv, 3])
        triangles = np.zeros([nt, 4], dtype=int)
        edges = np.zeros([ne, 3], dtype=int)
        
        for i in range(nv):
            line = f.readline()[:-1]
            line = np.array(line.split(' '), dtype=float)
            vertex[i, :] = line

        for i in range(nt):
            line = f.readline()[:-1]
            line = np.array(line.split(' '), dtype=int)
            triangles[i, :] = line
        triangles[:, :3] -= 1 #because counts starts from 1
        for i in range(ne):
            line = f.readline()[:-1]
            line = np.array(line.split(' '), dtype=int)
            edges[i, :] = line
            
        return vertex, triangles, edges
    

def ffreadBaseFlow(filename):
    '''Reads BaseFlow.txt'''
    rawdata = []
    with open(filename, 'r') as f:
        ndof = int(f.readline())
        while True:
            line = f.readline()
            line = line.split(' ')[0][1:-1]
            line = line.split('\t')
            if '' in line:
                rawdata.extend(line[:-1])
                break
            rawdata.extend(line)
    rawdata = np.array(rawdata, dtype=float)
    
    return rawdata



def ffreadEigenFlow(filename):
    '''Reads EigenFlow.txt'''
    # allrawdata = {}
    rawdata = []
    # i = 0
    with open(filename, 'r') as f:
        ndof0 = int(f.readline())
        # print(ndof)
        # i += 1
        while True:
            line = f.readline()
            line = line.replace('\t', ',')
            if line[0]==',':
                line = line[1:]
            # print(line, i, len(rawdata), ndof0)
            line = eval(line)
            rawdata.extend(line)
            if len(rawdata)==ndof0:# and len(allrawdata.keys())==0:#have read the eigenflow
                break
            # rawdata.extend(line)
            # i+=1
    rawdata = np.array(rawdata, dtype=float)
    
    return rawdata


# def ffreadconnectivityBaseFlow(filename):
#     with open(filename,'r') as f:
#         for i in range(4):
#             line = f.readline()
#         line = line.split('int.')[1].split(' ')[0]
#         ndof = int(line)
#         print(ndof)
    
#     connectivity = np.loadtxt(filename, skiprows=5, dtype=int)
#     connectivity = connectivity[:ndof]
#     return connectivity.reshape([ndof//15, 15])

# def ffreadconnectivityEigenFlow(filename):
#     with open(filename,'r') as f:
#         for i in range(4):
#             line = f.readline()
#         line = line.split('int.')
#         print(line)
#         ndof1 = int(line[1].split(' ')[0])
#         ndof2 = int(line[2].split(' ')[0])
#         print(ndof1, ndof2)
#         # line = line.split('int.')[1].split(' ')[0]
#         # ndof = int(line)
    
#     connectivity = np.loadtxt(filename, skiprows=5, dtype=int)
#     connectivity = connectivity[ndof1:ndof1 + ndof2]
#     # print(connectivity[0:2])
#     return connectivity.reshape([ndof2//21, 21])

def ffreadconnectivity(filename):
    connectivity = {}
    lnames = []#will contain 'P2P2P1', 'P2P2' etc..
    ldof = [] #the associated number of dof
    with open(filename,'r') as f:
        #ignore the first 3 lines
        for i in range(4):
            line = f.readline()
        #line where are the degrees of freedom
        line = line.split('int.')
        for elm in line[1:]:
            selm = elm.split(' ')
            ldof.append(int(selm[0]))
            key = selm[1].split('_')[1]
            lnames.append(key)
    
    connectivitydata = np.loadtxt(filename, skiprows=5, dtype=int)
    
    dof0 = 0
    for i, key in enumerate(lnames):
        dof1 = ldof[i]
        connectivity[key] = connectivitydata[dof0: dof0 + dof1]
        
        nfields = key.count('P2')*6 + key.count('P1')*3
        connectivity[key] = connectivity[key].reshape([dof1//nfields, nfields])
        dof0 = dof1
    # connectivity = connectivity[ndof1:ndof1 + ndof2]
    # print(connectivity[0:2])
    return connectivity
    


def get_triangulation(vertex, triangles):
    return Triangulation(vertex[:, 0], vertex[:, 1], triangles=triangles[:, :3])


def get_data(rawdata, vertex, triangles, subsetconnectivity):
    nv = vertex.shape[0]
    
    values = np.zeros(nv)
    for i in range(nv):
        #each vertex corresponds to one dof for pressure
        #there is a mapping between a vertex index and dof index
        mask = triangles[:, :3]==i #get the position of vertex of index i
        values[i] = rawdata[subsetconnectivity[mask]][0]#0 because they are all the same
        
    return values


def get_pressure_bf(rawdata, vertex, triangles, connectivity):
    '''
    Reads presssure field for the base flow. 
    
    ------
    rawdata = ffreadBaseFlow(filename)
    vertex, triangles, edges = ffreadmesh(filename)
    connectivity = ffreadconnectivity(filename)['P2P2P1']

    -------
    Returns pressure on the triangles.
    
    '''
    subsetconnectivity = connectivity[:, -3:]

    return get_data(rawdata, vertex, triangles, subsetconnectivity)
    

def get_ur_bf(rawdata, vertex, triangles, connectivity):
    subsetconnectivity = connectivity[:, :3]

    return get_data(rawdata, vertex, triangles, subsetconnectivity)
    
def get_uz_bf(rawdata, vertex, triangles, connectivity):
    subsetconnectivity = connectivity[:, 6:9]

    return get_data(rawdata, vertex, triangles, subsetconnectivity)
    
def get_ur_ef(rawdata, vertex, triangles, connectivity):
    subsetconnectivity = connectivity[:, :3]
    return get_data(rawdata, vertex, triangles, subsetconnectivity)

def get_uphi_ef(rawdata, vertex, triangles, connectivity):
    subsetconnectivity = connectivity[:, 6:9]
    return get_data(rawdata, vertex, triangles, subsetconnectivity)

def get_uz_ef(rawdata, vertex, triangles, connectivity):
    subsetconnectivity = connectivity[:, 12:15]
    return get_data(rawdata, vertex, triangles, subsetconnectivity)

def get_pressure_ef(rawdata, vertex, triangles, connectivity):
    subsetconnectivity = connectivity[:, -3:]
    return get_data(rawdata, vertex, triangles, subsetconnectivity)


def get_interface(folder):
    data = np.loadtxt(folder + 'interface_data.txt')
    interf = {}
    interf['dl'] = data[:, 0]
    interf['r'] = data[:, 1]
    interf['z'] = data[:, 2]
    interf['nr'] = data[:, -3]
    interf['nz'] = data[:, -2]
    interf['k0_a'] = data[:, 15]
    interf['k0_b'] = data[:, 16]
    
    return interf

def get_interfaceEM(folder, i0):
    data = np.loadtxt(folder + f"mode_interface{i0}.txt", skiprows=2)
    interf = {}
    interf['r_bf'] = data[:, 19] 
    interf['z_bf'] = data[:, 20]
    
    interf['etar_real'] = data[:, 1]*data[:, 21]
    interf['etar_imag'] = data[:, 2]*data[:, 21]
    
    interf['etaz_real'] = data[:, 1]*data[:, 22]
    interf['etaz_imag'] = data[:, 2]*data[:, 22]
    
    interf['s'] = data[:, 0]
    interf['sigma'] = data[0, -2]
    interf['omega'] = data[0, -1]
    # etarr = interf[:, 1]*interf[:, 21]
    # etazr = interf[:, 1]*interf[:, 22]

    # etari = interf[:, 2]*interf[:, 21]
    # etazi = interf[:, 2]*interf[:, 22]

    return interf

def reconstruct_interfaceBF(interf):
    #upper right quadrant
    r = list(interf['r'])
    z = list(interf['z'])
    #lower right    
    r.extend(list(interf['r'][::-1][1:]))
    z.extend(list(-interf['z'][::-1][1:]))
    #lower left
    r.extend(list(-interf['r'][1:]))
    z.extend(list(-interf['z'][1:]))
    #upper left
    r.extend(list(-interf['r'][::-1][1:]))
    z.extend(list(interf['z'][::-1][1:]))
    
    return np.array(r), np.array(z)


def reconstruct_interfaceEM(interfEM, m, sym):

    shapeBF= {}
    shapeBF['r'] = interfEM['r_bf']
    shapeBF['z'] = interfEM['z_bf']
    r, z = reconstruct_interfaceBF(shapeBF)
    
    interfEM['all_r_bf'] = r
    interfEM['all_z_bf'] = z
    
    if m%2==0:
        symr = 1
    else:
        symr = -1
    symz = sym
    
    for postfix in ['real', 'imag']:
        keyr = 'etar_' + postfix
        keyz = 'etaz_' + postfix
        
        etar = interfEM[keyr]
        etaz = interfEM[keyz]
        all_etar = list(etar) + list(symz*etar[::-1][1:]) + list(-etar[1:]*symz) + list(-etar[::-1][1:])
        all_etaz = list(etaz) + list(-etaz[::-1][1:]) + list(-etaz[1:]*symr) + list(etaz[::-1][1:]*symr)
        interfEM['all_' + keyr] = np.array(all_etar)
        interfEM['all_' + keyz] = np.array(all_etaz)
        
    return interfEM


def get_params(folder):
    data = np.loadtxt(folder + 'params.txt', skiprows=1)
    params = {}
    #oh we Re S Pb Chi Rx Ry m2 Vol Area Nv Nsurface NsF
    # 0 1   2 3 4   5   6  7  8  9  10   11  12      13

    keys = ['oh', 'we', 're', 'S', 'Pb', 'Chi', 'Rx', 'Ry', 'm2', 'Vol', \
            'Area', 'Nv', 'Nsurf', 'NsF']
    for i, elm in enumerate(keys):
        params[elm] = data[i]
    
    return params


def get_spectrum(folder):
    data = np.loadtxt(folder + 'Spectrum.txt')
    spectrum = {}
    keys = ['sigma', 'omega', 'm', 'sym', 'shift_sig', 'shift_omega']
    for i, key in enumerate(keys):
        if i<2:
            spectrum[key] = data[:, i]
        else:
            spectrum[key] = data[0, i]#all the same
            
    return spectrum



def find_nextfolder(folder0, folds, direction):
    params = get_params(folder0)
    oh = params['oh']
    we = params['we']
    pb = params['Pb']
    interf = get_interface(folder0)
    Chi0 = (interf['z'][0]-interf['r'][-1])/(interf['r'][-1]+interf['z'][0])
    
    nextfolder = ''
    
    dist0 = np.infty
    
    for fold in folds:
        if fold == folder0:
            continue
        params = get_params(fold)
        
        if params['oh']!=oh:
            continue
        if direction == 'increasing We' and params['we']<we:
            continue
        elif direction == 'decreasing We' and params['we']>we:
            continue
        
        interf = get_interface(fold)
        Chi = (interf['z'][0]-interf['r'][-1])/(interf['r'][-1]+interf['z'][0])
        
        dist = np.sqrt((params['we'] - we)**2 + (params['Pb'] - pb)**2 + 2*(Chi-Chi0)**2)
        if dist<dist0:
            dist0 = dist
            nextfolder = fold
            
    return nextfolder
        

def find_branches(folds):
    dico = {}
    #branch = 'upper' or 'lower'

    for fold in folds:        
        params = get_params(fold)
        oh = params['oh']
        if oh not in dico.keys():
            dico[oh] = {}
            dico[oh]['folds'] = []
            dico[oh]['chi'] = []
            dico[oh]['we'] = []
        dico[oh]['folds'].append(fold)
        dico[oh]['we'].append(params['we'])

        interf = get_interface(fold)
        Chi = (interf['z'][0]-interf['r'][-1])/(interf['r'][-1]+interf['z'][0])
        dico[oh]['chi'].append(Chi)
        
    dicobranches = {}
    for oh in dico.keys():
        for key in dico[oh].keys():
            dico[oh][key] = np.asarray(dico[oh][key])

        imin = np.argmin(dico[oh]['we'])
        chimin = dico[oh]['chi'][imin]

        #upper branch first
        indupper = dico[oh]['chi']>= chimin
        indsortedupper = np.argsort(dico[oh]['we'][indupper])

        indlower = dico[oh]['chi']<= chimin
        indsortedlower = np.argsort(dico[oh]['we'][indlower])
        
        dicobranches[oh] = {}
        for branch in ['upper', 'lower']:
            dicobranches[oh][branch] = {}
        for key in dico[oh]:
            dicobranches[oh]['upper'][key] = dico[oh][key][indupper][indsortedupper]        
            dicobranches[oh]['lower'][key] = dico[oh][key][indlower][indsortedlower]
            
    return dicobranches
        
        
        
        
def find_closest_eigenvalue(spectrum, sig_target, omega_target):
    return np.argmin((spectrum['sigma']-sig_target)**2 + (spectrum['omega'] - omega_target)**2)
    


