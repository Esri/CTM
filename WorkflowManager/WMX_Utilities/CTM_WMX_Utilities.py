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

import arcpy
import sys

wmx_workspace = r"C:\arcgisserver\mcs_pod\WMX\WMX_Utilities\CTM_WMX.sde"
extended_propert_table = "JTX_EXT_JOB_REPLICA"

def update_extended_properties(job_id, extended_property_field, field_value):
    try:
        arcpy.env.workspace = wmx_workspace
        tablelist = arcpy.ListTables()

        job_id_exisits = False
        extened_table = None
        dataset_versioned = False
        edit = arcpy.da.Editor(wmx_workspace)

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
            with arcpy.da.UpdateCursor(extened_table, ["JOBID", extended_property_field]) as ucur:
                for row in ucur:
                    table_job_id = row[0]
                    if int(table_job_id) == int(job_id):
                        row[1] = field_value
                        ucur.updateRow(row)
                        break
            del ucur, row
        else:
            incur = arcpy.da.InsertCursor(extened_table, ["JOBID", extended_property_field])
            incur.insertRow((job_id, field_value))
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
    #g = update_extended_properties(56803, "JOBREPLICA", r"\\sheffieldj\arcgisserver\MCS_POD\WMX\WMX_Jobs\WMX_JOB_56803\Job_56803_Replica.gdb")

#if __name__ == '__main__':
    #main()
