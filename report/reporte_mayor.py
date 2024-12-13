# -*- encoding: utf-8 -*-

from odoo import api, models, fields
import logging


class ReporteMayor(models.AbstractModel):
    _name = 'report.l10n_sv_extra.reporte_mayor'

    def retornar_saldo_inicial_todos_anios(self, cuenta, fecha_desde):

        saldo_inicial = 0
        # QUEREY PARA TRAER TODOS LAS LINEAS CONTABLES SEGUN LA CUENTA DE LO ACUMULADO HASTA UN DIA ANTERIOR, (SALDO ACUMULADO)
        self.env.cr.execute(
            'select a.id, a.code as codigo, a.name as cuenta, sum(l.debit) as debe, sum(l.credit) as haber ' \
            'from account_move_line l join account_account a on(l.account_id = a.id)' \
            'where l.parent_state = \'posted\' and a.id = %s and l.date < %s group by a.id, a.code, a.name',
            (cuenta, fecha_desde))
        for m in self.env.cr.dictfetchall():
            saldo_inicial += m['debe'] - m['haber']
        return saldo_inicial

    def lineas(self, datos):
        totales = {}
        lineas_resumidas = {}
        lineas = []
        totales['debe'] = 0
        totales['haber'] = 0
        totales['saldo_inicial'] = 0
        totales['saldo_final'] = 0

        account_ids = [x for x in datos['cuentas_id']]
        movimientos = self.env['account.move.line'].search([
            ('account_id', 'in', account_ids),
            ('date', '<=', datos['fecha_hasta']),
            ('date', '>=', datos['fecha_desde'])])

        accounts_str = ','.join(map(str, datos['cuentas_id']))
        print(accounts_str,"account!!!")
        if datos['agrupado_por_dia']:
            query = '''
                    SELECT 
                        a.id, 
                        a.code AS codigo, 
                        a.name AS cuenta, 
                        l.date AS fecha, 
                        SUM(l.debit) AS debe, 
                        SUM(l.credit) AS haber
                    FROM 
                        account_move_line l 
                    JOIN 
                        account_account a 
                        ON l.account_id = a.id
                    WHERE 
                        l.parent_state = 'posted' 
                        AND a.id IN ({accounts})
                        AND l.date >= %s 
                        AND l.date <= %s
                    GROUP BY 
                        a.id, 
                        a.code, 
                        a.name, 
                        l.date
                    ORDER BY 
                        a.code
                '''.format(accounts=accounts_str)
            self.env.cr.execute(query, (datos['fecha_desde'], datos['fecha_hasta']))
            for r in self.env.cr.dictfetchall():
                totales['debe'] += r['debe']
                totales['haber'] += r['haber']
                linea = {
                    'id': r['id'],
                    'fecha': r['fecha'],
                    'codigo': r['codigo'],
                    'cuenta': r['cuenta'],
                    'saldo_inicial': 0,
                    'debe': r['debe'],
                    'haber': r['haber'],
                    'saldo_final': 0,
                    # ESTO ES PARA SABER LO DEL BOLEANO
                    # 'balance_inicial': r['balance_inicial']
                }
                lineas.append(linea)

            cuentas_agrupadas = {}
            # obtenemos el codigo de la cuento del dict de la slineas atenriores
            llave = 'codigo'
            for l in lineas:
                if l[llave] not in cuentas_agrupadas:
                    cuentas_agrupadas[l[llave]] = {
                        'codigo': l[llave],
                        'cuenta': l['cuenta'],
                        'saldo_inicial': 0,
                        'saldo_final': 0,
                        'fechas': [],
                        'total_debe': 0,
                        'total_haber': 0
                    }
                    # AGREGAMOS EL SALDIO INICIAL DE LAC UENTA
                    cuentas_agrupadas[l[llave]]['saldo_inicial'] = self.retornar_saldo_inicial_todos_anios(l['id'],datos['fecha_desde'])
                # AGREGAMOS CADA LINEA A FECHAS
                cuentas_agrupadas[l[llave]]['fechas'].append(l)
                # SE AGREGA UN SUBNIVEL CON LAS FECHAS Y DEMAS CAMPOS DE CADA MOVIMIENTO AGRUPADO POR FECHA
            for cuenta in cuentas_agrupadas.values():
                for fecha in cuenta['fechas']:
                    cuenta['total_debe'] += fecha['debe']
                    cuenta['total_haber'] += fecha['haber']
                cuenta['saldo_final'] += cuenta['saldo_inicial'] + cuenta['total_debe'] - cuenta['total_haber']

            lineas = cuentas_agrupadas.values()


        return {'lineas': lineas, 'totales': totales}

    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_ids', []))

        diario = self.env['account.move.line'].browse(data['form']['cuentas_id'][0])

        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'lineas': self.lineas,
            'current_company_id': self.env.company,
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
