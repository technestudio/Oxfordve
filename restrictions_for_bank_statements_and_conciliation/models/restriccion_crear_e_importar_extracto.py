# -*- coding: utf-8 -*-


from odoo import models, fields, api, exceptions


class AccountBankStatementInherit(models.Model):
    _inherit = 'account.bank.statement'

    @api.model
    def create(self, vals):   
        
        res = super(AccountBankStatementInherit,self).create(vals)
        u = self.env['res.users'].search([('id', '=', self.env.uid)])
        if(not u.has_group('restrictions_for_bank_statements_and_conciliation.group_crear_e_importar_extractos_bancarios')):
           raise exceptions.UserError('No tienes permiso para crear extractos bancarios.')    

        return res


class AccountMoveLineInherit(models.Model):
    _inherit = "account.move.line"

    @api.model
    def action_reconcile(self):
        res = super(AccountMoveLineInherit,self).action_reconcile()
        u = self.env['res.users'].search([('id', '=', self.env.uid)])
        if(not u.has_group('restrictions_for_bank_statements_and_conciliation.group_conciliar_extractos_bancarios')):
           raise exceptions.UserError('No tienes permiso para conciliar extractos bancarios.')    

        return res

