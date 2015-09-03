CTM
===

Civilian Topographic Map (CTM)

<<<<<<< HEAD
Civilian Topographic Map (CTM) is a product designed to allow users to easily create civilian style topographic data and maps using Esri Production Mapping.  CTM includes a geodatabase data model as well as sample configurations for editing, quality assurance, and cartography. CTM can also be configured as a sample map product for Product on Demand (POD), a web application that allows users to create high quality cartographic products through a light weight web interface.

The schema of CTM is based on the National System for Geospatial Intelligence Feature Data dictionary (NFDD).   The NFDD is a comprehensive dictionary and coding scheme for feature types, feature attributes, and attribute values. The NFDD conforms to a subset of ISO 19126, Geographic information - Feature concept dictionaries and registers, and its information schema.  Esri has chosen a subset of NFDD feature types and attributes for CTM that are appropriate for those doing topographic mapping in a civilian context.

For more information about the NFDD specification visit: https://nsgreg.nga.mil/fdd/registers.jsp?register=NFDD. On this page you will see links that allow you to browse or search the NFDD specification for a complete list of feature and attribute types.  
=======
Civilian Topographic Map (CTM) is designed to allow users to easily create civilian style topographic data and maps using Esri Production Mapping.  CTM includes a geodatabase data model as well as sample configurations for editing, quality assurance, and cartography.  CTM provides the ability to collect and edit data that is suited for creating a 25K scale civilian style topographic map.  CTM provides generalization models to automate the production of 50K cartographic data from larger scale CTM data, such as the sample 25K data provided.  The Map Generation python toolbox automates the process for creating maps for unique areas of interest (AOI) for both the 25K and 50K scale map products.  The Map Generation functionality works on ArcGIS Desktop and ArcGIS Server which allows CTM to be configured as a map product for Product on Demand (POD), a web application that allows users to create high quality cartographic products through a light weight web interface.  More information on POD can be found at:  https://github.com/Esri/product-on-demand.

The schema of CTM is based on the National System for Geospatial Intelligence Feature Data dictionary (NFDD).   The NFDD is a comprehensive dictionary and coding scheme for feature types, feature attributes, and attribute values. The NFDD conforms to a subset of ISO 19126, Geographic information - Feature concept dictionaries and registers, and its information schema.  Esri has chosen a subset of NFDD feature types and attributes for CTM that are appropriate for those doing topographic mapping in a civilian context. 
 
For more information about the NFDD specification visit: https://nsgreg.nga.mil/fdd/registers.jsp?register=NFDD. On this page you will see links that allow you to browse or search the NFDD specification for a complete list of feature and attribute types.  
It is recommended that only the released product files be used in a production environment.  The CTM branches may contain updates that are not fully tested and therefore may not be functional.  The product files and sample scripts in the development branches contains functionality that are not in final form so using them could result in products that do not meet specifications and could cause data corruption.

>>>>>>> Fixed-50K-Development

Contents
---
<<<<<<< HEAD
  - Sample Data
  - Editing Configurations Rules
  - Data Quality Rules
  - Cartogtraphic Configuraiton Rules
  - Map Generator Python Tool
  - Product Library

Instructions
---
  - See the Getting Started Civilian Topographic Map word document

Requirements:
---
  1.  ArcGIS 10.3
  2.  Esri Production Mapping 10.3
=======
  - CTM Geodatabase Schema
  - Sample Data
  - Template Map Documents
  - Style File
  - Grid and Graticules XMLs
  - Map Generator Python Toolbox 
  - Product Library (contains the editing and cartographic specifications)
  - Generalization Toolbox


Instructions
---
  1.  Download the repro
  2.  Open the Getting Started with Civilian Topographic Map.docx for detailed instructions


Requirements:
---
  1.  ArcGIS 10.3.1
  2.  Esri Production Mapping 10.3.1 Patch 1

>>>>>>> Fixed-50K-Development
  
Issues
---
Find a bug or want to request a new feature? Please let us know by submitting an issue.

Contributing
---
Esri welcomes contributions from anyone and everyone. Please see our guidelines for contributing:  https://github.com/esri/contributing

Licensing
---

Copyright 2015 Esri

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

A copy of the license is available in the repository's [license.txt](LICENSE.txt?raw=true) file.
