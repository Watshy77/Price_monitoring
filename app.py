from bs4 import BeautifulSoup
import requests, sys

BASE_URL = "https://books.toscrape.com/"

def fetch_books_data(category_url):
    url = f"{BASE_URL}{category_url}"
    response = requests.get(url)

    if response.status_code != 200:
        print("Failed to fetch the page")

    soup = BeautifulSoup(response.text, "html.parser")
    liste = soup.find("ol", class_="row").find_all("li")

    csv_filename = category_url.replace("/", "_") + ".csv"
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as fichier_csv:
        fichier_csv.write("product_page_url,universal_product_code (upc),title,price_including_tax,")
        fichier_csv.write("price_excluding_tax,number_available,product_description,category,review_rating,image_url\n")
        for book in liste:
            product_page_url = book.h3.a['href'].replace('../../../', BASE_URL+'catalogue/')
            response = requests.get(product_page_url)
            if response.status_code != 200:
                print(f"Failed to fetch the book page {product_page_url}")
                continue
            soup = BeautifulSoup(response.text, "html.parser")
            upc = soup.find("td").text.replace(",", " ")
            title = soup.find("h1").text.replace(",", " ")
            price_including_tax = soup.find_all("td")[3].text.replace(",", " ")
            price_excluding_tax = soup.find_all("td")[2].text.replace(",", " ")
            number_available = soup.find_all("td")[5].text.replace(",", " ")
            product_description = soup.find_all("p")[3].text.replace(",", " ")
            category = soup.find_all("a")[3].text.replace(",", " ")
            review_rating = soup.find("p", class_="star-rating")['class'][1].replace(",", " ")
            image_url = soup.find("img")['src'].replace(",", " ")
            fichier_csv.write(f"{product_page_url},{upc},{title},{price_including_tax},")
            fichier_csv.write(f"{price_excluding_tax},{number_available},{product_description},")
            fichier_csv.write(f"{category},{review_rating},{image_url}\n")

    print(f"Successfully fetched and saved to {csv_filename}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python app.py <category_url>")
        sys.exit(1)
    
    category_url = " ".join(sys.argv[1:])
    fetch_books_data(category_url)