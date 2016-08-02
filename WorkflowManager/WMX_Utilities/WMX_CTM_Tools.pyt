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
import arcpywmx

# Global Variables
extended_propert_table = "CTM_WMX_Development.DBO.CTM_EXT_JOB_REPLICA"

class Utilities_WMX(object):
    
    # Logic to update the extended property values for WMX Jobs
    def update_extended_properties(self, job_id, extended_property_field, field_value):
        arcpy.CheckOutExtension('JTX')
        arcpy.AddMessage("Updating the job extended properties.")
            
        wmx_connection = arcpywmx.Connect()
        job = wmx_connection.getJob(int(job_id))
        extended_property_table = job.getExtendedPropertyTable(extended_propert_table)
        extended_property_table[extended_property_field].data = field_value
        job.save()

        return
    
    def get_geodatabase_path(self, input_table):
        '''Return the Geodatabase path from the input table or feature class.
        :param input_table: path to the input table or feature class 
        '''
        workspace = os.path.dirname(input_table)
        if [any(ext) for ext in ('.gdb', '.mdb', '.sde') if ext in os.path.splitext(workspace)]:
            return workspace
        else:
            return os.path.dirname(workspace)    

class Toolbox(object):
    """Toolbox classes, ArcMap needs this class."""
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the .pyt file)."""
        self.label = "Fixed 25K Tools"
        self.alias = "fixed25kTools"
        # List of tool classes associated with this toolbox
        self.tools = [CreateReplicaFileGDB, ReconcileAndPost, UpdateAOIDate, ResourceMXD, ExportMapDocumment, CreateJobFolder, IncreaseReviewLoopCount, CreateDataReviewerDatabase]

class CreateReplicaFileGDB(object):
    """ Class that contains the code to generate a new map based off the input aoi"""

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create Replica File Geodatabase"
        self.description = "Creates a Checkout Replica File Geodatabase used for CTM WMX Workflows."
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        input_job_id = arcpy.Parameter(name="input_job_id",
                                       displayName="Input WMX Job ID",
                                       direction="Input",
                                       datatype="GPLong",
                                       parameterType="Required")
        job_directory = arcpy.Parameter(name="job_directory",
                                               displayName="Job Directory",
                                               direction="Input",
                                               datatype="DEFolder",
                                               parameterType="Required")
        contractor_job = arcpy.Parameter(name="contractor_job",
                                         displayName="Contractor Job",
                                         direction="Input",
                                         datatype="GPBoolean",
                                         parameterType="Optional")
        #input_job_id.value = 2031
        #job_directory.value = r"C:\Data\MCS_POD\WorkflowManager\WMX_Store\WMX_JOB_2031"
        #contractor_job.value = True
        params = [input_job_id, job_directory, contractor_job]
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
            arcpy.CheckOutExtension("foundation")
            arcpy.CheckOutExtension("JTX")
            arcpy.env.overwriteOutput = True
            scratch_folder = arcpy.env.scratchFolder

            input_job_id = str(parameters[0].value)
            parent_job_directory = str(parameters[1].value)
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
            replica_file_gdb = arcpy.CreateFileGDB_management(parent_job_directory, file_gdb_name, "CURRENT")

            arcpy.AddMessage("Getting the JOB AOI feature.")
            aoi = arcpy.GetJobAOI_wmx(input_job_id, job_aoi_layer, "")

            arcpy.AddMessage("Creating Check-out Replica.")
            result = arcpy.CreateReplica_production(replica_item_list, 'CHECKOUT', str(replica_file_gdb), "Replica_" + str(input_job_id), 'DO_NOT_REUSE', 'FILTER_BY_GEOMETRY', 'INTERSECTS', aoi, 'FULL', 'NO_ARCHIVING', '#')
            arcpy.AddMessage(result.getMessages())

            utilities_class = Utilities_WMX()           

            if contractor_job == True:
                arcpy.AddMessage("Coping the JOB AOI into the Replica Database.")
                
                output_fc = os.path.join(str(replica_file_gdb), "Job_AOI")
                arcpy.CopyFeatures_management(aoi, output_fc)
                
                arcpy.AddMessage("Zipping the Replica File Geodatabase for the contractor.")
                zip_file_name = os.path.join(parent_job_directory, file_gdb_name + ".gdb" + ".zip")
                zfile = zipfile.ZipFile(zip_file_name, 'a')
                for root, dirs, files in os.walk(str(replica_file_gdb)):
                    for f in files:
                        zfile.write(os.path.join(root, f), f)
                zfile.close()
                shutil.rmtree(os.path.join(parent_job_directory, file_gdb_name + ".gdb"))

            arcpy.AddMessage("Updating the Job's extended properties.")
            utilities_class.update_extended_properties(input_job_id, "JOBREPLICA", os.path.join(parent_job_directory, file_gdb_name + ".gdb"))   
            utilities_class.update_extended_properties(input_job_id, "SDE_REPLICA", int(1))                
                
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


class UpdateAOIDate(object):
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

        job_type.filter.list = ["Data", "Cartography"]
        
        #input_job_id.value = 1
        #aoi_index_layer.value = r'Database Connections\Connection to ps000818_sqlexpress.sde\CTM_Data.DBO.Reference_Layer\CTM_Data.DBO.AOIs_24K'
        #job_type.value = "Data"

        params = [input_job_id, aoi_index_layer, job_type]
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
            arcpy.CheckOutExtension("JTX")
            
            input_job_id = str(parameters[0].value)
            aoi_index_layer = parameters[1].value
            job_type = parameters[2].value
            #workspace = parameters[3].value
            
            utilities_class = Utilities_WMX()

            aoi_index_layer_path = arcpy.Describe(aoi_index_layer).path
            
            workspace = utilities_class.get_geodatabase_path(aoi_index_layer_path)

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
            
            count = arcpy.GetCount_management(aoi_feature_layer)
            
            if int(count.getOutput(0)) == 1:
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
            else:
                arcpy.AddError("The Job AOI is contained by more than 1 AOI in the Index layer.  This Job does not match a single AOI.")
                raise arcpy.ExecuteError
            
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
        input_job_id = arcpy.Parameter(name="input_job_id",
                                       displayName="Input WMX Job ID",
                                       direction="Input",
                                       datatype="GPLong",
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

        #input_job_id.value = 6
        #job_folder.value = r"C:\Data\MCS_POD\WorkflowManager\WMX_Store\WMX_JOB_6"
        #workspace.value = r"C:\Data\MCS_POD\WorkflowManager\WMX_Store\WMX_JOB_6\Job_6_Replica.gdb"
        
        params = [input_job_id, job_folder, workspace]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return

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

            input_job_id = str(parameters[0].value)
            job_folder = str(parameters[1].value)
            workspace = str(parameters[2].value)
            
            arcpy.AddMessage("The job folder value is: " + job_folder)
            arcpy.AddMessage("The job workspace value is: " + workspace)
            
            #arcpy.CheckOutExtension('JTX')
            
            wmx_connection = arcpywmx.Connect()
            arcpy.AddMessage("Establish connection to the default WMX configuration on this machine.")
            job = wmx_connection.getJob(int(input_job_id)) 
            arcpy.AddMessage("Retervied the WMX Job Object.")
            
            # Retrives the Job Map Document and saves it to the Job Folder
            mxd_path = (os.path.join(job_folder, "JOB_" + str(job.ID) + ".mxd"))
            job.retrieveJobMap(mxd_path)
            arcpy.AddMessage("Extracted the job mxd to the job folder.")

            # Gets the MXD object
            job_mxd = arcpy.mapping.MapDocument(mxd_path)
            arcpy.AddMessage("Reterieved the MXD Object.")

            arcpy.AddMessage("Getting the list of data frames.")
            layerlist = arcpy.mapping.ListLayers(job_mxd)
            for layer in layerlist:
                if layer.isGroupLayer != True:
                    arcpy.AddMessage("Resourcing layer: " + layer.name)
                    layer.replaceDataSource(workspace, "FILEGDB_WORKSPACE", "", True)
            arcpy.AddMessage("The Data Source has been updated for each layer.")

            job_mxd.save()
            job.storeJobMap(job_mxd.filePath)
            job.save()
            arcpy.AddMessage("The MXD has been saved back to the job.")
            
            del job_mxd
            del job
            arcpy.Delete_management(mxd_path)
            
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
            product_location = CTM_WMX_Utilities.shared_products_path
            arcpy.AddMessage("PDF is: " + map_name)

            file_name = CTM_WMX_Utilities.export_map_document(product_location, final_mxd,
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
                                        datatype="GPString",
                                        parameterType="Required")

        job_id = arcpy.Parameter(name="job_id",
                                 displayName="JOB ID",
                                 direction="Input",
                                 datatype="GPString",
                                 parameterType="Required")

        #parent_folder.value = r"C:\Data\MCS_POD\WorkflowManager\WMX_Store"
        #job_id.value = 1603

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
            
            if arcpy.Exists(parent_folder) != True:
                arcpy.AddWarning(parent_folder + " doesn't exist, the WMX_Store folder will be created.")
                parent_directory = os.path.dirname(parent_folder)
                arcpy.CreateFolder_management(parent_directory, "WMX_Store")
                arcpy.CreateFolder_management(parent_folder, job_folder_name)
    
            elif arcpy.Exists(os.path.join(parent_folder, job_folder_name)) == True:
                arcpy.AddWarning("Job folder " + job_folder_name + " already eixsts in " + str(parent_folder) + ".")
                arcpy.AddWarning("Using the job folder that already exists.")
            else:
                arcpy.AddMessage("Creating the job folder: " + str(job_folder_name))
                arcpy.CreateFolder_management(parent_folder, job_folder_name)
            
            job_folder = os.path.join(parent_folder, job_folder_name)
            
            utilities_class = Utilities_WMX()
            utilities_class.update_extended_properties(job_id, "JOBFOLDER", job_folder)
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
        
        reviewer_ws = arcpy.Parameter(name="reviewer_ws",
                                      displayName="Reviewer Workspace",
                                      direction="Input",
                                      datatype="DEWorkspace",
                                      parameterType="Required")        
        session_id = arcpy.Parameter(name="session_id",
                          displayName="Reviewer Session ID",
                          direction="Input",
                          datatype="GPString",
                          parameterType="Required")
        
        #input_job_id.value = 21
        #session_id.value = 5609
        #reviewer_ws.value = r"C:\Data\MCS_POD\WorkflowManager\Database Configuration\CTM_DataReviewer.sde"
        
        params = [input_job_id, reviewer_ws, session_id]
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
            arcpy.CheckOutExtension('JTX')
            
            #Updating the Extending property for the Job
            job_id = parameters[0].value
            
            
            wmx_connection = arcpywmx.Connect()
            job = wmx_connection.getJob(int(job_id))
            extended_property_table = job.getExtendedPropertyTable(extended_propert_table)
            extended_property_field = 'REVCNT'
            data_reviewer_loop_count = None
            data_reviewer_loop_count = extended_property_table[extended_property_field].data
            if data_reviewer_loop_count != None:
                data_reviewer_loop_count = data_reviewer_loop_count + 1
            else:
                data_reviewer_loop_count = 1
            extended_property_table[extended_property_field].data = data_reviewer_loop_count
            job.save()
            
            #Updating the WMX JOB Id value in the Data Reviewer Table            
            dr_workspace = parameters[1].value
            dr_session_id = parameters[2].value
            
            arcpy.env.workspace = dr_workspace
        
            arcpy.AddMessage("Getting the List of tables and feature class to replicate.")
            table_list = [table for table in arcpy.ListTables() if table.endswith('REVTABLEMAIN')]
            
            rev_table_main = table_list[0]
            rev_table_main_layer = "rev_table_main_layer"
            
            #arcpy.MakeFeatureLayer_management(str(dr_workspace) + "\\" + rev_table_main, rev_table_main_layer)
            
            field_list = arcpy.ListFields(rev_table_main)
            field_list_temp = []
            for field in field_list:
                field_list_temp.append(field.name)
                
            
            wmx_job_id_field = "WMX_JOB_ID"
            if wmx_job_id_field not in field_list_temp:
                arcpy.AddError("The WMX_Job_Id field is missing from the Data Reviewer REVTABLEMAIN")
                arcpy.ExecuteError()
       
            edit = arcpy.da.Editor(dr_workspace)
            edit.startEditing(True, False)
            edit.startOperation()
    
            with arcpy.da.UpdateCursor(rev_table_main, [wmx_job_id_field, "SESSIONID"]) as ucur_dr:
                for row in ucur_dr:
                    print "Session ID is: " + str(row[1])
                    if str(row[1]) == str(dr_session_id):
                        if row[0] != job_id:
                            row[0] = job_id
                            ucur_dr.updateRow(row)
    
            edit.stopOperation()
            arcpy.AddMessage("The Loop Count and Job.")
            edit.stopEditing(True)            

            return

        except arcpy.ExecuteError:
            arcpy.AddError(arcpy.GetMessages(2))
        except SystemError:
            arcpy.AddError("System Error: " + sys.exc_info()[0])
        except Exception as ex:
            arcpy.AddError("Unexpected Error: " + ex.message)
            
class CreateDataReviewerDatabase(object):
    """ Class that contains the code to generate a new map based off the input aoi"""

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create Data Reviewer Database"
        self.description = "Creates and Enables a new File Geodatabase as a Data Reviewer Workspace"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        input_job_id = arcpy.Parameter(name="input_job_id",
                                       displayName="Input WMX Job ID",
                                       direction="Input",
                                       datatype="GPLong",
                                       parameterType="Required")
        job_directory = arcpy.Parameter(name="job_directory",
                                        displayName="Job Directory",
                                        direction="Input",
                                        datatype="DEFolder",
                                        parameterType="Required")   
        
        #input_job_id.value = 2033
        #job_directory.value = r"C:\Data\MCS_POD\WorkflowManager\WMX_Store\WMX_JOB_2033"
        params = [input_job_id, job_directory]
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
            job_id = parameters[0].value
            job_directory = str(parameters[1].value)
            
            arcpy.AddMessage("Creating the new File Geodatabase.")
            if arcpy.Exists(os.path.join(job_directory, "DataReviewer_Job_" + str(job_id) + ".gdb")) == True:
                arcpy.AddError("Data Reviewer Workspace already exists in the Job Directory.")
                raise arcpy.ExecuteError 
            
            result = arcpy.CreateFileGDB_management(job_directory, "DataReviewer_Job_" + str(job_id))
            dr_workspace = result.getOutput(0)
            
            arcpy.AddMessage("Enabling Data Reviewer on the new File Geodatbase.")
            arcpy.AddMessage("Using GCS_WGS_1984 for the spatial reference on the Data Reviewer Workspace.")
            arcpy.EnableDataReviewer_Reviewer(dr_workspace)
            
            arcpy.AddMessage("Updating the Job's Extended Properties.")
            utilities_class = Utilities_WMX()  
            utilities_class.update_extended_properties(job_id, "DR_WORKSPACE", dr_workspace)   
            
            
            
        except arcpy.ExecuteError:
            arcpy.AddError(arcpy.GetMessages(2))
        except SystemError:
            arcpy.AddError("System Error: " + sys.exc_info()[0])
        except Exception as ex:
            arcpy.AddError("Unexpected Error: " + ex.message)            
        

# For Debugging Python Toolbox Scripts
# comment out when running in ArcMap
#def main():
    #g = CreateDataReviewerDatabase()
    #par = g.getParameterInfo()
    #g.execute(par, None)

#if __name__ == '__main__':
    #main()
