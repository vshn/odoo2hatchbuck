"""
Sync Odoo contacts to Hatchbuck CRM
"""

import argparse
import logging
import os
import re

import odoorpc
from dotenv import load_dotenv
from hatchbuck import Hatchbuck

# pylint: disable=too-many-locals
# pylint: disable=too-many-branches
# pylint: disable=too-many-statements
# pylint: disable=too-many-nested-blocks

LOGFORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def split_name(fullname):
    """
    Heuristics to split "Firstname Lastname"
    """
    parts = fullname.strip().split(" ")
    if len(parts) < 2:
        # oops, no first/lastname
        first, last = ("", parts[0])
    elif len(parts) == 2:
        # the trivial case
        first, last = (parts[0], parts[1])
    else:
        # "jean marc de fleurier" -> "jean marc", "de fleurier"
        if parts[-2].lower() in ["van", "von", "de", "zu", "da"]:
            first, last = (" ".join(parts[:-2]), " ".join(parts[-2:]))
        else:
            first, last = (" ".join(parts[:-1]), " ".join(parts[-1:]))
    return first, last


def parse_arguments():
    """Parse arguments from command line"""
    parser = argparse.ArgumentParser(
        description="sync Odoo contacts into Hatchbuck.com CRM"
    )
    parser.add_argument(
        "-n",
        "--noop",
        help="dont actually post anything to hatchbuck,"
        " just log what would have been posted",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="set logging to debug",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-c", "--company", help="filter for company name", default=False
    )
    args_parser = parser.parse_args()
    return args_parser


