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


scratch_workspace = arcpy.GetParameterAsText(2)
scratch_path = os.path.dirname(scratch_workspace)


def create_backup(backup, gen_workspace, model, count):
    if backup == 'true':
        arcpy.AddMessage("Creating Backup")
        out = scratch_path + '\\after_' + str(count) + '_' + model + '.gdb'
        arcpy.Copy_management(gen_workspace, out)
    count += 1
    return count

def main():

    arcpy.env.overwriteOutput = True


    #get the path of the script being run to determine path of toolbox
    tbx_path = os.path.dirname(__file__)
    tbx = tbx_path + '\\CTM50KGeneralization.tbx'

    print(tbx)

    #import the toolbox
    arcpy.ImportToolbox(tbx)

    #get the inputs
    input_workspace = arcpy.GetParameterAsText(0)
    output_name = arcpy.GetParameterAsText(1)
    scratch_workspace = arcpy.GetParameterAsText(2)
    product_library = arcpy.GetParameterAsText(3)
    aoi_fc = arcpy.GetParameterAsText(4)
    backup = arcpy.GetParameterAsText(5)

    count = 0

##    scratch_path = os.path.dirname(scratch_workspace)
    input_path = os.path.dirname(input_workspace)

    start_start = datetime.datetime.now().replace(microsecond=0)

    #create the output database
    arcpy.AddMessage("Creating generalization database")
    gen_workspace = input_path + '\\' + output_name + '.gdb'
    arcpy.Copy_management(input_workspace, gen_workspace)


    #Run the prepare script
    arcpy.AddMessage("Running Prepare Model")


    start = datetime.datetime.now().replace(microsecond=0)

    arcpy.PrepareData_CTM50KGeneralization(gen_workspace, scratch_workspace, product_library)
    end = datetime.datetime.now().replace(microsecond=0)
    arcpy.AddMessage(arcpy.GetMessages())
    arcpy.AddMessage("Took " + str(end - start))


    count = create_backup(backup, gen_workspace, 'PrepareData', count)




    #Run the transportation script
    arcpy.AddMessage("Running Transportation Model")
    start = datetime.datetime.now().replace(microsecond=0)
    arcpy.arcpy.Transportation_CTM50KGeneralization(gen_workspace, scratch_workspace)
    arcpy.AddMessage(arcpy.GetMessages())
    end = datetime.datetime.now().replace(microsecond=0)
    arcpy.AddMessage(arcpy.GetMessages())
    arcpy.AddMessage("Took " + str(end - start))

    count = create_backup(backup, gen_workspace, 'Transportation', count)

    #Run the buildings script
    arcpy.AddMessage("Running Building Model")
    start = datetime.datetime.now().replace(microsecond=0)
    arcpy.arcpy.Buildings_CTM50KGeneralization(gen_workspace, scratch_workspace)
    arcpy.AddMessage(arcpy.GetMessages())
    end = datetime.datetime.now().replace(microsecond=0)
    arcpy.AddMessage(arcpy.GetMessages())
    arcpy.AddMessage("Took " + str(end - start))

    count = create_backup(backup, gen_workspace, 'Building', count)

    #Run the hydro script
    arcpy.AddMessage("Running Hydrography Model")
    start = datetime.datetime.now().replace(microsecond=0)
    arcpy.arcpy.Hydro_CTM50KGeneralization(gen_workspace, scratch_workspace)
    arcpy.AddMessage(arcpy.GetMessages())
    end = datetime.datetime.now().replace(microsecond=0)
    arcpy.AddMessage(arcpy.GetMessages())
    arcpy.AddMessage("Took " + str(end - start))

    count = create_backup(backup, gen_workspace, 'Hydro', count)

    #Run the Land Cover script
    arcpy.AddMessage("Running Land Cover Model")
    start = datetime.datetime.now().replace(microsecond=0)
    arcpy.arcpy.LandCov_CTM50KGeneralization(gen_workspace, scratch_workspace)
    arcpy.AddMessage(arcpy.GetMessages())
    end = datetime.datetime.now().replace(microsecond=0)
    arcpy.AddMessage(arcpy.GetMessages())
    arcpy.AddMessage("Took " + str(end - start))

    count = create_backup(backup, gen_workspace, 'LandCov', count)


    #Run the Elev script
    arcpy.AddMessage("Running Elevation Model")
    start = datetime.datetime.now().replace(microsecond=0)
    arcpy.arcpy.Elev_CTM50KGeneralization(gen_workspace, scratch_workspace, 100, 500, aoi_fc)
    arcpy.AddMessage(arcpy.GetMessages())
    end = datetime.datetime.now().replace(microsecond=0)
    arcpy.AddMessage(arcpy.GetMessages())
    arcpy.AddMessage("Took " + str(end - start))

    count = create_backup(backup, gen_workspace, 'Elev', count)

    #Run the Symbology script
    arcpy.AddMessage("Running Apply Symbology Model")
    start = datetime.datetime.now().replace(microsecond=0)
    arcpy.arcpy.ApplySymbology_CTM50KGeneralization(gen_workspace, product_library)
    arcpy.AddMessage(arcpy.GetMessages())
    end = datetime.datetime.now().replace(microsecond=0)
    arcpy.AddMessage(arcpy.GetMessages())
    arcpy.AddMessage("Took " + str(end - start))

    count = create_backup(backup, gen_workspace, 'Symbology', count)

    #Run the line conflicts script
    arcpy.AddMessage("Running Line Conflicts Model")
    start = datetime.datetime.now().replace(microsecond=0)
    arcpy.arcpy.ResolveLine_CTM50KGeneralization(gen_workspace, scratch_workspace)
    arcpy.AddMessage(arcpy.GetMessages())
    end = datetime.datetime.now().replace(microsecond=0)
    arcpy.AddMessage(arcpy.GetMessages())
    arcpy.AddMessage("Took " + str(end - start))

    count = create_backup(backup, gen_workspace, 'ResolveLine', count)

    #Run the point conflicts script
    arcpy.AddMessage("Running Structure Conflicts Model")
    start = datetime.datetime.now().replace(microsecond=0)
    arcpy.arcpy.ResolveStructure_CTM50KGeneralization(gen_workspace)
    arcpy.AddMessage(arcpy.GetMessages())
    end = datetime.datetime.now().replace(microsecond=0)
    arcpy.AddMessage(arcpy.GetMessages())
    arcpy.AddMessage("Took " + str(end - start))

    count = create_backup(backup, gen_workspace, 'ResolveStructure', count)


    #Run the hydro conflicts script
    arcpy.AddMessage("Running Hydro Conflicts Model")
    start = datetime.datetime.now().replace(microsecond=0)
    arcpy.arcpy.ResolveHydro_CTM50KGeneralization(gen_workspace, scratch_workspace)
    arcpy.AddMessage(arcpy.GetMessages())
    end = datetime.datetime.now().replace(microsecond=0)
    arcpy.AddMessage(arcpy.GetMessages())
    arcpy.AddMessage("Took " + str(end - start))

    count = create_backup(backup, gen_workspace, 'ResolveHydro', count)

    end_end = datetime.datetime.now().replace(microsecond=0)

    arcpy.AddMessage("Took Total " + str(end_end - start_start))
    arcpy.SetParameter(6, gen_workspace)
    pass

if __name__ == '__main__':
    main()
