import scrapy
import re

class JumboSpider(scrapy.Spider):
    name = "jumbo"
    allowed_domains = ["jumbo.tn"]
    start_urls = ["https://jumbo.tn/23-informatique",
                  "https://jumbo.tn/59-gaming",
                   "https://jumbo.tn/25-telephonie-objets-connectes",
                   "https://jumbo.tn/502-electromenager",
                   "https://jumbo.tn/513-son-image",
                   "https://jumbo.tn/80-maison-connectee",
                   "https://jumbo.tn/655-reseau-connectiques",
                   "https://jumbo.tn/53-beaute-forme-et-sante",
                   "https://jumbo.tn/421-bricolage",
                   "https://jumbo.tn/55-loisirs",
                   "https://jumbo.tn/668-maison-brico",]

    def parse(self, response):
        products = response.css("div[data-elementor-type='product-miniature']")

        for product in products:
            # Produit URL
            product_url = product.css("div.ce-product-image a::attr(href)").get(default="").strip()

            # Extraire catégorie depuis l’URL du produit
            category = ""
            match = re.search(r"jumbo\.tn/([^/]+)/", product_url)
            if match:
                category = match.group(1).replace("-", " ").strip()

            # Extraire la marque depuis l’URL (type: /14_asus)
            brand_link = product.css("div.elementor-widget-manufacturer-image a::attr(href)").get()
            brand = ""
            if brand_link:
                match = re.search(r"/\d+_([a-z0-9\-]+)", brand_link)
                if match:
                    brand = match.group(1).replace("-", " ").strip()

            # Disponibilité
            availability = product.css("span.ce-product-stock__availability-label::text").get(default="").strip()

            # Générer l’objet final
            yield {
                "title": product.css("h3.ce-product-name a::text").get(default="").strip(),
                "price": product.css("div.ce-product-price span::text").get(default="").strip(),
                "product_url": product_url,
                "image_url": product.css("div.ce-product-image img::attr(src)").get(default="").strip(),
                "availability": availability,
                "reference": product.css("span.ce-product-meta__value::text").get(default="").strip(),
                "category": category,
                "brand": brand,
            }

        # Pagination automatique
        next_page = response.css("a.next.js-search-link::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
            
    


