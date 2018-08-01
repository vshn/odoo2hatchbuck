"""
Sync Odoo contacts to Hatchbuck CRM
"""

import logging
import os
import odoorpc
from dotenv import load_dotenv  # pylint: disable=import-error

LOGFORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


def main():
    """
    Fetch Odoo ERP customer info
    """

    logging.basicConfig(level=logging.DEBUG, format=LOGFORMAT)

    odoo = odoorpc.ODOO(
        os.environ.get('ODOO_HOST'),
        protocol='jsonrpc+ssl',
        port=443
    )
    odoodb = os.environ.get('ODOO_DB', False)
    if not odoodb:
        # if the DB is not configured pick the first in the list
        # this takes another round-trip to the API
        odoodbs = odoo.db.list()
        odoodb = odoodbs[0]

    odoo.login(
        odoodb,
        os.environ.get('ODOO_USERNAME'),
        os.environ.get('ODOO_PASSWORD')
    )

    logging.debug(odoo.env)

    #  these are examples from the tutorial
    # user = odoo.env.user
    # print(user.name)            # name of the user connected
    # print(user.company_id.name) # the name of its company
    #  Simple 'raw' query
    # user_data = odoo.execute('res.users', 'read', [user.id])
    # print(user_data)

    partnerenv = odoo.env['res.partner']
    # search for all partners that are customers AND companies
    partner_ids = partnerenv.search(
        [
            ('customer', '=', True),
            ('is_company', '=', True)
        ]
    )

    # logging.debug(partner_ids)
    for pid in partner_ids:
        for partner in partnerenv.browse(pid):
            # browse() is similar to a database result set/pointer
            # it should be able to take a list of IDs
            # but it timeouted for my largish list of IDs
            for child in partner.child_ids:
                # child = person/contact in a company

                # Available fields:
                #     __last_update
                #     active
                #     bank_ids
                #     birthdate
                #     calendar_last_notif_ack
                #     category_id
                #     child_ids
                #     city
                #     color
                #     comment
                #     commercial_partner_id
                #     company_id
                #     contact_address
                #     contract_ids
                #     contracts_count
                #     country_id
                #     create_date
                #     create_uid
                #     credit
                #     credit_limit
                #     customer
                #     date
                #     debit
                #     debit_limit
                #     display_name
                #     ean13
                #     email
                #     employee
                #     fax
                #     function
                #     has_image
                #     image
                #     image_medium
                #     image_small
                #     invoice_ids
                #     is_company
                #     journal_item_count
                #     lang
                #     last_reconciliation_date
                #     meeting_count
                #     meeting_ids
                #     message_follower_ids
                #     message_ids
                #     message_is_follower
                #     message_last_post
                #     message_summary
                #     message_unread
                #     mobile
                #     name
                #     notify_email
                #     opportunity_count
                #     opportunity_ids
                #     opt_out
                #     parent_id
                #     parent_name
                #     phone
                #     phonecall_count
                #     phonecall_ids
                #     property_account_payable
                #     property_account_position
                #     property_account_receivable
                #     property_delivery_carrier
                #     property_payment_term
                #     property_product_pricelist
                #     property_product_pricelist_purchase
                #     property_stock_customer
                #     property_stock_supplier
                #     property_supplier_payment_term
                #     purchase_order_count
                #     ref
                #     ref_companies
                #     sale_order_count
                #     sale_order_ids
                #     section_id
                #     signup_expiration
                #     signup_token
                #     signup_type
                #     signup_url
                #     signup_valid
                #     state_id
                #     street
                #     street2
                #     supplier
                #     supplier_invoice_count
                #     task_count
                #     task_ids
                #     title
                #     total_invoiced
                #     type
                #     tz
                #     tz_offset
                #     use_parent_address
                #     user_id
                #     user_ids
                #     vat
                #     vat_subjected
                #     website
                #     write_date
                #     write_uid
                #     zip

                logging.debug(
                    (
                        child.name,
                        child.title.name,
                        child.function,
                        # child.parent_id.name,
                        child.parent_name,
                        child.email,
                        child.mobile,
                        child.phone,
                        [cat.name for cat in child.category_id],
                        child.opt_out,
                        child.lang,
                        child.street,
                        child.street2,
                        child.zip,
                        child.city,
                        child.country_id.name,
                        child.total_invoiced,
                        child.website,
                        child.comment,
                    )
                )

                # for field in child._columns:
                #     logging.debug((field,getattr(child, field)))
                # for category in child.category_id:
                #     logging.debug(category.name)


if __name__ == "__main__":
    # load settings from .env for development
    load_dotenv()
    main()
