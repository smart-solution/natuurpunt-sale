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
from natuurpunt_tools import compose
from functools import partial

class sale_order(osv.osv):
    _inherit = "sale.order"

    _columns = {
        'cancel_reason_id': fields.many2one('sale.order.cancel.reason', 'Reden annulatie'),
        'cancel_reason': fields.text('Cancel Reason'),
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
            ('paid', 'Betaald'),
            ], 'Status', readonly=True, track_visibility='onchange',
            help="", select=True),
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

    def action_done(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'paid'}, context=context)

    def in_progress(self, cr, uid, ids, context=None):
        for order_id in ids:
            self.write(cr, uid, [order_id], {'state':'manual'})
        return True

    def write(self, cr, uid, ids, vals, context=None):
        if 'user_id' in vals:
            so = self.browse(cr, uid, ids)[0]
            line_ids = [l.id for l in so.order_line]
            self.pool.get('sale.order.line').write(cr, uid, line_ids, {'user_id':vals['user_id']})

        if 'state' in vals:
            so = self.browse(cr, uid, ids)[0]
            line_ids = [l.id for l in so.order_line]

            if vals['state'] == 'sent':
                self.pool.get('sale.order.line').write(cr, uid, line_ids, {'state':'sent'})

            if vals['state'] == 'manual' or vals['state'] == 'closed':
                line_state = vals['state']
                for line in self.pool.get('sale.order.line').browse(cr, uid, line_ids):
                    if line.state in ['confirmed','manual']:
                        self.pool.get('sale.order.line').write(cr, uid, line.id, {'state':line_state})
                    if line.state == 'paid' and vals['state'] == 'closed':
                        vals['state'] = 'paid'

        return super(sale_order, self).write(cr, uid, ids, vals, context=context)

    def copy(self, cr, uid, id, default=None, context=None):
        res = super(sale_order, self).copy(cr, uid, id, default=default, context=context)
        so = self.browse(cr, uid, res)
        line_ids = [l.id for l in so.order_line]
        self.pool.get('sale.order.line').write(cr, uid, line_ids, {'delivered_flag':False,'delivered_qty':0})
        return res

    def test_state(self, cr, uid, ids, mode, *args):
        """
        override this function from sale_stock that
        will set all lines to done from workflow
        our last state is paid or closed so we need to
        handle it our self
        """
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
        sale_order = self.pool.get('sale.order').browse(cr, uid, wiz.order_id.id)
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
            'state': sale_order.state,
        }
        self.pool.get('sale.order.line').create(cr, uid, line_vals)
        return True

class sale_order_cancel_reason(osv.osv):
    _name = 'sale.order.cancel.reason'

    _columns = {
         'name': fields.char('Reden', size=128, required=True),
    }

class sale_invoice(osv.osv):
    _name = 'sale.invoice'

    _columns = {
        'order_id': fields.many2one('sale.order', 'sale order', select=True),
        'invoice_id': fields.many2one('account.invoice', 'sale invoice', select=True),
        'state':  fields.selection([
           ('open', 'Open'),
           ('done', 'Done'),
           ('cancel','Cancel'),
        ], 'Status'),
    }

    _defaults = {
        'state': 'open',
    }

    def action_sale_invoiced(self, cr, uid, ids, context=None):
        sale_invoice = self.browse(cr,uid,ids,context=context)
        return sale_invoice[0].invoice_id.id

    def action_invoice_end(self, cr, uid, ids, context=None):
        return self.write(cr,uid,ids,{'state':'done'})

    def action_invoice_except(self, cr, uid, ids, context=None):
        return self.write(cr,uid,ids,{'state':'cancel'})

    def action_invoice_cancel(self, cr, uid, ids, context=None):
        so_line_obj = self.pool.get('sale.order.line')
        sale_invoice = self.browse(cr,uid,ids,context=context)
        if sale_invoice[0].invoice_id.internal_number == False:
            order_id = sale_invoice[0].order_id.id
            so_line_ids = []
            for line in sale_invoice[0].invoice_id.invoice_line:
                so_line_ids += so_line_obj.search(cr, uid, [('invoice_line_id','=',line.id)])
            self.pool.get('sale.order').write(cr, uid, [order_id], {'state':'progress'})
            return so_line_obj.write(cr, uid, so_line_ids, {'state':'confirmed'})
        else:
            return True

    def action_done(self, cr, uid, ids, context=None):
        so_line_obj = self.pool.get('sale.order.line')
        sale_invoice = self.browse(cr,uid,ids,context=context)
        order_id = sale_invoice[0].order_id.id
        so_line_ids = []
        for line in sale_invoice[0].invoice_id.invoice_line:
            so_line_ids += so_line_obj.search(cr, uid, [('invoice_line_id','=',line.id)])
        domain = [('order_id','=',order_id),('state','not in',['paid','closed']),('id','not in',so_line_ids)]
        # inform sale_order that invoicing is complete
        if not so_line_obj.search(cr,uid,domain):
            wf_service = netsvc.LocalService('workflow')
            wf_service.trg_validate(uid, 'sale.order', order_id, 'all_lines', cr)
        # paid must be after the workflow because 'all_lines' will force the orderlines to done
        return so_line_obj.write(cr, uid, so_line_ids, {'state':'paid'})

