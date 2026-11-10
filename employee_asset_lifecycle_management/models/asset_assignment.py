# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AssetAssignment(models.Model):
    _name = 'asset.assignment'
    _description = 'Asset Assignment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'assignment_date desc'
    _rec_name = 'display_name'

    # ── Fields ───────────────────────────────────────────────────────────────
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        required=True,
        tracking=True,
        ondelete='restrict',
    )
    asset_id = fields.Many2one(
        comodel_name='asset.asset',
        string='Asset',
        required=True,
        tracking=True,
        ondelete='restrict',
        domain=[('status', 'in', ['available', 'returned'])],
    )
    assigned_by = fields.Many2one(
        comodel_name='res.users',
        string='Assigned By',
        default=lambda self: self.env.user,
        tracking=True,
    )
    assignment_date = fields.Date(
        string='Assignment Date',
        default=fields.Date.today,
        required=True,
        tracking=True,
    )
    expected_return_date = fields.Date(
        string='Expected Return Date',
        tracking=True,
    )
    actual_return_date = fields.Date(
        string='Actual Return Date',
        tracking=True,
    )
    condition_on_return = fields.Selection(
        selection=[
            ('new', 'New'),
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('poor', 'Poor'),
            ('damaged', 'Damaged'),
        ],
        string='Condition on Return',
        tracking=True,
    )
    remarks = fields.Text(string='Remarks')
    is_returned = fields.Boolean(
        string='Returned',
        compute='_compute_is_returned',
        store=True,
    )
    state = fields.Selection(
        selection=[
            ('active', 'Active'),
            ('returned', 'Returned'),
        ],
        string='State',
        default='active',
        tracking=True,
    )

    # ── Display Name ─────────────────────────────────────────────────────────
    display_name = fields.Char(
        string='Reference',
        compute='_compute_display_name',
        store=True,
    )

    @api.depends('employee_id', 'asset_id', 'assignment_date')
    def _compute_display_name(self):
        for rec in self:
            parts = []
            if rec.employee_id:
                parts.append(rec.employee_id.name)
            if rec.asset_id:
                parts.append(rec.asset_id.name)
            if rec.assignment_date:
                parts.append(str(rec.assignment_date))
            rec.display_name = ' / '.join(parts) if parts else _('New Assignment')

    @api.depends('actual_return_date')
    def _compute_is_returned(self):
        for rec in self:
            rec.is_returned = bool(rec.actual_return_date)

    # ── Constraints ──────────────────────────────────────────────────────────
    @api.constrains('expected_return_date', 'assignment_date')
    def _check_return_date(self):
        for rec in self:
            if rec.expected_return_date and rec.assignment_date:
                if rec.expected_return_date < rec.assignment_date:
                    raise ValidationError(
                        _('Expected Return Date cannot be before Assignment Date.')
                    )

    @api.constrains('actual_return_date', 'assignment_date')
    def _check_actual_return_date(self):
        for rec in self:
            if rec.actual_return_date and rec.assignment_date:
                if rec.actual_return_date < rec.assignment_date:
                    raise ValidationError(
                        _('Actual Return Date cannot be before Assignment Date.')
                    )

    @api.constrains('asset_id', 'actual_return_date')
    def _check_asset_not_double_assigned(self):
        for rec in self:
            if not rec.actual_return_date:
                # Find other active assignments for same asset
                duplicate = self.search([
                    ('asset_id', '=', rec.asset_id.id),
                    ('actual_return_date', '=', False),
                    ('id', '!=', rec.id),
                ])
                if duplicate:
                    raise ValidationError(
                        _('Asset "%s" is already actively assigned to another employee. '
                          'Please return it first.') % rec.asset_id.name
                    )

    # ── ORM Overrides ─────────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if record.asset_id:
                record.asset_id.write({'status': 'assigned'})
        return records

    def write(self, vals):
        result = super().write(vals)
        for rec in self:
            # If actual_return_date is set, mark asset as returned
            if rec.actual_return_date and rec.asset_id:
                rec.asset_id.write({'status': 'returned'})
                if rec.condition_on_return:
                    rec.asset_id.write({'condition': rec.condition_on_return})
                rec.state = 'returned'
        return result

    # ── Button Actions ────────────────────────────────────────────────────────
    def action_return_asset(self):
        """Mark the asset as returned today."""
        self.ensure_one()
        self.write({
            'actual_return_date': fields.Date.today(),
            'state': 'returned',
        })
        self.asset_id.write({'status': 'returned'})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Asset Returned'),
                'message': _('Asset "%s" has been successfully returned.') % self.asset_id.name,
                'type': 'success',
                'sticky': False,
            },
        }

