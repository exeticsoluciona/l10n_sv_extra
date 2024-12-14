# -*- encoding: utf-8 -*-

{
    'name': 'El Salvador - Reportes y funcionalidad extra',
    'version': '16.0.0.0',
    'category': 'Localization',
    'description': """ Reportes requeridos y otra funcionalidad extra para llevar un contabilidad en El Salvador. """,
      'author': 'Alexander Garzo',
    'website': 'http://integrall.solutions/',
    'depends': ['l10n_sv'],
    'data': [
        'views/account_view.xml',
        'views/reporte_ventas.xml',
        'views/reporte_compras.xml',
        'views/reporte_mayor.xml',
        'views/reporte_kardex.xml',
        'views/report.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'installable': True,
    'license': 'LGPL-3',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
