# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class SaleNewBusinessReport(models.Model):
    """
    Vista SQL per il calcolo del New Business per venditore.

    Logica per tipologia prodotto:
    ─────────────────────────────────────────────────────────────────────
    CANONE / OFFERTA A CORPO
      service_policy = 'delivered_milestones' AND auto_milestone = True
      → si considera SOLO il valore del primo anno = price_unit × 1
        (la qty rappresenta gli anni, si ignora)
      → Anno/Mese NB: anno/mese della DATA CONFERMA ORDINE (date_order)

    ATTIVAZIONE
      service_policy = 'delivered_milestones' AND auto_milestone = False
      → si considera il valore intero della riga (qty × prezzo)
      → Anno/Mese NB: anno/mese della data conferma ordine

    PACCHETTI ORE
      service_policy IN ('ordered_prepaid', 'delivered_manual')
      categoria IN ('Pacchetti Ore BU Digital Innovation',
                    'Pacchetti Ore BU Catering')
      → si considera il valore intero della riga
      → Anno/Mese NB: anno/mese della data conferma ordine
    ─────────────────────────────────────────────────────────────────────

    Sono esclusi:
      - Preventivi (stato draft / sent)
      - Ordini annullati (stato cancel)
    """

    _name = 'new.business.v1.17'
    _description = 'New Business Report'
    _auto = False          # Odoo non crea una tabella: usa la VIEW SQL
    _rec_name = 'order_name'
    _order = 'new_business_year desc, new_business_month desc, order_name'

    # ── Campi esposti ──────────────────────────────────────────────────

    order_name = fields.Char(
        string='Ordine di vendita',
        readonly=True,
    )
    salesperson_id = fields.Many2one(
        'res.users',
        string='Venditore',
        readonly=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        readonly=True,
    )
    indirect_partner_id = fields.Many2one(
        'res.partner',
        string='Cliente Indiretto',
        readonly=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Prodotto',
        readonly=True,
    )
    product_type = fields.Selection(
        selection=[
            ('canone',      'Canone / Offerta a corpo'),
            ('attivazione', 'Attivazione'),
            ('ore_di',      'Pacchetti Ore - Digital Innovation'),
            ('ore_cat',     'Pacchetti Ore - Catering'),
        ],
        string='Tipologia prodotto',
        readonly=True,
    )
    new_business_year = fields.Char(
        string='Anno New Business',
        readonly=True,
    )
    new_business_month = fields.Char(
        string='Mese New Business',
        readonly=True,
    )
    order_date = fields.Date(
        string='Data ordine',
        readonly=True,
    )
    product_qty = fields.Float(
        string='Quantita',
        digits=(16, 2),
        readonly=True,
    )
    price_unit_line = fields.Float(
        string='Prezzo Unitario',
        digits=(16, 2),
        readonly=True,
    )
    amount_new_business = fields.Float(
        string='Valore New Business (EUR)',
        digits=(16, 2),
        readonly=True,
    )
    order_line_id = fields.Many2one(
        'sale.order.line',
        string='Riga ODV',
        readonly=True,
    )
    order_id = fields.Many2one(
        'sale.order',
        string='Ordine',
        readonly=True,
    )

    # ── Vista SQL ──────────────────────────────────────────────────────

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(r"""
            CREATE OR REPLACE VIEW %(table)s AS (

            /* ============================================================
               BLOCCO 1 - CANONE / OFFERTA A CORPO
               Discriminante: invoice_policy = 'delivery'
                              AND service_type = 'milestones'
                              AND auto_milestone = True
               Regola:        valore del PRIMO ANNO = price_unit x 1
               Anno NB:       anno della DATA CONFERMA ORDINE (date_order)
               ============================================================ */
            SELECT
                sol.id * 10 + 1                              AS id,
                so.id                                        AS order_id,
                sol.id                                       AS order_line_id,
                so.name                                      AS order_name,
                so.user_id                                   AS salesperson_id,
                so.partner_id                                AS partner_id,
                so.x_studio_cliente_indiretto                AS indirect_partner_id,
                sol.product_id                               AS product_id,
                'canone'::varchar                            AS product_type,
                TO_CHAR(so.date_order, 'YYYY')               AS new_business_year,
                TO_CHAR(so.date_order, 'FMMM')               AS new_business_month,
                so.date_order::date                          AS order_date,
                sol.product_uom_qty                          AS product_qty,
                sol.price_unit                               AS price_unit_line,
                ROUND(
                    sol.price_unit * (1.0 - COALESCE(sol.discount, 0) / 100.0),
                    2
                )                                            AS amount_new_business

            FROM sale_order_line  sol
            JOIN sale_order       so   ON so.id  = sol.order_id
            JOIN product_product  pp   ON pp.id  = sol.product_id
            JOIN product_template pt   ON pt.id  = pp.product_tmpl_id

            WHERE so.state IN ('sale', 'done')
              AND pt.invoice_policy = 'delivery'
              AND pt.service_type   = 'milestones'
              AND pt.auto_milestone = True

            /* ============================================================
               BLOCCO 2 - ATTIVAZIONE
               Discriminante: invoice_policy = 'delivery'
                              AND service_type = 'milestones'
                              AND auto_milestone = False
               Regola:        valore intero della riga (qty x prezzo netto)
               Anno NB:       anno della data conferma ordine
               ============================================================ */
            UNION ALL

            SELECT
                sol.id * 10 + 2                              AS id,
                so.id                                        AS order_id,
                sol.id                                       AS order_line_id,
                so.name                                      AS order_name,
                so.user_id                                   AS salesperson_id,
                so.partner_id                                AS partner_id,
                so.x_studio_cliente_indiretto                AS indirect_partner_id,
                sol.product_id                               AS product_id,
                'attivazione'::varchar                       AS product_type,
                TO_CHAR(so.date_order, 'YYYY')               AS new_business_year,
                TO_CHAR(so.date_order, 'FMMM')               AS new_business_month,
                so.date_order::date                          AS order_date,
                sol.product_uom_qty                          AS product_qty,
                sol.price_unit                               AS price_unit_line,
                ROUND(sol.price_subtotal, 2)                 AS amount_new_business

            FROM sale_order_line  sol
            JOIN sale_order       so   ON so.id  = sol.order_id
            JOIN product_product  pp   ON pp.id  = sol.product_id
            JOIN product_template pt   ON pt.id  = pp.product_tmpl_id

            WHERE so.state IN ('sale', 'done')
              AND pt.invoice_policy = 'delivery'
              AND pt.service_type   = 'milestones'
              AND pt.auto_milestone = False

            /* ============================================================
               BLOCCO 3 - PACCHETTI ORE
               Discriminante: service_policy IN ('ordered_prepaid',
                                                 'delivered_manual')
                              AND categoria IN ('Pacchetti Ore BU ...')
               Regola:        valore intero della riga
               Anno NB:       anno della data conferma ordine
               ============================================================ */
            UNION ALL

            SELECT
                sol.id * 10 + 3                              AS id,
                so.id                                        AS order_id,
                sol.id                                       AS order_line_id,
                so.name                                      AS order_name,
                so.user_id                                   AS salesperson_id,
                so.partner_id                                AS partner_id,
                so.x_studio_cliente_indiretto                AS indirect_partner_id,
                sol.product_id                               AS product_id,
                CASE
                    WHEN pc.name = 'Pacchetti Ore BU Digital Innovation'
                        THEN 'ore_di'
                    WHEN pc.name = 'Pacchetti Ore BU Catering'
                        THEN 'ore_cat'
                END::varchar                                 AS product_type,
                TO_CHAR(so.date_order, 'YYYY')               AS new_business_year,
                TO_CHAR(so.date_order, 'FMMM')               AS new_business_month,
                so.date_order::date                          AS order_date,
                sol.product_uom_qty                          AS product_qty,
                sol.price_unit                               AS price_unit_line,
                ROUND(sol.price_subtotal, 2)                 AS amount_new_business

            FROM sale_order_line  sol
            JOIN sale_order       so   ON so.id  = sol.order_id
            JOIN product_product  pp   ON pp.id  = sol.product_id
            JOIN product_template pt   ON pt.id  = pp.product_tmpl_id
            JOIN product_category pc   ON pc.id  = pt.categ_id

            WHERE so.state IN ('sale', 'done')
              AND (
                  pt.invoice_policy = 'order'
                  OR (pt.invoice_policy = 'delivery' AND pt.service_type = 'manual')
              )
              AND pc.name IN (
                  'Pacchetti Ore BU Digital Innovation',
                  'Pacchetti Ore BU Catering'
              )

        )
        """ % {'table': self._table})
