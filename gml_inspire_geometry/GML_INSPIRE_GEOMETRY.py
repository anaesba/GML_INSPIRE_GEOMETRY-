from qgis.core import (
    QgsApplication, QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY, QgsField, QgsVectorFileWriter
)
from qgis.gui import QgsMapCanvas, QgsLayerTreeMapCanvasBridge
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox, QDialog, QFormLayout, QLineEdit, QDialogButtonBox
from qgis.PyQt.QtCore import QVariant
import os
import lxml.etree as ET
 
class DataInputDialog(QDialog):
    def __init__(self):
        """ Llama al constructor de la clase base QDialog """
        super().__init__();  
        """ Título de la ventana de diálogo """
        self.setWindowTitle("Datos Obligatorios") 
        
        """ Crea un diseño de formulario para organizar los widgets """
        self.layout = QFormLayout(self)  
        
        """ Crea dos campos de entrada (QLineEdit) para "Local ID" y "Namespace y los añade al formulario con etiquetas """ 
        self.localIdInput = QLineEdit(self)  
        self.namespaceInput = QLineEdit(self)

        self.layout.addRow("Local ID:", self.localIdInput)
        self.layout.addRow("Namespace:", self.namespaceInput)
        
        """ Crea una caja de botones con los botones Ok y Cancel """
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        
        """ Añade la caja de botones al diseño del formulario """
        self.layout.addWidget(self.buttonBox)
 
 
    def get_data(self):
        """Obtiene los datos ingresados por el usuario."""
        return self.localIdInput.text(), self.namespaceInput.text()
 
