Odoo to Hatchbuck CRM
=====================

[![Build Status](https://travis-ci.com/vshn/odoo2hatchbuck.svg?branch=master)](https://travis-ci.com/vshn/odoo2hatchbuck)

This application will sync Odoo ERP customer contacts to Hatchbuck CRM

## Configuration

For local development I use an =.env= file to configure the environment variables:
```
ODOO_HOST=odoo.example.com
ODOO_DB=myodoodatabasename
ODOO_USERNAME=myusername
ODOO_PASSWORD=mypassword
HATCHBUCK_APIKEY=ABC123DEF456
SENTRY_DSN=https://<key>@sentry.io/<project> (optional)
EMPLOYEE_COMPANYNAME="Example Company Inc"
```
