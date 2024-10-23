from bs4 import BeautifulSoup
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import requests, re, os, io, csv
import matplotlib.pyplot as plt

BASE_URL = "https://books.toscrape.com/"

def fetch_books_data(category_url):
    def write_book_data(url, writer):
        url = url.replace("../", "")
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to fetch the book page {url}")
            return
        soup = BeautifulSoup(response.text, "html.parser")
        data = {
            "upc": soup.find("td").text.replace(",", " "),
            "title": soup.find("h1").text.replace(",", " "),
            "price_including_tax": soup.find_all("td")[3].text.replace(",", " "),
            "price_excluding_tax": soup.find_all("td")[2].text.replace(",", " "),
            "number_available": soup.find_all("td")[5].text.replace(",", " "),
            "product_description": soup.find_all("p")[3].text.replace(",", " "),
            "category": soup.find_all("a")[3].text.replace(",", " "),
            "review_rating": soup.find("p", class_="star-rating")['class'][1].replace(",", " "),
            "image_url": f"{BASE_URL}{soup.find('img')['src'].replace('../', '')}"
        }
        download_images(data["image_url"], "IMAGES", data["title"], data["category"])
        writer.writerow([url, data["upc"], data["title"], data["price_including_tax"],
                         data["price_excluding_tax"], data["number_available"], data["product_description"],
                         data["category"], data["review_rating"], data["image_url"]])

    def download_images(url, folder, image_name, category):
        image_name = image_name.replace("/", " ") + ".jpg"
        category_folder = os.path.join(folder, category)
        os.makedirs(category_folder, exist_ok=True)
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to fetch the image {url}")
            return
        image_path = os.path.join(category_folder, image_name)
        with open(image_path, mode='wb') as image_file:
            image_file.write(response.content)
        print(f"Successfully downloaded the image {image_name} in category {category}")

    url = f"{BASE_URL}{category_url}"
    response = requests.get(url)
    if response.status_code != 200:
        print("Failed to fetch the page")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    liste = soup.find("ol", class_="row").find_all("li")
    numbers_books = int(soup.find("form", class_="form-horizontal").find("strong").text)

    match = re.search(r'(?<=/books/)[^/_]+', category_url)
    csv_filename = f"{match.group()}.csv" if match else "books.csv"

    csv_folder = "CSV"
    os.makedirs(csv_folder, exist_ok=True)
    csv_filepath = os.path.join(csv_folder, csv_filename)
    with open(csv_filepath, mode='w', newline='', encoding='utf-8') as fichier_csv:
        writer = csv.writer(fichier_csv)
        writer.writerow(["product_page_url", "universal_product_code (upc)", "title", "price_including_tax",
                         "price_excluding_tax", "number_available", "product_description", "category", "review_rating", "image_url"])
        for book in liste:
            write_book_data(f"{BASE_URL}catalogue/{book.h3.a['href']}", writer)
        
        if numbers_books > 20:
            for page in range(2, int(numbers_books)//20 + 2):
                category_url = category_url.replace("index.html", "")
                url = f"{BASE_URL}{category_url}/page-{page}.html"
                response = requests.get(url)
                if response.status_code != 200:
                    print(f"Failed to fetch the page {url}")
                    continue
                soup = BeautifulSoup(response.text, "html.parser")
                liste = soup.find("ol", class_="row").find_all("li")
                for book in liste:
                    write_book_data(f"{BASE_URL}catalogue/{book.h3.a['href']}", writer)

    print(f"Successfully fetched books data for this category")
    print(f"------------------------------------------------------------------------------------------------------------")

def fetch_all_categories():
    response = requests.get(BASE_URL)
    if response.status_code != 200:
        print("Failed to fetch the page")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    categories = soup.find("ul", class_="nav-list").find_all("li")

    for item in categories:
        category_name = item.a.text.strip()
        if category_name.lower() == "books":
            continue
        category_url = item.a['href']
        print(f"Fetching books for category: {category_name}")
        fetch_books_data(category_url)

def create_pdf_report():
    pdf_filename = "rapport_prix_livres.pdf"
    c = canvas.Canvas(pdf_filename, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 20)
    c.drawString(100, height - 50, "Rapport des prix des livres d'occasion")

    c.setFont("Helvetica", 12)
    c.drawString(100, height - 80, "Ce diagramme circulaire montre la répartition des livres par catégorie.")

    pie_chart_io = io.BytesIO()
    plt.figure(figsize=(12, 8))
    csv_folder = "CSV"
    category_counts = {}

    for csv_file in os.listdir(csv_folder):
        if csv_file.endswith(".csv"):
            category = csv_file.replace(".csv", "")
            total_stock = 0
            with open(os.path.join(csv_folder, csv_file), mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)
                for row in reader:
                    if len(row) > 5:
                        stock = int(row[5].strip())
                    else:
                        print(f"Skipping line due to unexpected format: {row}")
                        continue
                    total_stock += stock
            category_counts[category] = total_stock

    categories = list(category_counts.keys())
    counts = list(category_counts.values())

    plt.figure(figsize=(12, 8))
    wedges, texts, autotexts = plt.pie(counts, labels=categories, autopct='%1.1f%%', startangle=140, textprops=dict(color="w"))

    for text in texts:
        text.set_fontsize(10)
    for autotext in autotexts:
        autotext.set_fontsize(8)

    plt.legend(wedges, categories, title="Categories", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), ncol=2)
    plt.title('Distribution of Books by Category (Weighted by Stock)')
    plt.axis('equal')
    plt.subplots_adjust(right=0.7)
    plt.savefig(pie_chart_io, format='png')
    pie_chart_io.seek(0)
    pie_chart_image = ImageReader(pie_chart_io)
    c.drawImage(pie_chart_image, 100, height - 450, width=400, height=300)
    plt.close()

    c.setFont("Helvetica", 12)
    c.drawString(100, height - 470, "Ce graphique en barres montre le prix moyen des livres par catégorie.")

    bar_chart_io = io.BytesIO()
    plt.figure(figsize=(14, 8))
    category_prices = {}

    for csv_file in os.listdir(csv_folder):
        if csv_file.endswith(".csv"):
            category = csv_file.replace(".csv", "")
            total_price = 0
            total_stock = 0
            with open(os.path.join(csv_folder, csv_file), mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)
                for row in reader:
                    if len(row) > 5:
                        price_including_tax = float(row[3].replace('£', '').replace('Â', '').replace(',', '.').strip())
                        stock = int(row[5].strip())
                    else:
                        print(f"Skipping line due to unexpected format: {row}")
                        continue
                    total_price += price_including_tax * stock
                    total_stock += stock
            if total_stock > 0:
                category_prices[category] = total_price / total_stock

    categories = list(category_prices.keys())
    avg_prices = list(category_prices.values())

    plt.barh(categories, avg_prices, color='skyblue')
    plt.xlabel('Average Price (£)')
    plt.ylabel('Categories')
    plt.title('Average Book Price by Category (Weighted by Stock)')
    plt.tight_layout()
    plt.savefig(bar_chart_io, format='png')
    bar_chart_io.seek(0)
    bar_chart_image = ImageReader(bar_chart_io)
    c.drawImage(bar_chart_image, 100, height - 800, width=400, height=300)
    plt.close()

    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 820, "Statistiques clés:")

    total_price = 0
    total_books = 0
    category_counts = {}
    category_prices = {}

    for csv_file in os.listdir(csv_folder):
        if csv_file.endswith(".csv"):
            category = csv_file.replace(".csv", "")
            total_stock = 0
            total_category_price = 0
            with open(os.path.join(csv_folder, csv_file), mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)
                for row in reader:
                    if len(row) > 5:
                        price_including_tax = float(row[3].replace('£', '').replace('Â', '').replace(',', '.').strip())
                        stock = int(row[5].strip())
                    else:
                        continue
                    total_price += price_including_tax * stock
                    total_books += stock
                    total_category_price += price_including_tax * stock
                    total_stock += stock
            if total_stock > 0:
                category_counts[category] = total_stock
                category_prices[category] = total_category_price / total_stock

    avg_price = total_price / total_books if total_books > 0 else 0
    most_represented_category = max(category_counts, key=category_counts.get)
    most_expensive_category = max(category_prices, key=category_prices.get)

    c.setFont("Helvetica", 12)
    c.drawString(100, height - 840, f"Prix moyen global des livres: £{avg_price:.2f}")
    c.drawString(100, height - 860, f"Catégorie la plus représentée: {most_represented_category}")
    c.drawString(100, height - 880, f"Catégorie la plus chère: {most_expensive_category}")

    c.save()
    print(f"PDF report created: {pdf_filename}")

if __name__ == "__main__":
    fetch_all_categories()
    create_pdf_report()