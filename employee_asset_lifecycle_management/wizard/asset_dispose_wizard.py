# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AssetDisposeWizard(models.TransientModel):
    _name = 'asset.dispose.wizard'
    _description = 'Asset Disposal Wizard'

    asset_id = fields.Many2one(
        comodel_name='asset.asset',
        string='Asset',
        required=True,
        readonly=True,
    )
    disposal_date = fields.Date(
        string='Disposal Date',
        default=fields.Date.today,
        required=True,
    )
    disposal_reason = fields.Selection(
        selection=[
            ('end_of_life', 'End of Life'),
            ('damaged_beyond_repair', 'Damaged Beyond Repair'),
            ('stolen', 'Stolen / Lost'),
            ('obsolete', 'Obsolete'),
            ('sold', 'Sold'),
            ('other', 'Other'),
        ],
        string='Disposal Reason',
        required=True,
    )
    disposal_notes = fields.Text(string='Notes')
    salvage_value = fields.Float(string='Salvage / Recovered Value', digits=(16, 2))

    def action_confirm_disposal(self):
        self.ensure_one()
        if self.asset_id.status == 'assigned':
            raise ValidationError(
                _('Cannot dispose of an asset that is currently assigned to an employee. '
                  'Please return the asset first.')
            )
        self.asset_id.write({
            'status': 'disposed',
            'condition': 'damaged',
        })
        self.asset_id.message_post(
            body=_(
                'Asset disposed on <b>%s</b>.<br/>'
                'Reason: <b>%s</b><br/>'
                'Salvage Value: <b>%.2f</b><br/>'
                'Notes: %s'
            ) % (
                self.disposal_date,
                dict(self._fields['disposal_reason'].selection).get(self.disposal_reason, ''),
                self.salvage_value,
                self.disposal_notes or '-',
            )
        )
        return {'type': 'ir.actions.act_window_close'}

