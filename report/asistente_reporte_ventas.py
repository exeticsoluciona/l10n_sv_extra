# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import time
import xlsxwriter
import base64
import io
from datetime import datetime
from .formatos_excel import obtener_formatos_excel

class AsistenteReporteVentas(models.TransientModel):
    _name = 'l10n_sv_extra.asistente_reporte_ventas'

    diarios_id = fields.Many2many("account.journal", string="Diarios", required=True)
    impuesto_id = fields.Many2one("account.tax", string="Impuesto", required=True)
    folio_inicial = fields.Integer(string="Folio Inicial", required=True, default=1)
    resumido = fields.Boolean(string="Resumido")
    fecha_desde = fields.Date(string="Fecha Inicial", required=True, default=lambda self: time.strftime('%Y-%m-01'))
    fecha_hasta = fields.Date(string="Fecha Final", required=True, default=lambda self: time.strftime('%Y-%m-%d'))
    name = fields.Char('Nombre archivo', default='reporte_ventas.xlsx',size=32)
    archivo = fields.Binary('Archivo', filters='.xls')

    def print_report_contribuyente(self):
        self.resumido = False
        data = {
             'ids': [],
             'model': 'l10n_sv_extra.asistente_reporte_ventas',
             'form': self.read()[0]
        }
        return self.env.ref('l10n_sv_extra.action_reporte_ventas').report_action(self, data=data)

    def print_report_consumidor_final(self):
        self.resumido = True
        data = {
             'ids': [],
             'model': 'l10n_sv_extra.asistente_reporte_ventas',
             'form': self.read()[0]
        }
        return self.env.ref('l10n_sv_extra.action_reporte_ventas').report_action(self, data=data)\



    def print_report_excel_contribuyente(self):
        for w in self:

            dict = {}
            dict['fecha_hasta'] = w['fecha_hasta']
            dict['fecha_desde'] = w['fecha_desde']
            dict['impuesto_id'] = [w.impuesto_id.id, w.impuesto_id.name]
            dict['diarios_id'] =[x.id for x in w.diarios_id]

            
            res = self.env['report.l10n_sv_extra.reporte_ventas'].lineas(dict)
            lineas = res['lineas']
            totales = res['totales']
            f = io.BytesIO()
            libro = xlsxwriter.Workbook(f)
            hoja = libro.add_worksheet('LIBRO DE VENTAS')
            # FORMATOS DE EXCEL #####################
            title_format = libro.add_format({
                'bold': True,
                'font_size': 10,
                'align': 'center',
                'valign': 'vcenter',
            })
            text = libro.add_format({'font_size':9})
            expresadoendolares_format = libro.add_format({
                'bold': True,
                'font_size': 6,
                'align': 'center',
                'valign': 'vcenter',
            })

            column_format = libro.add_format({
                'bold': True,
                'font_size': 9,
                'align': 'center',
                'valign': 'vcenter',
                'border' :1,
            })
            num_format = libro.add_format({
                'font_size': 9,
                'right': 1,
                'left': 1,
                'num_format': '#,##0.00'
            })
            body_format = libro.add_format({
                'font_size': 9,
                'right': 1,
                'left': 1,
                # 'num_format': '#,##0.00'
            })
            formato_fecha = libro.add_format({'num_format': 'dd/mm/yy', 'font_size': '10','right': 1,
                'left': 1,})

            total_format = libro.add_format({
                'font_size': 8,
                'num_format': '#,##0.00',
                'border':1,
            })
            total_format2 = libro.add_format({
                'font_size': 8,
                'num_format': '#,##0.00',
                'right': 1,
                'left': 1,
                'align': 'center',


            })
            total_format3 = libro.add_format({
                'font_size': 8,
                'num_format': '#,##0.00',
                'right': 1,
                'left': 1,


            })
            total_format3bold = libro.add_format({
                'font_size': 8,
                'num_format': '#,##0.00',
                'right': 1,
                'left': 1,
                'bold':True

            })
            grantotal_format = libro.add_format({
                'font_size': 8,
                'num_format': '#,##0.00',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
            })
            grantotal_format_border = libro.add_format({
                'font_size': 8,
                'num_format': '#,##0.00',
                'right': 1,
                'left': 1,
                'align': 'center',
                'valign': 'vcenter',
            })
            total_formatrfinal = libro.add_format({
                'font_size': 8,
                'num_format': '#,##0.00',
                'right': 1,
                'left': 1,
                'bottom': 1,
                'bold':True

            })

            # FIN FORMATOS DE EXCEL ##########################
            mes = w.fecha_desde.month
            año = w.fecha_desde.year

            mes = self.env['report.l10n_sv_extra.reporte_ventas'].mes(str(mes))


            # Ajustar el ancho de las columnas
            hoja.set_column(2, 2, 8)  # No.
            hoja.set_column(3, 3, 15)  # Fecha Emision
            hoja.set_column(4, 6, 38)  # No. del CCF
            hoja.set_column(7, 7, 15) # Nit
            hoja.set_column(8, 8, 10) # Dui
            hoja.set_column(9, 9, 35) # Nombre del cliente
            hoja.set_column(10, 10, 13) # No. registro
            hoja.set_column(10, 11, 16) # Ventas Internas
            hoja.set_column(12, 12, 18) # IVA
            hoja.set_column(13, 15, 15) # VENTAS TERCEROS
            hoja.set_column(16, 16, 20) # TOTAL
            hoja.set_column(17, 17, 15) # IVA RETENCION


            hoja.merge_range('C3:T3', w.diarios_id[0].company_id.name, title_format)
            hoja.merge_range('C4:T4', f"REGISTRO, I.V.A. No. {w.folio_inicial}", title_format)
            hoja.merge_range('C5:T5', f"LIBRO DE VENTAS AL CONTRIBUYENTE", title_format)
            hoja.merge_range('C6:T6', f"MES: DE {mes} AÑO: {año}", title_format)
            hoja.merge_range('C7:T7', f"(EXPRESADO EN DOLARES DE LOS ESTADOS UNIDOS DE AMERICA)", expresadoendolares_format)

            y = 8
            # Utiliza merge_range en lugar de write_merge
            hoja.merge_range(y, 2, y + 1, 2, 'NO. CORR.', column_format)
            hoja.merge_range(y, 3, y + 1, 3, 'FECHA DE EMISION', column_format)
            hoja.merge_range(y, 4, y + 1, 4, 'No. DEL CCF', column_format)
            hoja.merge_range(y, 5, y + 1, 5, 'NUMERO DE RESOLUCION', column_format)
            hoja.merge_range(y, 6, y + 1, 6, 'NUMERO DE SERIE', column_format)
            hoja.merge_range(y, 7, y + 1, 7, 'NIT', column_format)
            hoja.merge_range(y, 8, y + 1, 8, 'DUI', column_format)
            hoja.merge_range(y, 9, y + 1, 9, 'NOMBRE DEL CLIENTE', column_format)
            hoja.merge_range(y, 10, y + 1, 10, 'NO. DEL REGISTRO', column_format)
            hoja.merge_range(y, 11, y, 12, 'VENTAS INTERNAS', column_format)
            hoja.write(y+1, 11, 'EXENTAS', column_format)
            hoja.write(y+1, 12, 'GRAVADAS', column_format)
            hoja.merge_range(y, 13, y + 1, 13, 'IVA (DEBITO FISCAL)', column_format)
            hoja.merge_range(y, 14, y + 1, 14, 'VENTA TERCEROS', column_format)
            hoja.merge_range(y, 15, y + 1, 15, 'IVA TERCEROS DEBITO FISCAL', column_format)
            hoja.merge_range(y, 16, y + 1, 16, 'IMPTO PERCIBIDO', column_format)
            hoja.merge_range(y, 17, y + 1, 17, 'TOTAL DE VENTAS', column_format)
            hoja.merge_range(y, 18, y + 1, 18, 'IVA RETENCION 1%', column_format)
            y += 1
            # LINEAS DE FACTURA
            for linea in lineas:
                y += 1
                hoja.write(y, 2, int(linea['correlativo']), body_format)
                hoja.write(y, 3, linea['fecha'], formato_fecha)
                hoja.write(y, 4, linea['ccf'],body_format)
                hoja.write(y, 5, linea['resolucion'],body_format)
                hoja.write(y, 6, linea['serie'],body_format)
                hoja.write(y, 7, linea['nit'],body_format)
                hoja.write(y, 8, linea['dui'],body_format)
                hoja.write(y, 9, linea['cliente'],body_format)
                hoja.write(y, 10, str(linea['numero_registro']),body_format)
                hoja.write(y, 11, linea['exento'],num_format)
                # SI ES EXENTO NO VA NADA EN LA COLUMNA DEL IVA
                hoja.write(y, 12, linea['base'],num_format)
                hoja.write(y, 13, linea['iva'],num_format)
                hoja.write(y, 14, 0,num_format)
                hoja.write(y, 15,0,num_format)
                hoja.write(y, 16, 0,num_format)
                hoja.write(y, 17, linea['total'],num_format)
                hoja.write(y, 18, 0,num_format)
            ####### TOTAL
            y += 1
            hoja.merge_range(f'C{y+1}:K{y+1}', '', total_format)
            hoja.write(y, 11, totales['grand_total']['exento'],total_format)
            hoja.write(y, 12, totales['grand_total']['base'],total_format)
            hoja.write(y, 13, totales['grand_total']['iva'],total_format)
            hoja.write(y, 14, 0,total_format)
            hoja.write(y, 15, 0,total_format)
            hoja.write(y, 16, 0,total_format)
            hoja.write(y, 17, totales['grand_total']['total'],total_format)
            hoja.write(y, 18, 0,total_format)
            y += 3
            # GRAN TOTAL
            hoja.merge_range(y, 2, y+1 , 10, '', total_format)

            hoja.merge_range(y, 11, y , 12, 'PROPIAS', grantotal_format)
            hoja.write(y+1, 11,  "VALOR NETO", grantotal_format)
            hoja.write(y+1, 12,  "DEBITO FISCAL", grantotal_format)

            hoja.merge_range(y, 13, y, 14, 'A CUENTA DE TERCEROS', grantotal_format)
            hoja.write(y + 1, 13, "VALOR NETO", grantotal_format)
            hoja.write(y + 1, 14,  "DEBITO FISCAL", grantotal_format)
            y += 2
            hoja.merge_range(y, 2, y, 10, 'VENTAS NETAS INTERNAS GRAVADAS A CONTRIBUYENTES',total_format3 )
            hoja.write(y, 11,totales['contribuyente']['gravadas'] , total_format2)
            hoja.write( y, 12,totales['contribuyente']['iva'] , total_format2)
            hoja.write( y, 13,0 , total_format2)
            hoja.write( y, 14,0 , total_format2)
            y += 1
            hoja.merge_range(y, 2, y, 10, 'NOTAS DE CREDITO', total_format3)
            hoja.write(y, 11, totales['nota_credito']['base'], total_format2)
            hoja.write(y, 12, totales['nota_credito']['iva'], total_format2)
            hoja.write(y, 13, 0, total_format2)
            hoja.write(y, 14, 0, total_format2)
            y += 1

            hoja.merge_range(y, 2, y, 10, 'VENTAS NETAS INTERNAS GRAVADAS A CONSUMIDOR FINAL', total_format3)
            hoja.write(y, 11, totales['consumidor_final']['gravadas'], total_format2)
            hoja.write(y, 12, totales['consumidor_final']['iva'], total_format2)
            hoja.write(y, 13, 0, total_format2)
            hoja.write(y, 14, 0, total_format2)
            y += 1
            TOTAL_GRAVADAS = totales['consumidor_final']['gravadas'] + totales['contribuyente']['gravadas'] + totales['nota_credito']['base']
            TOTAL_IVA_GRAVADAS = totales['consumidor_final']['iva'] + totales['contribuyente']['iva'] + totales['nota_credito']['iva']
            hoja.merge_range(y, 2, y, 10, 'TOTAL DE OPERACIONES INTERNAS GRABADAS', total_format3bold)
            hoja.write(y, 11, TOTAL_GRAVADAS, grantotal_format)
            hoja.write(y, 12, TOTAL_IVA_GRAVADAS, grantotal_format)
            hoja.write(y, 13, 0, grantotal_format)
            hoja.write(y, 14,0 , grantotal_format)
            y += 1
            hoja.merge_range(y, 2, y, 10, 'VENTAS NETAS INTERNAS EXENTAS CONTRIBUYENTE', total_format3)
            hoja.write(y, 11, totales['contribuyente']['exento'], grantotal_format_border)
            hoja.write(y, 12, 0, grantotal_format_border)
            hoja.write(y, 13, 0, grantotal_format_border)
            hoja.write(y, 14, 0, grantotal_format_border)
            y += 1
            hoja.merge_range(y, 2, y, 10, 'VENTAS NETAS INTERNAS EXENTAS ACONSUMIDOR FINAL', total_format3)
            hoja.write(y, 11, totales['consumidor_final']['exento'], grantotal_format_border)
            hoja.write(y, 12, 0, grantotal_format_border)
            hoja.write(y, 13, 0, grantotal_format_border)
            hoja.write(y, 14, 0, grantotal_format_border)
            y += 1
            TOTAL_EXENTO = totales['contribuyente']['exento'] + totales['consumidor_final']['exento']
            hoja.merge_range(y, 2, y, 10, 'TOTAL DE OPERACIONES INTERNAS EXENTAS', total_format3bold)
            hoja.write(y, 11, TOTAL_EXENTO, grantotal_format)
            hoja.write(y, 12, 0, grantotal_format)
            hoja.write(y, 13, 0, grantotal_format)
            hoja.write(y, 14, 0, grantotal_format)
            y += 1
            hoja.merge_range(y, 2, y, 10, 'EXPORTACIONES SEGUN FACTURAS', total_format3)
            hoja.write(y, 11, 0, grantotal_format)
            hoja.write(y, 12, 0, grantotal_format)
            hoja.write(y, 13, 0, grantotal_format)
            hoja.write(y, 14, 0, grantotal_format)
            y += 1
            TOTAL_VENTAS = totales['grand_total']['exento'] + totales['grand_total']['base']
            TOTAL_IVA = totales['grand_total']['iva']
            hoja.merge_range(y, 2, y, 10, 'TOTAL VENTAS', total_formatrfinal)
            hoja.write(y, 11, TOTAL_VENTAS, grantotal_format)
            hoja.write(y, 12, TOTAL_IVA, grantotal_format)
            hoja.write(y, 13, 0, grantotal_format)
            hoja.write(y, 14, 0, grantotal_format)

            #firma
            y += 2
            hoja.write(y, 2, "Nombre del contador", text)
            hoja.write(y, 11, "Firma:", text)

            libro.close()
            archivo = base64.b64encode(f.getvalue())
            self.write({'archivo':archivo})
            return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'l10n_sv_extra.asistente_reporte_ventas',
                'res_id': self.id,
                'view_id': False,
                'type': 'ir.actions.act_window',
                'target': 'new',
            }

    def print_report_excel_consumidor(self):
        for w in self:
            dict = {}
            dict['fecha_hasta'] = w['fecha_hasta']
            dict['fecha_desde'] = w['fecha_desde']
            dict['impuesto_id'] = [w.impuesto_id.id, w.impuesto_id.name]
            dict['diarios_id'] = [x.id for x in w.diarios_id]

            f = io.BytesIO()
            libro = xlsxwriter.Workbook(f)
            hoja = libro.add_worksheet('LIBRO DE VENTAS CONSUMIDOR')
            # FORMATOS DE EXCEL #####################
            # Obtener los formatos usando la función importada
            formatos = obtener_formatos_excel(libro)
            # FIN FORMATO EXCEL ##################
            mes = w.fecha_desde.month
            año = w.fecha_desde.year

            mes = self.env['report.l10n_sv_extra.reporte_ventas'].mes(str(mes))

            hoja.merge_range('C3:O3', w.diarios_id[0].company_id.name, formatos['title_format'])
            hoja.merge_range('C4:O4', f"REGISTRO, I.V.A. No. {w.folio_inicial}", formatos['title_format'])
            hoja.merge_range('C5:O5', f"LIBRO DE VENTAS AL CONSUMIDOR", formatos['title_format'])
            hoja.merge_range('C6:O6', f"MES: DE {mes} AÑO: {año}", formatos['title_format'])
            hoja.merge_range('C7:O7', "(EXPRESADO EN DOLARES DE LOS ESTADOS UNIDOS DE AMERICA)",
                              formatos['expresadoendolares_format'])
            # Ajustar el ancho de las columnas
            hoja.set_column(2, 2, 8)  # No.
            hoja.set_column(3, 3, 30)  # DEL  # No.
            hoja.set_column(4, 4, 30)  # AL  # No.
            hoja.set_column(5, 5, 30)  # No. SERIE
            hoja.set_column(6, 6, 30)  # No. RESOLU
            hoja.set_column(7, 7, 15)  # VENTAS
            hoja.set_column(8, 8, 15)  # EXENTAS
            hoja.set_column(9, 9, 15)  # LOCALES
            hoja.set_column(10, 10, 15)  # EXPORTACION
            hoja.set_column(11, 11, 15)  # EXPORTACION

            y = 8
            # Utiliza merge_range en lugar de write_merge
            hoja.merge_range(y, 2, y + 2, 2, 'FECHA DE EMISION', formatos['column_format'])
            hoja.merge_range(y, 3, y + 2, 3, 'NO. DE RESOLUCION.', formatos['column_format'])
            hoja.merge_range(y, 4, y + 2, 4, 'NO. DE SERIE', formatos['column_format'])
            hoja.merge_range(y, 5, y + 2, 5, 'NO. DOCUMENTO DEL', formatos['column_format'])
            hoja.merge_range(y, 6, y + 2, 6, 'NO. DOCUMENTO AL', formatos['column_format'])
            hoja.merge_range(y, 7, y , 10, 'VENTAS', formatos['column_format'])
            hoja.merge_range(y + 1, 7, y + 2, 7, 'EXENTAS', formatos['column_format'])
            hoja.merge_range(y + 1, 8, y + 2, 8,  'INTERNAS', formatos['column_format'])
            hoja.merge_range(y + 1, 9, y + 2, 9,  'NO SUJETAS', formatos['column_format'])
            hoja.merge_range(y + 1, 10,y + 2,10,  'GRAVADAS \n LOCALES', formatos['column_format'])
            hoja.merge_range(y , 11,y , 13,  'EXPORTACIONES', formatos['column_format'])
            hoja.merge_range( y + 1, 11, y + 2, 11, 'DENTRO C.A', formatos['column_format'])
            hoja.merge_range( y + 1, 12, y + 2, 12, 'FUERA C.A.', formatos['column_format'])
            hoja.merge_range( y + 1, 13, y + 2, 13, 'DPA.', formatos['column_format'])
            hoja.merge_range(y, 14, y + 2, 14, 'TOTAL DE VENTAS', formatos['column_format'])

            res = self.env['report.l10n_sv_extra.reporte_ventas'].lineas_consumidor(dict)
            lineas = res['lineas']
            totales = res['totales']
            y += 2
            for linea in lineas:
                y += 1
                hoja.write(y, 2, linea['dia'], formatos['formato_fecha'])
                hoja.write(y, 3, linea['resolucion'], formatos['body_format'])
                hoja.write(y, 4, linea['serie'], formatos['body_format'])
                hoja.write(y, 5, linea['del'], formatos['body_format'])
                hoja.write(y, 6, linea['al'], formatos['body_format'])
                hoja.write(y, 7, linea['exento'], formatos['body_format'])
                hoja.write(y, 8, 0, formatos['body_format'])
                hoja.write(y, 9, 0, formatos['body_format'])
                hoja.write(y, 10, linea['local'], formatos['body_format'])
                hoja.write(y, 11, linea['dentroCA'], formatos['body_format'])
                hoja.write(y, 12, linea['fueraCA'], formatos['body_format'])
                hoja.write(y, 13, linea['DPA'], formatos['body_format'])
                hoja.write(y, 14, linea['total'], formatos['body_format'])


            ####### TOTAL
            y += 1
            hoja.write(y, 2, '', formatos['total_format'])
            hoja.write(y, 3, 'TOTAL', formatos['total_format'])
            hoja.write(y, 4, '', formatos['total_format'])
            hoja.write(y, 5, '', formatos['total_format'])
            hoja.write(y, 6, '', formatos['total_format'])
            hoja.write(y, 7, totales['grand_total']['total_exento'], formatos['total_format'])
            hoja.write(y, 8, 0, formatos['total_format'])
            hoja.write(y, 9, 0, formatos['total_format'])
            hoja.write(y, 10, totales['grand_total']['total_locales'], formatos['total_format'])
            hoja.write(y, 11, totales['grand_total']['dentroCA'], formatos['total_format'])
            hoja.write(y, 12, totales['grand_total']['fueraCA'], formatos['total_format'])
            hoja.write(y, 13, totales['grand_total']['DPA'], formatos['total_format'])
            hoja.write(y, 14, totales['grand_total']['total_ventas'], formatos['total_format'])

            # RESUMEN
            y += 2
            hoja.write(y, 6, 'CALCULO I.V.A.', formatos['total_noborder'])
            y += 1
            hoja.write(y, 6, 'Total Ventas', formatos['text'])
            hoja.write(y, 10, totales['grand_total']['total_locales'], formatos['total_noborder'])
            y += 1
            hoja.write(y, 6, 'Entre factor I.V.A.', formatos['total_noborder'])
            hoja.write(y, 10, 1.13, formatos['text'])
            y += 1
            hoja.write(y, 6, 'Total Ventas Netas', formatos['text'])
            hoja.write(y, 10, totales['grand_total']['total_neto'], formatos['total_noborder'])
            y += 1
            hoja.write(y, 6, 'I.V.A.', formatos['text'])
            hoja.write(y, 10, totales['grand_total']['total_iva'], formatos['total_noborder'])
            y += 1
            hoja.write(y, 6, 'Exportaciones', formatos['text'])
            hoja.write(y, 10, totales['grand_total']['total_exportaciones'], formatos['total_noborder'])


            libro.close()
            archivo = base64.b64encode(f.getvalue())
            self.write({'archivo': archivo})

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'l10n_sv_extra.asistente_reporte_ventas',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
