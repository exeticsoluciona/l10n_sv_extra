# -*- encoding: utf-8 -*-

from odoo import api, models
from odoo.exceptions import UserError
import logging


class ReporteVentas(models.AbstractModel):
    _name = 'report.l10n_sv_extra.reporte_ventas'
    _description = 'reporte_ventas'


    def lineas(self, datos):
        totales = {}

        totales['num_facturas'] = 0
        # ESTO ES PARA LAS FACTURAS FISCALES
        totales['grand_total'] = {'exento': 0, 'base': 0, 'iva': 0, 'total': 0}
        totales['contribuyente'] = { 'gravadas': 0, 'iva': 0,'exento':0}
        totales['consumidor_final'] = {'gravadas': 0, 'iva': 0,'exento':0}
        totales['nota_credito'] = {'base': 0, 'iva': 0}


        journal_ids = [x for x in datos['diarios_id']]

        facturas = self.env['account.move'].search([
            ('state', 'in', ['posted']),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('journal_id', 'in', journal_ids),
            ('date', '<=', datos['fecha_hasta']),
            ('date', '>=', datos['fecha_desde']),
        ], order='date, name')

        lineas = []
        correlativo = 1
        for f in facturas:
            totales['num_facturas'] += 1

            tipo_cambio = 1
            impuesto = self.env['account.tax'].browse(datos['impuesto_id'][0])

            if f.currency_id.id != f.company_id.currency_id.id:
                # Probar con impuesto inicialmente
                for l in f.invoice_line_ids:
                    if impuesto in l.tax_ids:
                        if l.amount_currency != 0:
                            tipo_cambio = l.balance / l.amount_currency

                # Si la factura no tiene impuesto, entonces usar cuenta por cobrar/pagar
                if tipo_cambio == 1:
                    total = 0
                    for l in f.line_ids:
                        if l.account_id.reconcile:
                            total += l.debit - l.credit
                    if f.amount_total != 0:
                        tipo_cambio = abs(total / f.amount_total)

            tipo = 'FACT'
            if f.move_type == 'out_refund':
                if f.amount_untaxed >= 0:
                    tipo = 'NC'
                else:
                    tipo = 'ND'

            numero = f.name

            if f.name:
                serie = f.name  # [0:9]
            else:
                serie = ''

            linea = {
                'correlativo': correlativo,
                'fecha': f.date,
                # CODIGO DE GENERACION
                'ccf':f.firma_fel_sv,
                # NUMERO DE CONTROL
                'resolucion': f.numero_control,
                # SELLO DE RECEPCION
                'serie': f.sello_recepcion,
                'nit': f.partner_id.vat if f.partner_id.tipo_documento_fel == '36' else '',
                'dui': f.partner_id.vat if f.partner_id.tipo_documento_fel == '13' else '',
                'cliente': f.partner_id.name,
                'numero_registro': f.partner_id.numero_registro,
                'exento': 0,
                'base': 0,
                'iva': 0,
                'total': 0
            }

            correlativo += 1
            for l in f.invoice_line_ids:
                # DETERMINAMOS EL PRECIO POSITIVO O NEGATIVO SEGUN SI ES NC
                precio = (l.price_unit * (1 - (l.discount or 0.0) / 100.0)) * tipo_cambio
                if tipo == 'NC':
                    precio = precio * -1


                r = l.tax_ids.compute_all(precio, currency=f.currency_id, quantity=l.quantity, product=l.product_id,
                                          partner=f.partner_id)

                """ACA DIENTIFICAMOS EL TIPO DE LINEA CONTRIBUYENTE O CF"""
                tipo_linea = 'contribuyente'
                wizardtax_in_invoice = datos['impuesto_id'][0] in l.tax_ids.ids
                if f.partner_id.vat != "CF":
                    tipo_linea = 'contribuyente'
                elif f.partner_id.vat != 'CF' or not f.partner_id.vat:
                    tipo_linea = 'consumidor_final'


                multiplier = 1
                # PARA QUE RECONOZCA EL EXENTO HAY QUE  ELIMINAR EL IMPUESTO
                if len(l.tax_ids) > 0:
                    # BASE IMPONIBLE EN LA LINEA
                    linea['base'] += r['total_excluded']
                    # BASE IMPONIBLE EN EL TOTAL
                    totales['grand_total']['base'] += r['total_excluded']

                    for i in r['taxes']:
                        if i['id'] == datos['impuesto_id'][0]:
                            linea['iva'] += i['amount']
                            #IVA EN EL TOTAL
                            totales['grand_total']['iva'] += i['amount']

                            #GRAVADAS
                            if tipo == 'NC':
                                totales['nota_credito']['base'] += r['total_excluded']
                                totales['nota_credito']['iva'] += i['amount']
                            else:
                                totales[tipo_linea]['gravadas'] += r['total_excluded']
                                totales[tipo_linea]['iva'] += i['amount']

                        elif i['amount'] > 0:
                            # EXENTO
                            linea['exento'] += i['amount']
                            totales['grand_total']['exento'] += i['amount']
                            totales[tipo_linea]['exento'] += r['total_excluded']
                            # SI ES UN IMPUESTO DIFERENTE LO AGREGAMOS AL EXENTO
                            totales[tipo_linea]['iva'] +=  i['amount']
                else:
                    linea['exento'] += r['total_excluded']
                    totales['grand_total']['exento'] += r['total_excluded']
                    totales[tipo_linea]['exento'] += r['total_excluded']


                linea['total'] += precio * l.quantity
                totales['grand_total']['total'] += precio * l.quantity


            lineas.append(linea)

        return {'lineas': lineas, 'totales': totales}

    def lineas_consumidor(self, datos):
        totales = {}

        totales['num_facturas'] = 0
        totales['grand_total'] = {'total_exento': 0,'total_locales': 0,
                                  'total_exportaciones': 0,  'dentroCA': 0,
                                  'fueraCA': 0,  'DPA': 0,
                                  'total_neto': 0,'total_iva': 0, 'total_ventas': 0}

        journal_ids = [x for x in datos['diarios_id']]

        facturas = self.env['account.move'].search([
            ('state', 'in', ['posted']),
            ('move_type', 'in', ['out_invoice',]),
            ('journal_id', 'in', journal_ids),
            ('date', '<=', datos['fecha_hasta']),
            ('date', '>=', datos['fecha_desde']),
        ], order='date, name')

        lineas = []
        correlativo = 1
        for f in facturas:
            totales['num_facturas'] += 1

            tipo_cambio = 1
            impuesto = self.env['account.tax'].browse(datos['impuesto_id'][0])

            if f.currency_id.id != f.company_id.currency_id.id:
                # Probar con impuesto inicialmente
                for l in f.invoice_line_ids:
                    if impuesto in l.tax_ids:
                        if l.amount_currency != 0:
                            tipo_cambio = l.balance / l.amount_currency

                # Si la factura no tiene impuesto, entonces usar cuenta por cobrar/pagar
                if tipo_cambio == 1:
                    total = 0
                    for l in f.line_ids:
                        if l.account_id.reconcile:
                            total += l.debit - l.credit
                    if f.amount_total != 0:
                        tipo_cambio = abs(total / f.amount_total)

            # OJO PREGUNTAR SI AQUI HABRAN NOTAS DE CREDITO
            # if f.move_type == 'out_refund':
            #         tipo = 'NC'


            numero_control = f.numero_control

            if f.name:
                serie = f.name  # [0:9]
            else:
                serie = ''

            linea = {
                'corr':correlativo,
                'dia': f.date,
                'del': f.firma_fel_sv,
                'al': f.firma_fel_sv,
                'serie': f.sello_recepcion,
                'resolucion': numero_control,
                'exento': 0,
                'local': 0,
                'cliente':f.partner_id.name,
                'dentroCA': 0,
                'fueraCA': 0,
                'DPA': 0,
                'total': 0
            }

            correlativo += 1
            for l in f.invoice_line_ids:
                # DETERMINAMOS EL PRECIO POSITIVO O NEGATIVO SEGUN SI ES NC
                precio = (l.price_unit * (1 - (l.discount or 0.0) / 100.0)) * tipo_cambio
                # if tipo == 'NC':
                #     precio = precio * -1

                r = l.tax_ids.compute_all(precio, currency=f.currency_id, quantity=l.quantity, product=l.product_id,
                                          partner=f.partner_id)

                if len(l.tax_ids) > 0:
                    # TOTAL VENTAS NETAS <---> ACUMULADO UNICAMENTE LO LOCAL DEBERIAMOS DE AGREGAR ACA
                    # totales['grand_total']['total_neto'] += r['total_excluded']
                    for i in r['taxes']:
                        if i['id'] == datos['impuesto_id'][0]:
                            # IVA EN EL TOTAL
                            totales['grand_total']['total_iva'] += i['amount']

                        elif i['amount'] > 0:
                            # EXENTO
                            linea['exento'] += i['amount']
                            totales['grand_total']['total_exento'] += i['amount']
                else:
                    linea['exento'] += r['total_excluded']
                    totales['grand_total']['total_exento'] += r['total_excluded']

                # AQUI DEBEMOS DE IDENTIFICAR SI ES FACTURA LOCAL O DE EXPORTACION
                if f.journal_id.tipo_documento_fel_sv == '11':
                        linea[f.tipo_exportacion] += precio * l.quantity
                        totales['grand_total'][f.tipo_exportacion] += precio * l.quantity
                        totales['grand_total']['total_exportaciones'] += precio * l.quantity
                # ESTO ES PARA QUE EL EXENTO NO SE AGREGUE A GRAVADAS TAMBIEN
                elif not linea['exento']:
                    linea['local'] += precio * l.quantity
                    # GRAND TOTAL TOTAL VENTAS
                    totales['grand_total']['total_locales'] += precio * l.quantity
                    totales['grand_total']['total_neto'] += r['total_excluded']
                linea['total'] += precio * l.quantity
                #GRAND TOTAL TOTAL
                totales['grand_total']['total_ventas'] += precio * l.quantity

            lineas.append(linea)

        return {'lineas': lineas, 'totales': totales}

    def mes(self, numero):
        dict = {}
        dict['1'] = 'ENERO'
        dict['2'] = 'FEBRERO'
        dict['3'] = 'MARZO'
        dict['4'] = 'ABRIL'
        dict['5'] = 'MAYO'
        dict['6'] = 'JUNIO'
        dict['7'] = 'JULIO'
        dict['8'] = 'AGOSTO'
        dict['9'] = 'SEPTIEMBRE'
        dict['10'] = 'OCTUBRE'
        dict['11'] = 'NOVIEMBRE'
        dict['12'] = 'DICIEMBRE'
        return (dict[numero])

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
            'direccion_diario': diario.direccion and diario.direccion.street,
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
