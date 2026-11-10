# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # ── Relational (inverse) ──────────────────────────────────────────────────
    asset_assignment_ids = fields.One2many(
        comodel_name='asset.assignment',
        inverse_name='employee_id',
        string='Asset Assignments',
    )

    # ── Smart Button Counts ───────────────────────────────────────────────────
    asset_assignment_count = fields.Integer(
        string='Assets Assigned',
        compute='_compute_asset_counts',
    )
    asset_repair_count = fields.Integer(
        string='Repair Requests',
        compute='_compute_asset_counts',
    )

    @api.depends('asset_assignment_ids', 'asset_assignment_ids.actual_return_date')
    def _compute_asset_counts(self):
        AssetRepair = self.env['asset.repair']
        for emp in self:
            emp.asset_assignment_count = len(
                emp.asset_assignment_ids.filtered(lambda a: not a.actual_return_date)
            )
            emp.asset_repair_count = AssetRepair.search_count([
                ('requested_by', '=', emp.id),
            ])

    # ── Action Buttons ────────────────────────────────────────────────────────
    def action_view_assets(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Assigned Assets'),
            'res_model': 'asset.assignment',
            'view_mode': 'tree,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }

    def action_view_repairs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Repair History'),
            'res_model': 'asset.repair',
            'view_mode': 'tree,form',
            'domain': [('requested_by', '=', self.id)],
            'context': {'default_requested_by': self.id},
        }
