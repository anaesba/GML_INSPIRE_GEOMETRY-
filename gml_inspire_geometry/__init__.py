# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GML_INSPIRE_GEOMETRY
                                 A QGIS plugin
 Plugin para corregir geometrías y generar archivos GML en formato INSPIRE
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2024-06-27
        copyright            : (C) 2024 by Ana I. Escobar Bayon
        email                : aescobay@usal.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface): 
    from .GML_INSPIRE_GEOMETRY import GML_INSPIRE_GEOMETRY
    return GML_INSPIRE_GEOMETRY(iface)