class sale_order_line(osv.osv):
    _inherit = "sale.order.line"

    _columns = {
         'uitvoering_jaar': fields.char('Uitvoering Jaar', size=4),
         'facturatie_jaar': fields.char('Facturatie Jaar', size=4),
         'state': fields.selection([('cancel', 'Cancelled'),('draft', 'Draft'),('confirmed', 'Confirmed'),('sent','Verstuurd'),('manual', 'In uitvoering'),('closed', 'Gesloten'),('exception', 'Exception'),('done', 'Done'),('paid','Betaald')], 'Status', required=True, readonly=True,help=''),
         'invoice_line_id': fields.many2one('account.invoice.line', 'Invoice Line'),
    }

    def action_force_close(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'closed'})
        line = self.browse(cr, uid, ids)[0]
        order = line.order_id
        states = {'done':1,'paid':2,'closed':2}
        state = compose(
            partial(map,lambda line:(states[line.state] if line.state in states else 0,line.state)),
            sorted,
            min)(order.order_line)
        # write of sale.order takes care of closed/paid as they are equal in weight 
        return self.pool.get('sale.order').write(cr, uid, [order.id], {'state':state[1]}) if state[0] else True

    def create(self, cr, uid, vals, context=None):
        if 'price_unit' in vals and vals['price_unit'] < 0:
            raise osv.except_osv(_('Minus Price'),_("Minus values are not allowed for the price"))
        if 'product_uom_qty' in vals and vals['product_uom_qty'] < 0:
            raise osv.except_osv(_('Minus Qty'),_("Minus quantities are not allowed"))

        return super(sale_order_line, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if 'price_unit' in vals and vals['price_unit'] < 0:
            raise osv.except_osv(_('Minus Price'),_("Minus values are not allowed for the price"))
        if 'product_uom_qty' in vals and vals['product_uom_qty'] < 0:
            raise osv.except_osv(_('Minus Qty'),_("Minus quantities are not allowed"))

        return super(sale_order_line, self).write(cr, uid, ids, vals, context=context)

    def copy(self, cr, uid, id, default=None, context=None):
        default['delivered_flag'] = False
        default['delivered_qty'] = False
        default['delivered_text'] = False
        default['invoice_line_id'] = False
        return super(sale_order_line, self).copy(cr, uid, id, default=default, context=context)

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        result = super(sale_order_line, self).default_get(cr, uid, fields, context=context)

       # Copy the values of the last created line
        if 'order_id' in context and context['order_id']:
            lines = self.pool.get('sale.order').read(cr, uid, context['order_id'], ['order_line'])['order_line']
            if lines:
                line = self.pool.get('sale.order.line').browse(cr, uid, max(lines))
                result['analytic_dimension_1_id'] = line.analytic_dimension_1_id.id
                result['analytic_dimension_2_id'] = line.analytic_dimension_2_id.id
                result['analytic_dimension_3_id'] = line.analytic_dimension_3_id.id
        return result

    def product_uom_change(self, cursor, user, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, context=None):
        """
        set flag = True, keep name from input
        """
        context = context or {}
        lang = lang or ('lang' in context and context['lang'])
        if not uom:
            return {'value': {'price_unit': 0.0, 'product_uom' : uom or False}}
        return self.product_id_change(cursor, user, ids, pricelist, product,
                qty=qty, uom=uom, qty_uos=qty_uos, uos=uos, name=name,
                partner_id=partner_id, lang=lang, update_tax=update_tax,
                date_order=date_order, flag=True, context=context)

class sale_order_line_make_invoice(osv.osv_memory):

    _inherit="sale.order.line.make.invoice"

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        """
             custom default journal_id
        """
        res = super(sale_order_line_make_invoice, self)._prepare_invoice(cr, uid, order, lines, context=context)
        journal_ids = self.pool.get('account.journal').search(cr, uid, [('code','=','VF')])
        if journal_ids:
            res['journal_id'] = journal_ids[0]
        return res

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
        context = context or {}
        invoices = {}
        sales_order_line_obj = self.pool.get('sale.order.line')
        wf_service = netsvc.LocalService('workflow')

        for line in sales_order_line_obj.browse(cr, uid, context.get('active_ids', []), context=context):
            order = line.order_id
            if line.invoiced:
                warn = _('Invoice cannot be created for Sales Order {}. A Sales Order Line is already invoiced!').format(order.name)
                raise osv.except_osv(_('Warning!'), warn)
            if line.delivered_qty == 0 or line.delivered_flag == False:
                warn = _('Invoice cannot be created for Sales Order {}. A Sales Order Line is not ready for invoice!').format(order.name)
                raise osv.except_osv(_('Warning!'), warn)
            dif_qty = line.product_uom_qty - line.delivered_qty
            original_line_state = line.state
            if dif_qty < 0:
                sales_order_line_obj.write(cr, uid, [line.id], {'state':'done'})
                context['use_delivered_qty'] = True
            else:
                sales_order_line_obj.write(cr, uid, [line.id], {'product_uom_qty':line.delivered_qty, 'state':'done'})
                context['use_delivered_qty'] = False
            if not order in invoices:
                invoices[order] = []
            inv_line_id = sales_order_line_obj.invoice_line_create(cr, uid, [line.id], context=context)
            sales_order_line_obj.write(cr, uid, [line.id], {'invoice_line_id':inv_line_id[0]})
            invoices[order].append((inv_line_id[0],line.id))

            if dif_qty > 0:
                newline = sales_order_line_obj.copy(cr, uid, line.id, {
                   'product_uom_qty':dif_qty,
                   'delivered_qty': 0,
                   'delivered_flag': False,
                   'delivered_text': '',
                })
                sales_order_line_obj.write(cr, uid, [newline], {'state':original_line_state})

        for order, lines in invoices.items():
            inv_lines = [i[0] for i in lines]
            so_lines = [i[1] for i in lines]
            inv = self._prepare_invoice(cr, uid, order, inv_lines)
            inv_id = self.pool.get('account.invoice').create(cr, uid, inv)
            cr.execute('INSERT INTO sale_order_invoice_rel \
                    (order_id,invoice_id) values (%s,%s)', (order.id, inv_id))
            sale_invoice_vals = {
                'order_id': order.id,
                'invoice_id': inv_id,
            }
            order_done = compose(
                partial(map,lambda l:False if l.state in ['manual','confirmed'] and l.id not in so_lines else True),
                sorted,
                min)(order.order_line)
            # sale.order is done if no lines exists before the done state ( manual, confirmed )
            order.write({'state':'done'}) if order_done else True
            sale_invoice_id = self.pool.get('sale.invoice').create(cr,uid,sale_invoice_vals)
            wf_service.trg_validate(uid, 'sale.invoice', sale_invoice_id, 'sale_invoiced', cr)

        if context.get('open_invoices', False):
            return self.open_invoices(cr, uid, ids, inv_id, context=context)
        else:
            return {'type': 'ir.actions.act_window_close'}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
