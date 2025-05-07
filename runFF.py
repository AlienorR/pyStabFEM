#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr  9 14:24:50 2025

@author: ariviere

Functions to run StabFEM steps
"""

import subprocess
from varioustools.files import readgivenline
from os.path import exists

# def decode_outputs(output):
#     outs = []
#     for line in output.splitlines():
#         out = line.decode()
#         outs.append(out)
#     return outs


def mesh_initialization(ffscriptmesh = 'Mesh_square_medium_new.edp'):
    command = "FreeFem++-mpi -v 0 " + ffscriptmesh
    try:
        ls = subprocess.run([command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
        ls.check_returncode()
        print('Mesh correctly initialized')
        return []
    except subprocess.CalledProcessError as e:
        print ( "Error:\nreturn code: ", e.returncode, "\nOutput: ", e.stderr.decode("utf-8") )
        result = ls.stdout.decode("utf-8")
        return result


def runbasicNewton(we, oh, NsF=0, initdir = '', foldersave = ''):
    print('Oh =', oh, 'We = ', we)

    command = f"cp {initdir}mesh.msh mesh_guess.msh ; cp {initdir}BaseFlow.txt BaseFlow_guess.txt"
    result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
    
    if NsF==0:
        command = f"FreeFem++-mpi -v 0 Newton_ALE_StrainedBubble_Fourier_new.edp -Oh {oh} -We {we}"
    else:
        command = f"FreeFem++-mpi -v 0 Newton_ALE_StrainedBubble_Fourier_new.edp -Oh {oh} -We {we} -NsF {NsF}"
    try:
        ls = subprocess.run([command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
        ls.check_returncode()
    except subprocess.CalledProcessError as e:
        print ( "Error:\nreturn code: ", e.returncode, "\nOutput: ")
        result = ls.stdout.decode("utf-8")
        print(result)
        return result
    
    #no error : save data
    vwe = f'{we:.3f}'.replace('.', 'v').replace('-', 'm')
    voh = f'{oh:.3f}'.replace('.', 'v').replace('-', 'm')
    foldname = foldersave +  f'{vwe}_{voh}/'
    command = 'mkdir ' + foldname + ';'
    for elm in ['*.txt', '*.msh', '*.ff2m']:
        command += 'cp ' + elm + ' ' + foldname + ';'
    subprocess.run(command, shell=True)
    print('saved')
    return [foldname]

def runNewtonArcLength(dS, oh, NsF=0, initdir='', foldersave=''):
    command = f"cp {initdir}mesh.msh mesh_guess.msh ; cp {initdir}BaseFlow.txt BaseFlow_guess.txt"
    result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
    
    if NsF==0:
        command = f"FreeFem++-mpi -v 0 Newton_ALE_StrainedBubble_Fourier_arclength_new.edp -Oh {oh} -dS {dS}"
    else:
        command = f"FreeFem++-mpi -v 0 Newton_ALE_StrainedBubble_Fourier_arclength_new.edp -Oh {oh} -dS {dS} -NsF {NsF}"
    
    try:
        ls = subprocess.run([command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
        ls.check_returncode()
    except subprocess.CalledProcessError as e:
        print ( "Error:\nreturn code: ", e.returncode, "\nOutput: ")
        result = ls.stdout.decode("utf-8")
        print(result)
        return result

    
    we = float(readgivenline('BaseFlow.ff2m', 7))
    print('Oh =', oh, 'We = ', we)

    vwe = f'{we:.3f}'.replace('.', 'v').replace('-', 'm')
    voh = f'{oh:.3f}'.replace('.', 'v').replace('-', 'm')
    foldname = foldersave + f'{vwe}_{voh}/'
    command = 'mkdir ' + foldname + ';'
    for elm in ['*.txt', '*.msh', '*.ff2m']:
        command += 'cp ' + elm + ' ' + foldname + ';'
    subprocess.run(command, shell=True)
    print('saved')
    return [foldname]


def createMask(typemask='fitsurface', Hlayer=0.2, DX=0.02):
    command =  f"FreeFem++-mpi -v 0 AdaptationMask.edp -type {typemask} -Hlayer {Hlayer} -DX {DX}"
    subprocess.run(command, shell = True)

    
def runMeshAdaptation(Hlayer, DX, NsF=0, foldersave='', initdir='', cvgBF=False):
    
    command = f"cp {initdir}BaseFlow.txt .; cp {initdir}mesh.msh ."
    subprocess.run(command, shell=True)
    
    #1. Create a mask    
    createMask(Hlayer=Hlayer, DX=DX)

    #2. Adapt the grid
    command = "mv BaseFlow.txt FlowFieldToAdapt1.txt"
    subprocess.run(command, shell=True)

    command = 'mv Data.txt FlowFieldToAdapt2.txt'
    subprocess.run(command, shell=True)
    command = "echo 2 ReP2P2P1 6 CxP2P2 0| FreeFem++-mpi -v 0 AdaptMesh.edp"
    
    result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
    
    command = "mv FlowFieldAdapted1.txt BaseFlow_guess.txt; mv mesh_adapt.msh mesh.msh; "
    subprocess.run(command, shell=True)
    print('successfully created adapted mesh')
    
    command = "FreeFem++-mpi -v 0 Redistribute_Surface_Points_ALE_new.edp"
    result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)        
    print('successfully redistributed points')


    command = "mv BaseFlow.txt BaseFlow_guess.txt"
    subprocess.run(command, shell=True)


    if NsF==0:
        command = "FreeFem++-mpi -v 0 Smooth_Surface_ALE_new.edp"
    else:
        command = f"FreeFem++-mpi -v 0 Smooth_Surface_ALE_new.edp -NsF {NsF}"

    result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)

    print('successfully smoothed the interface')
    
    if cvgBF:
    
        command = "mv mesh.msh mesh_guess.msh; mv BaseFlow.txt BaseFlow_guess.txt"    
        subprocess.run(command, shell=True)    
        command = "FreeFem++-mpi -v 0 Newton_ALE_StrainedBubble_Fourier_new.edp"
        result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        print('successfully recomputed the base flow')
    
    oh = float(readgivenline('BaseFlow.ff2m', 6))
    we = float(readgivenline('BaseFlow.ff2m', 7))
    
    print('Oh =', oh, 'We = ', we)
    
    vwe = f'{we:.3f}'.replace('.', 'v').replace('-', 'm')
    voh = f'{oh:.3f}'.replace('.', 'v').replace('-', 'm')

    
    foldname = foldersave +  f'{vwe}_{voh}/'
    command = ''
    for elm in ['*.txt', '*.msh', '*.ff2m']:
        command += 'cp ' + elm + ' ' + foldname + ';'
    subprocess.run(command, shell=True)

    print('ok!')
    return []


def runStability(m, sym, nev, shiftr, shifti, folder='', recompute=True):
    command = 'rm *.txt *.ff2m *.msh; '
    subprocess.run(command, shell=True)

    
    vsym = str(sym).replace('-', 'm')
    vshiftr = f'{shiftr:.3f}'.replace('.', 'v').replace('-', 'm')
    vshifti = f'{shifti:.3f}'.replace('.', 'v').replace('-', 'm')
    
    foldsave = folder + f'eigen_{m}_{vsym}_{nev}_{vshiftr}_{vshifti}/'
    print(foldsave)
    if exists(foldsave):
        print('already exists')
        return []
    
    command = f"mkdir {foldsave}"
    subprocess.run(command, shell=True)
    print('folder created')
    
    command = f"cp {folder}BaseFlow.txt .; cp {folder}mesh.msh ."
    subprocess.run(command, shell=True)
    
    if recompute:#remcompute the base flow
        command = "mv mesh.msh mesh_guess.msh; mv BaseFlow.txt BaseFlow_guess.txt"    
        subprocess.run(command, shell=True)    
        command = "FreeFem++-mpi -v 0 Newton_ALE_StrainedBubble_Fourier_new.edp"
        result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        print('successfully recomputed the base flow')
    
    
    command = f'FreeFem++-mpi -v 0 Stability_FreeSurface_ALE_new.edp  -m {m} -sym {sym}  -nev {nev} -shift_r {shiftr} -shift_i {shifti} -savedata y'

    try:
        ls = subprocess.run([command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
        ls.check_returncode()
    except subprocess.CalledProcessError as e:
        print ( "Error:\nreturn code: ", e.returncode, "\nOutput: ")
        result = ls.stdout.decode("utf-8")
        print(result)
        return result


    command = ''
    for elm in ['*.txt', '*.msh', '*.ff2m']:
        command += 'mv ' + elm + ' ' + foldsave + ';'
    subprocess.run(command, shell=True)
    print('computed!')
    return []

























