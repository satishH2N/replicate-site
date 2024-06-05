import logging
import requests
from jinja2 import Environment, FileSystemLoader
import os
import azure.functions as func
import json


# Load data from language.json
with open('language.json', 'r') as f:
    data = json.load(f)

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'jp-connect-site-utils', 'locale-to-store-map.json')
    try:
        with open(config_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Failed to load config: {e}")
        raise

def get_route_params(req: func.HttpRequest):
    webAlias = req.route_params.get('webAlias')
    country = req.route_params.get('country', 'us')
    language = req.route_params.get('language', 'en')
    return webAlias, country, language

def redirect_to_juiceplus():
    return func.HttpResponse(
        "Redirecting to juiceplus.com",
        status_code=302,
        headers={'Location': 'https://www.juiceplus.com'}
    )

def get_partner_details(webAlias):
    api_url = "https://jp-connect-apim.azure-api.net/jp-connect-func/getPartnerForWebAlias"
    params = {
        'subscription-key': '1cb9afd163b64ae9890d8b499e133855',
        'webAlias': webAlias
    }
    response = requests.get(api_url, params=params)
    if response.status_code != 200:
        logging.error(f"Failed to get partner details: {response.status_code} - {response.text}")
        raise Exception("Failed to get partner details")
    return response.json()

def get_store_url(config, country, language):
    for store in config['stores']:
        if store['country'] == country and store['language'] == language:
            return store['store']
    raise Exception("Store not found for the given country and language")

def render_template(partner_details, country, language, store_url, stores):
    pname = partner_details['FirstName']+" "+partner_details['LastName']
    template_dir = os.path.join(os.path.dirname(__file__), '..', 'jp-connect-site-utils')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('partner_site_template.html')
    shop_now_url = f"{store_url}?commSysPartnerID={partner_details['commSysPartnerID']}"
    
    return template.render(partner=partner_details, country=country, language=language, store_url=store_url, shop_now_url=shop_now_url, stores=stores,pname=pname,  **data[language])

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        logging.info('Processing a request.')

        logging.info('Getting Route Params')
        webAlias, country, language = get_route_params(req)
        logging.info(f'webAlias: {webAlias}, country: {country}, language: {language}')

        if not webAlias:
            return redirect_to_juiceplus()

        logging.info('Getting Partner Details')
        partner_details = get_partner_details(webAlias)
        print(partner_details)
        logging.info(f'partner_details: {partner_details}')

        logging.info('Loading Config')
        config = load_config()

        logging.info('Getting Store URL from config')
        store_url = get_store_url(config, country, language)

        logging.info('Updating Template')
        # html_content = render_template(partner_details, country, language, store_url, config['stores'])
        html_content = render_template(partner_details, country, language, store_url, config['stores'])

        logging.info('Returning Response of rendered template')
        return func.HttpResponse(
            html_content,
            mimetype="text/html",
            status_code=200
        )
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return func.HttpResponse(
            "An error occurred while processing your request.",
            status_code=500
        )
