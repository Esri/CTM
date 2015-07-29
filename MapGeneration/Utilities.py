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

"""Utilities file for use by multiple POD scripts"""

import arcpy
import arcpyproduction
import os
import datetime
import traceback
import sys

# Path to the Products folder
shared_products_path = r"\\SHEFFIELDJ\arcgisserver\MCS_POD\Products"

# Path to the ArcGIS Server output directory
output_directory = r"\\SHEFFIELDJ\arcgisserver\directories\arcgisoutput"
output_url = r"http://SHEFFIELDJ.esri.com:6080/arcgis/rest/directories/arcgisoutput/"

def get_largest_data_frame(mxd):
    """Returns the largest data frame from mxd"""
    data_frame_list = arcpy.mapping.ListDataFrames(mxd)
    area = 0
    for df in data_frame_list:
        if area < df.elementWidth * df.elementHeight:
            area = df.elementWidth * df.elementHeight
            data_frame = df
    return data_frame

def get_date_time():
    """Returns the current date and time"""
    date = datetime.datetime.now()
    return date.strftime("%m%d%Y_%H%M%S")

def export_map_document(product_location, mxd, map_doc_name, data_frame,
                        outputdirectory, export_type, production_xml=None):
    """Exports MXD to chosen file type"""

    try:
        export = export_type.upper()

        if export == "PDF":
            filename = "_ags_" + map_doc_name  + ".pdf"
            outfile = os.path.join(outputdirectory, filename)

            # Export to PDF optional parameters
            data_frame = "PAGE_LAYOUT"
            df_export_width = 640
            df_export_height = 480
            resolution = 300
            image_quality = "BEST"
            colorspace = "RGB"
            compress_vectors = True
            image_compression = "ADAPTIVE"
            picture_symbol = "RASTERIZE_BITMAP"
            convert_markers = False
            embed_fonts = True
            layers_attributes = "LAYERS_ONLY"
            georef_info = True
            jpeg_compression_quality = 80

            # Run the export tool
            arcpy.mapping.ExportToPDF(mxd, outfile, data_frame, df_export_width,
                                      df_export_height, resolution,
                                      image_quality, colorspace,
                                      compress_vectors, image_compression,
                                      picture_symbol, convert_markers,
                                      embed_fonts, layers_attributes,
                                      georef_info, jpeg_compression_quality)
            arcpy.AddMessage("PDF is located: " + outfile)
            arcpy.AddMessage(filename)
            return filename

        elif export == 'JPEG':
            filename = "_ags_" + map_doc_name  + ".jpg"
            outfile = os.path.join(outputdirectory, filename)

            # Export to JEPG optional parameters
            data_frame = "PAGE_LAYOUT"
            df_export_width = 640
            df_export_height = 480
            resolution = 96
            world_file = False
            color_mode = "24-BIT_TRUE_COLOR"
            jpeg_quality = 100
            progressive = False

            # Run the export tool
            arcpy.mapping.ExportToJPEG(mxd, outfile, data_frame,
                                       df_export_width, df_export_height,
                                       resolution, world_file, color_mode,
                                       jpeg_quality, progressive)

            arcpy.AddMessage("JPEG is located: " + outfile)
            return filename

        elif export == 'TIFF':
            filename = "_ags_" + map_doc_name  + ".tif"
            outfile = os.path.join(outputdirectory, filename)

            # Export to JPEG optional parameters
            data_frame = "PAGE_LAYOUT"
            df_export_width = 640
            df_export_height = 480
            resolution = 96
            world_file = False
            color_mode = "24-BIT_TRUE_COLOR"
            tiff_compression = "LZW"

            # Run the export tool
            arcpy.mapping.ExportToTIFF(mxd, outfile, data_frame,
                                       df_export_width, df_export_height,
                                       resolution, world_file, color_mode,
                                       tiff_compression)
            arcpy.AddMessage("TIFF is located: " + outfile)
            return filename

        elif export == "MAP PACKAGE":
            filename = "_ags_" + map_doc_name + ".mpk"
            outfile = os.path.join(outputdirectory, filename)
            dfextent = data_frame.extent
            mxd = mxd.filePath
            arcpy.AddMessage(mxd)

            # Export to MPK optional parameters
            convert_data = "CONVERT"
            convert_arcsde_data = "CONVERT_ARCSDE"
            apply_extent_to_arcsde = "ALL"
            arcgisruntime = "DESKTOP"
            reference_all_data = "NOT_REFERENCED"
            version = "ALL"

            # Run the export tool
            arcpy.PackageMap_management(mxd, outfile, convert_data,
                                        convert_arcsde_data, dfextent,
                                        apply_extent_to_arcsde, arcgisruntime,
                                        reference_all_data, version)
            arcpy.AddMessage("MPK is located: " + outfile)
            return filename

        elif export == 'LAYOUT GEOTIFF':
            filename = "_ags_" + map_doc_name  + ".tif"
            outfile = os.path.join(outputdirectory, filename)

            # Export to Layout GeoTIFF optional parameters:
            resolution = 96
            world_file = False
            color_mode = "24-BIT_TRUE_COLOR"
            tiff_compression = "LZW"

            # Run the export tool
            arcpyproduction.mapping.ExportToLayoutGeoTIFF(mxd, outfile,
                                                          data_frame,
                                                          resolution,
                                                          world_file,
                                                          color_mode,
                                                          tiff_compression)
            arcpy.AddMessage("Layout GeoTIFF is located: " + outfile)
            return filename

        elif export == 'PRODUCTION PDF' or export == 'MULTI-PAGE PDF':
            filename = "_ags_" + map_doc_name  + ".pdf"
            outfile = os.path.join(outputdirectory, filename)
            setting_file = os.path.join(product_location, production_xml)

            if os.path.exists(setting_file) == True:
                arcpyproduction.mapping.ExportToProductionPDF(mxd, outfile,
                                                              setting_file)
                arcpy.AddMessage("Production PDF is located: " + outfile)
            else:
                arcpy.AddMessage("Production PDF is the default exporter for a Multi-page PDF.")
                arcpy.AddWarning("Color mapping rules file doesn't exist, using "
                               "standard ExportToPDF exporter with default "
                               "settings.")
                arcpy.mapping.ExportToPDF(mxd, outfile)
                arcpy.AddMessage("PDF is located: " + outfile)
            return filename

        else:
            arcpy.AddError("The exporter : " + export + " is not supported, "
                           "please contact your system administrator.")

    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as ex:
        arcpy.AddError(ex.message)
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        arcpy.AddError("Traceback info:\n" + tbinfo)

class DictToObject(dict):
    """Convert dictionary into class"""
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
    def __getattr__(self, name):
        return self[name]
    def __setattr__(self, name, value):
        self[name] = value
