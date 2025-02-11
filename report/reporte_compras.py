# -*- encoding: utf-8 -*-

from odoo import api, models
from odoo.exceptions import UserError
from datetime import datetime
import logging

class ReporteCompras(models.AbstractModel):
    _name = 'report.l10n_sv_extra.reporte_compras'
    _description = 'reporte_compras'

    def lineas(self, datos):
        totales = {}

        totales['num_facturas'] = 0
        totales['grand_total'] = {
            'exento_interno':0,
            'exento_importaciones':0,
            'exento_internaciones':0,
            'gravadas_internas': 0,
            'gravadas_importaciones': 0,
            'gravadas_internaciones': 0,
            'iva':0,
            'total':0,
            'terceros':0,
            'excl':0,
        }
        totales['servicio'] = {'exento':0,'neto':0,'iva':0,'percepcion':0,'total':0}

        journal_ids = [x for x in datos['diarios_id']]
        facturas = self.env['account.move'].search([
            ('state','in',['posted']),
            ('move_type','in',['in_invoice','in_refund']),
            ('journal_id','in',journal_ids),
            ('date','<=',datos['fecha_hasta']),
            ('date','>=',datos['fecha_desde']),
        ], order='date, name')

        lineas = []
        correlativo = 1
        mes_actual = ''
        for f in facturas:
            if mes_actual != datetime.strftime(f.date, '%Y-%m'):
                mes_actual = datetime.strftime(f.date, '%Y-%m')
                correlativo = 1

            totales['num_facturas'] += 1

            tipo_cambio = 1
            if f.currency_id.id != f.company_id.currency_id.id:
                total = 0
                for l in f.line_ids:
                    if l.account_id.id == f.account_id.id:
                        total += l.credit - l.debit
                tipo_cambio = abs(total / f.amount_total)

            tipo = 'FACT'
            if f.move_type != 'in_invoice':
                tipo = 'NC'
            if f.partner_id.pequenio_contribuyente:
                tipo += ' PEQ'

            linea = {
                'correlativo': correlativo,
                'fecha': f.date,
                'numero_comprobante': f.payment_reference or '',
                'numero_registro': f.partner_id.numero_registro or '',
                'nit': f.partner_id.vat,
                'proveedor': f.partner_id.name,
                'exentas_internas': 0,
                'exentas_importaciones': 0,
                'exentas_internaciones': 0,

                'gravadas_internas': 0,
                'gravadas_importaciones': 0,
                'gravadas_internaciones': 0,
                'iva': 0,
                'total': 0,
                'terceros':0,
                'excl':0
            }



            correlativo += 1
            for l in f.invoice_line_ids:
                precio = ( l.price_unit * (1-(l.discount or 0.0)/100.0) ) * tipo_cambio
                if tipo == 'NC':
                    precio = precio * -1
                # TIPO DE LINEA NO SE ESTA USANDO EN EL REPORTE
                tipo_linea = 'servicio'
                # if f.tipo_gasto == 'mixto':
                #     if l.product_id.type == 'product':
                #         tipo_linea = 'compra'
                #     else:
                #         tipo_linea = 'servicio'

                r = l.tax_ids.compute_all(precio, currency=f.currency_id, quantity=l.quantity, product=l.product_id, partner=f.partner_id)


                if len(l.tax_ids) > 0:
                    for i in r['taxes']:
                        print(f.name,"nameee")
                        print(i,'iiiiiii')
                        if i['id'] == datos['impuesto_id'][0]:
                            # AQUI DEBERIA DE CLASIFICARLO SEGUN EL TIPO DE GRAVADAS POR AHORA TODAS VAN PARA INTERNAS
                            linea['gravadas_internas'] += r['total_excluded']
                            linea['iva'] += i['amount']
                            # GRAND TOTAL
                            totales['grand_total']['gravadas_internas'] += r['total_excluded']
                            totales['grand_total']['iva'] += i['amount']
                        elif i['amount'] > 0:

                            linea['exentas_internas'] += r['total_excluded']
                            # TOTAL AL FINAL DE LA COLUMNA SEGUN TIPO DE LINEA
                            totales[tipo_linea]['exento'] += i['amount']
                        # SI TIENE RETENCION ES NEGATIVO Y QUEIRE DECIR QUE ES FSE
                        elif i['amount'] < 0:
                            #
                            linea['excl'] += r['total_excluded']
                            totales['grand_total']['excl'] += r['total_excluded']

                else:
                    linea['exentas_internas'] += r['total_excluded']
                # SI ES DIFERETEN A FACTRUA DE SUJETO EXCLUIDO LO SUMAMOS EN LA COLUMNA TOTAL COMPRAS, SINO SE QUEDA EN COMPRAS SUJETO EXCL
                if f.journal_id.tipo_documento_fel_sv != '14':
                    # TOTAL AL FINAL DE LA FILA
                    linea['total'] += precio * l.quantity
                    # COLUMNA TOTAL COMPRAS
                    totales['grand_total']['total'] += precio * l.quantity

            # if f.partner_id.pequenio_contribuyente:
            #     totales['pequenio_contribuyente'] += linea['base']

            lineas.append(linea)

        return { 'lineas': lineas, 'totales': totales }

    def mes(self, numero):
        dict = {}
        dict['01'] = 'ENERO'
        dict['02'] = 'FEBRERO'
        dict['03'] = 'MARZO'
        dict['04'] = 'ABRIL'
        dict['05'] = 'MAYO'
        dict['06'] = 'JUNIO'
        dict['07'] = 'JULIO'
        dict['08'] = 'AGOSTO'
        dict['09'] = 'SEPTIEMBRE'
        dict['10'] = 'OCTUBRE'
        dict['11'] = 'NOVIEMBRE'
        dict['12'] = 'DICIEMBRE'
        return(dict[numero])

    @api.model
    def _get_report_values(self, docids, data=None):
        return self.get_report_values(docids, data)

    @api.model
    def get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_ids', []))

        if len(data['form']['diarios_id']) == 0:
            raise UserError("Por favor ingrese al menos un diario.")

        diario = self.env['account.journal'].browse(data['form']['diarios_id'][0])

        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'lineas': self.lineas,
            'mes': self.mes,
            'direccion': diario.direccion and diario.direccion.street,
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
