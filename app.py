import os
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from pyhtml2pdf import converter

def download_wayback_page(url):
    wayback_url = f'http://archive.org/wayback/available?url={url}'
    response = requests.get(wayback_url)
    if response.status_code == 200:
        data = response.json()
        if 'archived_snapshots' in data and 'closest' in data['archived_snapshots'] and data['archived_snapshots']['closest']['available']:
            snapshot_url = data['archived_snapshots']['closest']['url']
            page_response = requests.get(snapshot_url)
            if page_response.status_code == 200:
                return page_response.text
    return None

def convert_to_pdf(html_file_path, pdf_file_path):
    # Ensure the HTML file path is absolute
    absolute_html_path = os.path.abspath(html_file_path)

    # Convert the HTML file to a PDF file
    converter.convert(f'file:///{absolute_html_path}', pdf_file_path)

    print(f"PDF saved to {pdf_file_path}")


def update_image_sources(html_content, base_wayback_url):
    soup = BeautifulSoup(html_content, 'html.parser')
    images = soup.find_all('img')
    for img in images:
        original_src = img.get('src')
        if original_src:
            archived_src = f'{base_wayback_url}/{original_src}'
            img['src'] = archived_src
    return str(soup)

def download_pages(urls, directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    for index, url in enumerate(urls):
        print(f"Downloading {url}...")
        html_content = download_wayback_page(url)
        if html_content:
            base_wayback_url = html_content.split('/web/')[0]
            updated_html_content = update_image_sources(html_content, base_wayback_url)

            # Extract a distinctive name from the URL
            url_parts = url.split('/')
            file_name_core = url_parts[-2] if url.endswith('/') else url_parts[-1]
            file_name_core = re.sub(r'\W+', '_', file_name_core)  # Replace non-word characters with underscore

            file_name = f"{file_name_core}.html"
            file_path = os.path.join(directory, file_name)

            # Ensure unique filenames by appending an index if the file already exists
            counter = 1
            while os.path.exists(file_path):
                file_name = f"{file_name_core}_{counter}.html"
                file_path = os.path.join(directory, file_name)
                counter += 1

            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(updated_html_content)
            print(f"Page with updated images downloaded successfully to {file_path}.")

            # Convert to PDF
            convert_to_pdf(updated_html_content, file_path)
            print(f"Converted to PDF: {file_path.replace('.html', '.pdf')}")

        else:
            print("Failed to download the page. The Wayback Machine may not have archived snapshots for the given URL.")

if __name__ == "__main__":
    urls = [
        'https://growingdata.com.au/a-guided-introduction-to-exploratory-data-analysis-eda-using-python/',
        'https://growingdata.com.au/automated-ai-approaches-to-clinical-coding-a-case-study/',
        'https://growingdata.com.au/data-engineering-with-sql-server-integration-services-ssis/',
        'https://growingdata.com.au/online-learning-the-challenging-data-frontier/',
        'https://growingdata.com.au/data-quality-management-for-machine-learning-quality-monitoring/',
        'https://growingdata.com.au/machine-learning-models-debugging-testing-1-2/'
    ]
    directory = 'downloaded_articles'
    download_pages(urls, directory)
