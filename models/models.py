# -*- coding: utf-8 -*-

from odoo import models, fields

class PickingExt(models.Model):
    _inherit = 'stock.picking'


    def _action_done(self):
        self._check_company()

        todo_moves = self.mapped('move_lines').filtered(lambda self: self.state in ['draft', 'waiting', 'partially_available', 'assigned', 'confirmed'])
        for picking in self:
            if picking.owner_id:
                picking.move_lines.write({'restrict_partner_id': picking.owner_id.id})
                picking.move_line_ids.write({'owner_id': picking.owner_id.id})
        todo_moves._action_done(cancel_backorder=self.env.context.get('cancel_backorder'))
        self.write({'date_done': self.scheduled_date, 'priority': '0'})

        done_incoming_moves = self.filtered(lambda p: p.picking_type_id.code == 'incoming').move_lines.filtered(lambda m: m.state == 'done')
        done_incoming_moves._trigger_assign()

        self._send_confirmation_email()
        return True


    def button_validate(self):
        res = super(PickingExt, self).button_validate()
        if res == True:
            for move_id in self.move_lines:
                move_id.date = self.date_done
                for move_line_id in move_id.move_line_ids:
                    move_line_id.date = self.date_done
        return res


class StockValuationLayerExt(models.Model):
    _inherit = 'stock.valuation.layer'

    historical_date = fields.Datetime(string='Historical Date', related='stock_move_id.date', store=True)



class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def action_create_invoice(self):
        res = super(PurchaseOrder, self).action_create_invoice()
        account_moves = self.invoice_ids.filtered(lambda inv: inv.state == 'draft')
        for account_move in account_moves:
            account_move.date = self.effective_date
            account_move.invoice_date = self.effective_date
            for account_move_line in account_move.line_ids:
                account_move_line.date = self.effective_date
        return res