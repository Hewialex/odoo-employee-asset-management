# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class AssetDepreciationWizard(models.TransientModel):
    _name = 'asset.depreciation.wizard'
    _description = 'Asset Depreciation Wizard'

    asset_ids = fields.Many2many(
        comodel_name='asset.asset',
        string='Assets to Depreciate',
        default=lambda self: self.env['asset.asset'].browse(self.env.context.get('active_ids', [])),
    )
    compute_all = fields.Boolean(
        string='Compute for ALL Active Assets',
        default=False,
    )

    def action_compute(self):
        if self.compute_all:
            assets = self.env['asset.asset'].search([
                ('status', 'not in', ['disposed']),
                ('depreciation_rate', '>', 0),
            ])
        else:
            assets = self.asset_ids

        assets._compute_current_value()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Depreciation Computed'),
                'message': _('Depreciation has been recalculated for %d asset(s).') % len(assets),
                'type': 'success',
                'sticky': False,
            },
        }

