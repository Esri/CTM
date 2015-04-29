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
import arcpyproduction
import os
import sys
import json
import shutil

# The current design of the Python Files for MCS_POD require that
# MCS_POD's produce files be located in the ArcGIS Server Directory.
# If this changes, the following 4 lines of code will be required to be
# modified to point to the coorect arcgisserver\MCS_POD\Utilities location
SCRIPTPATH = sys.path[0]
PARENTDIRECTORY = os.path._abspath_split(SCRIPTPATH)
if PARENTDIRECTORY[0] == False:
    SCRIPTSDIRECTORY = os.path.join(PARENTDIRECTORY[1], r"\arcgisserver\MCS_POD\Utilities")
elif PARENTDIRECTORY[0] == True:
    SCRIPTSDIRECTORY = os.path.join(PARENTDIRECTORY[1], r"MCS_POD\Utilities")
sys.path.append(SCRIPTSDIRECTORY)
import Utilities

del SCRIPTPATH, PARENTDIRECTORY, SCRIPTSDIRECTORY

class Toolbox(object):
    """Toolbox classes, ArcMap needs this class."""
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the .pyt file)."""
        self.label = "Fixed 25K Tools"
        self.alias = "fixed25kTools"
        # List of tool classes associated with this toolbox
        self.tools = [MapGenerator, DesktopGateway]

class MapGenerator(object):
    """ Class that contains the code to generate a new map based off the input aoi"""

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Map Generation JSON"
        self.description = "Python Script used to create the a new map at a 1:25000 scale"
        self.canRunInBackground = False

        #Path to the AGS Output Directory
        self.outputdirectory = Utilities.output_directory
        # Path to MCS_POD's Product Location
        self.shared_prod_path = Utilities.shared_products_path

    def getParameterInfo(self):
        """Define parameter definitions"""
        product_as_json = arcpy.Parameter(name="product_as_json",
                                          displayName="Product As JSON",
                                          direction="Input",
                                          datatype="GPString",
                                          parameterType="Required")

        output_file = arcpy.Parameter(name="output_file",
                                      displayName="Output File",
                                      direction="Output",
                                      datatype="GPString",
                                      parameterType="Derived")

        #product_as_json.value = '{"productName":"Fixed 25K","makeMapScript":"Fixed25K_MapGenerator.pyt","toolName":"MapGenerator","mxd":"CTM25KTemplate.mxd","gridXml":"CTM_UTM_WGS84_grid.xml","pageMargin":"4.5 8 23 8 CENTIMETERS","exporter":"PDF","exportOption":"Export","geometry":{"rings":[[[-12453869.338275107,4938870.05400884],[-12453869.339388302,4957186.4929140275],[-12439954.400256153,4957186.4943807106],[-12439954.399142958,4938870.0554727865],[-12453869.338275107,4938870.05400884]]],"spatialReference":{"wkid":102100,"latestWkid":3857}},"angle":3.5201989238640496e-006,"pageSize":"CUSTOM PORTRAIT 63 88 CENTIMETERS","quad_id":403011145,"mapSheetName":"Draper","customName":""}'
        params = [product_as_json, output_file]
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

    def updateLayoutElements(self, layout_element_list, map_name, state_name, mapsheetname, mapseries, mapedition, mapsheet):
        """code to update the surround elements"""
        # Updates layout elements for final map
        for element in layout_element_list:
            if element.name == "Title Text":
                element.text = map_name.upper()
            elif element.name == "Country Name":
                element.text = state_name.upper()
            elif element.name == "MapInformationLL":
                element.text = element.text.replace('<%map_name%>', mapsheetname)
                element.text = element.text.replace('<%map_series%>', str(mapseries))
                element.text = element.text.replace('<%map_edition%>', str(mapedition))
                element.text = element.text.replace('<%map_sheet%>', str(mapsheet))
            elif element.name == "MapInformationUR":
                element.text = element.text.replace('<%map_name%>', mapsheetname)
                element.text = element.text.replace('<%map_series%>', str(mapseries))
                element.text = element.text.replace('<%map_edition%>', str(mapedition))
                element.text = element.text.replace('<%map_sheet%>', str(mapsheet))
            elif element.name == "Date Time Text":
                element.text = element.text.replace('<%Map Name%>', mapsheetname)
        del layout_element_list
        arcpy.AddMessage("Updating the Layout Surround Elements...")
        return
            
    def execute(self, parameters, messages):
        """The source code of the tool."""
        import zipfile
        
        try:
            arcpy.env.overwriteOutput = True

            #Getting the Data and time
            timestamp = Utilities.get_date_time()

            #Paths to the ArcGIS Scratch workspaces
            scratch_workspace = arcpy.env.scratchGDB

            # uncomment code for debugging in python IDEs
            test = arcpy.CheckExtension("foundation")
            arcpy.CheckOutExtension('foundation')

            # Gets the inputs and converts to a Python Object
            product_json = parameters[0].value
            product = json.loads(product_json)
            product = Utilities.DictToObject(product)
            
            # Setting a working directory
            if "workingDirectory" in product.keys():
                scratch_folder = product.workingDirectory
                self.outputdirectory = product.workingDirectory
                self.shared_prod_path = os.path.dirname(product.mxd)
                # Sets the product_name to nothing, as this is already in the shared_prod_path variable
                product_name = ""                
            else:
                scratch_folder = arcpy.env.scratchFolder
                # Gets the Product Name
                product_name = product.productName
            
            # Makes sure the output directory exists
            if arcpy.Exists(self.outputdirectory) != True:
                arcpy.AddError(self.outputdirectory + " doesn't exist")
                raise arcpy.ExecuteError

                
            # Gets the Map Name
            # Default is the Custom Name
            # uses the Map Sheet Name if the Custom Name is blank
            map_name = product.customName
            if map_name == "":
                map_name = product.mapSheetName

            # Gets the geometry for the AOI
            if product.geometry == "":
                arcpy.AddError("Geometry Object can't be NULL.")
                raise arcpy.ExecuteError
            aoi = arcpy.AsShape(json.dumps(product.geometry), True)

            # Gets the product folder
            product_location = os.path.join(self.shared_prod_path, product_name)
            # Gets the mxd path
            if arcpy.Exists(os.path.dirname(product.mxd)) != True:
                mxd_path = os.path.join(product_location, product.mxd)
            else:
                mxd_path = product.mxd

            # Validates the template mxd exists
            if arcpy.Exists(mxd_path) != True:
                arcpy.AddError(map_name + " doesn't exist at " + os.path.join(self.shared_prod_path, product_name) + ".")
                raise arcpy.ExecuteError

            # Creates the AOI specific mxd in the scratch location
            map_doc_name = map_name + "_" + timestamp
            arcpy.AddMessage("Creating the map for the " + map_name + " aoi...")
            final_mxd_path = os.path.join(scratch_folder, map_doc_name + ".mxd")
            arcpy.AddMessage("MXD path is: " + final_mxd_path)
            shutil.copy(mxd_path, final_mxd_path)
            del mxd_path

            # Gets the mxd object
            final_mxd = arcpy.mapping.MapDocument(final_mxd_path)
            
            # Validates the job mxd does not have broken links
            layerlist = arcpy.mapping.ListLayers(final_mxd)
            broken_layer = False
            for layer in layerlist:
                broken_layer = layer.isBroken
                if broken_layer == True:
                    arcpy.AddError("Map Document has boken data soruces.")
                    exit(0)
                
            
            
            # Updating the Data Sources to the Production Database if provided.
            if "productionWorkspace" in product.keys():
                if product.productionWorkspace != "None":
                    production_database = product.productionWorkspace
                    arcpy.AddMessage("Getting the list of data frames.")
                    for layer in layerlist:
                        #arcpy.AddMessage("Replacing data source for layer: " + str(layer))
                        layer.replaceDataSource(production_database, "FILEGDB_WORKSPACE", "", True)
                    final_mxd.save()
            
            # Gets the largest data frame (page size not data frame extent)
            data_frame = Utilities.get_largest_data_frame(final_mxd)

            # Code to generate a Preview for the POD wed app
            if product.exportOption == 'Preview':
                # Turn off labels and annotation layers in MXD
                for lyr in arcpy.mapping.ListLayers(final_mxd, "", data_frame):
                    if lyr.isBroken:
                        continue
                    if lyr.supports("LABELCLASSES"):
                        for label_class in lyr.labelClasses:
                            label_class.showClassLabels = False
                    if lyr.supports("DEFINITIONQUERY"):
                        desc = arcpy.Describe(lyr)
                        ftype = desc.featureClass.featureType
                        if ftype == 'Annotation':
                            lyr.visible = False

                grid = arcpyproduction.mapping.Grid(os.path.join(product_location, product.gridXml))
                new_aoi = aoi.projectAs(grid.baseSpatialReference)
                aoi_centroid = arcpy.Geometry("point", new_aoi.centroid, grid.baseSpatialReference)

                arcpy.AddMessage("data_frame.extent = " + str(data_frame.extent))
                arcpy.AddMessage("data_frame.elementWidth = " + str(data_frame.elementWidth))
                arcpy.AddMessage("data_frame.elementHeight = " + str(data_frame.elementHeight))
                arcpy.AddMessage("aoi_centroid.centroid = " + str(aoi_centroid.centroid))

                map_aoi = grid.calculateExtent(data_frame.elementWidth,
                                               data_frame.elementHeight,
                                               aoi_centroid, 25000)

                new_map_aoi = map_aoi.projectAs(data_frame.spatialReference)
                arcpy.AddMessage("map_aoi.extent = " + str(new_aoi.extent))

                data_frame.panToExtent(new_map_aoi.extent)
                arcpy.AddMessage("data_frame.extent = " + str(data_frame.extent))

                #arcpyproduction.mapping.ClipDataFrameToGeometry(data_frame, aoi)
                final_mxd.save()

                # Full-size export
                preview_name = "_ags_" + map_doc_name + "_preview.jpg"
                preview_path = os.path.join(self.outputdirectory, preview_name)
                arcpy.mapping.ExportToJPEG(final_mxd, preview_path, resolution=96, jpeg_quality=50)
                parameters[1].value = preview_name

            elif product.exportOption == 'Export':
                #Variables required for the script
                non_zipper_xml = product.gridXml
                utm_zone_fc = "UTMZones_WGS84"
                grid_fds_name = "Grids_WGS84" + timestamp

                # Gets the Grid XML path
                #grid_xml = os.path.join(self.shared_prod_path, product_name, non_zipper_xml)
                
                if arcpy.Exists(os.path.dirname(product.gridXml)) != True:
                    grid_xml = os.path.join(product_location, product.gridXml)
                    
                else:
                    grid_xml = product.gridXml                

                if arcpy.Exists(grid_xml) != True:
                    arcpy.AddError(non_zipper_xml + " doesn't exist at " + os.path.join(self.shared_prod_path, product_name) + ".")
                    raise arcpy.ExecuteError

                # Creates a grid object
                grid = arcpyproduction.mapping.Grid(grid_xml)
                if arcpy.Exists(os.path.join(scratch_workspace, grid_fds_name)):
                    #Checks the FDS to insure a grid with the same name doesn't exist
                    arcpy.AddWarning(grid_fds_name + " already exists, deleting the existing Feature Dataset.")
                    arcpy.Delete_management(os.path.join(scratch_workspace, grid_fds_name))

                # Creating the Feature Dataset for the grid
                arcpy.AddMessage("Creating the Feature Dataset for the Grid...")
                grid_fds = arcpy.CreateFeatureDataset_management(scratch_workspace, grid_fds_name, grid.baseSpatialReference.GCS)
                gfds = str(grid_fds)

                #Determines if the aoi over laps UTM Zones
                coord_system_file_gdb = "CoordinateSystemZones.gdb"
                csz_fc_location = os.path.join(self.shared_prod_path,
                                               product_name,
                                               coord_system_file_gdb)
                # Checks to see if the CoodinateSystemZones.gdb is in the Product Location
                # If not it will be extracted from the install location.
                if os.path.exists(csz_fc_location) != True:
                    arcpy.AddMessage("The CoordinateSystemZones.gdb doesn't exist in %s. The database will be extracted." %os.path.join(self.shared_prod_path,
                                               product_name,
                                               coord_system_file_gdb))
                    install_location = arcpy.GetInstallInfo()['InstallDir']
                    zipped_file = os.path.join(install_location, r"GridTemplates\ProductionMapping", "CoordinateSystemZones.zip")
                    z = zipfile.ZipFile(zipped_file)
                    z.extractall(os.path.join(self.shared_prod_path, product_name))

                    arcpy.AddMessage("CoordinateSystemZones.gdb extracted successfully at %s." %os.path.join(self.shared_prod_path, product_name))
                                       

                temp_fc = os.path.join(csz_fc_location, utm_zone_fc)
                utm_lyr = arcpy.mapping.Layer(temp_fc)
                arcpy.SelectLayerByLocation_management(utm_lyr, "INTERSECT", aoi)
                result = arcpy.GetCount_management(utm_lyr)
                zone_count = int(result.getOutput(0))

                arcpy.AddMessage("Checking for overlapping UTM Zones..")
                # Checking for unique UTM zones in selection set
                if zone_count > 1:
                    zone_num = {}
                    with arcpy.da.SearchCursor(utm_lyr, ["OBJECTID", "ZONE_NUM"]) as zone_cursor:
                        for row in zone_cursor:
                            zone_num[row[1]] = row[0]
                    if len(zone_num) != zone_count:
                        zone_count = len(zone_num)
                    del zone_cursor, zone_num

                del utm_lyr

                # Once we have a zipper xml, replace the defualt on with zipper.
                zipper_xml = product.gridXml
                if zone_count > 1: # Use zipper
                    grid_xml = os.path.join(self.shared_prod_path, product_name, zipper_xml)

                #Uses the appropriate XML for to create the grid
                arcpy.AddMessage("Creating the Grid...")
                output_layer = map_name + '_' + grid.type
                grid_result = arcpy.MakeGridsAndGraticulesLayer_cartography(grid_xml, aoi, gfds, output_layer, map_name)
                arcpy.AddMessage(grid_result.getMessages())
                grid_layer = grid_result.getOutput(0)

                # Updates the current map document using grid object and methods
                # Add/Update the grid layer to the top of the map
                layers = arcpy.mapping.ListLayers(final_mxd, grid_layer.name, data_frame)
                if len(layers) > 0:
                    arcpy.AddWarning("Grid Layer "+ grid_layer.name + " already exists in the map. It will be updated to use the new grid.")
                    for layer in layers:
                        arcpy.mapping.RemoveLayer(data_frame, layer)
                    arcpy.RefreshTOC()

                arcpy.mapping.AddLayer(data_frame, grid_layer, "TOP")
                arcpy.AddMessage("Grid Layer added to map...")

                # Updates the data frame properties base on the grid
                final_mxd.activeView = 'PAGE_LAYOUT'
                grid.updateDataFrameProperties(data_frame, aoi)

                arcpy.AddMessage("Dataframe's extent is now = " + str(data_frame.extent))

                # Masks the ladder values i.e. interior grid
                # annotion that overlap the grid line.
                anno_layer = arcpy.mapping.ListLayers(final_mxd, "ANO_*", data_frame)[0]
                gridline_layer = arcpy.mapping.ListLayers(final_mxd, "GLN_*", data_frame)[0]

                # Returns a new mask feature class for masking the
                # gridlines that intersect interior annotation or ladder values
                annomask_ctr = 1
                workspace = os.path.dirname(gfds)
                for directory, dirnames, filenames in arcpy.da.Walk(workspace,
                                                                    datatype="FeatureClass",
                                                                    type="Polygon"):
                    for filename in filenames:
                        if filename.find("AnnoMask") > -1:
                            annomask_ctr = annomask_ctr +1
                annomask_fc = gfds + "\\AnnoMask_" + str(annomask_ctr)

                if not arcpy.env.overwriteOutput and arcpy.Exists(annomask_fc):
                    arcpy.AddError(annomask_fc + "already exists. Cannot create output.")
                arcpy.AddMessage("making the feature outline masks")
                masks = arcpy.FeatureOutlineMasks_cartography(anno_layer, annomask_fc,
                                                              grid.scale, grid.baseSpatialReference.GCS,
                                                              '2.5 Points', 'CONVEX_HULL',
                                                              'ALL_FEATURES')
                # Masking the grid ladder values and annotations
                arcpy.AddMessage("getting output of masks.")
                anno_mask_layer = arcpy.mapping.Layer(masks.getOutput(0))
                arcpy.mapping.AddLayer(data_frame, anno_mask_layer, 'BOTTOM')
                anno_mask = arcpy.mapping.ListLayers(final_mxd, anno_mask_layer.name, data_frame)[0]
                arcpy.AddMessage("Annotation Mask '" + anno_mask.name + "' layer added to the map...")
                arcpyproduction.mapping.EnableLayerMasking(data_frame, 'true')
                arcpyproduction.mapping.MaskLayer(data_frame, 'APPEND', anno_mask, gridline_layer)
                arcpy.AddMessage("Masking applied to gridlines...")

                #Clips the Data Frame to the AOI and exculdes the Grid
                gird_components = arcpy.mapping.ListLayers(final_mxd, grid_layer, data_frame)
                arcpyproduction.mapping.ClipDataFrameToGeometry(data_frame, aoi, gird_components)
                arcpy.AddMessage("Clipping the Data Frame to the AOI...")

                #Getting the list of data frames
                data_frame_list = arcpy.mapping.ListDataFrames(final_mxd)
                adjoining_data_frame = None
                boundaries_data_frame = None
                for b_data_frame in data_frame_list:
                    if b_data_frame.name == "AdjoiningSheet":
                        adjoining_data_frame = b_data_frame
                    elif b_data_frame.name == "LocationDiagram":
                        boundaries_data_frame = b_data_frame

                #Gets the list of layout elements
                layout_elements = arcpy.mapping.ListLayoutElements(final_mxd)
                
                product.quad_id = ""

                # Makes the mask layer invisible and prepares map for save
                anno_mask.visible = "false"
                #Logic for update the adjoining sheet and location diagrams
                
                arcpy.AddMessage("This is a custom extent")

                map_aoi_layer = None

                # Creates a new AOI Feature class to
                layers = arcpy.mapping.ListLayers(final_mxd, "", data_frame)
                for layer in layers:
                    if layer.name == "Map_AOI":
                        map_aoi_layer = layer
                        layer_sr = arcpy.Describe(layer).spatialReference
                        break
                del layers, layer

                # Creates a temporary AOI feature class
                custom_aoi_fc = arcpy.CreateFeatureclass_management(scratch_workspace,
                                                                    "Custom_Map_AOI",
                                                                    "POLYGON",
                                                                    "",
                                                                    "",
                                                                    "",
                                                                    layer_sr)
                arcpy.AddField_management(custom_aoi_fc, "AOI_Name", "TEXT")
                # Creates the AOI feature in the AOI Feature class
                insert_fields = ['SHAPE@', "AOI_Name"]
                in_cur = arcpy.da.InsertCursor(custom_aoi_fc, insert_fields)
                in_cur.insertRow([aoi, product.mapSheetName])

                # Makes the Temp AOI FC a layer
                custom_aoi_layer = arcpy.MakeFeatureLayer_management(custom_aoi_fc, "Custom_AOI_Index")
                custom_aoi_lyr = None
                for aoi in custom_aoi_layer:
                    if aoi.name == "Custom_AOI_Index":
                        custom_aoi_lyr = aoi
                del in_cur

                #Updating the Adjoining Sheet Guide
                layers = arcpy.mapping.ListLayers(final_mxd, "", adjoining_data_frame)
                for layer in layers:
                    if layer.name == "Index_AOI":
                        # Copies the symbology from the existing AOI Layer
                        arcpy.ApplySymbologyFromLayer_management(custom_aoi_layer, layer)
                        # Adds the temp AOI FC
                        arcpy.mapping.AddLayer(adjoining_data_frame, custom_aoi_lyr, "TOP")
                        # Removes the AOI Index Layer
                        arcpy.mapping.RemoveLayer(adjoining_data_frame, layer)
                        # Pans and zooms the DF to the correct location for the new AOI Layer
                        arcpy.SelectLayerByAttribute_management(custom_aoi_lyr, "CLEAR_SELECTION")
                        sql_statement = "AOI_Name = '" + str(product.mapSheetName) + "'"
                        arcpy.SelectLayerByAttribute_management(custom_aoi_lyr, "NEW_SELECTION", sql_statement)
                        adjoining_data_frame.extent = custom_aoi_lyr.getSelectedExtent()
                        adjoining_data_frame.scale = 690000
                        arcpy.SelectLayerByAttribute_management(custom_aoi_lyr, "CLEAR_SELECTION")
                        break
                arcpy.AddMessage("Updating the Adjoining Sheet Data Frame...")
                del layers

                # Updating the Boundaries Data Frame
                arcpy.AddMessage(str(boundaries_data_frame.spatialReference))
                boundaries_data_frame.spatialReference = grid.baseSpatialReference
                layers = arcpy.mapping.ListLayers(final_mxd, "", boundaries_data_frame)
                index_aoi = None
                us_states = None

                for layer in layers:
                    if layer.name == "Index_AOI":
                        index_aoi = layer
                    elif layer.name == "US_States":
                        us_states = layer
                del layers
                us_states_count = arcpy.GetCount_management(us_states)
                arcpy.AddMessage("US States get is: "+ str(us_states_count))
                # Adding the custom AOI Layer
                arcpy.mapping.AddLayer(boundaries_data_frame, custom_aoi_lyr, "TOP")
                # Removing the current AOI Index Layer
                arcpy.mapping.RemoveLayer(boundaries_data_frame, index_aoi)
                us_states.definitionQuery = ""
                us_states_count = arcpy.GetCount_management(us_states)
                arcpy.AddMessage("US States get is: "+ str(us_states_count))              

                # Determining which US State interested the Custom AOI
                arcpy.SelectLayerByLocation_management(us_states, "INTERSECT", custom_aoi_lyr, "#", "NEW_SELECTION")
                us_states_count = arcpy.GetCount_management(us_states)
                arcpy.AddMessage("US States get is: "+ str(us_states_count))                
                state_name = None
                with arcpy.da.SearchCursor(us_states, ["STATE_NAME"]) as s_cursor:
                    for row in s_cursor:
                        state_name = row[0]
                        break
                arcpy.SelectLayerByAttribute_management(us_states, "CLEAR_SELECTION")

                # Updating the States Layer with the correct State
                us_states.definitionQuery = "STATE_NAME = '" + str(state_name) + "'"
                sql_querry = "STATE_NAME = '" + str(state_name) + "'"
                arcpy.AddMessage(sql_querry)
                arcpy.SelectLayerByAttribute_management(us_states, "NEW_SELECTION", sql_querry)
                # Zooming to the correct State
                boundaries_data_frame.zoomToSelectedFeatures()
                arcpy.SelectLayerByAttribute_management(us_states, "CLEAR_SELECTION")
                arcpy.AddMessage("Updating the Boundaries Data Frame...")

                # Setting the Map Sheet Information
                map_aoi_layer.definitionQuery = ""
                arcpy.SelectLayerByLocation_management(map_aoi_layer, "CONTAINS", custom_aoi_lyr, "#", "NEW_SELECTION")
                aoi_count = arcpy.GetCount_management(map_aoi_layer)
                map_series = None
                map_edition = None
                map_sheet = None                
                if int(aoi_count.getOutput(0)) == 1:
                    with arcpy.da.SearchCursor(map_aoi_layer, ["SHEET", "SERIES", "EDITION"]) as s_cursor:
                        for row in s_cursor:
                            map_series = row[1]
                            map_edition = row[2]
                            map_sheet = row[0]                     
                else:
                    map_series = "Custom Extent"
                    map_edition = "Custom Extent"
                    map_sheet = "Custom Extent"

                # Updating the Surround Elements
                
                MapGenerator.updateLayoutElements(self, layout_elements, map_name, state_name, product.mapSheetName, map_series, map_edition, map_sheet)

                arcpy.RefreshActiveView()
                arcpy.RefreshTOC()

                final_mxd.save()

                arcpy.AddMessage("Finalizing the map document...")

                # Export the Map to the selected format
                file_name = Utilities.export_map_document(product_location, final_mxd,
                                                          map_doc_name, data_frame,
                                                          self.outputdirectory, product.exporter, product.productionPDFXML)
                parameters[1].value = file_name
                
                arcpy.AddMessage("Cleaning up all the intermediate data.")

                # Delete feature dataset created for grid (Option for Development)
                arcpy.Delete_management(gfds)
                del final_mxd, grid, custom_aoi_layer, custom_aoi_lyr
                arcpy.Delete_management(final_mxd_path)
                rst = arcpy.Delete_management(os.path.join(scratch_workspace, "Custom_Map_AOI"))

            return

        except arcpy.ExecuteError:
            arcpy.AddError(arcpy.GetMessages(2))
        except SystemError:
            arcpy.AddError("System Error: " + sys.exc_info()[0])
        except Exception as ex:
            arcpy.AddError("Unexpected Error: " + ex.message)



class DesktopGateway(object):
    """ Class that contains the code to generate a new map based off the input aoi"""

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Map Generation"
        self.description = "Python Script used to call the Map Generator script on ArcMap or WMX."
        self.canRunInBackground = False

        #Path to the AGS Output Directory
        self.outputdirectory = Utilities.output_directory
        # Path to MCS_POD's Product Location
        self.shared_prod_path = Utilities.shared_products_path

    def getParameterInfo(self):
        """Define parameter definitions"""
        map_aoi = arcpy.Parameter(name="map_aoi",
                                  displayName="Map AOI",
                                  direction="Input",
                                  datatype="GPFeatureLayer",
                                  parameterType="Required")
    
        map_name_field = arcpy.Parameter(name = "map_name_field",
                                         displayName = "Map Name Field",
                                         direction = "Input",
                                         datatype="Field",
                                         parameterType="Required")

        map_template = arcpy.Parameter(name="map_template",
                                       displayName="Map Document Template",
                                       direction="Input",
                                       datatype="DEMapDocument",
                                       parameterType="Required")
        
        grid_xml = arcpy.Parameter(name="grid_xml", 
                                   displayName="Grid and Graticules XML",
                                   direction="Input",
                                   datatype="DEFile",
                                   parameterType="Required")        
        
        export_type = arcpy.Parameter(name="export_type", 
                                      displayName="Export Type", 
                                      direction="Input", 
                                      datatype="GPString", 
                                      parameterType="Required")
        
        working_directory = arcpy.Parameter(name= "working_directory",
                                            displayName= "Working Directory",
                                            direction= "Input",
                                            datatype="DEFolder",
                                            parameterType= "Required")
        
        production_workspace = arcpy.Parameter(name= "production_workspace",
                                               displayName= "Production Workspace",
                                               direction= "Input",
                                               datatype= "DEWorkspace", 
                                               parameterType="Optional")
        
        production_pdf_xml = arcpy.Parameter(name="production_pdf_xml", 
                                   displayName="Production PDF XML",
                                   direction="Input",
                                   datatype="DEFile",
                                   parameterType="Optional")           
        
        output_file = arcpy.Parameter(name="output_file",
                              displayName="Output File",
                              direction="Output",
                              datatype="GPString",
                              parameterType="Derived")

        grid_xml.filter.list = ["xml"]
        export_type.filter.type = "ValueList"
        export_type.filter.list = ["PDF", "TIFF", "JPEG", "Multi-page PDF", "Production PDF", "Layout GeoTIFF", "Map Package"]
        production_pdf_xml.filter.list = ["xml"]
        map_name_field.parameterDependencies = [map_aoi.name]
        map_name_field.filter.list = ["Text", "Short", "Long", "Double"]
        map_aoi.filter.list = ["Polygon"]

        params = [map_aoi, map_name_field, map_template, grid_xml, export_type, working_directory, production_pdf_xml, production_workspace, output_file]

        # Default Values for Debugging
        #map_aoi.value = r"C:\arcgisserver\MCS_POD\Products\Fixed 25K\SaltLakeCity.gdb\SLC_AOIs"
        #map_name_field.value = "QUAD_NAME"
        #map_template.value = r"C:\arcgisserver\MCS_POD\Products\Fixed 25K\CTM25KTemplate.mxd"
        #grid_xml.value = r"C:\arcgisserver\MCS_POD\Products\Fixed 25K\CTM_UTM_WGS84_grid.xml"
        #export_type.value = "Multi-page PDF"
        #export_type.value = "PDF"
        #working_directory.value = r"C:\arcgisserver\MCS_POD\WMX\Test_Working_Dir"
        #production_workspace.value = r"C:\arcgisserver\MCS_POD\WMX\WMX_Templates\SaltLakeCity.gdb"
        #production_pdf_xml.value = r"C:\arcgisserver\MCS_POD\WMX\WMX_Templates\CTM_Production_PDF.xml"
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
        # Checks to see if the Map AOI parameter has changed
        if parameters[0].altered == True:
            # Gets the Feature count
            feature_count = arcpy.GetCount_management(parameters[0].value)
            # Returns a warning if the AOI Layer has more than 25 features.
            if int(feature_count.getOutput(0)) > 25:
                parameters[0].setWarningMessage("The Map AOI layer has more than 25 features, process might be slow.  The AOI Layer has: " + str(feature_count.getOutput(0)) + " features.")
        elif parameters[4].altered == True:
            if parameters[4].value <> "Production PDF":
                parameters[6].enabled = False
            elif parameters[4].value == "Production PDF":
                parameters[6].enabled = True
                xml_value = parameters[6].value
                if not xml_value:
                    parameters[6].setErrorMessage("If Production PDF Exporter is choosen, you must input a Production PDF XML color mapping file.")
          
        return        

    def execute(self, parameters, messages):
        try:
            # Getting the input parameters
            map_aoi = parameters[0].value
            map_name_field = parameters[1].value
            map_template_file = parameters[2].value
            grid_xml_file = parameters[3].value
            export_type = parameters[4].value
            working_directory = parameters[5].value
            production_workspace = parameters[7].value
            production_pdf_xml = parameters[6].value

            multi_page_pdf_list = []
            output_files = []
            
            if parameters[4].value == "Production PDF":
                if not parameters[6].value:
                    arcpy.AddError("If Production PDF Exporter is choosen, a Production PDF color mapping XML file must be provided.")
                    exit(0)
            
            # Getting output location from Utilities
            if working_directory == "":
                output_location = Utilities.output_directory
            else: 
                output_location = str(working_directory)
            
            # Starting a Seach Cursor to loop through the AOI Layer
            with arcpy.da.SearchCursor(map_aoi, ['SHAPE@JSON', str(map_name_field), 'OID@']) as scur:
                for row in scur:
                    map_name = None
                    # Getting the Map name from the AOI Layer or setting a Default Name
                    if row[1] == '':
                        arcpy.AddWarning("Map name is NULL, map name will be based on the GFID for the AOI Feature.")
                        map_name = "GFID_" + row[2]
                    else:
                        map_name = row[1]
                    # Getting the parent dirctory and file names for the template files
                    direcotry = os.path.dirname(str(map_template_file))
                    product_name = os.path.basename(direcotry)
                    # Creating the JSON Sting
                    input_json = json.dumps({'productName': product_name, 'mxd': str(map_template_file), 'gridXml': str(grid_xml_file), 'exporter': str(export_type), 'exportOption': 'Export', 'geometry': json.loads(row[0]), 'quad_id': str(row[2]), 'mapSheetName': map_name, 'customName': '', 'workingDirectory': str(working_directory), 'productionWorkspace': str(production_workspace), 'productionPDFXML': str(production_pdf_xml)}, sort_keys=True, separators=(',', ': '))
                    print input_json
                    
                    # Calls the Map Generation locgic
                    arcpy.AddMessage("Call the Map Generation tool for the: " + map_name + " AOI.")
                    mp_generator = MapGenerator()
                    par = mp_generator.getParameterInfo()
                    par[0].value = input_json
                    mp_generator.execute(par, None)
                    outfile = os.path.join(output_location, par[1].value)
                    
                    # Creates the array for the list of output(s)
                    if export_type == "Multi-page PDF":
                        multi_page_pdf_list.append(outfile)
                    else:
                        output_files.append(outfile)
                
                # Creates a Map Book for the multi-page PDFs
                map_book_name = ""
                if multi_page_pdf_list != []:
                    map_book_name = "_ags_MultipagePDF_" + str(Utilities.get_date_time()) + ".pdf"
                    map_book_path = os.path.join(output_location, map_book_name)
    
                    # Create the file and append pages
                    pdfdoc = arcpy.mapping.PDFDocumentCreate(map_book_path)

                    # Loops through each single page PDF and adds them together in 1 Mutli-page PDF
                    for pdf_name in multi_page_pdf_list:
                        pdf_path = os.path.join(output_location, pdf_name)
                        pdfdoc.appendPages(pdf_path)
    
                    pdfdoc.saveAndClose()
                    output_files.append(os.path.join(output_location, map_book_name))
    
                    arcpy.AddMessage("Output Files: " + json.dumps(output_files))                   
                        
                        
                arcpy.SetParameterAsText(8, output_files)
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
    #g = DesktopGateway()
    ##g = MapGenerator()
    #par = g.getParameterInfo()
    #g.execute(par, None)

#if __name__ == '__main__':
    #main()

