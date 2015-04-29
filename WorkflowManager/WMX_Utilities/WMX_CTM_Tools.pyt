###| Copyright 2014 Esri
###|
###| Licensed under the Apache License, Version 2.0 (the "License");
###| you may not use this file except in compliance with the License.
###| You may obtain a copy of the License at
###|
###|    http://www.apache.org/licenses/LICENSE-2.0
###|
###| Unless required by applicable law or agreed to in writing, software
###| distributed under the License is distributed on an "AS IS" BASIS,
###| WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
###| See the License for the specific language governing permissions and
###| limitations under the License.

"""This python toolbox contains tools for
creating a new map for the Fixed 25K Product"""
import arcpy
import os
import sys
import shutil
import zipfile
import datetime
SCRIPTPATH = sys.path[0]
PARENTDIRECTORY = os.path._abspath_split(SCRIPTPATH)
if PARENTDIRECTORY[0] == False:
    SCRIPTSDIRECTORY = os.path.join(PARENTDIRECTORY[1], r"\arcgisserver\MCS_POD\Utilities")
elif PARENTDIRECTORY[0] == True:
    SCRIPTSDIRECTORY = os.path.join(PARENTDIRECTORY[1], r"MCS_POD\Utilities")
sys.path.append(SCRIPTSDIRECTORY)
import Utilities
import CTM_WMX_Utilities

del SCRIPTPATH, PARENTDIRECTORY, SCRIPTSDIRECTORY

