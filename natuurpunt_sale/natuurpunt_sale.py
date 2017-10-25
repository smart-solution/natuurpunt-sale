# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp


class sale_order(osv.osv):
    _inherit = "sale.order"

    _columns = {
	'cancel_reason_id': fields.many2one('sale.order.cancel.reason', 'Reden annulatie'),
	'has_deposit': fields.boolean('Borg'),
	'deposit_amount': fields.float('Borg bedrag'),
    } 

    def action_wait(self, cr, uid, ids, context=None):
        context = context or {}
        for o in self.browse(cr, uid, ids):
            if not o.order_line:
                raise osv.except_osv(_('Error!'),_('You cannot confirm a sales order which has no line.'))
            noprod = self.test_no_product(cr, uid, o, context)
            self.write(cr, uid, [o.id], {'state': 'progress', 'date_confirm': fields.date.context_today(self, cr, uid, context=context)})
            self.pool.get('sale.order.line').button_confirm(cr, uid, [x.id for x in o.order_line])
        return True

    def in_progress(self, cr, uid, ids, context=None):
        for order_id in ids:
            self.write(cr, uid, [order_id], {'state':'manual'})
#            for line_id in self.pool.get('purchase.order.line').search(cr, uid, [('order_id','=',order_id)]):
#                self.pool.get('purchase.order.line').write(cr, uid, [line_id], {'state':'done'})
        return True

class sale_order_add_line(osv.osv_memory):
    _name = 'sale.order.add.line'

    def _get_uom_id(self, cr, uid, *args):
        try:
            proxy = self.pool.get('ir.model.data')
            result = proxy.get_object_reference(cr, uid, 'product', 'product_uom_unit')
            return result[1]
        except Exception, ex:
            return False

    def onchange_product_id(self, cr, uid, ids, product, context=None):
	print "PRODUCT:",product
        result = {}
	prod = self.pool.get('product.product').browse(cr, uid, product)
	tax_ids = [t.id for t in prod.taxes_id]
	result['name'] = prod.name
	result['price_unit'] = prod.list_price
	result['tax_id'] = [(6,0,tax_ids)]

        return {'value': result}


    _columns = {
	'name': fields.char('Description', required=True),
	'product_id': fields.many2one('product.product', 'Product'),
	'analytic_dimension_1_id': fields.many2one('account.analytic.account', 'Dimensie 1'),	
	'analytic_dimension_2_id': fields.many2one('account.analytic.account', 'Dimensie 2'),	
	'analytic_dimension_3_id': fields.many2one('account.analytic.account', 'Dimensie 3'),	
        'analytic_dimension_1_required': fields.boolean("Analytic Dimension 1 Required"),
        'analytic_dimension_2_required': fields.boolean("Analytic Dimension 2 Required"),
        'analytic_dimension_3_required': fields.boolean("Analytic Dimension 3 Required"),
        'product_uom_qty': fields.float('Quantity', digits_compute= dp.get_precision('Product UoS'), required=True),
        'product_uom': fields.many2one('product.uom', 'Unit of Measure ', required=True),
        'tax_id': fields.many2many('account.tax', 'sale_order_tax', 'order_line_id', 'tax_id', 'Taxes'),
        'price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Product Price')),
	'state': fields.selection([
            ('draft', 'Draft Quotation'),
            ('sent', 'Quotation Sent'),
            ('cancel', 'Cancelled'),
            ('waiting_date', 'Waiting Schedule'),
            ('progress', 'Sales Order'),
            ('manual', 'Sale to Invoice'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done'),
            ], 'Status'),
	'order_id': fields.many2one('sale.order', 'Order'),
    }

    _defaults = {
	'state': 'draft',
	'product_uom' : _get_uom_id,
	'product_uom_qty': 1,
    }

    def order_add_line(self, cr, uid, ids, context=None):
	"""
	Create order line from wizard
	"""

	wiz = self.browse(cr, uid, ids[0])
	print "WIZ TAX:", wiz.tax_id

	tax_ids = [t.id for t in wiz.tax_id]

	line_vals = {
	    'name': wiz.name,
	    'product_id': wiz.product_id.id,
	    'analytic_dimension_1_id': wiz.analytic_dimension_1_id.id,
	    'analytic_dimension_2_id': wiz.analytic_dimension_2_id.id,
	    'analytic_dimension_3_id': wiz.analytic_dimension_3_id.id,
	    'product_uom_qty': wiz.product_uom_qty,
	    'product_uom': wiz.product_uom.id,
	    'tax_id': [(6,0,tax_ids)],
	    'price_unit': wiz.price_unit,
	    'order_id': wiz.order_id.id,
	    'state': 'confirmed',
	}

	self.pool.get('sale.order.line').create(cr, uid, line_vals)

	return True


class sale_order_cancel_reason(osv.osv):
    _name = 'sale.order.cancel.reason'

    _columns = {
         'name': fields.char('Reden', size=128, required=True),
    }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
