# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import time
from datetime import datetime
import xlsxwriter
import base64
import io
import logging
from .formatos_excel import obtener_formatos_excel

class AsistenteReporteCompras(models.TransientModel):
    _name = 'l10n_sv_extra.asistente_reporte_compras'
    _description = 'asistente_reporte_compras'


    diarios_id = fields.Many2many("account.journal", string="Diarios", required=True)
    impuesto_id = fields.Many2one("account.tax", string="Impuesto", required=True)
    folio_inicial = fields.Integer(string="Folio Inicial", required=True, default=1)
    fecha_desde = fields.Date(string="Fecha Inicial", required=True, default=lambda self: time.strftime('%Y-%m-01'))
    fecha_hasta = fields.Date(string="Fecha Final", required=True, default=lambda self: time.strftime('%Y-%m-%d'))
    name = fields.Char('Reporte de compras',default='reporte_compras.xlsx', size=32)
    archivo = fields.Binary('Archivo')

    def print_report(self):
        data = {
             'ids': [],
             'model': 'l10n_sv_extra.asistente_reporte_compras',
             'form': self.read()[0]
        }
        logging.warn(data)
        return self.env.ref('l10n_sv_extra.action_reporte_compras').report_action(self, data=data)

    def print_report_excel(self):
        for w in self:
            dict = {}
            dict['fecha_hasta'] = w['fecha_hasta']
            dict['fecha_desde'] = w['fecha_desde']
            dict['impuesto_id'] = [w.impuesto_id.id, w.impuesto_id.name]
            dict['diarios_id'] =[x.id for x in w.diarios_id]

            res = self.env['report.l10n_sv_extra.reporte_compras'].lineas(dict)
            lineas = res['lineas']
            totales = res['totales']
            f = io.BytesIO()
            libro = xlsxwriter.Workbook(f)
            hoja = libro.add_worksheet('LIBRO DE COMPRAS')

            # FORMATOS DE EXCEL #####################
            formatos = obtener_formatos_excel(libro)

            # MES Y AÑO ##########
            mes = w.fecha_desde.month
            año = w.fecha_desde.year

            mes = self.env['report.l10n_sv_extra.reporte_ventas'].mes(str(mes))

            hoja.merge_range('C3:Q3', w.diarios_id[0].company_id.name, formatos['title_format'])
            hoja.merge_range('C4:Q4', f"REGISTRO, I.V.A. No. {w.folio_inicial}", formatos['title_format'])
            hoja.merge_range('C5:Q5', f"LIBRO DE COMPRAS", formatos['title_format'])
            hoja.merge_range('C6:Q6', f"MES: DE {mes} AÑO: {año}", formatos['title_format'])

            # Ajustar el ancho de las columnas
            hoja.set_column(2, 2, 8)  # No.
            hoja.set_column(3, 3, 10)  # Fecha
            hoja.set_column(4, 4, 12)  #  No. Compro
            hoja.set_column(5, 5, 8)  # No. Registro
            hoja.set_column(6, 6, 12)  # No. Nit
            hoja.set_column(7, 7, 25)  # Proveedor
            #EXENTAS
            hoja.set_column(8, 8, 12)  # EXENTAS
            hoja.set_column(9, 9, 12)  # Importaciones
            hoja.set_column(10, 10, 12)  # Internacionales
            #GRAVADAS
            hoja.set_column(11, 11, 12)  # Internas
            hoja.set_column(12, 12, 12)  # Importaciones
            hoja.set_column(13, 13, 12)  # Inernacionales
            hoja.set_column(14, 14, 12)  # IVA
            hoja.set_column(15, 15, 13)  # Total Compras
            hoja.set_column(16, 16, 13)  # Retencion
            hoja.set_column(17, 17, 13)  # Excl.
            # AJUSTE FILA
            hoja.set_row(9, 25)

            y = 8
            # Utiliza merge_range en lugar de write_merge
            hoja.merge_range(y, 2, y + 1, 2, 'No. Corr', formatos['column_format'])
            hoja.merge_range(y, 3, y + 1, 3, 'Fecha de\nEmisión', formatos['column_format'])
            hoja.merge_range(y, 4, y + 1, 4, 'No. del\nComprobante', formatos['column_format'])
            hoja.merge_range(y, 5, y + 1, 5, 'No. de Registro', formatos['column_format'])
            hoja.merge_range(y, 6, y + 1, 6, 'No. de NIT Sujeto\n Excl. del Impto', formatos['column_format'])
            hoja.merge_range(y, 7, y + 1, 7, 'Nombre del Proveedor', formatos['column_format'])
            hoja.merge_range(y , 8, y , 10, 'Compras Exentas', formatos['column_format'])
            hoja.write(y + 1, 8, 'Internas', formatos['column_format'])
            hoja.write(y + 1, 9, 'Importaciones', formatos['column_format'])
            hoja.write(y + 1, 10, 'Internaciones', formatos['column_format'])
            hoja.merge_range(y, 11, y, 14, 'Compras Gravadas', formatos['column_format'])
            hoja.write(y + 1, 11, 'Internas', formatos['column_format'])
            hoja.write(y + 1, 12, 'Importaciones', formatos['column_format'])
            hoja.write(y + 1, 13, 'Internaciones\nde Servicios', formatos['column_format'])
            hoja.write(y + 1, 14, 'I.V.A. Crédito\nFiscal', formatos['column_format'])
            hoja.merge_range(y, 15, y + 1, 15, 'Total Compras', formatos['column_format'])
            hoja.merge_range(y, 16, y + 1, 16, 'Retención a\nTerceros', formatos['column_format'])
            hoja.merge_range(y, 17, y + 1, 17, 'Compras a\nSujetos Excl\nDel Impto.', formatos['column_format'])

            res = self.env['report.l10n_sv_extra.reporte_compras'].lineas(dict)
            lineas = res['lineas']
            totales = res['totales']
            y += 1
            # LINEAS DE FACTURA
            for linea in lineas:
                y += 1
                hoja.write(y, 2, linea['correlativo'], formatos['text_border'])
                hoja.write(y, 3, linea['fecha'], formatos['formato_fecha'])
                hoja.write(y, 4, linea['numero_comprobante'], formatos['body_format'])
                hoja.write(y, 5, linea['numero_registro'], formatos['body_format'])
                hoja.write(y, 6, linea['nit'], formatos['body_format'])
                hoja.write(y, 7, linea['proveedor'], formatos['body_format'])
                hoja.write(y, 8, linea['exentas_internas'], formatos['body_format'])
                hoja.write(y, 9, linea['exentas_importaciones'], formatos['body_format'])
                hoja.write(y, 10, linea['exentas_internaciones'], formatos['body_format'])
                hoja.write(y, 11, linea['gravadas_internas'], formatos['body_format'])
                hoja.write(y, 12, linea['gravadas_importaciones'], formatos['body_format'])
                hoja.write(y, 13, linea['gravadas_internaciones'], formatos['body_format'])
                hoja.write(y, 14, linea['iva'], formatos['body_format'])
                hoja.write(y, 15, linea['total'], formatos['body_format'])
                hoja.write(y, 16, linea['terceros'], formatos['body_format'])
                hoja.write(y, 17, linea['excl'], formatos['body_format'])
            ####### TOTAL
            y += 1
            hoja.write(y, 2, '', formatos['grantotal_format'])
            hoja.write(y, 3, '', formatos['grantotal_format'])
            hoja.write(y, 4, '', formatos['grantotal_format'])
            hoja.write(y, 5, '', formatos['grantotal_format'])
            hoja.write(y, 6, '', formatos['grantotal_format'])
            hoja.write(y, 7, 'TOTAL', formatos['grantotal_format'])
            hoja.write(y, 8, totales['grand_total']['exento_interno'], formatos['grantotal_format'])
            hoja.write(y, 9, totales['grand_total']['exento_importaciones'], formatos['grantotal_format'])
            hoja.write(y, 10, totales['grand_total']['exento_internaciones'], formatos['grantotal_format'])
            hoja.write(y, 11, totales['grand_total']['gravadas_internas'], formatos['grantotal_format'])
            hoja.write(y, 12, totales['grand_total']['gravadas_importaciones'], formatos['grantotal_format'])
            hoja.write(y, 13, totales['grand_total']['gravadas_internaciones'], formatos['grantotal_format'])
            hoja.write(y, 14, totales['grand_total']['iva'], formatos['grantotal_format'])
            hoja.write(y, 15, totales['grand_total']['total'], formatos['grantotal_format'])
            hoja.write(y, 16, totales['grand_total']['terceros'], formatos['grantotal_format'])
            hoja.write(y, 17, totales['grand_total']['excl'], formatos['grantotal_format'])

            y += 2
            hoja.write(y, 5, "Nombre del contador", formatos['text'])
            hoja.write(y, 11, "Firma:", formatos['text'])

            libro.close()
            archivo = base64.b64encode(f.getvalue())
            self.write({'archivo': archivo})

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'l10n_sv_extra.asistente_reporte_compras',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
