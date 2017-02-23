#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      ambe3073
#
# Created:     07/04/2015
# Copyright:   (c) ambe3073 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import os
import arcpy
import datetime
import arcpywmx


def getfcs(in_workspace):
    """ gets a list of all feature classes in a database, includes feature
    classes inside and outside of the feature datasets"""

    fcs = []

    walk = arcpy.da.Walk(in_workspace, datatype="FeatureClass")

    for dirpath, dirnames, filenames in walk:
        for filename in filenames:
           fcs.append(os.path.join(dirpath, filename))
    arcpy.AddMessage("found " + str(len(fcs)) + " feature classes")
    return fcs



def setEdgeHierarchy(fcs, aoi, hier_field):
    """ sets the hierarchy of all features touching the aoi to 0"""
    arcpy.AddMessage("Setting hierarcy for edge features")
    for fc in fcs:
        fields = [f.name for f in arcpy.ListFields(fc)]
        if hier_field in fields:
            lyr = arcpy.MakeFeatureLayer_management(fc, "layera")
            arcpy.SelectLayerByLocation_management(lyr, "INTERSECT", aoi)
            arcpy.CalculateField_management(lyr, hier_field, "0")
            arcpy.Delete_management(lyr)



def splitLines(in_workspace, job_aoi, names=[]):
    """ gets a list of all feature classes in a database, includes feature
    classes inside and outside of the feature datasets"""

    fcs = []

    walk = arcpy.da.Walk(in_workspace, datatype="FeatureClass")

    for dirpath, dirnames, filenames in walk:
        for filename in filenames:
            if filename in names:
                fc = os.path.join(dirpath, filename)
                split = arcpy.Identity_analysis(fc, job_aoi, "in_memory\\split_"+filename)
                single = arcpy.MultipartToSinglepart_management(split, "in_memory\\split"+filename)
                arcpy.DeleteFeatures_management(fc)
                arcpy.Append_management(single, fc, "NO_TEST")

                arcpy.Delete_management(split)
                arcpy.Delete_management(single)


    return fcs


def updateOverrides(fcs):
    """ loops through all feature classes and applies overrides to the geometry"""
    for fc in fcs:
        arcpy.env.overwriteOutput = True
        arcpy.env.addOutputsToMap = False
        desc = arcpy.Describe(fc)
        rep_name = ""
        if hasattr(desc, "representations"):
            reps = desc.representations
            for rep in reps:
                rep_name = rep.name
                arcpy.AddMessage("Applying Rep Overrides for " + str(fc))
                arcpy.UpdateOverride_cartography(fc, rep_name, "BOTH")
        arcpy.AddMessage("Repairing Geometry for " + str(fc))
        arcpy.RepairGeometry_management(fc)

    return fcs





def create_backup(backup, gen_workspace, output_folder, model, count):
    if backup == 'true':
        arcpy.AddMessage("Creating Backup")
        out = output_folder + '\\after_' +  model + '.gdb'
        arcpy.Copy_management(gen_workspace, out)
    count += 1
    return count

def main():

    arcpy.env.overwriteOutput = True

    if arcpy.CheckExtension("Spatial") != "Available":

        arcpy.AddError("The Spatial Analyst Extension is not available.")
        raise arcpy.ExecuteError
    arcpy.CheckOutExtension('foundation')
    if arcpy.CheckExtension("foundation") != "Available":

        arcpy.AddError("The Production Mapping Extension is not available.")
        raise arcpy.ExecuteError
    arcpy.CheckOutExtension('jtx')
    if arcpy.CheckExtension("jtx") != "Available":

        arcpy.AddError("The Workflow Manager Extension is not available.")
        raise arcpy.ExecuteError

    #get the path of the script being run to determine path of toolbox
    tbx_path = os.path.dirname(__file__)
    tbx = tbx_path + '\\CTM50KGeneralization.tbx'

    arcpy.AddMessage("Toolbox path is: " + tbx)

    #import the toolbox
    arcpy.ImportToolbox(tbx)

    #get the inputs
    input_workspace = arcpy.GetParameterAsText(0)
    job_id = arcpy.GetParameterAsText(1)
    output_folder = arcpy.GetParameterAsText(2)

    product_library = arcpy.GetParameterAsText(3)
    vvs = arcpy.GetParameterAsText(4)
    backup = arcpy.GetParameterAsText(5)
