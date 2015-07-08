#!/usr/bin/python

import connectVSDExt
import sys
import argparse
from pathlib import Path, PurePath, WindowsPath

parser = argparse.ArgumentParser(description='Upload segmentation files to the SMIR to a specific folder, optionally link to source image and create ontology based on a reference segmentation object.')
parser.add_argument('--targetFolderID', dest='targetFolder', default=None, required=0,
                   help='ID of folder to store images in')
parser.add_argument('--id', dest='ID', default="./",required=1,
                   help='VSD object ID of original image ')
parser.add_argument('--referenceSegID', dest='referenceSegID', default=None,required=0,
                   help='VSD object ID of reference segmentation object for passing the ontology ')
parser.add_argument('--file', dest='filename', default=None,required=1,
                   help='filename of segmentation to upload')


args=parser.parse_args()
con=connectVSDExt.VSDConnecterExtension()


segmentationOfOriginalObject=con.getLinkedSegmentation(args.ID)
if (segmentationOfOriginalObject!=None):
    print("Segmentation of image already exists, aborting")
    sys.exit(0)


print("Uploading ",args.filename)
segmentationObject=con.uploadSegmentation(Path(args.filename))
segID=segmentationObject.id
originalImageObject=con.getObject(int(args.ID))
con.addLink(segmentationObject,originalImageObject)
print("done")

if args.referenceSegID==None:
    args.referenceSegID=con.getLinkedSegmentation(int(args.ID))
if args.referenceSegID==None:
    print("No reference seg ID was given on command line or could be found in the database, skipping ontology setting")
else:
    con.setOntologyBasedOnReferenceObject(int(segID),int(args.referenceSegID))

if (args.targetFolder != None):
    folder=con.getFolder(int(args.targetFolder))
    print("Copying file to target folder")
    con.addObjectToFolder(segmentationObject,folder)

print ("Setting permissions based on reference")
con.setRightsBasedOnReferenceObject(segID,int(args.ID))
sys.exit()