def main(noop=False, company=False, verbose=False):
    """
    Fetch Odoo ERP customer info
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG, format=LOGFORMAT)
    else:
        logging.basicConfig(level=logging.INFO, format=LOGFORMAT)
    hatchbuck = Hatchbuck(os.environ.get("HATCHBUCK_APIKEY"), noop=noop)

    odoo = odoorpc.ODOO(os.environ.get("ODOO_HOST"), protocol="jsonrpc+ssl", port=443)
    odoodb = os.environ.get("ODOO_DB", False)
    if not odoodb:
        # if the DB is not configured pick the first in the list
        # this takes another round-trip to the API
        odoodbs = odoo.db.list()
        odoodb = odoodbs[0]

    odoo.login(odoodb, os.environ.get("ODOO_USERNAME"), os.environ.get("ODOO_PASSWORD"))

    logging.debug(odoo.env)

    #  these are examples from the tutorial
    # user = odoo.env.user
    # print(user.name)            # name of the user connected
    # print(user.company_id.name) # the name of its company
    #  Simple 'raw' query
    # user_data = odoo.execute('res.users', 'read', [user.id])
    # print(user_data)

    partnerenv = odoo.env["res.partner"]
    # search for all partners that are customers AND companies
    odoo_filter = [("customer", "=", True), ("is_company", "=", True)]
    # optionally filter partner company name, mostly used for debugging
    if company:
        odoo_filter.append(("name", "ilike", company))
    partner_ids = partnerenv.search(odoo_filter)

    # logging.debug(partner_ids)
    for pid in partner_ids:
        for partner in partnerenv.browse(pid):
            # browse() is similar to a database result set/pointer
            # it should be able to take a list of IDs
            # but it timeouted for my largish list of IDs

            partner_turnover = str(round(partner.total_invoiced))
            # looking at
            # https://github.com
            # /odoo/odoo/blob/master/addons/account/models/partner.py#L260
            # this uses account.invoice.report in the background and returns 0
            # if the user does not have access to it
            # permission: "Accounting & Finance": "Invoicing & Payments"

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

                logging.info(
                    (
                        child.name,  # vorname nachname
                        # child.title.name,  # titel ("Dr.")
                        # child.function,  # "DevOps Engineer"
                        # child.parent_id.invoice_ids.amount_total,
                        partner.name,  # Firmenname
                        # child.email,
                        # child.mobile,
                        # child.phone,
                        [cat.name for cat in child.category_id],
                        # child.opt_out,
                        # child.lang,
                        # child.street,
                        # child.street2,
                        # child.zip,
                        # child.city,
                        # child.country_id.name,
                        # child.total_invoiced,
                        # child.invoice_ids.amount_total,
                        # partner.total_invoiced,
                        # partner_turnover,
                        # child.website,
                        # child.comment,
                    )
                )
                categories = [cat.name for cat in child.category_id]

                if not child.email:
                    logging.error("no email found for contact")
                else:
                    emails = child.email.replace("mailto:", "")
                    emails = [x.strip() for x in emails.split(",")]
                    profile = hatchbuck.search_email_multi(emails)
                    if profile is None:
                        logging.debug("user not found in CRM")
                        if (
                            "Customer" not in categories
                            and "Opportunity" not in categories
                            and "Partner" not in categories
                        ):
                            # don't add administrative contacts to CRM
                            logging.info(
                                "not adding contact because no relevant category"
                            )
                            continue

                        # create profile
                        profile = dict()
                        firstname, lastname = split_name(child.name)
                        profile["firstName"] = firstname
                        profile["lastName"] = lastname
                        profile["subscribed"] = True
                        profile["status"] = {"name": "Customer"}
                        profile["emails"] = []
                        for addr in emails:
                            profile["emails"].append({"address": addr, "type": "Work"})
                        profile = hatchbuck.create(profile)
                        logging.info("added profile: %s", profile)
                        if profile is None:
                            logging.error("adding contact failed: %s", profile)
                            os._exit(1)
                    else:
                        logging.info("contact found: %s", profile)

                    if "Customer" in categories:
                        if noop:
                            profile["status"] = "Customer"
                        else:
                            profile = hatchbuck.update(
                                profile["contactId"], {"status": "Customer"}
                            )
                    elif "Opportunity" in categories:
                        if noop:
                            profile["status"] = "Opportunity"
                        else:
                            profile = hatchbuck.update(
                                profile["contactId"], {"status": "Opportunity"}
                            )
                    elif "Partner" in categories:
                        if noop:
                            profile["status"] = "Partner"
                        else:
                            profile = hatchbuck.update(
                                profile["contactId"], {"status": "Partner"}
                            )
                    else:
                        pass

                    logging.info(
                        "contact has category vip %s and tag %s",
                        "VIP" in categories,
                        hatchbuck.profile_contains(profile, "tags", "name", "VIP"),
                    )

                    if "VIP" in categories and not hatchbuck.profile_contains(
                        profile, "tags", "name", "VIP"
                    ):
                        logging.info("adding VIP tag")
                        hatchbuck.add_tag(profile["contactId"], "VIP")

                    if "VIP" not in categories and hatchbuck.profile_contains(
                        profile, "tags", "name", "VIP"
                    ):
                        logging.info("removing VIP tag")
                        hatchbuck.remove_tag(profile["contactId"], "VIP")

                    if child.opt_out:
                        hatchbuck.update(profile["contactId"], {"subscribed": False})

                    # update profile with information from odoo
                    if profile.get("firstName", "") == "":
                        firstname, _ = split_name(child.name)
                        profile = hatchbuck.profile_add(
                            profile, "firstName", None, firstname
                        )

                    if profile.get("lastName", "") == "":
                        _, lastname = split_name(child.name)
                        profile = hatchbuck.profile_add(
                            profile, "lastName", None, lastname
                        )

                    for addr in emails:
                        profile = hatchbuck.profile_add(
                            profile, "emails", "address", addr, {"type": "Work"}
                        )

                    if profile.get("title", "") == "" and child.function:
                        profile = hatchbuck.profile_add(
                            profile, "title", None, child.function
                        )

                    if profile.get("company", "") == "" and child.parent_name:
                        profile = hatchbuck.profile_add(
                            profile, "company", None, child.parent_name
                        )

                    if profile.get("company", "") == "":
                        # empty company name ->
                        # maybe we can guess the company name
                        #  from the email address?
                        # logging.warning("empty company with emails: {0}".
                        #                format(profile['emails']))
                        pass

                    # clean up company name
                    if re.match(r";$", profile.get("company", "")):
                        logging.warning(
                            "found unclean company name: %s", format(profile["company"])
                        )

                    if re.match(r"\|", profile.get("company", "")):
                        logging.warning(
                            "found unclean company name: %s", format(profile["company"])
                        )

                    # Add address
                    address = {
                        "street": child.street,
                        "zip_code": child.zip,
                        "city": child.city,
                        "country": child.country_id.name,
                    }

                    kind = "Work"
                    logging.debug("adding address %s %s", address, profile)
                    profile = hatchbuck.profile_add_address(profile, address, kind)

                    # # Add website field to Hatchbuck Contact
                    if child.website:
                        profile = hatchbuck.profile_add(
                            profile, "website", "websiteUrl", child.website
                        )

                    # Add phones and mobile fields to Hatchbuck Contact
                    if child.phone:
                        profile = hatchbuck.profile_add(
                            profile, "phones", "number", child.phone, {"type": "Work"}
                        )

                    if child.mobile:
                        profile = hatchbuck.profile_add(
                            profile,
                            "phones",
                            "number",
                            child.mobile,
                            {"type": "Mobile"},
                        )

                    # Add customFields(comment, amount_total, lang) to
                    #  Hatchbuck Contact
                    if child.comment:
                        profile = hatchbuck.profile_add(
                            profile,
                            "customFields",
                            "value",
                            child.comment,
                            {"name": "Comments"},
                        )

                    profile = hatchbuck.profile_add(
                        profile,
                        "customFields",
                        "value",
                        child.lang,
                        {"name": "Language"},
                    )

                    profile = hatchbuck.profile_add(
                        profile,
                        "customFields",
                        "value",
                        partner_turnover,
                        {"name": "Invoiced"},
                    )

                    # Add ERP tag to Hatchbuck Contact
                    if not hatchbuck.profile_contains(profile, "tags", "name", "ERP"):
                        hatchbuck.add_tag(profile["contactId"], "ERP")


if __name__ == "__main__":
    # load settings from .env for development
    load_dotenv()
    ARG = parse_arguments()
    main(noop=ARG.noop, company=ARG.company, verbose=ARG.verbose)
