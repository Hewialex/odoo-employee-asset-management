# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date


class AssetAsset(models.Model):
    _name = 'asset.asset'
    _description = 'Asset'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc'

    # ── Basic Info ──────────────────────────────────────────────────────────
    name = fields.Char(
        string='Asset Name',
        required=True,
        tracking=True,
    )
    asset_ref = fields.Char(
        string='Asset Reference',
        readonly=True,
        copy=False,
        default='New',
    )
    asset_tag = fields.Char(
        string='Asset Tag',
        required=True,
        copy=False,
        tracking=True,
    )
    asset_type = fields.Selection(
        selection=[
            ('laptop', 'Laptop'),
            ('phone', 'Phone'),
            ('id_card', 'ID Card'),
            ('vehicle', 'Vehicle'),
            ('monitor', 'Monitor'),
            ('keyboard', 'Keyboard'),
            ('mouse', 'Mouse'),
            ('tablet', 'Tablet'),
            ('printer', 'Printer'),
            ('other', 'Other'),
        ],
        string='Asset Type',
        required=True,
        tracking=True,
    )
    serial_number = fields.Char(string='Serial Number', copy=False)
    purchase_date = fields.Date(string='Purchase Date')
    warranty_expiry_date = fields.Date(string='Warranty Expiry Date')

    # ── Financial ────────────────────────────────────────────────────────────
    value = fields.Float(
        string='Original Purchase Value',
        digits=(16, 2),
        tracking=True,
    )
    depreciation_rate = fields.Float(
        string='Monthly Depreciation Rate (%)',
        digits=(5, 2),
        help='Percentage of original value depreciated per month.',
    )
    current_value = fields.Float(
        string='Current Value',
        compute='_compute_current_value',
        store=True,
        digits=(16, 2),
        tracking=True,
    )

    # ── Status / Condition ───────────────────────────────────────────────────
    status = fields.Selection(
        selection=[
            ('available', 'Available'),
            ('assigned', 'Assigned'),
            ('under_repair', 'Under Repair'),
            ('returned', 'Returned'),
            ('lost', 'Lost'),
            ('disposed', 'Disposed'),
        ],
        string='Status',
        default='available',
        required=True,
        tracking=True,
    )
    condition = fields.Selection(
        selection=[
            ('new', 'New'),
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('poor', 'Poor'),
            ('damaged', 'Damaged'),
        ],
        string='Condition',
        default='new',
        required=True,
        tracking=True,
    )

    # ── Relational ───────────────────────────────────────────────────────────
    assignment_ids = fields.One2many(
        comodel_name='asset.assignment',
        inverse_name='asset_id',
        string='Assignments',
    )
    repair_ids = fields.One2many(
        comodel_name='asset.repair',
        inverse_name='asset_id',
        string='Repair Requests',
    )
    current_employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Currently Assigned To',
        compute='_compute_current_employee',
        store=True,
    )

    # ── Smart button counts ──────────────────────────────────────────────────
    assignment_count = fields.Integer(
        string='Assignments',
        compute='_compute_assignment_count',
    )
    repair_count = fields.Integer(
        string='Repairs',
        compute='_compute_repair_count',
    )

    # ── Notes ────────────────────────────────────────────────────────────────
    notes = fields.Text(string='Internal Notes')
    image = fields.Image(string='Asset Image', max_width=1920, max_height=1920)

    # ────────────────────────────────────────────────────────────────────────
    # SQL Constraints
    # ────────────────────────────────────────────────────────────────────────
    _sql_constraints = [
        (
            'asset_tag_unique',
            'UNIQUE(asset_tag)',
            'Asset Tag must be unique!',
        ),
    ]

    # ────────────────────────────────────────────────────────────────────────
    # ORM Overrides
    # ────────────────────────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('asset_ref', 'New') == 'New':
                vals['asset_ref'] = self.env['ir.sequence'].next_by_code('asset.asset') or 'New'
        return super().create(vals_list)

    # ────────────────────────────────────────────────────────────────────────
    # Computed Fields
    # ────────────────────────────────────────────────────────────────────────
    @api.depends('value', 'depreciation_rate', 'purchase_date')
    def _compute_current_value(self):
        today = date.today()
        for rec in self:
            if rec.value and rec.purchase_date and rec.depreciation_rate:
                months = (today.year - rec.purchase_date.year) * 12 + (today.month - rec.purchase_date.month)
                months = max(months, 0)
                depreciation = (months * rec.depreciation_rate / 100) * rec.value
                rec.current_value = max(rec.value - depreciation, 0.0)
            else:
                rec.current_value = rec.value or 0.0

    @api.depends('assignment_ids', 'assignment_ids.actual_return_date', 'assignment_ids.employee_id')
    def _compute_current_employee(self):
        for rec in self:
            active_assignment = rec.assignment_ids.filtered(
                lambda a: not a.actual_return_date
            )
            rec.current_employee_id = active_assignment[:1].employee_id if active_assignment else False

    @api.depends('assignment_ids')
    def _compute_assignment_count(self):
        for rec in self:
            rec.assignment_count = len(rec.assignment_ids)

    @api.depends('repair_ids')
    def _compute_repair_count(self):
        for rec in self:
            rec.repair_count = len(rec.repair_ids)

    # ────────────────────────────────────────────────────────────────────────
    # Constraints
    # ────────────────────────────────────────────────────────────────────────
    @api.constrains('warranty_expiry_date', 'purchase_date')
    def _check_warranty_date(self):
        for rec in self:
            if rec.warranty_expiry_date and rec.purchase_date:
                if rec.warranty_expiry_date < rec.purchase_date:
                    raise ValidationError(_('Warranty Expiry Date cannot be before Purchase Date.'))

    @api.constrains('depreciation_rate')
    def _check_depreciation_rate(self):
        for rec in self:
            if rec.depreciation_rate < 0 or rec.depreciation_rate > 100:
                raise ValidationError(_('Depreciation Rate must be between 0 and 100.'))

    # ────────────────────────────────────────────────────────────────────────
    # Action Buttons
    # ────────────────────────────────────────────────────────────────────────
    def action_set_available(self):
        self.write({'status': 'available'})

    def action_set_lost(self):
        self.write({'status': 'lost'})

    def action_dispose(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Dispose Asset'),
            'res_model': 'asset.dispose.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_asset_id': self.id},
        }

    def action_compute_depreciation(self):
        """Manually trigger depreciation recompute."""
        self._compute_current_value()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Depreciation Updated'),
                'message': _('Current value has been recalculated for all selected assets.'),
                'type': 'success',
                'sticky': False,
            },
        }

    def action_view_assignments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Assignments'),
            'res_model': 'asset.assignment',
            'view_mode': 'tree,form',
            'domain': [('asset_id', '=', self.id)],
            'context': {'default_asset_id': self.id},
        }

    def action_view_repairs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Repair Requests'),
            'res_model': 'asset.repair',
            'view_mode': 'tree,form',
            'domain': [('asset_id', '=', self.id)],
            'context': {'default_asset_id': self.id},
        }

    # ────────────────────────────────────────────────────────────────────────
    # Scheduled Action
    # ────────────────────────────────────────────────────────────────────────
    @api.model
    def cron_compute_depreciation(self):
        """Called by scheduled action to recompute depreciation for all assets."""
        assets = self.search([
            ('status', 'not in', ['disposed']),
            ('depreciation_rate', '>', 0),
        ])
        assets._compute_current_value()

