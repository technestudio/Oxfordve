# -*- coding: utf-8 -*-

from functools import reduce

from odoo import _, api, fields, models
from odoo.osv.expression import (AND, AND_OPERATOR, OR_OPERATOR, is_leaf,
                                 is_operator, normalize_domain, normalize_leaf)


def compute_existence(previous, record):
    if (record.product_id.qty_available - record.qty_done) == 0:
        return record.qty_done
    elif record.location_id.usage == 'inventory' and record.location_id.scrap_location == False:
        return record.qty_done + previous
    elif not record.picking_code and record.location_dest_id.scrap_location == False and record.location_dest_id.usage == 'inventory':
        return previous - record.qty_done
    elif record.picking_code == "internal":
        return previous
    elif record.picking_code == "outgoing":
        return previous - record.qty_done
    else:
        return record.qty_done + previous


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    number = fields.Char(
        string='Numero',
        related='picking_id.origin'
    )
    customer_id = fields.Many2one(
        'res.partner',
        string='Cliente o Proveedor',
        related='picking_id.partner_id'
    )
    entrada = fields.Float(
        string='Entrada',
        compute='_compute_in_out'
    )
    salida = fields.Float(
        string='Salida',
        compute='_compute_in_out'
    )
    saldo_existencia = fields.Float(
        string='Saldo en existencia',
        compute='_compute_in_out'
    )

    extra_context = {}

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        self.extra_context.update(
            {"domain": args, "offset": offset, "order": order})
        return super().search(args, offset=offset, limit=limit, order=order, count=count)

    @api.depends('qty_done', 'reference')
    def _compute_in_out(self):
        order = self.extra_context.get('order', 'date ASC')
        show_existence = False
        anterior = 0.0

        first_order, *_ = order.split(",")

        if first_order.lower().strip() in {"date asc", "date"}:
            show_existence = True
            offset = self.extra_context.get('offset', 0)
            extra_domain = self.extra_context.get('domain', [])
            domain = [('id', 'not in', self.ids)]

            if extra_domain:
                new_domain = []

                for i, elm in enumerate(extra_domain):
                    if is_leaf(elm) and i > 0:
                        field, operator, value = normalize_leaf(elm)
                        if field == 'date' and operator in {'>', '>='}:
                            for j, olm in enumerate(new_domain[::-1]):
                                if is_operator(olm):
                                    new_domain.pop(-j-1)
                                    if olm in {AND_OPERATOR, OR_OPERATOR}:
                                        break
                            continue
                    new_domain.append(elm)

                domain = AND([domain, normalize_domain(new_domain)])

            anterior = reduce(
                compute_existence,
                self.sudo().search(domain, limit=(offset if offset > 0 else None), order=order),
                anterior
            )

        for record in self:
            entrada = 0.0
            salida = 0.0

            if (
                record.location_id.usage == 'inventory' and
                record.location_id.scrap_location == False
            ) or record.picking_code in {'incoming', 'internal', 'mrp_operation'}:
                entrada = record.qty_done

            if (
                not record.picking_code and record.location_dest_id.usage == 'inventory' and
                record.location_dest_id.scrap_location == False
            ) or record.picking_code in {'outgoing', 'internal'}:
                salida = record.qty_done

            record.salida = salida
            record.entrada = entrada

            if show_existence:
                record.saldo_existencia = anterior = compute_existence(
                    anterior, record)
            else:
                record.saldo_existencia = False