class Toolbox(object):
    """Toolbox classes, ArcMap needs this class."""
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the .pyt file)."""
        self.label = "Fixed 25K Tools"
        self.alias = "fixed25kTools"
        # List of tool classes associated with this toolbox
        self.tools = [CreateReplicaFileGDB, ReconcileAndPost, UpdateAOI, ResourceMXD, ExportMapDocumment, ExecuteDataReviewBatchJob, CreateJobFolder, IncreaseReviewLoopCount]

class CreateReplicaFileGDB(object):
    """ Class that contains the code to generate a new map based off the input aoi"""

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create Replica File Geodatabase"
        self.description = "Creates a Checkout Replica File Geodatabase used for CTM WMX Workflows."
        self.canRunInBackground = False

        #Path to the AGS Output Directory
        self.outputdirectory = Utilities.output_directory
        # Path to MCS_POD's Product Location
        self.shared_prod_path = Utilities.shared_products_path

    def getParameterInfo(self):
        """Define parameter definitions"""
        input_job_id = arcpy.Parameter(name="input_job_id",
                                       displayName="Input WMX Job ID",
                                       direction="Input",
                                       datatype="GPLong",
                                       parameterType="Required")
        parent_job_direcotry = arcpy.Parameter(name="job_direcotry",
                                               displayName="Parent Job Direcotry",
                                               direction="Input",
                                               datatype="DEFolder",
                                               parameterType="Required")
        contractor_job = arcpy.Parameter(name="contractor_job",
                                         displayName="Contractor Job",
                                         direction="Input",
                                         datatype="GPBoolean",
                                         parameterType="Optional")
        #input_job_id.value = 56803
        #parent_job_direcotry.value = r"\\sheffieldj\arcgisserver\mcs_pod\WMX\WMX_Jobs\WMX_JOB_56803"
        #contractor_job.value = False
        params = [input_job_id, parent_job_direcotry, contractor_job]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        if arcpy.CheckExtension("foundation") == "Available":
            return True
        return False

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        try:
            #arcpy.CheckOutExtension("foundation")
            #arcpy.CheckOutExtension("JTX")
            arcpy.env.overwriteOutput = True
            scratch_folder = arcpy.env.scratchFolder

            input_job_id = str(parameters[0].value)
            parent_job_direcotry = str(parameters[1].value)
            contractor_job = parameters[2].value

            file_gdb_name = "Job_" + input_job_id + "_Replica"
            job_aoi_layer = "AOILayer_Job" + input_job_id

            arcpy.AddMessage("Getting the Job Workspace.")
            arcpy.GetJobDataWorkspace_wmx(input_job_id, "", scratch_folder)
            parent_workspace = os.path.join(scratch_folder, "JobDataWorkspaceCopy.sde")

            arcpy.env.workspace = parent_workspace

            arcpy.AddMessage("Getting the List of tables and feature class to replicate.")
            table_list = [table for table in arcpy.ListTables() if not table.endswith('_log')]

            feature_class_list = arcpy.ListFeatureClasses()
            feature_dataset_list = arcpy.ListDatasets()

            replica_item_list = ""

            for t in table_list:
                replica_item_list = replica_item_list + str(parent_workspace) + "//" + str(t) + " ALL_ROWS" + ";"
            for fc in feature_class_list:
                replica_item_list = replica_item_list + str(parent_workspace) + "//" + str(fc) + " USE_FILTERS" + ";"
            for fd in feature_dataset_list:
                fc_list = arcpy.ListFeatureClasses("", "", fd)
                for fc in fc_list:
                    replica_item_list = replica_item_list + str(parent_workspace) + "//" + str(fc) + " USE_FILTERS" + ";"
            arcpy.AddMessage("Creating the File Geodatabase for the Check Out Replica.")
            replica_file_gdb = arcpy.CreateFileGDB_management(parent_job_direcotry, file_gdb_name, "CURRENT")

            arcpy.AddMessage("Getting the JOB AOI feature.")
            aoi = arcpy.GetJobAOI_wmx(input_job_id, job_aoi_layer, "")

            arcpy.AddMessage("Creating Check-out Replica.")
            result = arcpy.CreateReplica_production(replica_item_list, 'CHECKOUT', str(replica_file_gdb), "Replica_" + str(input_job_id), 'DO_NOT_REUSE', 'FILTER_BY_GEOMETRY', 'INTERSECTS', aoi, 'FULL', 'NO_ARCHIVING', '#')
            arcpy.AddMessage(result.getMessages())

            if contractor_job == True:
                arcpy.AddMessage("Zipping the Replica File Geodatabase for the contractor.")
                zip_file_name = os.path.join(parent_job_direcotry, file_gdb_name + ".gdb" + ".zip")
                zfile = zipfile.ZipFile(zip_file_name, 'a')
                for root, dirs, files in os.walk(str(replica_file_gdb)):
                    for f in files:
                        zfile.write(os.path.join(root, f), f)
                zfile.close()
                shutil.rmtree(os.path.join(parent_job_direcotry, file_gdb_name + ".gdb"))
                CTM_WMX_Utilities.update_extended_properties(input_job_id, "JOBREPLICA", zip_file_name)
            else:
                CTM_WMX_Utilities.update_extended_properties(input_job_id, "JOBREPLICA", os.path.join(parent_job_direcotry, file_gdb_name + ".gdb"))

            #arcpy.CheckInExtension("foundation")
            return

        except arcpy.ExecuteError:
            arcpy.AddError(arcpy.GetMessages(2))
        except SystemError:
            arcpy.AddError("System Error: " + sys.exc_info()[0])
        except Exception as ex:
            arcpy.AddError("Unexpected Error: " + ex.message)


class ReconcileAndPost(object):
    """ Class that contains the code to generate a new map based off the input aoi"""

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Reconcile and Post Job Version"
        self.description = "Reconcile and Post all changes to the Parent version of the Job."
        self.canRunInBackground = False

        #Path to the AGS Output Directory
        self.outputdirectory = Utilities.output_directory
        # Path to MCS_POD's Product Location
        self.shared_prod_path = Utilities.shared_products_path

    def getParameterInfo(self):
        """Define parameter definitions"""
        input_job_id = arcpy.Parameter(name="input_job_id",
                                       displayName="Input WMX Job ID",
                                       direction="Input",
                                       datatype="GPLong",
                                       parameterType="Required")
        result = arcpy.Parameter(name="result",
                                 displayName="Result",
                                 direction="Output",
                                 datatype="GPString",
                                 parameterType="Derived")
        params = [input_job_id, result]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        if arcpy.CheckExtension("foundation") == "Available":
            return True
        return False

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        try:
            arcpy.env.overwriteOutput = True
            #arcpy.CheckOutExtension("JTX")
            scratch_folder = arcpy.env.scratchFolder

            input_job_id = str(parameters[0].value)

            #Get's the job workspace information
            arcpy.AddMessage("Getting the Job Workspace and Version information.")
            arcpy.GetJobDataWorkspace_wmx(input_job_id, "", scratch_folder)
            job_workspace = os.path.join(scratch_folder, "JobDataWorkspaceCopy.sde")
            parentversion = arcpy.GetJobParentVersion_wmx(input_job_id, "")
            jobversion = arcpy.GetJobVersion_wmx(input_job_id, "")

            #Reconcile Versions
            arcpy.AddMessage("Reconile and Posting the Job version with the Parent Version.")
            result = arcpy.ReconcileVersions_management(job_workspace, "ALL_VERSIONS", parentversion, jobversion, "LOCK_ACQUIRED", "ABORT_CONFLICTS", "BY_OBJECT", "FAVOR_EDIT_VERSION", "POST", "KEEP_VERSION", "")
            arcpy.AddMessage(result.getMessages())
            if "WARNING 000084" in result.getMessages(1):
                parameters[1].value = 1
            else:
                parameters[1].value = 0

            #Post Job Version
            #arcpy.AddMessage("Postin the changes from the Job version to the Parent Version.")
            #result = arcpy.PostJobVersion_wmx(input_job_id, "")
            #arcpy.AddMessage(result.getMessages())
            return

        except arcpy.ExecuteError:
            arcpy.AddError(arcpy.GetMessages(2))
        except SystemError:
            arcpy.AddError("System Error: " + sys.exc_info()[0])
        except Exception as ex:
            arcpy.AddError("Unexpected Error: " + ex.message)


class UpdateAOI(object):
    """ Class that contains the code to generate a new map based off the input aoi"""

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Updates the Date Modified Field"
        self.description = "Updates the date modified field for the AOI for the Production Manager App"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        input_job_id = arcpy.Parameter(name="input_job_id",
                                       displayName="Input WMX Job ID",
                                       direction="Input",
                                       datatype="GPLong",
                                       parameterType="Required")

        aoi_index_layer = arcpy.Parameter(name="aoi_index_layer",
                                          displayName="AOI Index Layer",
                                          direction="Input",
                                          datatype="DEFeatureClass",
                                          parameterType="Required")

        job_type = arcpy.Parameter(name="job_type",
                                   displayName="Job Type",
                                   direction="Input",
                                   datatype="GPString",
                                   parameterType="Required")

        workspace = arcpy.Parameter(name="workspace",
                                    displayName="Production Workspace",
                                    direction="Input",
                                    datatype="DEWorkspace",
                                    parameterType="Required")


        job_type.filter.list = ["Data", "Cartography"]

        params = [input_job_id, aoi_index_layer, job_type, workspace]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        if arcpy.CheckExtension("foundation") == "Available":
            return True
        return False

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        try:
            arcpy.env.overwriteOutput = True
            #arcpy.CheckOutExtension("JTX")
            input_job_id = str(parameters[0].value)
            aoi_index_layer = parameters[1].value
            job_type = parameters[2].value
            workspace = parameters[3].value

            job_aoi_layer = "AOILayer_Job" + input_job_id
            aoi_feature_layer = "aoi_feature_layer"
            date_field_name = "Data_Mod_Date"
            carto_field_name = "Carto_Mod_Date"

            #Get's the job workspace information
            arcpy.AddMessage("Getting the Job AOI.")
            aoi = arcpy.GetJobAOI_wmx(input_job_id, job_aoi_layer, "")

            # Process: Make Feature Layer
            arcpy.MakeFeatureLayer_management(aoi_index_layer, aoi_feature_layer, "", "", "OBJECTID OBJECTID VISIBLE NONE;INDEXMAP10 INDEXMAP10 VISIBLE NONE;INDEXMAP_1 INDEXMAP_1 VISIBLE NONE;MAP_NAME MAP_NAME VISIBLE NONE;MAP_NO MAP_NO VISIBLE NONE;REMARKS REMARKS VISIBLE NONE;REMARKS1 REMARKS1 VISIBLE NONE;Data_Mod_Date Data_Mod_Date VISIBLE NONE;Carto_Mod_Date Carto_Mod_Date VISIBLE NONE;Province Province VISIBLE NONE;Shape Shape VISIBLE NONE;Shape.STArea() Shape.STArea() VISIBLE NONE;Shape.STLength() Shape.STLength() VISIBLE NONE")

            # Process: Select Layer By Location
            arcpy.SelectLayerByLocation_management(aoi_feature_layer, "CONTAINS", aoi, "", "NEW_SELECTION")

            cur_date = datetime.datetime.now()

            update_field = None

            if job_type == "Data":
                update_field = date_field_name
            elif job_type == "Cartography":
                update_field = carto_field_name

            edit = arcpy.da.Editor(workspace)
            edit.startEditing(True, False)
            edit.startOperation()


            with arcpy.da.UpdateCursor(aoi_feature_layer, [update_field]) as ucur_aoi:
                for row in ucur_aoi:
                    row[0] = cur_date
                    ucur_aoi.updateRow(row)


            edit.stopOperation()
            arcpy.AddMessage("The AOI has been successfully updated.")
            edit.stopEditing(True)
            return

        except arcpy.ExecuteError:
            arcpy.AddError(arcpy.GetMessages(2))
        except SystemError:
            arcpy.AddError("System Error: " + sys.exc_info()[0])
        except Exception as ex:
            arcpy.AddError("Unexpected Error: " + ex.message)

class ResourceMXD(object):
    """ Class that contains the code to generate a new map based off the input aoi"""
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Resources Map Document"
        self.description = "Resource the Job MXD."
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        parent_mxd = arcpy.Parameter(name="parent_mxd",
                                     displayName="Parent Map Document",
                                     direction="Input",
                                     datatype="DEMapDocument",
                                     parameterType="Required")

        job_folder = arcpy.Parameter(name="job_folder",
                                     displayName="Job Folder",
                                     direction="Input",
                                     datatype="DEFolder",
                                     parameterType="Required")

        workspace = arcpy.Parameter(name="workspace",
                                    displayName="Job Workspace",
                                    direction="Input",
                                    datatype="DEWorkspace",
                                    parameterType="Required")

        params = [parent_mxd, job_folder, workspace]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        if arcpy.CheckExtension("foundation") == "Available":
            return True
        return False

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        try:
            arcpy.env.overwriteOutput = True

            parent_mxd = str(parameters[0].value)
            job_folder = str(parameters[1].value)
            workspace = str(parameters[2].value)

            arcpy.AddMessage("Coping Parent MXD to the Job Folder.")
            shutil.copy(parent_mxd, job_folder)

            final_mxd_path = os.path.join(job_folder, os.path.basename(parent_mxd))
            final_mxd = arcpy.mapping.MapDocument(final_mxd_path)

            arcpy.AddMessage("Getting the list of data frames.")
            layerlist = arcpy.mapping.ListLayers(final_mxd)
            for layer in layerlist:
                layer.replaceDataSource(workspace, "FILEGDB_WORKSPACE", "", True)

            final_mxd.save()
            return

        except arcpy.ExecuteError:
            arcpy.AddError(arcpy.GetMessages(2))
        except SystemError:
            arcpy.AddError("System Error: " + sys.exc_info()[0])
        except Exception as ex:
            arcpy.AddError("Unexpected Error: " + ex.message)

class ExportMapDocumment(object):
    """ Class that contains the code to generate a new map based off the input aoi"""

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Map Document Export"
        self.description = "Exports the Map Document"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        job_mxd = arcpy.Parameter(name="job_mxd",
                                  displayName="Job Map Document",
                                  direction="Input",
                                  datatype="DEMapDocument",
                                  parameterType="Required")

        job_workspace = arcpy.Parameter(name="job_workspace",
                                        displayName="Job Directory",
                                        direction="Input",
                                        datatype="DEFolder",
                                        parameterType="Required")

        export_type = arcpy.Parameter(name="export_type",
                                      displayName="Export Type",
                                      direction="Input",
                                      datatype="GPString",
                                      parameterType="Required")

        map_name = arcpy.Parameter(name="map_name",
                                   displayName="Map Name",
                                   direction="Input",
                                   datatype="GPString",
                                   parameterType="Required")


        export_type.filter.list = ["PDF", "PRODUCTION PDF", "TIFF"]

        params = [job_mxd, job_workspace, export_type, map_name]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        if arcpy.CheckExtension("foundation") == "Available":
            return True
        return False

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        try:
            arcpy.env.overwriteOutput = True

            job_mxd = str(parameters[0].value)
            output_directory = str(parameters[1].value)
            map_output_type = str(parameters[2].value)
            map_name = parameters[3].value

            final_mxd = arcpy.mapping.MapDocument(job_mxd)
            data_frame = None
            product_location = Utilities.shared_products_path
            arcpy.AddMessage("PDF is: " + map_name)

            file_name = Utilities.export_map_document(product_location, final_mxd,
                                                      map_name, data_frame,
                                                      output_directory, map_output_type)

            arcpy.AddMessage("PDF is: " + file_name)
            return

        except arcpy.ExecuteError:
            arcpy.AddError(arcpy.GetMessages(2))
        except SystemError:
            arcpy.AddError("System Error: " + sys.exc_info()[0])
        except Exception as ex:
            arcpy.AddError("Unexpected Error: " + ex.message)

class ExecuteDataReviewBatchJob(object):
    """ Class that contains the code to generate a new map based off the input aoi"""

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Execute Data Review BatchJob"
        self.description = "Execute Data Review BatchJob"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        reviewer_ws = arcpy.Parameter(name="reviewer_ws",
                                      displayName="Reviewer Workspace",
                                      direction="Input",
                                      datatype="DEWorkspace",
                                      parameterType="Required")

        session = arcpy.Parameter(name="session",
                                  displayName="Reviewer Session",
                                  direction="Input",
                                  datatype="GPString",
                                  parameterType="Required")
        batch_job_file = arcpy.Parameter(name="batch_job_file",
                                         displayName="Batch Job File",
                                         direction="Input",
                                         datatype="DEFile",
                                         parameterType="Required")
        production_ws = arcpy.Parameter(name="production_ws",
                                        displayName="Production Workspace",
                                        direction="Input",
                                        datatype="DEWorkspace",
                                        parameterType="Required")
        result = arcpy.Parameter(name="result",
                                 displayName="Result",
                                 direction="Output",
                                 datatype="GPString",
                                 parameterType="Derived")
        #reviewer_ws.value = r"\\sheffieldj\arcgisserver\mcs_pod\WMX\WMX_Utilities\CTM_DR.sde"
        #session.value = "Session 4904 : 55203"
        #batch_job_file.value = r"C:\Temp\Test_1.rbj"
        #production_ws.value = r"\\sheffieldj\arcgisserver\MCS_POD\WMX\WMX_Jobs\WMX_JOB_60403\Job_60403_Replica.gdb"

        params = [reviewer_ws, session, batch_job_file, production_ws, result]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        if arcpy.CheckExtension("datareviewer") == "Available":
            return True
        return False

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        try:
            arcpy.CheckOutExtension("datareviewer")
            arcpy.env.overwriteOutput = True

            reviewer_ws = parameters[0].value
            session = parameters[1].value
            batch_job_file = parameters[2].value
            production_ws = parameters[3].value

            arcpy.env.workspace = reviewer_ws
            tablelist = arcpy.ListTables()
            rev_table_mian_lyr = None
            rbj_result = None

            session_id = session.split(" ")[1]

            for table in tablelist:
                t = table.split(".")
                lenght = len(t)
                if t[(lenght -1)].upper() == "REVTABLEMAIN":
                    rev_table_mian_lyr = arcpy.MakeTableView_management(table, r"in_memory\rev_table_main_lyr")
                    break

            table_selection = arcpy.SelectLayerByAttribute_management(rev_table_mian_lyr, "NEW_SELECTION", "SESSIONID = " + session_id)
            inital_count = int(arcpy.GetCount_management(table_selection).getOutput(0))
            arcpy.AddMessage("Initial Count is: " + str(inital_count))
            table_selection = arcpy.SelectLayerByAttribute_management(rev_table_mian_lyr, "CLEAR_SELECTION")
            arcpy.AddMessage("Selection has been cleared.")

            result_table = arcpy.ExecuteReviewerBatchJob_Reviewer(reviewer_ws, session, batch_job_file, production_ws)
            arcpy.AddMessage(result_table.getMessages())

            table_selection = arcpy.SelectLayerByAttribute_management(rev_table_mian_lyr, "NEW_SELECTION", "SESSIONID = " + session_id)
            final_count = int(arcpy.GetCount_management(table_selection).getOutput(0))
            arcpy.AddMessage("Final Count is: " +  str(final_count))

            with arcpy.da.SearchCursor(result_table, ["STATUS"]) as scur:
                for row in scur:
                    rbj_result = row[0]
            arcpy.AddMessage("Batch Job Result is: " + str(rbj_result))

            if rbj_result == 0 and (inital_count == final_count):
                parameters[4].value = 0
                arcpy.AddMessage("Batch job executed successfully, and no results were returned.")
            elif rbj_result == 0 and (final_count > inital_count):
                parameters[4].value = 1
                arcpy.AddMessage("Batch job executed successfully, and results were written to the Reviewer session.")
            elif rbj_result == 4:
                parameters[4].value = 2
                arcpy.AddMessage("Batch job failed to execute.")
            elif (rbj_result == 1 or rbj_result == 2 or rbj_result == 3) and (inital_count == final_count):
                parameters[4].value = 3
                arcpy.AddMessage("Batch job executed successfully with errors or warnings, and no results were returned. ")
            elif (rbj_result == 1 or rbj_result == 2 or rbj_result == 3) and (final_count > inital_count):
                parameters[4].value = 4
                arcpy.AddMessage("Batch job executed successfully with errors or warnings, and results were written to the Reviewer session.")
            return

        except arcpy.ExecuteError:
            arcpy.AddError(arcpy.GetMessages(2))
        except SystemError:
            arcpy.AddError("System Error: " + sys.exc_info()[0])
        except Exception as ex:
            arcpy.AddError("Unexpected Error: " + ex.message)

class CreateJobFolder(object):
    """ Class that contains the code to generate a new map based off the input aoi"""

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create Job Folder"
        self.description = "Creates the Job Folder"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        parent_folder = arcpy.Parameter(name="parent_folder",
                                        displayName="Parent Folder",
                                        direction="Input",
                                        datatype="DEFolder",
                                        parameterType="Required")

        job_id = arcpy.Parameter(name="job_id",
                                 displayName="JOB ID",
                                 direction="Input",
                                 datatype="GPString",
                                 parameterType="Required")

        #parent_folder.value = r"\\sheffieldj\arcgisserver\MCS_POD\WMX\WMX_Jobs"
        #job_id.value = 3252

        params = [parent_folder, job_id]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        try:
            arcpy.env.overwriteOutput = True

            parent_folder = parameters[0].value
            job_id = str(parameters[1].value)
            job_folder_name = "WMX_JOB_" + job_id

            arcpy.CreateFolder_management(parent_folder, job_folder_name)
            job_folder = os.path.join(parent_folder.value, job_folder_name)

            CTM_WMX_Utilities.update_extended_properties(job_id, "JOBFOLDER", job_folder)
            return

        except arcpy.ExecuteError:
            arcpy.AddError(arcpy.GetMessages(2))
        except SystemError:
            arcpy.AddError("System Error: " + sys.exc_info()[0])
        except Exception as ex:
            arcpy.AddError("Unexpected Error: " + ex.message)

class IncreaseReviewLoopCount(object):
    """ Class that contains the code to update the Data Review Loop Count."""
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Review Loop Count"
        self.description = "Updates the extended property field for the number of review loops."
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        input_job_id = arcpy.Parameter(name="input_job_id",
                                       displayName="Input WMX Job ID",
                                       direction="Input",
                                       datatype="GPString",
                                       parameterType="Required")
        #input_job_id.value = 69203
        params = [input_job_id]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        try:
            arcpy.env.workspace = CTM_WMX_Utilities.wmx_workspace
            tablelist = arcpy.ListTables()

            job_id = int(parameters[0].value)

            job_id_exisits = False
            extened_table = None
            dataset_versioned = False
            edit = arcpy.da.Editor(CTM_WMX_Utilities.wmx_workspace)

            for table in tablelist:
                t = table.split(".")
                lenght = len(t)
                if t[(lenght-1)].upper() == "JTX_EXT_JOB_REPLICA":
                    extened_table = table
                    with arcpy.da.SearchCursor(table, ["JOBID"]) as scur:
                        for row in scur:
                            table_job_id = row[0]
                            if int(table_job_id) == int(job_id):
                                job_id_exisits = True
                                dataset_versioned = arcpy.Describe(table).isVersioned
                                break
            del scur, row

            if dataset_versioned == True:
                edit.startEditing(True, True)
            else:
                edit.startEditing(True, False)

            edit.startOperation()
            if job_id_exisits == True:
                with arcpy.da.UpdateCursor(extened_table, ["JOBID", "REVCNT"]) as ucur:
                    for row in ucur:
                        table_job_id = row[0]
                        if int(table_job_id) == int(job_id):
                            intial_vlaue = row[1]
                            if intial_vlaue == None:
                                row[1] = 1
                                ucur.updateRow(row)
                                break
                            else:
                                row[1] = int(row[1]) + 1
                                ucur.updateRow(row)
                                break
                del ucur, row
            else:
                incur = arcpy.da.InsertCursor(extened_table, ["JOBID", "DATAREVCNT"])
                incur.insertRow((job_id, 1))
                del incur

            edit.stopOperation()
            edit.stopEditing(True)
            arcpy.AddMessage("The Extended Property Value has been updated")
            return

        except arcpy.ExecuteError:
            arcpy.AddError(arcpy.GetMessages(2))
        except SystemError:
            arcpy.AddError("System Error: " + sys.exc_info()[0])
        except Exception as ex:
            arcpy.AddError("Unexpected Error: " + ex.message)
# For Debugging Python Toolbox Scripts
# comment out when running in ArcMap
#def main():
    #g = DataReviewLoopCount()
    #par = g.getParameterInfo()
    #g.execute(par, None)

#if __name__ == '__main__':
    #main()