class GML_INSPIRE_GEOMETRY:
    def __init__(self, iface):
        """Inicializa el plugin con la interfaz de QGIS."""
        self.iface = iface
        self.canvas = iface.mapCanvas()
 
    def initGui(self):
        """Inicializa la GUI del plugin."""
        self.action = QAction("GML_INSPIRE_GEOMETRY ", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&GML_INSPIRE_GEOMETRY ", self.action)
 
    def unload(self):
        """Desactiva el plugin y elimina los íconos."""
        self.iface.removePluginMenu("&GML_INSPIRE_GEOMETRY", self.action)
        self.iface.removeToolBarIcon(self.action)
 
    def run(self):
        """Se ejecuta el plugin, permitiendo al usuario seleccionar un archivo y procesarlo."""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        """Muestra un diálogo para seleccionar el archivo vectorial de formato .gml o .shp"""
        file_dialog.setNameFilter("Vector files (*.shp *.gml)")  
        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            self.process_file(file_path)
 
    def process_file(self, file_path):
        """Procesa el archivo seleccionado, corrige geometrías y guarda el archivo GML."""
        """carga el archivo seleccionado como una capa vectorial y verifica si es válida; sino, muestra en error."""
        layer = QgsVectorLayer(file_path, "Input Layer", "ogr") 
        if not layer.isValid():
            QMessageBox.critical(None, "Error", "No se pudo cargar el archivo.")
            return
        self.correct_geometries(layer)

        dialog = DataInputDialog()
        """Al aceptar se guarda la capa como un archivo GML en formato INSPIRE."""
        if dialog.exec_() == QDialog.Accepted: 
            local_id, namespace = dialog.get_data() 
            output_path = QFileDialog.getSaveFileName(None, "Guardar archivo GML", "", "GML files (*.gml)")[0]
            if output_path:
                self.save_to_gml(layer, output_path, local_id, namespace)
                self.validate_gml(output_path)
 
    def correct_geometries(self, layer):
        """Corrige las geometrías inválidas en la capa."""
        error_count = 0
        for feature in layer.getFeatures():
            geom = feature.geometry()
            """Verifica las geometrías válidas y en caso contratio las corrige."""
            if not geom.isGeosValid():  
                fixed_geom = geom.makeValid()
                if fixed_geom.isEmpty():
                    error_count += 1
                else:
                    feature.setGeometry(fixed_geom)
                    layer.updateFeature(feature)
        if error_count > 0:
            QMessageBox.warning(None, "Advertencia", f"Se encontraron y no se pudieron corregir {error_count} errores geométricos.")
 
    def save_to_gml(self, layer, output_path, local_id, namespace):
        """Guarda la capa procesada en formato GML en la ruta especificada."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.generate_gml(layer, local_id, namespace))
 
    def generate_gml(self, layer, local_id, namespace):
        """Genera el contenido GML conforme al estándar INSPIRE, utilizando los datos proporcionados como “Local ID” y “Namespace”."""
        gml = [
            '<?xml version="1.0" encoding="utf-8"?>',
            '<FeatureCollection xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
            'xmlns:gml="http://www.opengis.net/gml/3.2"',
            'xmlns:xlink="http://www.w3.org/1999/xlink"',
            'xmlns:cp="http://inspire.ec.europa.eu/schemas/cp/4.0"',
            'xmlns:gmd="http://www.isotc211.org/2005/gmd"',
            'xsi:schemaLocation="http://www.opengis.net/wfs/2.0 http://schemas.opengis.net/wfs/2.0/wfs.xsd',
            'http://inspire.ec.europa.eu/schemas/cp/4.0 http://inspire.ec.europa.eu/schemas/cp/4.0/CadastralParcels.xsd"',
            'xmlns="http://www.opengis.net/wfs/2.0" timeStamp="2024-06-19T18:50:11" numberMatched="1" numberReturned="1">',
            '<member>',
        ]
        for feature in layer.getFeatures():
            geom = feature.geometry()
            area = round(geom.area(), 2)  # Redondea el área a dos decimales
            if geom.isMultipart():
                polygons = geom.asMultiPolygon()
            else:
                polygons = [geom.asPolygon()]

            for poly in polygons:
                coords = " ".join(f"{pt.x()} {pt.y()}" for pt in poly[0])
                gml.extend([
                    f'<cp:CadastralParcel gml:id="{local_id}">',
                    f'<cp:areaValue uom="m2">{area}</cp:areaValue>',
                    '<cp:beginLifespanVersion xsi:nil="true" nilReason="other:unpopulated"/>',
                    '<cp:geometry>',
                    f'<gml:MultiSurface gml:id="MultiSurface_{local_id}" srsName="urn:ogc:def:crs:EPSG::25830">',
                    '<gml:surfaceMember>',
                    f'<gml:Surface gml:id="Surface_{local_id}" srsName="urn:ogc:def:crs:EPSG::25830">',
                    '<gml:patches>',
                    '<gml:PolygonPatch>',
                    '<gml:exterior>',
                    '<gml:LinearRing>',
                    f'<gml:posList srsDimension="2">{coords}</gml:posList>',
                    '</gml:LinearRing>',
                    '</gml:exterior>',
                    '</gml:PolygonPatch>',
                    '</gml:patches>',
                    '</gml:Surface>',
                    '</gml:surfaceMember>',
                    '</gml:MultiSurface>',
                    '</cp:geometry>',
                    f'<cp:inspireId xmlns:base="http://inspire.ec.europa.eu/schemas/base/3.3">',
                    '<Identifier xmlns="http://inspire.ec.europa.eu/schemas/base/3.3">',
                    f'<localId>{local_id}</localId>',
                    f'<namespace>{namespace}</namespace>',
                    '</Identifier>',
                    '</cp:inspireId>',
                    '<cp:label/>',
                    '<cp:nationalCadastralReference/>',
                    '</cp:CadastralParcel>',
                ])
        gml.extend([
            '</member>',
            '</FeatureCollection>'
        ])
        return "\n".join(gml)
 
    def validate_gml(self, gml_path):
        """Valida el archivo GML contra el esquema INSPIRE utilizando el archivo .xsd generado."""
        try:
            schema_path = os.path.join(os.path.dirname(__file__), 'schemas', 'CadastralParcels.xsd')
            schema = ET.XMLSchema(file=schema_path)
            parser = ET.XMLParser(schema=schema)
            with open(gml_path, 'r', encoding='utf-8') as f:
                ET.fromstring(f.read(), parser)
                """Muestra si el archivo GML es válido"""
            QMessageBox.information(None, "Validación", "El archivo GML es válido según el esquema INSPIRE.") 
        except ET.XMLSchemaError as e:
            QMessageBox.critical(None, "Error de validación", f"El archivo GML no es válido: {e}")
 
def classFactory(iface):
    """Función de fábrica para el plugin."""
    return GML_INSPIRE_GEOMETRY (iface)
