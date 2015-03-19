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
import zipfile

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
        self.tools = [MapGenerator]

class MapGenerator(object):
    """ Class that contains the code to generate a new map based off the input aoi"""

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Generate Map"
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
        
        product_as_json.value = '{"productName":"Fixed 25K","makeMapScript":"Fixed25K.pyt","mxd":"CTM25KTemplate.mxd","gridXml":"CTM_UTM_WGS84_grid.xml","pageMargin":"0","exporter":"PDF","exportOption":"Export","geometry":{"rings":[[[-12453869.338275107,4938870.05400884],[-12453869.339388302,4957186.4929140275],[-12439954.400256153,4957186.4943807106],[-12439954.399142958,4938870.0554727865],[-12453869.338275107,4938870.05400884]]],"spatialReference":{"wkid":102100,"latestWkid":3857}},"scale":500000,"pageSize":"LETTER PORTRAIT","quad_id":403011145,"mapSheetName":"Draper","customName":""}'
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
        # Updates layout elements
        for element in layout_element_list:
            if element.name == "Title Text":
                element.text = map_name.upper()
            elif element.name == "Country Name":
                element.text = state_name
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
        arcpy.AddMessage("Updating the Lyout Surround Elements...")
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        try:
            arcpy.env.overwriteOutput = True

            # Makes sure the output directory exists
            if arcpy.Exists(self.outputdirectory) != True:
                arcpy.AddError(self.outputdirectory + " doesn't exist")
                raise arcpy.ExecuteError

            #Getting the Data and time
            timestamp = Utilities.get_date_time()

            #Paths to the ArcGIS Scratch workspaces
            scratch_folder = arcpy.env.scratchFolder
            scratch_workspace = arcpy.env.scratchGDB

            # uncomment code for debugging in python IDEs
            #test = arcpy.CheckExtension("foundation")
            #arcpy.CheckOutExtension('foundation')
            #product_json = '{"productName":"Fixed 25K","makeMapScript":"Fixed25K.pyt","mxd":"CTM25KTemplate.mxd","gridXml":"CTM_UTM_WGS84_grid.xml","pageMargin":"0","exporter":"PDF","exportOption":"Export","geometry":{"rings":[[[-12453869.338275107,4938870.05400884],[-12453869.339388302,4957186.4929140275],[-12439954.400256153,4957186.4943807106],[-12439954.399142958,4938870.0554727865],[-12453869.338275107,4938870.05400884]]],"spatialReference":{"wkid":102100,"latestWkid":3857}},"scale":500000,"pageSize":"LETTER PORTRAIT","quad_id":403011145,"mapSheetName":"Draper","customName":""}'


            # Gets the inputs
            product_json = parameters[0].value
            product = json.loads(product_json)
            product = Utilities.DictToObject(product)

            product_name = product.productName
            map_name = product.customName
            if map_name == "":
                map_name = product.mapSheetName

            # validate aoi
            if product.geometry == "":
                arcpy.AddError("Geometry Object can't be NULL.")
                raise arcpy.ExecuteError
            aoi = arcpy.AsShape(json.dumps(product.geometry), True)

                #User defined variables for the template map
            product_location = os.path.join(self.shared_prod_path, product_name)
            mxd_path = os.path.join(product_location, product.mxd)

            #Validation check
            if arcpy.Exists(mxd_path) != True:
                arcpy.AddError(map_name + " doesn't exist at " + os.path.join(self.shared_prod_path, product_name) + ".")
                raise arcpy.ExecuteError

            map_doc_name = map_name + "_" + timestamp
            arcpy.AddMessage("Creating the map for the " + map_name + " aoi...")
            final_mxd_path = os.path.join(scratch_folder, map_doc_name + ".mxd")
            shutil.copy(mxd_path, final_mxd_path)
            del mxd_path

            final_mxd = arcpy.mapping.MapDocument(final_mxd_path)
            data_frame = Utilities.get_largest_data_frame(final_mxd)

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
                new_aoi = aoi.projectAs(data_frame.spatialReference)
                aoi_centroid = arcpy.Geometry("point", new_aoi.centroid, grid.baseSpatialReference)

                arcpy.AddMessage("data_frame.extent = " + str(data_frame.extent))
                arcpy.AddMessage("data_frame.elementWidth = " + str(data_frame.elementWidth))
                arcpy.AddMessage("data_frame.elementHeight = " + str(data_frame.elementHeight))
                arcpy.AddMessage("aoi_centroid.centroid = " + str(aoi_centroid.centroid))

                map_aoi = grid.calculateExtent(data_frame.elementWidth, data_frame.elementHeight, aoi_centroid, 25000)

                arcpy.AddMessage("map_aoi.extent = " + str(map_aoi.extent))

                data_frame.panToExtent(map_aoi.extent)

                arcpy.AddMessage("data_frame.extent = " + str(data_frame.extent))

                #arcpyproduction.mapping.ClipDataFrameToGeometry(data_frame, aoi)
                #final_mxd.save()

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

                #Creating the Feature Dataset for the grid
                grid_xml = os.path.join(self.shared_prod_path, product_name, non_zipper_xml)
                if arcpy.Exists(grid_xml) != True:
                    arcpy.AddError(non_zipper_xml + " doesn't exist at " + os.path.join(self.shared_prod_path, product_name) + ".")
                    raise arcpy.ExecuteError

                grid = arcpyproduction.mapping.Grid(grid_xml)
                if arcpy.Exists(os.path.join(scratch_workspace, grid_fds_name)):
                    arcpy.AddWarning(grid_fds_name + " already exists, deleting the existing Feature Dataset.")
                    arcpy.Delete_management(os.path.join(scratch_workspace, grid_fds_name))

                arcpy.AddMessage("Creating the Feature Dataset for the Grid...")
                grid_fds = arcpy.CreateFeatureDataset_management(scratch_workspace, grid_fds_name, grid.baseSpatialReference.GCS)
                gfds = str(grid_fds)

                #Determines if the aoi over laps UTM Zones
                coord_system_file_gdb = "CoordinateSystemZones.gdb"
                csz_fc_location = os.path.join(self.shared_prod_path, product_name, coord_system_file_gdb)
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
                for directory, dirnames, filenames in arcpy.da.Walk(workspace, datatype="FeatureClass", type="Polygon"):
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
                arcpy.AddMessage("getting output of masks.")
                anno_mask_layer = arcpy.mapping.Layer(masks.getOutput(0))
                arcpy.mapping.AddLayer(data_frame, anno_mask_layer, 'BOTTOM')
                anno_mask = arcpy.mapping.ListLayers(final_mxd, anno_mask_layer.name, data_frame)[0]
                arcpy.AddMessage("Annotation Mask '" + anno_mask.name + "' layer added to the map...")
                #transgndcrv_layer = arcpy.mapping.ListLayers(final_mxd, "TransportationGroundCurves", data_frame)[0]
                #contour_layer = arcpy.mapping.ListLayers(final_mxd, "HypsographyCurves", data_frame)[0]
                #boundary_crv_layer = arcpy.mapping.ListLayers(final_mxd, "BoundaryCurves", data_frame)[0]
                
                #agriculture_srf_layer = arcpy.mapping.ListLayers(final_mxd, "AgricultureSurfaces", data_frame)[0]                
                #agriculture_srf_layer.definitionQuery = 
                
                
                #boundary_crv_layer = arcpy.mapping.ListLayers(final_mxd, "BoundaryCurves", data_frame)[0]
                #boundary_crv_layer = arcpy.mapping.ListLayers(final_mxd, "BoundaryCurves", data_frame)[0]
                #boundary_crv_layer = arcpy.mapping.ListLayers(final_mxd, "BoundaryCurves", data_frame)[0]
                #boundary_crv_layer = arcpy.mapping.ListLayers(final_mxd, "BoundaryCurves", data_frame)[0]
                #boundary_crv_layer = arcpy.mapping.ListLayers(final_mxd, "BoundaryCurves", data_frame)[0]
                #boundary_crv_layer = arcpy.mapping.ListLayers(final_mxd, "BoundaryCurves", data_frame)[0]
                #boundary_crv_layer = arcpy.mapping.ListLayers(final_mxd, "BoundaryCurves", data_frame)[0]
                

                arcpyproduction.mapping.EnableLayerMasking(data_frame, 'true')
                arcpyproduction.mapping.MaskLayer(data_frame, 'APPEND', anno_mask, gridline_layer)
                #arcpyproduction.mapping.MaskLayer(data_frame, 'APPEND', anno_mask, transgndcrv_layer)
                #arcpyproduction.mapping.MaskLayer(data_frame, 'APPEND', anno_mask, contour_layer)
                #arcpyproduction.mapping.MaskLayer(data_frame, 'APPEND', anno_mask, boundary_crv_layer)
                arcpy.AddMessage("Masking applied to gridlines...")

                #Clips the Data Frame to the AOI and exculdes the Grid
                gird_components = arcpy.mapping.ListLayers(final_mxd, grid_layer, data_frame)
                arcpyproduction.mapping.ClipDataFrameToGeometry(data_frame, aoi, gird_components)
                arcpy.AddMessage("Clipping the Data Frame to the AOI...")

                #Getting the list of data frames
                data_frame_list = arcpy.mapping.ListDataFrames(final_mxd)
                adjoining_data_frame = None
                boundaries_data_frame = None
                for d in data_frame_list:
                    if d.name == "AdjoiningSheet":
                        adjoining_data_frame = d
                    elif d.name == "LocationDiagram":
                        boundaries_data_frame = d

                #Gets the list of layout elements
                layout_elements = arcpy.mapping.ListLayoutElements(final_mxd)

                # Makes the mask layer invisible and prepares map for save
                anno_mask.visible = "false"

                #Logic for update the adjoining sheet and location diagrams
                if product.quad_id == "":
                    arcpy.AddMessage("This is a custom extent")

                    map_aoi_layer = None

                    # Creates a new AOI Feature class to
                    layers = arcpy.mapping.ListLayers(final_mxd, "", data_frame)
                    for l in layers:
                        if l.name == "Map_AOI":
                            map_aoi_layer = l
                            layer_sr = arcpy.Describe(l).spatialReference
                            break
                    del layers

                    custom_aoi_fc = arcpy.CreateFeatureclass_management(scratch_workspace,
                                                       "Custom_Map_AOI",
                                                       "POLYGON",
                                                       "",
                                                       "",
                                                       "",
                                                       layer_sr)
                    arcpy.AddField_management(custom_aoi_fc, "AOI_Name", "TEXT")

                    insert_fields = ['SHAPE@', "AOI_Name"]
                    in_cur = arcpy.da.InsertCursor(custom_aoi_fc, insert_fields)

                    in_cur.insertRow([aoi, product.mapSheetName])

                    custom_aoi_Layer = arcpy.MakeFeatureLayer_management(custom_aoi_fc, "Custom_AOI_Index")
                    custom_aoi_lyr = None
                    for aoi in custom_aoi_Layer:
                        if aoi.name == "Custom_AOI_Index":
                            custom_aoi_lyr = aoi
                    del in_cur, custom_aoi_fc

                    #Updating the Adjoining Sheet Guide
                    layers = arcpy.mapping.ListLayers(final_mxd, "", adjoining_data_frame)
                    for l in layers:
                        if l.name == "Index_AOI":
                            arcpy.ApplySymbologyFromLayer_management(custom_aoi_Layer, l)
                            arcpy.mapping.AddLayer(adjoining_data_frame, custom_aoi_lyr, "TOP")
                            arcpy.mapping.RemoveLayer(adjoining_data_frame, l)
                            arcpy.SelectLayerByAttribute_management(custom_aoi_lyr, "CLEAR_SELECTION")
                            sql_statement = "AOI_Name = '" + str(product.mapSheetName) + "'"
                            arcpy.SelectLayerByAttribute_management(custom_aoi_lyr, "NEW_SELECTION", sql_statement)
                            adjoining_data_frame.extent = custom_aoi_lyr.getSelectedExtent()
                            adjoining_data_frame.scale = 690000
                            arcpy.SelectLayerByAttribute_management(custom_aoi_lyr, "CLEAR_SELECTION")
                            break
                    arcpy.AddMessage("Updating the Adjoining Sheet Data Frame...")
                    del layers

                    #Updating the Boundaries Data Frame
                    arcpy.AddMessage(str(boundaries_data_frame.spatialReference))
                    boundaries_data_frame.spatialReference = grid.baseSpatialReference
                    layers = arcpy.mapping.ListLayers(final_mxd, "", boundaries_data_frame)
                    index_aoi = None
                    us_states = None
                    for l in layers:
                        if l.name == "Index_AOI":
                            index_aoi = l
                        elif l.name == "US_States":
                            us_states = l
                    del layers

                    arcpy.mapping.AddLayer(boundaries_data_frame, custom_aoi_lyr, "TOP")
                    arcpy.mapping.RemoveLayer(boundaries_data_frame, index_aoi)

                    arcpy.SelectLayerByLocation_management(us_states, "INTERSECT", custom_aoi_lyr, "#", "NEW_SELECTION")
                    state_name = None
                    with arcpy.da.SearchCursor(us_states, ["STATE_NAME"]) as s_cursor:
                        for row in s_cursor:
                            state_name = row[0]
                            break
                    arcpy.SelectLayerByAttribute_management(us_states, "CLEAR_SELECTION")

                    us_states.definitionQuery = "STATE_NAME = '" + str(state_name) + "'"
                    sql_querry = "STATE_NAME = '" + str(state_name) + "'"
                    arcpy.AddMessage(sql_querry)
                    arcpy.SelectLayerByAttribute_management(us_states, "NEW_SELECTION", sql_querry)
                    boundaries_data_frame.zoomToSelectedFeatures()
                    arcpy.SelectLayerByAttribute_management(us_states, "CLEAR_SELECTION")
                    arcpy.AddMessage("Updating the Boundaries Data Frame...")

                    mapSeries = "Custom Extent"
                    mapEdition = "Custom Extent"
                    mapSheet = "Custom Extent"

                    MapGenerator.updateLayoutElements(self, layout_elements, map_name, state_name, product.mapSheetName, mapSeries, mapEdition, mapSheet)

                else:
                    arcpy.AddMessage("This is a fixed extent")

                    map_aoi_layer = None

                    # Resets to Definition Querry for the AOI FC
                    layers = arcpy.mapping.ListLayers(final_mxd, "", data_frame)
                    for l in layers:
                        if l.name == "Map_AOI":
                            arcpy.AddMessage(l.definitionQuery)
                            l.definitionQuery = "SECOORD = " + str(product.quad_id)
                            arcpy.AddMessage(l.definitionQuery)
                            map_aoi_layer = l
                            arcpy.AddMessage(map_aoi_layer.definitionQuery)

                    del layers

                    # Updates the Map Sheet Information
                    mapSeries = None
                    mapEdition = None
                    mapSheet = None
                    state_name = None

                    with arcpy.da.SearchCursor(map_aoi_layer, ["SHEET", "SERIES", "EDITION", "STATE_NAME1"]) as s_cursor:
                        for row in s_cursor:
                            state_name = row[3]
                            mapSeries = row[1]
                            mapEdition = row[2]
                            mapSheet = row[0]
                    arcpy.AddMessage("Getting the Map Sheet Information...")
                    state_name = state_name.lower()
                    state_name = state_name[0].upper() + state_name[1:]
                    arcpy.AddMessage(state_name)

                    MapGenerator.updateLayoutElements(self, layout_elements, map_name, state_name, product.mapSheetName, mapSeries, mapEdition, mapSheet)

                    #Updating the Adjoining Sheet Guide
                    layers = arcpy.mapping.ListLayers(final_mxd, "", adjoining_data_frame)
                    for l in layers:
                        if l.name == "Index_AOI":
                            l.definitionQuery = "SECOORD = " + str(product.quad_id)
                            arcpy.SelectLayerByAttribute_management(l, "NEW_SELECTION", "SECOORD = " + str(product.quad_id))
                            adjoining_data_frame.zoomToSelectedFeatures()
                            adjoining_data_frame.scale = 690000
                            arcpy.SelectLayerByAttribute_management(l, "CLEAR_SELECTION")
                            break
                    arcpy.AddMessage("Updating the Adjoining Sheet Data Frame...")
                    del layers

                    #Updating the Boundaries Data Frame
                    boundaries_data_frame.spatialReference = grid.baseSpatialReference
                    layers = arcpy.mapping.ListLayers(final_mxd, "", boundaries_data_frame)
                    for l in layers:
                        if l.name == "Index_AOI":
                            l.definitionQuery = "SECOORD = " + str(product.quad_id)
                        elif l.name == "US_States":
                            l.definitionQuery = "STATE_NAME = '" + str(state_name) + "'"
                            sql_querry = "STATE_NAME = '" + str(state_name) + "'"
                            arcpy.AddMessage(sql_querry)
                            arcpy.SelectLayerByAttribute_management(l, "NEW_SELECTION", sql_querry)
                            boundaries_data_frame.zoomToSelectedFeatures()
                            arcpy.SelectLayerByAttribute_management(l, "CLEAR_SELECTION")
                            break
                    arcpy.AddMessage("Updating the Boundaries Data Frame...")

                arcpy.RefreshActiveView()
                arcpy.RefreshTOC()

                final_mxd.save()

                arcpy.AddMessage("Finalizing the map document...")


                file_name = Utilities.export_map_document(product_location, final_mxd,
                                                          map_doc_name, data_frame,
                                                          self.outputdirectory, product.exporter)
                parameters[1].value = file_name

                # delete feature dataset created for grid
                #arcpy.Delete_management(gfds)

                del final_mxd, grid

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
    #g = MapGenerator()
    #par = g.getParameterInfo()
    #g.execute(par, None)

#if __name__ == '__main__':
    #main()