#!/usr/bin/python

import connectVSD
import sys
import argparse
import json

parser = argparse.ArgumentParser(description='Download original image files from SMIR to a specific folder.')
parser.add_argument('--targetFolderID', dest='targetFolder', default="./", required=1,
                   help='ID of folder to store images in')
parser.add_argument('--id', dest='ID', default="./",required=1,
                   help='VSD object ID of original image ')
parser.add_argument('--referenceSegID', dest='referenceSegID', default="./",required=1,
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
con.setOntologyBasedOnReferenceObject(segID,args.referenceSegID)
print "done"
print "Copying file to target folder"
con.addFileToFolder(segID,int(args.targetFolder))
#print "Setting permissions based on reference"
#con.setRightsBasedOnReferenceObject(segID,referenceID)
sys.exit()