##    backup = 'true'
    arcpy.AddMessage(backup)

    count = 0


    try:
        conn = arcpywmx.Connect()

        if conn:
            job = conn.getJob(int(job_id))
            if job:
                job_name = job.name
                aoi_fc = None

                # add job AOI to database
                if job.hasAOI:
                    job_lyr = arcpy.GetJobAOI_wmx(job_id, "Job_Layer")


                # if the AOI feature class exists in the input feature class, use it
                # the Extract AOI tool creates this feature class and it is the
                # buffered job extent
                if arcpy.Exists(input_workspace + "\\AOI"):
                    aoi_fc = input_workspace + "\\AOI"
                else:
                    # if the AOI feature class does not exist use the Job AOI

                    aoi_fc = job_lyr

##                else:
##                    if arcpy.Exists(input_workspace + "\\AOI"):
##                        aoi_fc = input_workspace + "\\AOI"

                if aoi_fc:
                    gen_name = job_name + "_Generalize"
                    gen_workspace = output_folder + '\\' + gen_name + '.gdb'

                    scratch_db_name = 'scratch'
                    scratch_db = output_folder + '\\' + scratch_db_name + '.gdb'
                    if not arcpy.Exists(scratch_db):
                        arcpy.CreateFileGDB_management(output_folder, scratch_db_name)

                    arcpy.env.workspace = scratch_db



                    #input_path = os.path.dirname(input_workspace)

                    start_start = datetime.datetime.now().replace(microsecond=0)

                    #create the output database
                    arcpy.AddMessage("Creating generalization database")
            ##
                    if arcpy.Exists(gen_workspace):
                        arcpy.Delete_management(gen_workspace)
                    arcpy.Copy_management(input_workspace, gen_workspace)

                    #Creating the Scratch workspace
                    #scratch_workspace = arcpy.CreateFileGDB_management(output_folder, "Scratch")
                    scratch_workspace = 'in_memory'

                    #Run the prepare script
                    arcpy.AddMessage("Running Prepare Model")

                    start = datetime.datetime.now().replace(microsecond=0)

                    arcpy.PrepareData_CTM50KGeneralization(gen_workspace, scratch_workspace, aoi_fc, vvs)
                    end = datetime.datetime.now().replace(microsecond=0)
                    arcpy.AddMessage(arcpy.GetMessages())
                    arcpy.AddMessage("Took " + str(end - start))

                    arcpy.AddMessage("Prepping Transportation")
                    splitLines(gen_workspace, job_lyr, names=['TransportationGroundCrv'])

                    #Run the transportation script
                    arcpy.AddMessage("Running Transportation Model")
                    start = datetime.datetime.now().replace(microsecond=0)
                    arcpy.Transportation_CTM50KGeneralization(gen_workspace, scratch_workspace)
                    arcpy.AddMessage(arcpy.GetMessages())
                    end = datetime.datetime.now().replace(microsecond=0)
                    arcpy.AddMessage(arcpy.GetMessages())
                    arcpy.AddMessage("Took " + str(end - start))



                    #Run the buildings script
                    arcpy.AddMessage("Running Building Model")
                    start = datetime.datetime.now().replace(microsecond=0)
                    arcpy.Buildings_CTM50KGeneralization(gen_workspace, scratch_workspace)
                    arcpy.AddMessage(arcpy.GetMessages())
                    end = datetime.datetime.now().replace(microsecond=0)
                    arcpy.AddMessage(arcpy.GetMessages())
                    arcpy.AddMessage("Took " + str(end - start))



                    #Run the hydro script
                    arcpy.AddMessage("Running Hydrography Model")
                    start = datetime.datetime.now().replace(microsecond=0)
                    arcpy.Hydro_CTM50KGeneralization(gen_workspace, scratch_workspace, scratch_db)
                    arcpy.AddMessage(arcpy.GetMessages())
                    end = datetime.datetime.now().replace(microsecond=0)
                    arcpy.AddMessage(arcpy.GetMessages())
                    arcpy.AddMessage("Took " + str(end - start))



                    #Run the Land Cover script
                    arcpy.AddMessage("Running Land Cover Model")
                    start = datetime.datetime.now().replace(microsecond=0)
                    arcpy.arcpy.LandCov_CTM50KGeneralization(gen_workspace, scratch_workspace, scratch_db)
                    arcpy.AddMessage(arcpy.GetMessages())
                    end = datetime.datetime.now().replace(microsecond=0)
                    arcpy.AddMessage(arcpy.GetMessages())
                    arcpy.AddMessage("Took " + str(end - start))



                    #Run the Elev script
                    arcpy.AddMessage("Running Elevation Model")
                    start = datetime.datetime.now().replace(microsecond=0)
                    arcpy.Elev_CTM50KGeneralization(gen_workspace, scratch_db)
                    arcpy.AddMessage(arcpy.GetMessages())
                    end = datetime.datetime.now().replace(microsecond=0)
                    arcpy.AddMessage(arcpy.GetMessages())
                    arcpy.AddMessage("Took " + str(end - start))



                    #Run the Symbology script
                    arcpy.AddMessage("Running Apply Symbology Model")
                    start = datetime.datetime.now().replace(microsecond=0)
                    arcpy.ApplySymbology_CTM50KGeneralization(gen_workspace, product_library, vvs)
                    arcpy.AddMessage(arcpy.GetMessages())
                    end = datetime.datetime.now().replace(microsecond=0)
                    arcpy.AddMessage(arcpy.GetMessages())
                    arcpy.AddMessage("Took " + str(end - start))


                    #update hierarchy for edge features
                    feature_classes = getfcs(gen_workspace)
                    job_lines = arcpy.FeatureToLine_management(job_lyr, "job_lines")
                    setEdgeHierarchy(feature_classes, job_lines, "Hierarchy")



                    #Run the line conflicts script
                    arcpy.AddMessage("Running Line Conflicts Model")
                    start = datetime.datetime.now().replace(microsecond=0)
                    arcpy.ResolveLine_CTM50KGeneralization(gen_workspace, scratch_workspace)
                    arcpy.AddMessage(arcpy.GetMessages())
                    end = datetime.datetime.now().replace(microsecond=0)
                    arcpy.AddMessage(arcpy.GetMessages())
                    arcpy.AddMessage("Took " + str(end - start))



                    #Run the point conflicts script
                    arcpy.AddMessage("Running Structure Conflicts Model")
                    start = datetime.datetime.now().replace(microsecond=0)
                    arcpy.ResolveStructure_CTM50KGeneralization(gen_workspace)
                    arcpy.AddMessage(arcpy.GetMessages())
                    end = datetime.datetime.now().replace(microsecond=0)
                    arcpy.AddMessage(arcpy.GetMessages())
                    arcpy.AddMessage("Took " + str(end - start))



                    #Run the hydro conflicts script
                    arcpy.AddMessage("Running Hydro Conflicts Model")
                    start = datetime.datetime.now().replace(microsecond=0)
                    arcpy.ResolveHydro_CTM50KGeneralization(gen_workspace, scratch_db)
                    arcpy.AddMessage(arcpy.GetMessages())
                    end = datetime.datetime.now().replace(microsecond=0)
                    arcpy.AddMessage(arcpy.GetMessages())
                    arcpy.AddMessage("Took " + str(end - start))



                    #Run the veg conflicts script
                    arcpy.AddMessage("Running Vegetation Conflicts Model")
                    start = datetime.datetime.now().replace(microsecond=0)
                    arcpy.ResolveVeg_CTM50KGeneralization(gen_workspace, scratch_workspace)
                    arcpy.AddMessage(arcpy.GetMessages())
                    end = datetime.datetime.now().replace(microsecond=0)
                    arcpy.AddMessage(arcpy.GetMessages())
                    arcpy.AddMessage("Took " + str(end - start))



                    arcpy.AddMessage("Creating Backup")
                    out = output_folder + '\\' + job_name + 'after_generalization.gdb'
                    arcpy.Copy_management(gen_workspace, out)

                    #final updates
                    feature_classes = getfcs(gen_workspace)
                    updateOverrides(feature_classes)


                else:
                    arcpy.AddError("Job " + str(job_id) + " does not have an area of interest.")
            else:
                arcpy.AddMessage("Unable to find job " + str(job_id))
        else:
            arcpy.AddError("Cannot connect to Workflow Manager.  Ensure you have a default Workflow Manager connection.")
    except:
        arcpy.AddError("Unknown error running generalization models.")
        arcpy.AddError(arcpy.GetMessages(2))

    finally:

        end_end = datetime.datetime.now().replace(microsecond=0)

        arcpy.AddMessage("Took Total " + str(end_end - start_start))




if __name__ == '__main__':
    main()
