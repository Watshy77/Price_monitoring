from bs4 import BeautifulSoup
import requests, sys, re, os

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

if __name__ == "__main__":
    fetch_all_categories()