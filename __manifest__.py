# -*- coding: utf-8 -*-
{
    'name': 'New Business Report',
    'version': '17.0.1.17.0',
    'summary': 'Vista SQL per calcolo New Business venditori',
    'description': """
        Modulo che espone una vista SQL per il calcolo del New Business.
        Gestisce 3 tipologie di prodotto:
        - Canone / Offerta a corpo (solo prima milestone)
        - Attivazione (valore intero)
        - Pacchetti Ore BU Digital Innovation / Catering (valore intero)
    """,
    'author': 'Progetto e Soluzioni',
    'category': 'Sales',
    'depends': ['sale', 'project', 'sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/new_business_v1_17_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
