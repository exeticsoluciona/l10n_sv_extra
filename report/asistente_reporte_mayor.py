# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import time
import xlsxwriter
import base64
import io
from .formatos_excel import obtener_formatos_excel

class AsistenteReporteMayor(models.TransientModel):
    _name = 'l10n_sv_extra.asistente_reporte_mayor'
    _description = 'asistente_reporte_mayor'


    def _default_cuenta(self):
        if len(self.env.context.get('active_ids', [])) > 0:
            return self.env.context.get('active_ids')
        else:
            accounts = self.env['account.account'].search([]).ids
            return self.env['account.account'].search([]).ids

    cuentas_id = fields.Many2many("account.account", string="Cuentas", required=True, default=_default_cuenta)
    grupos_id = fields.Many2many("account.group", string="Grupos", required=True)
    folio_inicial = fields.Integer(string="Folio Inicial", required=True, default=1)
    agrupado_por_dia = fields.Boolean(string="Agrupado por dia")
    fecha_desde = fields.Date(string="Fecha Inicial", required=True, default=lambda self: time.strftime('%Y-%m-01'))
    fecha_hasta = fields.Date(string="Fecha Final", required=True, default=lambda self: time.strftime('%Y-%m-%d'))
    name = fields.Char('Nombre archivo', size=32)
    archivo = fields.Binary('Archivo', )

    def print_report(self):
        data = {
             'ids': [],
             'model': 'l10n_sv_extra.asistente_reporte_mayor',
             'form': self.read()[0]
        }
        return self.env.ref('l10n_sv_extra.action_reporte_mayor').report_action(self, data=data)

    def print_report_excel(self):
        for w in self:
            dict = {}
            dict['fecha_hasta'] = w['fecha_hasta']
            dict['fecha_desde'] = w['fecha_desde']
            dict['agrupado_por_dia'] = w['agrupado_por_dia']
            dict['cuentas_id'] =[x.id for x in w.cuentas_id]
            res = self.env['report.l10n_sv_extra.reporte_mayor'].lineas(dict)

            f = io.BytesIO()
            libro = xlsxwriter.Workbook(f)
            hoja = libro.add_worksheet('LIBRO MAYOR')

            formatos = obtener_formatos_excel(libro)
            # ANCHOOO
            hoja.set_column(1, 1, 8)  # No.
            hoja.set_column(2, 2, 10)  #FECHA
            hoja.set_column(3, 3, 30)  #Concepto
            hoja.set_column(4, 4, 15)  #Debe
            hoja.set_column(5, 5, 15)  #Haber
            hoja.set_column(6, 6, 15)  #Acumulado
            # ANCHOOOO
            hoja.merge_range('B3:H3', self.env.company.name, formatos['title_format'])
            hoja.merge_range('B4:H4', 'LIBRO DIARIO MAYOR', formatos['title_format'])
            y = 5
            fecha_hasta = w['fecha_hasta']
            hoja.merge_range(y,1,y,3,f'Movimientos al {fecha_hasta}',formatos['text_bottom'])
            hoja.write(y,4,'',formatos['text_bottom'])
            hoja.merge_range(y,5,y,6,'Expresado en dolares',formatos['text_bottom'])
            y += 1
            hoja.write(y,1,'',formatos['text_bottom'])
            hoja.write(y,2,'Fecha',formatos['text_bottom'])
            hoja.write(y,3,'Conceptos',formatos['text_bottom'])
            hoja.write(y,4,'Debe',formatos['text_bottom'])
            hoja.write(y,5,'Haber',formatos['text_bottom'])
            hoja.write(y,6,'Saldo Acumulado',formatos['text_bottom'])


            lineas = res['lineas']
            totales = res['totales']

            for cuenta in lineas:
                y += 1
                hoja.write(y, 1, cuenta['codigo'],formatos['total_noborder'])
                hoja.write(y, 3, cuenta['cuenta'],formatos['total_noborder'])
                hoja.write(y, 5,'Saldo Anterior')
                hoja.write(y, 6, cuenta['saldo_inicial'],formatos['total_noborder'])
                # LOS MIVIMIENTOS POR FECHAS
                for fechas in cuenta['fechas']:
                    y += 1
                    hoja.write(y, 2, fechas['fecha'],formatos['fecha_mayor'])
                    hoja.write(y, 3, 'Movimientos Del Día')
                    hoja.write(y, 4, fechas['debe'],formatos['total_noborder'])
                    hoja.write(y, 5, fechas['haber'],formatos['total_noborder'])
                y += 1

                hoja.write(y, 3, 'TOTAL')
                total_acumulado =  cuenta['saldo_inicial'] + cuenta['total_debe'] -cuenta['total_haber']
                hoja.write(y, 4, cuenta['total_debe'],formatos['total_topbottom'])
                hoja.write(y, 5, cuenta['total_haber'],formatos['total_topbottom'])
                hoja.write(y, 6, total_acumulado,formatos['total_topbottom'])
                y += 1

            y+=1
            hoja.write(y, 3, 'GRAN TOTAL', formatos['total_topbottom'])
            hoja.write(y, 4, totales['debe'], formatos['total_topbottom'])
            hoja.write(y, 5, totales['haber'], formatos['total_topbottom'])
            libro.close()
            datos = base64.b64encode(f.getvalue())
            self.write({'archivo':datos, 'name':'libro_mayor.xlsx'})

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'l10n_sv_extra.asistente_reporte_mayor',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
