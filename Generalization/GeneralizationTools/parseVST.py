#-------------------------------------------------------------------------------
# Name:        module2
# Purpose:
#
# Author:      ambe3073
#
# Created:     03/06/2016
# Copyright:   (c) ambe3073 2016
# Licence:     <your licence>
#-------------------------------------------------------------------------------
from xml.dom import minidom
import arcpy

def get_fcs(workspace):
    print("Getting Feature Classes from Workspace")

    fcs = {}

    walk = arcpy.da.Walk(workspace, datatype="FeatureClass")

    for dirpath, dirnames, filenames in walk:
        print(str(len(filenames)) + " feature classes in " + str(dirpath))
        for filename in filenames:
            fcClass = dirpath + "\\" + filename

            fcs[filename] = fcClass

    return fcs

def check_field(fc_class, field):
    print("Checking for " + field + " on " + fc_class)
    field_names = [f.name for f in arcpy.ListFields(fc_class)]
    if field not in field_names:
        arcpy.AddMessage("Adding Field to " + str(fc_class))
        arcpy.AddField_management(fc_class, field, "Long")


def main():
    xml_file = arcpy.GetParameterAsText(1)
    input_workspace = arcpy.GetParameterAsText(0)
    field =  arcpy.GetParameterAsText(2)
    checked = []

    fcs = get_fcs(input_workspace)

    xmldoc = minidom.parse(xml_file)
    value_list = xmldoc.getElementsByTagName('Expression')
    fc_list = xmldoc.getElementsByTagName('FeatureClass')
    where_list = xmldoc.getElementsByTagName('WhereClause')

##    print(len(value_list))
##    print(len(fc_list))
##    print(len(where_list))

    for index, fc_item in enumerate(fc_list):
        fc = fc_item.firstChild.data
        where_item = where_list[index]
        where = where_item.firstChild.data
        value_item = value_list[index]
        value_str = value_item.firstChild.data
        string_list = str(value_str).split("Generate = ")
        value = string_list[1][:1]
        value = int(value)

        if fc in fcs:
            update_fc = fcs[str(fc)]
            print update_fc
            if update_fc not in checked:
                check_field(update_fc, field)
                checked.append(update_fc)
            print("updating " + str(fc) + " where " + str(where) )
            up_cnt = 0
            with arcpy.da.UpdateCursor(update_fc, '*', where) as cursor:
                cfields = cursor.fields
                field_ind = 0
                for index, item in enumerate(cfields):
                    if item == field:
                        field_ind = index
                if field_ind >= 0:
                    for row in cursor:
                        row[field_ind] = value
                        cursor.updateRow(row)
                        up_cnt += 1

            arcpy.AddMessage(str(up_cnt) + " features updated in " + str(fc) + " where " + str(where))


    pass

if __name__ == '__main__':
    main()


##print(itemlist[0].attributes['name'].value)
##for s in itemlist:
##    print(s.attributes['Generate'].value)

