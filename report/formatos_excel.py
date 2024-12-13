def obtener_formatos_excel( libro):
    """Crea y devuelve los formatos de Excel reutilizables."""
    return {
        'title_format': libro.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'center',
            'valign': 'vcenter',
        }),
        'text': libro.add_format({'font_size': 9}),
        'text_border': libro.add_format({
            'font_size': 9,
            'right': 1,
            'left': 1,
        }),
        'expresadoendolares_format': libro.add_format({
            'bold': True,
            'font_size': 6,
            'align': 'center',
            'valign': 'vcenter',
        }),
        'column_format': libro.add_format({
            'bold': True,
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'text_wrap': True,

        }),
        'num_format': libro.add_format({
            'font_size': 9,
            'right': 1,
            'left': 1,
            'num_format': '#,##0.00',
        }),
        'body_format': libro.add_format({
            'font_size': 9,
            'right': 1,
            'left': 1,
            'num_format': '#,##0.00',
        }),
        'formato_fecha': libro.add_format({
            'num_format': 'dd/mm/yyyy',
            'font_size': '10',
            'right': 1,
            'left': 1,
        }),
        'total_format': libro.add_format({
            'font_size': 8,
            'num_format': '#,##0.00',
            'border': 1,
        }),
        'total_format2': libro.add_format({
                'font_size': 8,
                'num_format': '#,##0.00',
                'right': 1,
                'left': 1,
                'align': 'center',


            }),
        'total_format3' : libro.add_format({
                'font_size': 8,
                'num_format': '#,##0.00',
                'right': 1,
                'left': 1,


            }),
        'total_format3bold': libro.add_format({
            'font_size': 8,
            'num_format': '#,##0.00',
            'right': 1,
            'left': 1,
            'bold': True,
        }),
        'grantotal_format': libro.add_format({
            'font_size': 8,
            'num_format': '#,##0.00',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        }),
        'grantotal_format_border': libro.add_format({
            'font_size': 8,
            'num_format': '#,##0.00',
            'right': 1,
            'left': 1,
            'align': 'center',
            'valign': 'vcenter',
        }),
        'total_formatrfinal': libro.add_format({
            'font_size': 8,
            'num_format': '#,##0.00',
            'right': 1,
            'left': 1,
            'bottom': 1,
            'bold': True,
        }),
        'total_noborder': libro.add_format({
            'num_format': '#,##0.00',

        }),
        'total_topbottom': libro.add_format({
            'font_size': 8,
            'num_format': '#,##0.00',
            'top': 1,
            'bottom': 1,
            'bold': True,
        }),
        'text_bottom': libro.add_format({
            'font_size': 12,
            'bottom': 1,
            'num_format': 'dd/mm/yy',
        }),
        'fecha_mayor': libro.add_format({
            'num_format': 'dd/mm/yy',
        })


    }