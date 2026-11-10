# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AssetRepair(models.Model):
    _name = 'asset.repair'
    _description = 'Asset Repair Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'request_date desc'
    _rec_name = 'name'

    # ── Fields ───────────────────────────────────────────────────────────────
    name = fields.Char(
        string='Repair Reference',
        readonly=True,
        copy=False,
        default='New',
    )
    asset_id = fields.Many2one(
        comodel_name='asset.asset',
        string='Asset',
        required=True,
        tracking=True,
        ondelete='restrict',
    )
    requested_by = fields.Many2one(
        comodel_name='hr.employee',
        string='Requested By',
        required=True,
        default=lambda self: self.env.user.employee_id,
        tracking=True,
    )
    request_date = fields.Date(
        string='Request Date',
        default=fields.Date.today,
        required=True,
        tracking=True,
    )
    issue_description = fields.Text(
        string='Issue Description',
        required=True,
    )
    repair_cost = fields.Float(
        string='Repair Cost',
        digits=(16, 2),
        tracking=True,
    )
    status = fields.Selection(
        selection=[
            ('new', 'New'),
            ('in_progress', 'In Progress'),
            ('done', 'Done'),
            ('rejected', 'Rejected'),
        ],
        string='Status',
        default='new',
        required=True,
        tracking=True,
    )
    completion_date = fields.Date(string='Completion Date', tracking=True)
    technician_notes = fields.Text(string='Technician Notes')

    # ── Computed ─────────────────────────────────────────────────────────────
    asset_status = fields.Selection(
        related='asset_id.status',
        string='Asset Status',
        readonly=True,
    )
    asset_condition = fields.Selection(
        related='asset_id.condition',
        string='Asset Condition',
        readonly=True,
    )

    # ── ORM Overrides ─────────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('asset.repair') or 'New'
        return super().create(vals_list)

    # ── Status Actions ────────────────────────────────────────────────────────
    def action_set_in_progress(self):
        for rec in self:
            rec.write({'status': 'in_progress'})
            rec.asset_id.write({'status': 'under_repair'})

    def action_set_done(self):
        for rec in self:
            rec.write({
                'status': 'done',
                'completion_date': fields.Date.today(),
            })
            # Restore asset status to available (or assigned if still assigned)
            active_assignment = self.env['asset.assignment'].search([
                ('asset_id', '=', rec.asset_id.id),
                ('actual_return_date', '=', False),
            ], limit=1)
            new_status = 'assigned' if active_assignment else 'available'
            rec.asset_id.write({'status': new_status})

    def action_set_rejected(self):
        for rec in self:
            rec.write({'status': 'rejected'})
            # Restore asset status
            active_assignment = self.env['asset.assignment'].search([
                ('asset_id', '=', rec.asset_id.id),
                ('actual_return_date', '=', False),
            ], limit=1)
            new_status = 'assigned' if active_assignment else 'available'
            rec.asset_id.write({'status': new_status})

    def action_reset_to_new(self):
        for rec in self:
            if rec.status in ('rejected',):
                rec.write({'status': 'new'})

    # ── Constraint ───────────────────────────────────────────────────────────
    @api.constrains('repair_cost')
    def _check_repair_cost(self):
        for rec in self:
            if rec.repair_cost < 0:
                raise ValidationError(_('Repair cost cannot be negative.'))

