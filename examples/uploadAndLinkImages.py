#!/usr/bin/python

import connectVSD
import sys
import argparse
import json

parser = argparse.ArgumentParser(description='Upload segmentation files to the SMIR to a specific folder, optionally link to source image and create ontology based on a reference segmentation object.')
parser.add_argument('--targetFolderID', dest='targetFolder', default="./", required=0,
                   help='ID of folder to store images in')
parser.add_argument('--id', dest='ID', default="./",required=1,
                   help='VSD object ID of original image ')
parser.add_argument('--referenceSegID', dest='referenceSegID', default="./",required=0,
                   help='VSD object ID of reference segmentation object for passing the ontology ')
parser.add_argument('--file', dest='filename', default="./",required=1,
                   help='filename of segmentation to upload')


args=parser.parse_args()
#con=connectVSD.VSDConnecter("username","password")
#con=connectVSD.VSDConnecter()



print "Uploading ",args.filename
#referenceID=57489
segID=con.uploadSegmentation(int(args.ID),args.filename)
con.addLink(segID,args.ID)
print "done"

if args.referenceSegID==None:
    args.referenceSegID=con.getLinkedSegmentation(args.ID)
if args.referenceSegID==None:
    print "No reference seg ID was given on command line or could be found in the database, skipping ontology setting"
else:
    con.setOntologyBasedOnReferenceObject(segID,args.referenceSegID)

if (args.targetFolder != None):
    print "Copying file to target folder"
    con.addFileToFolder(segID,int(args.targetFolder))

#print "Setting permissions based on reference"
#con.setRightsBasedOnReferenceObject(segID,args.ID)
sys.exit()
