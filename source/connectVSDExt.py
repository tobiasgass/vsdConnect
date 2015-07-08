#!/usr/bin/python

# connectVSD 0.1
# (c) Tobias Gass, 2015
# conncetVSD 0.2 python 3 @Michael Kistler 2015
# changed / added auth 

import sys
import math

import json

from connectVSD import VSDConnecter




class VSDConnecterExtension(VSDConnecter):
    def __init__(self, 
        authtype = 'basic',
        url = "https://demo.virtualskeleton.ch/api/",
        username = "demo@virtualskeleton.ch", 
        password = "demo", 
        version = "",
        token = None,
        ):
        super().__init__(authtype,url,username,password,version,token)
        
    def getLinkedSegmentation(self,objectID):
        result=None
        obj=self.getObject(objectID)
        if obj==None:
            return None
        for link in obj.linkedObjects:
            linkedObject=self.getRequest(link['selfUrl'])
            if linkedObject['type']==2:
                result=linkedObject['id']
        return result


    def uploadSegmentation(self,segmentationFilename):
       
        #upload Segmentation and get ID
        segFile=self.chunkFileUpload(segmentationFilename)
 
        if segFile.type!=2:
            print("Error retrieving segmentation object after upload, aborting")
            sys.exit(0)
        return segFile
    
    def addOntologyRelation(self,ontologyRelation):
        oType=ontologyRelation['type']
        result=self.postRequest('/object-ontologies/'+str(oType),ontologyRelation)
        #result2=self.putRequestSimple("/object-ontologies/"+str(oType)+"/"+str(result["id"]))
        return result
    
    def setOntologyBasedOnReferenceObject(self,targetObjectID, origObjectID):
        origObject=self.getObject(origObjectID)

        #add Ontology relations
        for ontRel in origObject.ontologyItemRelations:
           
            ont=self.getRequest(ontRel['selfUrl'])
            newOntRel={}
            newOntRel["object"]={"selfUrl":self.url+'/objects/'+str(targetObjectID)}
            newOntRel["type"]=ont["type"]
            newOntRel["position"]=ont["position"]
            newOntRel["ontologyItem"]=ont["ontologyItem"]
       
            result=self.addOntologyRelation(newOntRel)
            print ("done, result:",result)
           
       

    def setRightsBasedOnReferenceObject(self,objectID,referenceObjectID):
        #get reference object
        referenceObject=self.getObject(referenceObjectID)
        
        #set group rights
        print("Setting group rights")
        if referenceObject.objectGroupRights is not None:
            for right in referenceObject.objectGroupRights:
            #get object
                rightObject=self.getRequest(right["selfUrl"])
               #create new right with the correct objectID
                newRight={}
                newRight["relatedRights"]=rightObject["relatedRights"]
                newRight["relatedGroup"]=rightObject["relatedGroup"]
                newRight["relatedObject"]={"selfUrl":self.url+"/objects/"+str(objectID)}
                self.postRequest("/object-group-rights",newRight)
            
        #set user rights
        print ("Setting user rights")
        if referenceObject.objectUserRights is not None:
            
            for right in referenceObject.objectUserRights:
            #get object
                rightObject=self.getRequest(right["selfUrl"])
            #create new right with the correct objectID
                newRight={}
                newRight["relatedRights"]=rightObject['relatedRights']
                newRight["relatedUser"]=rightObject['relatedUser']
                newRight["relatedObject"]={"selfUrl":self.url+"/objects"+str(objectID)}
                result=self.postRequest("/object-user-rights",newRight)
                print(result)
                                       
        
