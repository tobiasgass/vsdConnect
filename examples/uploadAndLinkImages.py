#!/usr/bin/python

import connectVSD
import sys
import argparse

parser = argparse.ArgumentParser(description='Upload segmentation to  SMIR to a specific folder and set acces rights based on reference object.')
parser.add_argument('--targetFolderID', dest='targetFolder', default="./", required=1,
                   help='ID of folder to store images in')
parser.add_argument('--id', dest='ID', default="./",required=1,
                   help='VSD object ID of original image ')
parser.add_argument('--file', dest='filename', default="./",required=1,
                   help='filename of segmentation to upload')


args=parser.parse_args()
#con=connectVSD.VSDConnecter("username","password")
#con=connectVSD.VSDConnecter()
con=connectVSD.VSDConnecter("ZGVtb0B2aXJ0dWFsc2tlbGV0b24uY2g6ZGVtbw==")
con.seturl("https://demo.virtualskeleton.ch/api/")


print "Uploading ",args.filename
#referenceID=57489
segID=con.uploadSegmentation(int(args.ID),args.filename)
print "done"
print "Copying file to target folder"
con.addFileToFolder(segID,int(args.targetFolder))
#print "Setting permissions based on reference"
#TODO: does not work
#con.setRightsBasedOnReferenceObject(segID,referenceID)
sys.exit()
