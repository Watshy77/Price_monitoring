from bs4 import BeautifulSoup
import requests, re, os
import matplotlib.pyplot as plt

BASE_URL = "https://books.toscrape.com/"

def fetch_books_data(category_url):
    def write_book_data(url, fichier_csv):
        url = url.replace("../", "")
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to fetch the book page {url}")
            return
        soup = BeautifulSoup(response.text, "html.parser")
        upc = soup.find("td").text.replace(",", " ")
        title = soup.find("h1").text.replace(",", " ")
        price_including_tax = soup.find_all("td")[3].text.replace(",", " ")
        price_excluding_tax = soup.find_all("td")[2].text.replace(",", " ")
        number_available = soup.find_all("td")[5].text.replace(",", " ")
        product_description = soup.find_all("p")[3].text.replace(",", " ")
        category = soup.find_all("a")[3].text.replace(",", " ")
        review_rating = soup.find("p", class_="star-rating")['class'][1].replace(",", " ")
        image_url = soup.find("img")['src'].replace("../", "")
        image_url = f"{BASE_URL}{image_url}"
        download_images(image_url, "IMAGES", title, category)
        fichier_csv.write(f"{url},{upc},{title},{price_including_tax},")
        fichier_csv.write(f"{price_excluding_tax},{number_available},{product_description},")
        fichier_csv.write(f"{category},{review_rating},{image_url}\n")
    
    def download_images(url, folder, image_name, category):
        image_name = image_name.replace("/", " ") + ".jpg"
        category_folder = os.path.join(folder, category)
        if not os.path.exists(category_folder):
            os.makedirs(category_folder)
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
    if match:
        csv_filename = f"{match.group()}.csv"
    else:
        csv_filename = "books.csv"

    csv_folder = "CSV"
    if not os.path.exists(csv_folder):
        os.makedirs(csv_folder)
    csv_filepath = os.path.join(csv_folder, csv_filename)
    with open(csv_filepath, mode='w', newline='', encoding='utf-8') as fichier_csv:
        fichier_csv.write("product_page_url,universal_product_code (upc),title,price_including_tax,")
        fichier_csv.write("price_excluding_tax,number_available,product_description,category,review_rating,image_url\n")
        for book in liste:
            write_book_data(f"{BASE_URL}catalogue/{book.h3.a['href']}", fichier_csv)
        
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
                    write_book_data(f"{BASE_URL}catalogue/{book.h3.a['href']}", fichier_csv)

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

def create_pie_chart():
    csv_folder = "CSV"
    category_counts = {}

    for csv_file in os.listdir(csv_folder):
        if csv_file.endswith(".csv"):
            category = csv_file.replace(".csv", "")
            total_stock = 0
            with open(os.path.join(csv_folder, csv_file), mode='r', encoding='utf-8') as file:
                lines = file.readlines()[1:]
                for line in lines:
                    if not line.strip():
                        continue
                    data = line.split(',')
                    if len(data) > 5:
                        stock = int(data[5].strip())
                    else:
                        print(f"Skipping line due to unexpected format: {line}")
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
    plt.show()

def create_bar_chart():
    csv_folder = "CSV"
    category_prices = {}

    for csv_file in os.listdir(csv_folder):
        if csv_file.endswith(".csv"):
            category = csv_file.replace(".csv", "")
            total_price = 0
            total_stock = 0
            with open(os.path.join(csv_folder, csv_file), mode='r', encoding='utf-8') as file:
                lines = file.readlines()[1:]
                for line in lines:
                    if not line.strip():
                        continue
                    data = line.split(',')
                    if len(data) > 5:
                        price_including_tax = float(data[3].replace('£', '').replace('Â', '').replace(',', '.').strip())
                        stock = int(data[5].strip())
                    else:
                        print(f"Skipping line due to unexpected format: {line}")
                        continue
                    total_price += price_including_tax * stock
                    total_stock += stock
            if total_stock > 0:
                category_prices[category] = total_price / total_stock

    categories = list(category_prices.keys())
    avg_prices = list(category_prices.values())

    plt.figure(figsize=(14, 8))
    plt.barh(categories, avg_prices, color='skyblue')
    plt.xlabel('Average Price (£)')
    plt.ylabel('Categories')
    plt.title('Average Book Price by Category (Weighted by Stock)')
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    fetch_all_categories()
    create_pie_chart()
    create_bar_chart()