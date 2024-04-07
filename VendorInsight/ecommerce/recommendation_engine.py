from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from .models import Product
import numpy as np


def get_product_features():
    products = Product.objects.all()
    features = []
    for product in products:
        # Combine textual data and normalize price
        feature = f"{product.name} {product.description} {product.categories.all()} {product.average_sentiment()}"
        features.append(feature)
    return features, [product.id for product in products]


def recommend_products(product_id, num_recommendations=5):
    features, product_ids = get_product_features()
    vectorizer = TfidfVectorizer(stop_words='english')
    feature_matrix = vectorizer.fit_transform(features)
    product_idx = product_ids.index(product_id)
    cosine_similarities = cosine_similarity(
        feature_matrix[product_idx:product_idx+1], feature_matrix).flatten()
    related_product_indices = cosine_similarities.argsort(
    )[-num_recommendations-1:-1][::-1]

    # Exclude the product itself
    recommended_product_ids = [product_ids[i]
                               for i in related_product_indices if i != product_idx]
    return Product.objects.filter(id__in=recommended_product_ids)
