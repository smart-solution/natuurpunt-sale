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
from openerp import netsvc



class sale_order(osv.osv):
    _inherit = "sale.order"

    _columns = {
	'cancel_reason_id': fields.many2one('sale.order.cancel.reason', 'Reden annulatie'),
	'has_deposit': fields.boolean('Borg'),
	'deposit_amount': fields.float('Borg bedrag'),
	'deposit_credit_note_id': fields.many2one('account.invoice', 'Borg Credit Nota'),
        'state': fields.selection([
            ('draft', 'Draft Quotation'),
            ('sent', 'Quotation Sent'),
            ('cancel', 'Cancelled'),
            ('waiting_date', 'Waiting Schedule'),
            ('progress', 'Sales Order'),
            ('manual', 'Sale to Invoice'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done'),
	    ('closed', 'Gesloten'),
            ], 'Status', readonly=True, track_visibility='onchange',
            help="Gives the status of the quotation or sales order. \nThe exception status is automatically set when a cancel operation occurs in the processing of a document linked to the sales order. \nThe 'Waiting Schedule' status is set when the invoice is confirmed but waiting for the scheduler to run on the order date.", select=True),

    } 

    def action_force_close(self, cr, uid, ids, context=None):
	self.write(cr, uid, ids, {'state':'closed'})
	return True	

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

    def write(self, cr, uid, ids, vals, context=None):
		
        res = super(sale_order, self).write(cr, uid, ids, vals, context=context)

        if 'user_id' in vals:
            so = self.browse(cr, uid, ids)[0]
	    line_ids = [l.id for l in so.order_line]
	    self.pool.get('sale.order.line').write(cr, uid, line_ids, {'user_id':vals['user_id']})

        return res

    def copy(self, cr, uid, id, default=None, context=None):
        res = super(sale_order, self).copy(cr, uid, id, default=default, context=context)
	print "RES:",res

	so = self.browse(cr, uid, res)
	line_ids = [l.id for l in so.order_line]
	self.pool.get('sale.order.line').write(cr, uid, line_ids, {'delivered_flag':False,'delivered_qty':0})

	return res

    def deposit_create(self, cr, uid, ids, context=None):

	Invoice = self.pool.get('account.invoice')
	InvoiceLine = self.pool.get('account.invoice.line')
	Account = self.pool.get('account.account')
	wf_service = netsvc.LocalService('workflow')

	order = self.browse(cr, uid, ids)[0]

        if context is None:
            context = {}
        journal_ids = self.pool.get('account.journal').search(cr, uid,
            [('type', '=', 'sale_refund'), ('company_id', '=', order.company_id.id)],
            limit=4)
        if not journal_ids:
            raise osv.except_osv(_('Error!'),
                _('Please define sales journal for this company: "%s" (id:%d).') % (order.company_id.name, order.company_id.id))

	invoice_vals = {
	    'name': order.client_order_ref or '',
	    'origin': order.name,
	    'type': 'out_refund',
	    'reference': order.client_order_ref or order.name,
	    'account_id': order.partner_id.property_account_receivable.id,
	    'partner_id': order.partner_invoice_id.id,
	    'journal_id': journal_ids[1],
	    'currency_id': order.pricelist_id.currency_id.id,
	    'comment': order.note,
	    'payment_term': order.payment_term and order.payment_term.id or False,
	    'fiscal_position': order.fiscal_position.id or order.partner_id.property_account_position.id,
	    'date_invoice': context.get('date_invoice', False),
	    'company_id': order.company_id.id,
	    'user_id': order.user_id and order.user_id.id or False
	}

	invoice_id = Invoice.create(cr, uid, invoice_vals)

        account_id = Account.search(cr, uid, [('code','=','404002')])

	line_vals = {
	    'name': 'Borg',
	    'invoice_id': invoice_id,
	    'price_unit': order.deposit_amount,
	    'product_uom_qty': 1,
	    'account_id': account_id[0],
	}
	InvoiceLine.create(cr, uid, line_vals)	

	order.write({'deposit_credit_note_id': invoice_id})

	flag = True
        for line in order.order_line:
            if not line.invoiced:
                flag = False
                break
        if flag:
            order.write({'state': 'done'})
            wf_service.trg_validate(uid, 'sale.order', order.id, 'all_lines', cr)

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


class sale_order_line(osv.osv):
    _inherit = "sale.order.line"


    def create(self, cr, uid, vals, context=None):

        if 'price_unit' in vals and vals['price_unit'] < 0:
	    raise osv.except_osv(_('Minus Price'),_("Minus values are not allowed for the price"))

        return super(sale_order_line, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):

        if 'price_unit' in vals and vals['price_unit'] < 0:
	    raise osv.except_osv(_('Minus Price'),_("Minus values are not allowed for the price"))

        return super(sale_order_line, self).write(cr, uid, ids, vals, context=context)

    def copy(self, cr, uid, id, default=None, context=None):
        default['delivered_flag'] = False
        default['delivered_qty'] = False
        default['delivered_text'] = False
        return super(sale_order_line, self).copy(cr, uid, id, default=default, context=context)


class sale_order_line_make_invoice(osv.osv_memory):

    _inherit="sale.order.line.make.invoice"

    def make_invoices(self, cr, uid, ids, context=None):
        """
             To make invoices.

             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param ids: the ID or list of IDs
             @param context: A standard dictionary

             @return: A dictionary which of fields with values.

        """
        if context is None: context = {}
        res = False
        invoices = {}

        def make_invoice(order, lines):
            """
                 To make invoices.

                 @param order:
                 @param lines:

                 @return:

            """
            inv = self._prepare_invoice(cr, uid, order, lines)
            inv_id = self.pool.get('account.invoice').create(cr, uid, inv)
            return inv_id

        sales_order_line_obj = self.pool.get('sale.order.line')
        sales_order_obj = self.pool.get('sale.order')
        wf_service = netsvc.LocalService('workflow')
        wizard = self.browse(cr, uid ,ids)[0]
        for line in sales_order_line_obj.browse(cr, uid, context.get('active_ids', []), context=context):
            if (not line.invoiced) and (line.state not in ('draft', 'cancel')):
                if not line.order_id in invoices:
                    invoices[line.order_id] = []
                print "1"
                context['use_delivered_qty'] = wizard.use_delivered_qty
                line_id = sales_order_line_obj.invoice_line_create(cr, uid, [line.id], context=context)
                for lid in line_id:
                    invoices[line.order_id].append(lid)
        for order, il in invoices.items():
            res = make_invoice(order, il)
            cr.execute('INSERT INTO sale_order_invoice_rel \
                    (order_id,invoice_id) values (%s,%s)', (order.id, res))
            flag = True
            data_sale = sales_order_obj.browse(cr, uid, order.id, context=context)
            for line in data_sale.order_line:
                if not line.invoiced:
                    flag = False
                    break
            if flag and data_sale.deposit_credit_note_id:
                line.order_id.write({'state': 'done'})
                wf_service.trg_validate(uid, 'sale.order', order.id, 'all_lines', cr)

        if not invoices:
            raise osv.except_osv(_('Warning!'), _('Invoice cannot be created for this Sales Order Line due to one of the following reasons:\n1.The state of this sales order line is either "draft" or "cancel"!\n2.The Sales Order Line is Invoiced!'))
        if context.get('open_invoices', False):
            return self.open_invoices(cr, uid, ids, res, context=context)

        # Copy line and change quantities
        if line.delivered_qty < line.product_uom_qty:
            dif_qty = line.product_uom_qty - line.delivered_qty
            newline = sales_order_line_obj.copy(cr, uid, line.id, {
                'product_uom_qty':dif_qty,
                'delivered_qty': 0,
                'delivered_flag': False,
                'delivered_text': "",
		'state': 'confirmed',
            })
            sales_order_line_obj.write(cr, uid, [line.id], {'product_uom_qty':line.delivered_qty, 'state':'done'})
            sales_order_line_obj.write(cr, uid, [newline], {'state':'confirmed'})

        if line.delivered_qty == line.product_uom_qty:
            sales_order_line_obj.write(cr, uid, [line.id], {'state':'done'})

        return {'type': 'ir.actions.act_window_close'}





# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
